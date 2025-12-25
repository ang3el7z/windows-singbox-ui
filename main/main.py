"""Главный файл приложения SingBox-UI"""
import sys
import subprocess
import ctypes
import os
import zipfile
import shutil
import tempfile
import time
import atexit
from pathlib import Path
from typing import Optional


def get_version() -> str:
    """
    Читает версию из файла .version
    Сначала пытается прочитать из data/.version (для собранного приложения),
    затем из корневого .version (для разработки)
    """
    # Определяем корневую папку
    if getattr(sys, 'frozen', False):
        # В собранном приложении
        exe_path = Path(sys.executable)
        if exe_path.parent.name == '_internal':
            root = exe_path.parent.parent
        else:
            root = exe_path.parent
        # Пробуем data/.version
        data_version = root / "data" / ".version"
        if data_version.exists():
            try:
                version = data_version.read_text(encoding="utf-8").strip()
                if version:
                    return version
            except Exception:
                pass
    else:
        # В режиме разработки
        root = Path(__file__).parent.parent
    
    # Пробуем корневой .version
    root_version = root / ".version"
    if root_version.exists():
        try:
            version = root_version.read_text(encoding="utf-8").strip()
            if version:
                return version
        except Exception:
            pass
    
    # Fallback на дефолтную версию
    return "1.0.0"


__version__ = get_version()  # Версия приложения

# Глобальный mutex для единственного экземпляра (охватывает admin / non-admin)
GLOBAL_MUTEX_HANDLE = None


def create_global_mutex():
    """
    Создает глобальный mutex, доступный между сессиями (Global\\).
    Возвращает (handle, already_exists: bool)
    """
    global GLOBAL_MUTEX_HANDLE
    if sys.platform != "win32":
        return None, False
    try:
        kernel32 = ctypes.windll.kernel32
        mutex_name = "Global\\SingBox-UI-Instance"
        handle = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        GLOBAL_MUTEX_HANDLE = handle
        already_exists = last_error == 183  # ERROR_ALREADY_EXISTS
        return handle, already_exists
    except Exception:
        return None, False


def release_global_mutex():
    """Закрывает дескриптор глобального mutex"""
    global GLOBAL_MUTEX_HANDLE
    if GLOBAL_MUTEX_HANDLE:
        try:
            ctypes.windll.kernel32.CloseHandle(GLOBAL_MUTEX_HANDLE)
        except Exception:
            pass
        GLOBAL_MUTEX_HANDLE = None


def cleanup_single_instance(server_name: str, local_server: 'QLocalServer | None'):
    """Освобождает локальный сервер и глобальный mutex"""
    try:
        if local_server:
            local_server.close()
        QLocalServer.removeServer(server_name)
    except Exception:
        pass
    release_global_mutex()

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QTextEdit, QStackedWidget,
    QSpinBox, QCheckBox, QDialog, QProgressBar,
    QLineEdit, QSystemTrayIcon, QMenu, QAction, QComboBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QByteArray
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from utils.icon_helper import icon

# Импорты новых UI компонентов
from ui.widgets import CardWidget, NavButton, TitleBar
from ui.styles import StyleSheet, theme
from ui.tray_manager import TrayManager
from ui.dialogs.info_dialog import show_info_dialog
from ui.dialogs.confirm_dialog import show_confirm_dialog
from ui.dialogs.input_dialog import show_input_dialog
from ui.dialogs.add_subscription_dialog import show_add_subscription_dialog

# Импорты из архитектуры проекта
from config.paths import (
    ensure_dirs, CORE_EXE, CONFIG_FILE, LOG_FILE, CORE_DIR
)
from managers.settings import SettingsManager
from managers.subscriptions import SubscriptionManager
from managers.log_ui_manager import LogUIManager
from utils.i18n import tr, set_language, get_available_languages, get_language_name, Translator
from utils.singbox import get_singbox_version, get_latest_version, compare_versions, get_app_latest_version
from core.downloader import DownloadThread
from core.deep_link_handler import DeepLinkHandler
from core.protocol import register_protocols, is_admin
from core.restart_manager import restart_application
from core.singbox_manager import StartSingBoxThread
from workers.init_worker import InitOperationsWorker
from workers.version_worker import CheckVersionWorker, CheckAppVersionWorker
from ui.dialogs.language_dialog import show_language_selection_dialog
from ui.dialogs.confirm_dialog import show_restart_admin_dialog, show_kill_all_confirm_dialog
from ui.dialogs.info_dialog import show_kill_all_success_dialog
import requests
from datetime import datetime
from utils.logger import log_to_file, set_main_window
from utils.icon_manager import get_icon, set_window_icon


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        # Сначала создаем папки
        ensure_dirs()
        
        # Фреймлесс-режим, чтобы отрисовывать собственный статус-бар
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        
        # Инициализируем менеджеры
        self.settings = SettingsManager()
        self.subs = SubscriptionManager()
        
        # Инициализируем менеджеры UI
        self.tray_manager = TrayManager(self)
        self.log_ui_manager = LogUIManager(self)
        self.deep_link_handler = DeepLinkHandler(self)
        
        
        # Локальный сервер будет установлен из main() после создания окна
        if not hasattr(self, "local_server"):
            self.local_server = None
        self._pending_args = []
        # Подключение newConnection настраивается в main при передаче сервера
        
        # Проверяем, выбран ли язык (первый запуск)
        language = self.settings.get("language", "")
        if not language or language == "":
            # Первый запуск - показываем диалог выбора языка
            # Сначала устанавливаем английский для отображения диалога
            set_language("en")
            # Показываем диалог выбора языка
            language = show_language_selection_dialog(self)
            # Сохраняем выбранный язык
            self.settings.set("language", language)
            self.settings.save()
        
        # Устанавливаем выбранный язык
        set_language(language)

        self.proc: subprocess.Popen | None = None
        self.current_sub_index: int = -1  # -1 означает что профиль не выбран
        self.running_sub_index: int = -1  # Индекс запущенного профиля (-1 если не запущен)
        self.cached_latest_version = None  # Кэш последней версии
        self.version_check_failed_count = 0  # Счетчик неудачных проверок
        self.version_check_retry_timer = None  # Таймер для повторных попыток проверки версии
        self.version_check_retry_delay = 5 * 60 * 1000  # Начальная задержка: 5 минут
        self.version_checked = False  # Флаг: была ли проверка версии выполнена в этой сессии
        self.app_version = __version__  # Версия приложения
        self.cached_app_latest_version = None  # Кэш последней версии приложения
        self.app_update_checked = False  # Флаг: была ли проверка обновлений приложения выполнена
        self.version_click_count = 0  # Счетчик кликов по версии для дебаг меню

        self.setWindowTitle(tr("app.title"))
        self.setMinimumSize(420, 780)
        self.setMaximumSize(420, 780)

        # Устанавливаем иконку окна через IconManager
        set_window_icon(self)

        central = QWidget()
        self.setCentralWidget(central)
        # Устанавливаем фон центрального виджета
        from ui.styles import theme
        central.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.get_color('background_primary')};
            }}
        """)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Собственный статус-бар в стиле приложения
        self.title_bar = TitleBar(self)
        root.addWidget(self.title_bar)

        # Стек страниц
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        from ui.pages import ProfilePage, HomePage, SettingsPage
        self.page_profile = ProfilePage(self)
        self.page_home = HomePage(self)
        self.page_settings = SettingsPage(self)
        self.stack.addWidget(self.page_profile)
        self.stack.addWidget(self.page_home)
        self.stack.addWidget(self.page_settings)

        # По умолчанию открываем home (индекс 1)
        self.stack.setCurrentIndex(1)
        
        # Нижняя навигация
        nav = QWidget()
        nav.setObjectName("nav")
        nav.setMinimumHeight(80)
        nav.setMaximumHeight(120)
        nav.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        
        # Используем новый компонент NavButton
        self.btn_nav_profile = NavButton(tr("nav.profile"), "mdi.account")
        self.btn_nav_home = NavButton(tr("nav.home"), "mdi.home")
        self.btn_nav_settings = NavButton(tr("nav.settings"), "mdi.cog")

        for i, btn in enumerate([self.btn_nav_profile, self.btn_nav_home, self.btn_nav_settings]):
            btn.clicked.connect(lambda _, idx=i: self.switch_page(idx))
            nav_layout.addWidget(btn, 1)

        self.btn_nav_home.setChecked(True)

        # Используем новый стиль навигации
        nav.setStyleSheet(StyleSheet.navigation())

        root.addWidget(self.stack, 1)
        
        # Версия приложения над навигацией
        self.version_container = QWidget()
        self.version_container.setFixedHeight(30)
        version_layout = QHBoxLayout(self.version_container)
        version_layout.setContentsMargins(16, 0, 16, 0)
        version_layout.setAlignment(Qt.AlignCenter)
        
        self.lbl_app_version = QLabel()
        self.lbl_app_version.setFont(QFont("Segoe UI", 10))
        self.lbl_app_version.setStyleSheet(StyleSheet.label(variant="secondary", size="medium"))
        self.lbl_app_version.setAlignment(Qt.AlignCenter)
        self.lbl_app_version.setCursor(Qt.PointingHandCursor)
        self.lbl_app_version.mousePressEvent = self.on_version_clicked
        version_layout.addWidget(self.lbl_app_version)
        
        from ui.styles import theme
        self.version_container.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.get_color('background_primary')};
                border: none;
            }}
        """)
        
        root.addWidget(self.version_container)
        root.addWidget(nav)

        # Инициализация
        # Проверяем права администратора
        self.is_admin = is_admin()
        
        # Выносим тяжелые операции в потоки, чтобы не блокировать UI
        QTimer.singleShot(0, self._init_async_operations)
        
        # Обновляем UI элементы, которые не требуют данных
        if hasattr(self, 'page_home') and hasattr(self.page_home, 'lbl_admin_status'):
            self.update_admin_status_label()
        self.update_big_button_state()
        self.update_app_version_display()
    
    def _init_async_operations(self):
        """Инициализация тяжелых операций в фоновом потоке"""
        try:
            log_to_file("[Init] Начало асинхронной инициализации")
            running = self.proc and self.proc.poll() is None
            running_index = -1
            current_index = -1
            
            # Безопасная проверка наличия page_profile и sub_list
            if hasattr(self, 'page_profile'):
                if hasattr(self.page_profile, 'sub_list'):
                    if self.page_profile.sub_list.count() > 0:
                        if running:
                            running_index = self.running_sub_index
                        current_index = self.current_sub_index
            
            log_to_file(f"[Init] Индексы: running={running_index}, current={current_index}")
            
            self._init_thread = InitOperationsWorker(self.subs, self.settings, running_index, current_index)
            self._init_thread.subscriptions_loaded.connect(self._on_subscriptions_loaded)
            self._init_thread.version_checked.connect(self._on_version_checked)
            self._init_thread.profile_info_loaded.connect(self._on_profile_info_loaded)
            self._init_thread.cleanup_finished.connect(self._on_cleanup_finished)
            self._init_thread.start()
            log_to_file("[Init] InitOperationsWorker запущен")
            
            # Проверки версий в отдельном потоке
            QTimer.singleShot(1000, self._check_versions_async)
            QTimer.singleShot(2000, self._check_app_version_async)
            log_to_file("[Init] Таймеры проверки версий установлены")
        except Exception as e:
            import traceback
            error_msg = f"[Init Error] Ошибка в _init_async_operations: {e}\n{traceback.format_exc()}"
            log_to_file(error_msg)
    
    def _on_subscriptions_loaded(self, names):
        """Обработка загруженных подписок"""
        if hasattr(self, 'page_profile') and hasattr(self.page_profile, 'sub_list'):
            self.page_profile.refresh_subscriptions()
        if hasattr(self, 'update_big_button_state'):
            self.update_big_button_state()
    
    def _on_version_checked(self, version):
        """Обработка проверенной версии sing-box"""
        if not hasattr(self, 'page_home') or not hasattr(self.page_home, 'lbl_version'):
            return
        if version:
            self.page_home.lbl_version.setText(tr("home.installed", version=version))
            self.page_home.lbl_version.setStyleSheet(StyleSheet.label(variant="primary"))
            if hasattr(self.page_home, 'btn_version_warning'):
                self.page_home.btn_version_warning.hide()
        else:
            self.page_home.lbl_version.setText(tr("home.not_installed"))
            self.page_home.lbl_version.setStyleSheet(StyleSheet.label(variant="error"))
            if hasattr(self.page_home, 'lbl_update_info'):
                self.page_home.lbl_update_info.hide()
            if hasattr(self.page_home, 'btn_version_warning'):
                self.page_home.btn_version_warning.show()
            if hasattr(self.page_home, 'btn_version_update'):
                self.page_home.btn_version_update.hide()
    
    def _on_profile_info_loaded(self, data):
        """Обработка загруженной информации о профиле"""
        if not hasattr(self, 'page_home') or not hasattr(self.page_home, 'lbl_profile'):
            return
        running_sub = data.get('running_sub')
        selected_sub = data.get('selected_sub')
        
        from ui.styles import theme
        accent_color = theme.get_color('accent')
        profile_style = f"color: {accent_color}; background-color: transparent; border: none; padding: 0px; padding-left: 4px;"
        
        if running_sub and selected_sub:
            if self.running_sub_index == self.current_sub_index:
                self.page_home.lbl_profile.setText(tr("home.current_profile", name=running_sub.get("name", tr("profile.unknown"))))
                self.page_home.lbl_profile.setStyleSheet(profile_style)
            else:
                text = f"{tr('home.current_profile', name=running_sub.get('name', tr('profile.unknown')))}\n    {tr('home.selected_profile', name=selected_sub.get('name', tr('profile.unknown')))}"
                self.page_home.lbl_profile.setText(text)
                self.page_home.lbl_profile.setStyleSheet(profile_style)
                self.page_home.lbl_profile.setCursor(Qt.ArrowCursor)
        elif running_sub:
            self.page_home.lbl_profile.setText(tr("home.current_profile", name=running_sub.get("name", tr("profile.unknown"))))
            self.page_home.lbl_profile.setStyleSheet(profile_style)
            self.page_home.lbl_profile.setCursor(Qt.ArrowCursor)
        elif selected_sub:
            self.page_home.lbl_profile.setText(tr("home.selected_profile", name=selected_sub.get("name", tr("profile.unknown"))))
            self.page_home.lbl_profile.setStyleSheet(profile_style)
            self.page_home.lbl_profile.setCursor(Qt.ArrowCursor)
        else:
            from ui.styles import theme
            warning_color = theme.get_color('warning')
            self.page_home.lbl_profile.setText(tr("home.profile_not_selected_click"))
            self.page_home.lbl_profile.setStyleSheet(f"color: {warning_color}; background-color: transparent; border: none; padding: 0px;")
            self.page_home.lbl_profile.setCursor(Qt.PointingHandCursor)
            if not hasattr(self.page_home.lbl_profile, '_original_mousePressEvent'):
                self.page_home.lbl_profile._original_mousePressEvent = self.page_home.lbl_profile.mousePressEvent
            
            def handle_click(event):
                if event.button() == Qt.LeftButton:
                    self.switch_page(0)
                else:
                    if hasattr(self.page_home.lbl_profile, '_original_mousePressEvent') and self.page_home.lbl_profile._original_mousePressEvent:
                        self.page_home.lbl_profile._original_mousePressEvent(event)
            
            self.page_home.lbl_profile.mousePressEvent = handle_click
    
    def _on_cleanup_finished(self):
        """Очистка логов завершена"""
        pass
    
    def _check_versions_async(self):
        """Асинхронная проверка версий sing-box"""
        if hasattr(self, '_version_thread') and self._version_thread.isRunning():
            return
        
        self._version_thread = CheckVersionWorker()
        self._version_thread.version_info_ready.connect(self._on_version_info_ready)
        self._version_thread.start()
    
    def _on_version_info_ready(self, current_version, latest_version):
        """Обработка проверенных версий sing-box"""
        if not hasattr(self, 'page_home') or not hasattr(self.page_home, 'lbl_version'):
            return
        from ui.styles import theme
        if current_version:
            self.page_home.lbl_version.setText(tr("home.installed", version=current_version))
            accent_color = theme.get_color('accent')
            self.page_home.lbl_version.setStyleSheet(f"color: {accent_color}; background-color: transparent; border: none; padding: 0px;")
            if hasattr(self.page_home, 'btn_version_warning'):
                self.page_home.btn_version_warning.hide()
            
            if latest_version:
                self.cached_latest_version = latest_version
                self.version_checked = True
                self.version_check_failed_count = 0
                from utils.singbox import compare_versions
                comparison = compare_versions(current_version, latest_version)
                if comparison < 0:
                    if hasattr(self.page_home, 'lbl_update_info'):
                        self.page_home.lbl_update_info.setText(tr("home.update_available", version=latest_version))
                        self.page_home.lbl_update_info.show()
                        # Делаем текст кликабельным
                        if not hasattr(self.page_home.lbl_update_info, '_click_handler_set'):
                            def handle_update_click(event):
                                if event.button() == Qt.LeftButton:
                                    self.show_download_dialog()
                            self.page_home.lbl_update_info.mousePressEvent = handle_update_click
                            self.page_home.lbl_update_info._click_handler_set = True
                    if hasattr(self.page_home, 'btn_version_update'):
                        self.page_home.btn_version_update.hide()
                else:
                    if hasattr(self.page_home, 'lbl_update_info'):
                        self.page_home.lbl_update_info.hide()
                    if hasattr(self.page_home, 'btn_version_update'):
                        self.page_home.btn_version_update.hide()
        else:
            self.page_home.lbl_version.setText(tr("home.not_installed"))
            self.page_home.lbl_version.setStyleSheet(StyleSheet.label(variant="error"))
            if hasattr(self.page_home, 'lbl_update_info'):
                self.page_home.lbl_update_info.hide()
            if hasattr(self.page_home, 'btn_version_warning'):
                self.page_home.btn_version_warning.show()
            if hasattr(self.page_home, 'btn_version_update'):
                self.page_home.btn_version_update.hide()
    
    def _check_app_version_async(self):
        """Асинхронная проверка версии приложения"""
        if hasattr(self, '_app_version_thread') and self._app_version_thread.isRunning():
            return
        
        self._app_version_thread = CheckAppVersionWorker()
        self._app_version_thread.app_version_ready.connect(self._on_app_version_ready)
        self._app_version_thread.start()
    
    def _on_app_version_ready(self, latest_version):
        """Обработка проверенной версии приложения"""
        if latest_version:
            self.cached_app_latest_version = latest_version
            self.app_update_checked = True
            self.update_app_version_display()
        else:
            self.update_app_version_display()
        
        if hasattr(self, 'lbl_admin_status'):
            self.update_admin_status_label()
        self.update_big_button_state()

        # Обработка deep link (если передан URL как аргумент)
        self.handle_deep_link()
        
        # Автозапуск sing-box при запуске приложения
        if self.settings.get("auto_start_singbox", False):
            # Запускаем с небольшой задержкой, чтобы UI успел загрузиться
            QTimer.singleShot(500, self.start_singbox)
        
        # Инициализация системного трея
        # Настраиваем трей только если включена настройка
        if self.settings.get("minimize_to_tray", True):
            self.tray_manager.setup()
            if self.tray_manager.tray_icon:
                self.tray_manager.show()
        
        # Таймеры
        # Проверка версии только при запуске, не периодически
        self.update_info_timer = QTimer(self)
        self.update_info_timer.timeout.connect(self.update_profile_info)
        self.update_info_timer.start(5000)  # Обновление профиля каждые 5 секунд
        
        self.proc_timer = QTimer(self)
        self.proc_timer.timeout.connect(self.poll_process)
        self.proc_timer.start(700)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.auto_update_config)
        self.update_timer.start(self.settings.get("auto_update_minutes", 90) * 60 * 1000)
        
        # Таймер для ежесуточной очистки логов (проверка раз в час)
        self.log_cleanup_timer = QTimer(self)
        self.log_cleanup_timer.timeout.connect(self.cleanup_logs_if_needed)
        self.log_cleanup_timer.start(60 * 60 * 1000)  # Проверка каждый час
        
        # Таймер для обновления логов из файлов (если открыта страница настроек)
        self.logs_refresh_timer = QTimer(self)
        self.logs_refresh_timer.timeout.connect(self.refresh_logs_from_files)
        self.logs_refresh_timer.start(1000)  # Каждую секунду

        # Автозапуск
        if self.settings.get("start_with_windows", False):
            self.set_autostart(True)

    # Страницы перенесены в ui/pages/ - ProfilePage, HomePage, SettingsPage

    # Навигация
    def switch_page(self, index: int):
        """Переключение страниц"""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate([self.btn_nav_profile, self.btn_nav_home, self.btn_nav_settings]):
            btn.setChecked(i == index)
        if index == 2:  # Settings page
            # Обновляем видимость дебаг элементов при открытии страницы
            if hasattr(self, 'page_settings'):
                self.page_settings.update_debug_logs_visibility()

    # Подписки
    def refresh_subscriptions_ui(self):
        """Обновление списка подписок"""
        if hasattr(self, 'page_profile'):
            self.page_profile.refresh_subscriptions()

    def on_sub_changed(self, row: int):
        """Изменение выбранной подписки"""
        if not hasattr(self, 'page_profile') or not hasattr(self.page_profile, 'sub_list'):
            return
        # Проверяем, что список не пустой и индекс валидный
        if row < 0 or self.page_profile.sub_list.count() == 0:
            self.current_sub_index = -1
        else:
            self.current_sub_index = row
        self.update_profile_info()
        self.update_big_button_state()

    def on_add_sub(self):
        """Добавление подписки"""
        name, url, ok = show_add_subscription_dialog(self)
        if ok and name and url:
            # Сохраняем текущий выбранный профиль
            saved_index = self.current_sub_index
            self.subs.add(name, url)
            self.refresh_subscriptions_ui()
            # Восстанавливаем выбор профиля
            if hasattr(self, 'page_profile') and hasattr(self.page_profile, 'sub_list'):
                if saved_index >= 0 and saved_index < self.page_profile.sub_list.count():
                    self.page_profile.sub_list.setCurrentRow(saved_index)
                self.current_sub_index = saved_index
            self.log(tr("profile.added", name=name))

    def on_del_sub(self):
        """Удаление подписки"""
        if not hasattr(self, 'page_profile') or not hasattr(self.page_profile, 'sub_list'):
            return
        row = self.page_profile.sub_list.currentRow()
        if row < 0 or self.page_profile.sub_list.count() == 0:
            return
        if row >= self.page_profile.sub_list.count():
            return
        sub = self.subs.get(row)
        if not sub:
            return
        
        # Используем красивое диалоговое окно
        if show_kill_all_success_dialog(self, tr("profile.delete_question"),
                                        tr("profile.delete_confirm", name=sub['name'])):
            was_running = self.running_sub_index == row
            self.subs.remove(row)
            
            # Обновляем индексы если нужно
            if row < self.current_sub_index:
                self.current_sub_index -= 1
            elif row == self.current_sub_index:
                self.current_sub_index = -1
            
            if was_running:
                self.running_sub_index = -1
                # Если удалили запущенный профиль - останавливаем
                if self.proc and self.proc.poll() is None:
                    self.stop_singbox()
            
            self.refresh_subscriptions_ui()
            self.update_profile_info()
            self.update_big_button_state()
            self.log(tr("profile.removed", name=sub['name']))

    def on_rename_sub(self):
        """Переименование подписки"""
        if not hasattr(self, 'page_profile') or not hasattr(self.page_profile, 'sub_list'):
            return
        row = self.page_profile.sub_list.currentRow()
        if row < 0 or self.page_profile.sub_list.count() == 0:
            return
        if row >= self.page_profile.sub_list.count():
            return
        sub = self.subs.get(row)
        if not sub:
            return
        
        # Диалог для ввода нового имени
        new_name, ok = show_input_dialog(
            self,
            tr("profile.rename_subscription"),
            tr("profile.rename_confirm", name=sub['name']),
            text=sub['name']
        )
        
        if ok and new_name.strip():
            old_name = sub['name']
            sub['name'] = new_name.strip()
            self.subs.save()
            self.refresh_subscriptions_ui()
            # Восстанавливаем выбор
            if self.page_profile.sub_list.count() > 0 and 0 <= row < self.page_profile.sub_list.count():
                self.page_profile.sub_list.setCurrentRow(row)
                self.current_sub_index = row
            self.log(tr("profile.renamed", old_name=old_name, new_name=new_name.strip()))
    
    def on_test_sub(self):
        """Тест подписки"""
        if not hasattr(self, 'page_profile') or not hasattr(self.page_profile, 'sub_list'):
            return
        row = self.page_profile.sub_list.currentRow()
        if row < 0 or self.page_profile.sub_list.count() == 0:
            self.log(tr("profile.select_for_test"))
            return
        if row >= self.page_profile.sub_list.count():
            return
        
        # Получаем название подписки для отображения
        sub = self.subs.get(row)
        sub_name = sub.get("name", "Unknown") if sub else "Unknown"
        
        self.log(tr("profile.test_loading"))
        
        try:
            ok = self.subs.download_config(row)
            if ok:
                self.log(tr("profile.test_success"))
                # Показываем успешное сообщение
                show_info_dialog(
                    self,
                    tr("profile.test"),
                    f"{tr('profile.test_success')}\n\nSubscription '{sub_name}' works correctly. Config downloaded successfully.",
                    success=True
                )
            else:
                self.log(tr("profile.test_error"))
                # Показываем ошибку
                show_info_dialog(
                    self,
                    tr("profile.test"),
                    f"{tr('profile.test_error')}\n\nFailed to download config from subscription '{sub_name}'. Please check the URL."
                )
        finally:
            pass
    
    def _log_version_debug(self, msg: str):
        """Логирование версий в debug логи"""
        log_to_file(msg)
    
    
    # Версия и профиль
    def update_version_info(self):
        """Обновление информации о версии (только UI, использует кэш)"""
        if not hasattr(self, 'page_home') or not hasattr(self.page_home, 'lbl_version'):
            return
        from utils.singbox import get_singbox_version, compare_versions
        version = get_singbox_version()
        if version:
            self.page_home.lbl_version.setText(tr("home.installed", version=version))
            self.page_home.lbl_version.setStyleSheet(StyleSheet.label(variant="primary"))
            if hasattr(self.page_home, 'btn_version_warning'):
                self.page_home.btn_version_warning.hide()
            
            if self.cached_latest_version:
                from utils.singbox import compare_versions
                comparison = compare_versions(version, self.cached_latest_version)
                if comparison < 0:
                    if hasattr(self.page_home, 'lbl_update_info'):
                        self.page_home.lbl_update_info.setText(tr("home.update_available", version=self.cached_latest_version))
                        self.page_home.lbl_update_info.show()
                        # Делаем текст кликабельным
                        if not hasattr(self.page_home.lbl_update_info, '_click_handler_set'):
                            def handle_update_click(event):
                                if event.button() == Qt.LeftButton:
                                    self.show_download_dialog()
                            self.page_home.lbl_update_info.mousePressEvent = handle_update_click
                            self.page_home.lbl_update_info._click_handler_set = True
                    if hasattr(self.page_home, 'btn_version_update'):
                        self.page_home.btn_version_update.hide()
                else:
                    if hasattr(self.page_home, 'lbl_update_info'):
                        self.page_home.lbl_update_info.hide()
                    if hasattr(self.page_home, 'btn_version_update'):
                        self.page_home.btn_version_update.hide()
            else:
                if hasattr(self.page_home, 'lbl_update_info'):
                    self.page_home.lbl_update_info.hide()
                if hasattr(self.page_home, 'btn_version_update'):
                    self.page_home.btn_version_update.hide()
    
    def update_app_version_display(self):
        """Обновление отображения версии приложения"""
        if self.cached_app_latest_version:
            comparison = compare_versions(self.app_version, self.cached_app_latest_version)
            if comparison < 0:
                # Есть обновление
                self.lbl_app_version.setText(tr("app.update_available", version=self.cached_app_latest_version))
                self.lbl_app_version.setStyleSheet(StyleSheet.label(variant="warning") + "cursor: pointer;")
                # Обработчик клика уже установлен в __init__, он обрабатывает и обновления, и дебаг режим
            else:
                # Нет обновления
                self.lbl_app_version.setText(tr("app.version", version=self.app_version))
                self.lbl_app_version.setStyleSheet(StyleSheet.label(variant="secondary") + "cursor: pointer;")
        else:
            # Показываем текущую версию
            self.lbl_app_version.setText(tr("app.version", version=self.app_version))
            self.lbl_app_version.setStyleSheet(StyleSheet.label(variant="secondary") + "cursor: pointer;")
    
    
    def show_app_update_dialog(self):
        """Показать диалог обновления приложения"""
        if not self.cached_app_latest_version:
            return
        
        comparison = compare_versions(self.app_version, self.cached_app_latest_version)
        if comparison >= 0:
            # Нет обновления
            return
        
        # Используем красивое диалоговое окно
        if show_kill_all_success_dialog(
            self,
            tr("app.update_title"),
            tr("app.update_message", version=self.cached_app_latest_version, current=self.app_version)
        ):
            # Пользователь хочет обновиться - запускаем автоматическое обновление
            self.start_app_update()
    
    def start_app_update(self):
        """Запуск автоматического обновления приложения"""
        if not self.cached_app_latest_version:
            return
        
        # Останавливаем SingBox если запущен
        if self.proc and self.proc.poll() is None:
            self.stop_singbox()
        
        from config.paths import DATA_DIR
        
        # Находим updater.exe в data
        updater_exe = DATA_DIR / "updater.exe"
        
        if not updater_exe.exists():
            show_info_dialog(self, tr("app.update_error_title"), f"updater.exe not found at {updater_exe}")
            return
        
        log_to_file(f"[App Update] Starting updater.exe (target={self.cached_app_latest_version or 'latest main'})")
        
        # Запускаем updater.exe (updater сам узнает последнюю версию из main)
        try:
            subprocess.Popen(
                [str(updater_exe)],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            # Даем время на запуск updater
            time.sleep(1)
            
            # Закрываем приложение - updater сам все сделает
            self.log(tr("app.update_complete"))
            QApplication.quit()
        except Exception as e:
            log_to_file(f"[App Update] Error starting updater: {e}")
            show_info_dialog(self, tr("app.update_error_title"), f"Error starting updater: {e}")
    
    def update_profile_info(self):
        """Обновление информации о профиле"""
        if not hasattr(self, 'page_home') or not hasattr(self.page_home, 'lbl_profile'):
            return
        running = self.proc and self.proc.poll() is None
        running_sub = None
        selected_sub = None
        
        # Получаем запущенный профиль
        if running and self.running_sub_index >= 0:
            if hasattr(self, 'page_profile') and hasattr(self.page_profile, 'sub_list'):
                if self.page_profile.sub_list.count() > 0:
                    running_sub = self.subs.get(self.running_sub_index)
        
        # Получаем выбранный профиль
        if self.current_sub_index >= 0:
            if hasattr(self, 'page_profile') and hasattr(self.page_profile, 'sub_list'):
                if self.page_profile.sub_list.count() > 0:
                    selected_sub = self.subs.get(self.current_sub_index)
        
        # Формируем текст
        from ui.styles import theme
        accent_color = theme.get_color('accent')
        profile_style = f"color: {accent_color}; background-color: transparent; border: none; padding: 0px; padding-left: 4px;"
        
        if running_sub and selected_sub:
            if self.running_sub_index == self.current_sub_index:
                # Профили совпадают
                self.page_home.lbl_profile.setText(tr("home.current_profile", name=running_sub.get("name", tr("profile.unknown"))))
                self.page_home.lbl_profile.setStyleSheet(profile_style)
            else:
                # Профили разные - добавляем отступ для второй строки
                text = f"{tr('home.current_profile', name=running_sub.get('name', tr('profile.unknown')))}\n    {tr('home.selected_profile', name=selected_sub.get('name', tr('profile.unknown')))}"
                self.page_home.lbl_profile.setText(text)
                self.page_home.lbl_profile.setStyleSheet(profile_style)
                self.page_home.lbl_profile.setCursor(Qt.ArrowCursor)
        elif running_sub:
            # Только запущенный профиль
            self.page_home.lbl_profile.setText(tr("home.current_profile", name=running_sub.get("name", tr("profile.unknown"))))
            self.page_home.lbl_profile.setStyleSheet(profile_style)
            self.page_home.lbl_profile.setCursor(Qt.ArrowCursor)
        elif selected_sub:
            # Только выбранный профиль
            self.page_home.lbl_profile.setText(tr("home.selected_profile", name=selected_sub.get("name", tr("profile.unknown"))))
            self.page_home.lbl_profile.setStyleSheet(profile_style)
            self.page_home.lbl_profile.setCursor(Qt.ArrowCursor)
        else:
            # Нет профиля
            from ui.styles import theme
            warning_color = theme.get_color('warning')
            self.page_home.lbl_profile.setText(tr("home.profile_not_selected_click"))
            self.page_home.lbl_profile.setStyleSheet(f"color: {warning_color}; background-color: transparent; border: none; padding: 0px;")
            self.page_home.lbl_profile.setCursor(Qt.PointingHandCursor)
            # Делаем кликабельным для перехода в профили
            # Сохраняем оригинальный mousePressEvent если он есть
            if not hasattr(self.page_home.lbl_profile, '_original_mousePressEvent'):
                self.page_home.lbl_profile._original_mousePressEvent = self.page_home.lbl_profile.mousePressEvent
            
            def handle_click(event):
                if event.button() == Qt.LeftButton:
                    self.switch_page(0)  # Переход на страницу профилей (индекс 0)
                else:
                    # Вызываем оригинальный обработчик для других кнопок
                    if hasattr(self.page_home.lbl_profile, '_original_mousePressEvent') and self.page_home.lbl_profile._original_mousePressEvent:
                        self.page_home.lbl_profile._original_mousePressEvent(event)
            
            self.page_home.lbl_profile.mousePressEvent = handle_click
    
    def update_admin_status_label(self):
        """Обновление надписи о правах администратора"""
        if not hasattr(self, 'page_home') or not hasattr(self.page_home, 'lbl_admin_status'):
            return
        from ui.styles import theme
        if is_admin():
            self.page_home.lbl_admin_status.setText(tr("home.admin_running"))
            # Используем цвета из темы
            accent_color = theme.get_color('accent')
            self.page_home.lbl_admin_status.setStyleSheet(f"color: {accent_color}; background-color: transparent; border: none; padding: 0px;")
            self.page_home.lbl_admin_status.setCursor(Qt.ArrowCursor)
        else:
            self.page_home.lbl_admin_status.setText(tr("home.admin_not_running"))
            # Используем цвета из темы (warning для не запущенного)
            warning_color = theme.get_color('warning')
            self.page_home.lbl_admin_status.setStyleSheet(f"color: {warning_color}; background-color: transparent; border: none; padding: 0px;")
            self.page_home.lbl_admin_status.setCursor(Qt.PointingHandCursor)
    
    def admin_status_mouse_press(self, event):
        """Обработка клика по надписи о правах администратора"""
        if not is_admin():
            if show_restart_admin_dialog(
                self,
                tr("messages.admin_required_title"),
                tr("messages.restart_as_admin_question")
            ):
                if not restart_application(self, run_as_admin=True):
                    self.log(tr("messages.admin_restart_failed"))
        else:
            event.ignore()
    
    def handle_deep_link(self):
        """Обработка deep link для импорта подписки (поддержка sing-box:// и singbox-ui://)"""
        self.deep_link_handler.handle()
    
    def show_download_dialog(self):
        """Диалог загрузки SingBox"""
        dialog = QDialog(self)
        # Фреймлесс-режим, чтобы отрисовывать собственный статус-бар
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Window | Qt.Dialog)
        dialog.setWindowTitle(tr("download.title"))
        dialog.setMinimumWidth(400)
        dialog.setModal(True)
        
        # Стили диалога через дизайн-систему
        dialog.setStyleSheet(StyleSheet.dialog() + StyleSheet.progress_bar())
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Собственный статус-бар в стиле приложения
        title_bar = TitleBar(dialog)
        title_bar.set_title(tr("download.title"))
        layout.addWidget(title_bar)
        
        # Внутренний layout для содержимого
        content_layout = QVBoxLayout()
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(24, 24, 24, 24)
        
        # Заголовок
        title = QLabel(tr("download.not_installed"))
        title.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
        title.setStyleSheet(StyleSheet.label(variant="default", size="xlarge") + "margin-bottom: 8px;")
        content_layout.addWidget(title)
        
        # Описание
        info = QLabel(tr("download.description"))
        info.setWordWrap(True)
        info.setStyleSheet(StyleSheet.label(variant="secondary", size="medium"))
        content_layout.addWidget(info)
        
        # Прогресс-бар
        self.download_progress = QProgressBar()
        self.download_progress.setRange(0, 100)
        self.download_progress.setValue(0)
        self.download_progress.hide()
        self.download_progress.setStyleSheet(StyleSheet.progress_bar())
        content_layout.addWidget(self.download_progress)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        # Кнопка отмены слева
        btn_cancel = QPushButton(tr("download.cancel"))
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(StyleSheet.dialog_button(variant="cancel"))
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)
        
        # Растяжка между кнопками
        btn_layout.addStretch()
        
        # Кнопка загрузки справа
        btn_download = QPushButton(tr("download.download"))
        btn_download.setCursor(Qt.PointingHandCursor)
        btn_download.setDefault(True)
        btn_download.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
        btn_download.clicked.connect(lambda: self.start_download(dialog, btn_download))
        btn_layout.addWidget(btn_download)
        
        content_layout.addLayout(btn_layout)
        
        # Добавляем content_layout в основной layout
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget, 1)
        
        dialog.exec_()
    
    def start_download(self, dialog, btn_download):
        """Начало загрузки"""
        btn_download.setEnabled(False)
        btn_download.setText(tr("download.downloading"))
        
        self.download_progress.show()
        self.download_progress.setValue(0)
        
        self.download_thread = DownloadThread()
        self.download_thread.progress.connect(self.download_progress.setValue)
        self.download_thread.finished.connect(
            lambda success, msg: self.on_download_finished(success, msg, dialog, btn_download)
        )
        self.download_thread.start()
    
    def on_download_finished(self, success: bool, message: str, dialog: QDialog, btn_download):
        """Завершение загрузки"""
        self.download_progress.hide()
        if success:
            show_info_dialog(dialog, tr("download.success"), message, success=True)
            dialog.accept()
            self.update_version_info()
        else:
            show_info_dialog(dialog, tr("download.error"), message)
            btn_download.setEnabled(True)
            btn_download.setText(tr("download.download"))
    
    # Кнопка Start/Stop
    def _apply_big_btn_wrapper_style(self, glow_color: Optional[str] = None):
        """Обновляет стиль подложки большой кнопки с мягким градиентным свечением"""
        if not hasattr(self, 'page_home') or not hasattr(self.page_home, 'btn_wrapper'):
            return
        from ui.styles import theme
        bg_secondary = theme.get_color('background_secondary')
        if glow_color is None:
            glow_color = theme.get_color('accent')
        # Создаем радиальный градиент: от цвета в центре к прозрачности по краям
        self.page_home.btn_wrapper.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_secondary};
                border-radius: 50%;
                border: none;
                background: qradialgradient(
                    cx:0.5, cy:0.5, radius:0.55,
                    fx:0.5, fy:0.5,
                    stop:0 {glow_color},
                    stop:0.6 {glow_color},
                    stop:1 rgba(0,0,0,0)
                );
            }}
        """)

    def style_big_btn_running(self, running: bool, font_size: int = None):
        """Стиль большой кнопки с использованием цветов темы"""
        if not hasattr(self, 'page_home'):
            return
        from ui.styles import theme
        
        # Если размер шрифта не указан, вычисляем на основе текущего размера кнопки
        if font_size is None:
            if hasattr(self.page_home, 'big_btn'):
                btn_size = self.page_home.big_btn.width()
                if btn_size == 0:
                    btn_size = 210  # Дефолтный размер
                # Вычисляем размер шрифта на основе размера кнопки, затем уменьшаем на 3 пункта
                font_size = max(18, min(32, int(btn_size / 7)))
                font_size = font_size - 3  # Уменьшаем размер текста на 3 пункта
            else:
                font_size = 25  # Дефолтный размер (28 - 4)
        
        # Проверяем, нужно ли показать "Сменить" (оранжевый цвет)
        is_change_mode = (running and 
                         self.running_sub_index != self.current_sub_index and 
                         self.current_sub_index >= 0)
        
        # Получаем цвета из темы
        bg_secondary = theme.get_color('background_secondary')
        accent = theme.get_color('accent')
        accent_hover = theme.get_color('accent_hover')
        warning = theme.get_color('warning')
        error = theme.get_color('error')
        text_disabled = theme.get_color('text_disabled')
        bg_disabled = theme.get_color('background_secondary')
        
        # Определяем цвет состояния (для текста и обводки)
        state_color = accent
        if running:
            state_color = warning if is_change_mode else error
        
        if running:
            # Текст кнопки устанавливается в update_big_button_state, здесь только стиль
            if is_change_mode:
                # Оранжевый стиль для кнопки "Сменить"
                self.page_home.big_btn.setStyleSheet(f"""
                    QPushButton {{
                        border-radius: 80px;
                        background-color: {bg_secondary};
                        color: {warning};
                        font-size: {font_size}px;
                        font-weight: 700;
                        font-family: 'Segoe UI', sans-serif;
                        border: 2px solid {warning};
                        padding: 0px;
                    }}
                    QPushButton:hover {{
                        background-color: {theme.get_color('accent_light')};
                        border: 2px solid {warning};
                    }}
                    QPushButton:disabled {{
                        background-color: {bg_disabled};
                        color: {text_disabled};
                        border: 2px solid {bg_disabled};
                    }}
                """)
            else:
                # Красный стиль для кнопки "Остановить"
                self.page_home.big_btn.setStyleSheet(f"""
                    QPushButton {{
                        border-radius: 80px;
                        background-color: {bg_secondary};
                        color: {error};
                        font-size: {font_size}px;
                        font-weight: 700;
                        font-family: 'Segoe UI', sans-serif;
                        border: 2px solid {error};
                        padding: 0px;
                    }}
                    QPushButton:hover {{
                        background-color: {theme.get_color('accent_light')};
                        border: 2px solid {error};
                    }}
                    QPushButton:disabled {{
                        background-color: {bg_disabled};
                        color: {text_disabled};
                        border: 2px solid {bg_disabled};
                    }}
                """)
        else:
            # Текст кнопки устанавливается в update_big_button_state, здесь только стиль
            self.page_home.big_btn.setStyleSheet(f"""
                QPushButton {{
                    border-radius: 80px;
                    background-color: {bg_secondary};
                    color: {accent};
                    font-size: {font_size}px;
                    font-weight: 700;
                    font-family: 'Segoe UI', sans-serif;
                    border: 2px solid {accent};
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {theme.get_color('accent_light')};
                    border: 2px solid {accent_hover};
                }}
                QPushButton:disabled {{
                    background-color: {bg_disabled};
                    color: {text_disabled};
                    border: 3px solid {bg_disabled};
                }}
            """)

    def update_big_button_state(self):
        """Обновление состояния большой кнопки"""
        if not hasattr(self, 'page_home') or not hasattr(self.page_home, 'big_btn'):
            return
        core_ok = CORE_EXE.exists()
        running = self.proc and self.proc.poll() is None
        
        # Обновляем анимацию если используется AnimatedStartButton
        if hasattr(self.page_home, 'big_btn') and hasattr(self.page_home.big_btn, 'set_running'):
            self.page_home.big_btn.set_running(running)
        
        if running:
            # Если запущен - кнопка всегда видна и активна (можно остановить), даже если профиль не выбран
            if hasattr(self.page_home, 'btn_container'):
                self.page_home.btn_container.show()
            self.page_home.big_btn.setEnabled(True)
            # Проверяем, совпадает ли выбранный профиль с запущенным
            if self.running_sub_index != self.current_sub_index and self.current_sub_index >= 0:
                # Выбран другой профиль - показываем "Сменить"
                self.page_home.big_btn.setText(tr("home.button_change"))
            else:
                # Профили совпадают или не выбран - показываем "Остановить"
                self.page_home.big_btn.setText(tr("home.button_stop"))
        else:
            # Если не запущен - нужен выбранный профиль для запуска
            has_sub = False
            if hasattr(self, 'page_profile') and hasattr(self.page_profile, 'sub_list'):
                has_sub = self.page_profile.sub_list.count() > 0 and self.current_sub_index >= 0
            
            if has_sub and core_ok:
                # Профиль выбран и core доступен - показываем кнопку
                if hasattr(self.page_home, 'btn_container'):
                    self.page_home.btn_container.show()
                self.page_home.big_btn.setEnabled(True)
                self.page_home.big_btn.setText(tr("home.button_start"))
            else:
                # Профиль не выбран или core недоступен - показываем кнопку как неактивную
                if hasattr(self.page_home, 'btn_container'):
                    self.page_home.btn_container.show()
                self.page_home.big_btn.setEnabled(False)
                self.page_home.big_btn.setText(tr("home.button_unavailable", default="НЕДОСТУПЕН"))
        
        self.style_big_btn_running(bool(running))

    def on_big_button(self):
        """Обработка нажатия большой кнопки"""
        running = self.proc and self.proc.poll() is None
        
        if running:
            # Проверяем, нужно ли переключить профиль
            if self.running_sub_index != self.current_sub_index and self.current_sub_index >= 0:
                # Выбран другой профиль - останавливаем текущий и запускаем новый
                self.log(tr("messages.switching_profile"))
                self.stop_singbox()
                # Запускаем новый профиль после остановки
                # Используем QTimer для небольшой задержки, чтобы процесс успел остановиться
                QTimer.singleShot(500, self.start_singbox)
            else:
                # Профили совпадают - просто останавливаем
                self.stop_singbox()
        else:
            self.start_singbox()

    # Запуск/остановка
    def start_singbox(self):
        """Запуск SingBox"""
        if not CORE_EXE.exists():
            self.log(tr("messages.no_core"))
            self.update_version_info()
            return
        if not hasattr(self, 'page_profile') or not hasattr(self.page_profile, 'sub_list'):
            return
        if self.current_sub_index < 0 or self.page_profile.sub_list.count() == 0:
            self.log(tr("messages.no_subscription"))
            return
        
        # Проверяем права администратора
        if not is_admin():
            if show_restart_admin_dialog(
                self,
                tr("messages.admin_required_title"),
                tr("messages.admin_required_start")
            ):
                if not restart_application(self, run_as_admin=True):
                    self.log(tr("messages.admin_restart_failed"))
                return
            else:
                return
        
        log_to_file(tr("messages.downloading_config"))
        ok = self.subs.download_config(self.current_sub_index)
        if not ok:
            self.log(tr("messages.config_error"))
            return
        
        # Запускаем в отдельном потоке чтобы не блокировать UI
        self.log(tr("messages.starting"))
        # Отключаем кнопку на время запуска
        if hasattr(self, 'page_home') and hasattr(self.page_home, 'big_btn'):
            self.page_home.big_btn.setEnabled(False)
        
        self.start_thread = StartSingBoxThread(CORE_EXE, CONFIG_FILE, CORE_DIR)
        self.start_thread.finished.connect(self.on_singbox_started)
        self.start_thread.error.connect(self.on_singbox_start_error)
        self.start_thread.start()
    
    def on_singbox_started(self, proc):
        """Обработка успешного запуска SingBox"""
        self.proc = proc
        # Проверяем, что процесс действительно запущен
        if proc is not None and proc.poll() is None:
            self.running_sub_index = self.current_sub_index  # Запоминаем запущенный профиль
            self.log(tr("messages.started_success"))
            self.update_profile_info()
        else:
            # Процесс завершился сразу после запуска
            if proc:
                code = proc.returncode if proc.returncode is not None else -1
                self.log(tr("messages.stopped", code=code))
            self.proc = None
            self.running_sub_index = -1
        self.update_big_button_state()
    
    def on_singbox_start_error(self, error_msg):
        """Обработка ошибки запуска SingBox"""
        self.log(tr("messages.start_error", error=error_msg))
        self.proc = None
        self.running_sub_index = -1
        self.update_big_button_state()
        self.update_profile_info()

    def stop_singbox(self):
        """Остановка SingBox"""
        if not self.proc:
            return
        
        # Проверяем права администратора перед остановкой
        if not is_admin():
            if show_restart_admin_dialog(
                self,
                tr("messages.admin_required_title"),
                tr("messages.admin_required_stop")
            ):
                if not restart_application(self, run_as_admin=True):
                    self.log(tr("messages.admin_restart_failed"))
                return
            else:
                return
        
        self.log(tr("messages.stopping"))
        try:
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        self.proc = None
        self.running_sub_index = -1  # Сбрасываем запущенный профиль
        self.update_big_button_state()
        self.update_profile_info()

    def auto_update_config(self):
        """Автообновление конфига"""
        if not hasattr(self, 'page_profile') or not hasattr(self.page_profile, 'sub_list'):
            return
        if self.current_sub_index < 0 or self.page_profile.sub_list.count() == 0:
            return
        log_to_file(tr("messages.auto_update"))
        ok = self.subs.download_config(self.current_sub_index)
        if not ok:
            self.log(tr("messages.auto_update_error"))
            return
        if self.proc and self.proc.poll() is None:
            self.log(tr("messages.auto_update_restart"))
            self.stop_singbox()
            self.start_singbox()
        else:
            log_to_file(tr("messages.auto_update_not_running"))

    def poll_process(self):
        """Опрос процесса - проверяем, не завершился ли процесс"""
        if self.proc and self.proc.poll() is not None:
            code = self.proc.returncode
            self.log(tr("messages.stopped", code=code))
            self.proc = None
            self.update_big_button_state()

    # Настройки
    def on_interval_changed(self):
        """Изменение интервала автообновления (старый метод для обратной совместимости)"""
        # Этот метод больше не используется, оставлен для совместимости
        pass
    
    def on_interval_changed_from_radio(self, value: int):
        """Изменение интервала автообновления через радиокнопки"""
        if 30 <= value <= 120:
            self.settings.set("auto_update_minutes", value)
            self.update_timer.start(value * 60 * 1000)
            self.log(tr("messages.interval_changed", value=value))
    
    def on_version_clicked(self, event):
        """Обработка клика по версии для показа дебаг меню и обновлений"""
        if event.button() != Qt.LeftButton:
            return
        
        # Проверяем, есть ли обновление приложения
        if self.cached_app_latest_version:
            comparison = compare_versions(self.app_version, self.cached_app_latest_version)
            if comparison < 0:
                # Есть обновление - показываем диалог обновления
                self.show_app_update_dialog()
                return
        
        # Если нет обновления, обрабатываем клики для дебаг режима
        self.version_click_count += 1
        
        # На 5-м клике показываем сообщение
        if self.version_click_count == 5:
            show_info_dialog(
                self,
                "Debug Mode",
                "Нажмите ещё один раз, чтобы активировать режим разработчика"
            )
        elif self.version_click_count >= 6:
            self.version_click_count = 0  # Сбрасываем счетчик
            
            # Переключаем настройку isDebug
            current_debug = self.settings.get("isDebug", False)
            new_debug = not current_debug
            self.settings.set("isDebug", new_debug)
            
            # Обновляем видимость всей дебаг секции на основе isDebug
            self._update_debug_logs_visibility()
            
            if new_debug:
                log_to_file(f"Debug меню активировано (isDebug: {new_debug})")
                show_info_dialog(
                    self,
                    "Debug Mode",
                    "Режим разработчика активирован"
                )
            else:
                log_to_file(f"Debug меню скрыто (isDebug: {new_debug})")
    
    def _update_debug_logs_visibility(self):
        """Обновляет видимость всей дебаг секции (debug_card и debug_logs) на основе настройки isDebug"""
        if hasattr(self, 'page_settings'):
            self.page_settings.update_debug_logs_visibility()
    
    def on_allow_multiple_changed(self, state: int):
        """Изменение настройки разрешения нескольких процессов"""
        if not hasattr(self, 'page_settings') or not hasattr(self.page_settings, 'cb_allow_multiple'):
            return
        enabled = state == Qt.Checked
        try:
            self.settings.set("allow_multiple_processes", enabled)
            log_to_file(f"Разрешение нескольких процессов: {'включено' if enabled else 'выключено'}")
        except Exception as e:
            log_to_file(f"Ошибка при изменении настройки нескольких процессов: {e}")
            # Восстанавливаем состояние чекбокса при ошибке
            self.page_settings.cb_allow_multiple.blockSignals(True)
            self.page_settings.cb_allow_multiple.setChecked(not enabled)
            self.page_settings.cb_allow_multiple.blockSignals(False)

    def set_autostart(self, enabled: bool):
        """Установка автозапуска"""
        import winreg
        run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "SingBox-UI"
        task_name = "SingBox-UI-AutoStart"

        if getattr(sys, "frozen", False):
            exe_path = sys.executable
        else:
            exe_path = str((Path(__file__).parent / "run_dev.bat").resolve())
        
        run_as_admin = self.settings.get("run_as_admin", False)

        try:
            if enabled:
                if run_as_admin:
                    # Используем Task Scheduler для запуска от имени администратора
                    xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>"{exe_path}"</Command>
      <WorkingDirectory>{Path(exe_path).parent}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
                    xml_file = Path(os.getenv("TEMP")) / f"{task_name}.xml"
                    xml_file.write_text(xml_content, encoding="utf-16")
                    try:
                        # Удаляем старую задачу если есть
                        subprocess.run(["schtasks", "/delete", "/tn", task_name, "/f"], 
                                     capture_output=True, check=False)
                        # Создаем новую задачу
                        result = subprocess.run(["schtasks", "/create", "/tn", task_name, "/xml", str(xml_file), "/f"], 
                                             check=True, capture_output=True, text=True)
                        xml_file.unlink()
                        log_to_file("Автозапуск от имени администратора настроен через Task Scheduler")
                    except subprocess.CalledProcessError as e:
                        log_to_file(f"Ошибка создания задачи автозапуска: {e.stderr if e.stderr else str(e)}")
                        # Fallback: используем реестр с PowerShell
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_ALL_ACCESS) as key:
                            ps_command = f'powershell -Command "Start-Process -FilePath \\"{exe_path}\\" -Verb RunAs"'
                            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, ps_command)
                        log_to_file("Автозапуск настроен через реестр (PowerShell)")
                    except Exception as e:
                        log_to_file(f"Ошибка настройки автозапуска: {e}")
                        xml_file.unlink(missing_ok=True)
                else:
                    # Обычный автозапуск без прав админа через реестр
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_ALL_ACCESS) as key:
                        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
                    # Удаляем задачу если есть
                    try:
                        subprocess.run(["schtasks", "/delete", "/tn", task_name, "/f"], 
                                     capture_output=True, check=False)
                    except:
                        pass
            else:
                # Отключаем автозапуск
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_ALL_ACCESS) as key:
                        winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
                # Удаляем задачу если есть
                try:
                    subprocess.run(["schtasks", "/delete", "/tn", task_name, "/f"], 
                                 capture_output=True, check=False)
                except:
                    pass
        except OSError as e:
            self.log(tr("messages.autostart_error", error=str(e)))

    def on_autostart_changed(self, state: int):
        """Изменение автозапуска"""
        enabled = state == Qt.Checked
        try:
            self.settings.set("start_with_windows", enabled)
            self.set_autostart(enabled)
            self.log(tr("messages.autostart_enabled") if enabled else tr("messages.autostart_disabled"))
        except Exception as e:
            log_to_file(f"Ошибка при изменении автозапуска: {e}")
            # Восстанавливаем состояние чекбокса при ошибке
            if hasattr(self, 'page_settings') and hasattr(self.page_settings, 'cb_autostart'):
                self.page_settings.cb_autostart.blockSignals(True)
                self.page_settings.cb_autostart.setChecked(not enabled)
                self.page_settings.cb_autostart.blockSignals(False)
    
    def on_run_as_admin_changed(self, state: int):
        """Изменение настройки запуска от имени администратора"""
        enabled = state == Qt.Checked
        self.settings.set("run_as_admin", enabled)
        
        # Если автозапуск включен, обновляем его с новой настройкой
        if self.settings.get("start_with_windows", False):
            self.set_autostart(True)
        
        # Если включили запуск от имени администратора, предлагаем перезапустить
        if enabled and not is_admin():
            if show_restart_admin_dialog(
                self,
                tr("messages.restart_required_title"),
                tr("messages.restart_required_text")
            ):
                if not restart_application(self, run_as_admin=True):
                    self.log(tr("messages.admin_restart_failed"))
                    # Восстанавливаем состояние чекбокса при ошибке
                    if hasattr(self, 'page_settings') and hasattr(self.page_settings, 'cb_run_as_admin'):
                        self.page_settings.cb_run_as_admin.blockSignals(True)
                        self.page_settings.cb_run_as_admin.setChecked(False)
                        self.settings.set("run_as_admin", False)
                        self.page_settings.cb_run_as_admin.blockSignals(False)
                    return
                return
        # Если выключили галочку — не требуем перезапуска. Настройка вступит в силу при следующем старте.
        
        # Действия пользователя - в обычные логи
        if enabled:
            self.log(tr("messages.run_as_admin_enabled"))
        else:
            self.log(tr("messages.run_as_admin_disabled"))
    
    def on_auto_start_singbox_changed(self, state: int):
        """Изменение настройки автозапуска sing-box при запуске приложения"""
        enabled = state == Qt.Checked
        try:
            self.settings.set("auto_start_singbox", enabled)
            self.log(tr("messages.auto_start_singbox_enabled") if enabled else tr("messages.auto_start_singbox_disabled"))
        except Exception as e:
            log_to_file(f"Ошибка при изменении автозапуска sing-box: {e}")
            # Восстанавливаем состояние чекбокса при ошибке
            if hasattr(self, 'page_settings') and hasattr(self.page_settings, 'cb_auto_start_singbox'):
                self.page_settings.cb_auto_start_singbox.blockSignals(True)
                self.page_settings.cb_auto_start_singbox.setChecked(not enabled)
                self.page_settings.cb_auto_start_singbox.blockSignals(False)
    
    def on_language_changed(self, index: int):
        """Обработка изменения языка"""
        if not hasattr(self, 'page_settings') or not hasattr(self.page_settings, 'combo_language'):
            return
        if index >= 0:
            lang_code = self.page_settings.combo_language.itemData(index)
            if lang_code:
                old_language = self.settings.get("language", "en")
                if lang_code != old_language:
                    self.settings.set("language", lang_code)
                    set_language(lang_code)
                    self.log(tr("settings.language_changed", language=get_language_name(lang_code)))
                    # Обновляем все тексты в интерфейсе
                    self.refresh_ui_texts()
                    # Обновляем названия тем в комбобоксе
                    if hasattr(self.page_settings, 'combo_theme'):
                        current_theme_id = self.page_settings.combo_theme.itemData(self.page_settings.combo_theme.currentIndex())
                        self.page_settings.combo_theme.clear()
                        from utils.theme_manager import get_available_themes, get_theme_name
                        available_themes = get_available_themes()
                        for theme_info in available_themes:
                            theme_name = get_theme_name(theme_info["id"], lang_code)
                            self.page_settings.combo_theme.addItem(theme_name, theme_info["id"])
                            if theme_info["id"] == current_theme_id:
                                self.page_settings.combo_theme.setCurrentIndex(self.page_settings.combo_theme.count() - 1)
    
    def on_theme_changed(self, index: int):
        """Обработка изменения темы"""
        if not hasattr(self, 'page_settings') or not hasattr(self.page_settings, 'combo_theme'):
            return
        if index >= 0:
            theme_id = self.page_settings.combo_theme.itemData(index)
            if theme_id:
                old_theme = self.settings.get("theme", "dark")
                if theme_id != old_theme:
                    self.settings.set("theme", theme_id)
                    from utils.theme_manager import set_theme, get_theme_name
                    from utils.i18n import get_translator
                    set_theme(theme_id)
                    theme.reload_theme()
                    current_language = get_translator().language
                    theme_name = get_theme_name(theme_id, current_language)
                    self.log(tr("settings.theme_changed", theme=theme_name))
                    
                    # Обновляем все стили UI при смене темы
                    self.refresh_ui_styles()


    def refresh_ui_styles(self):
        """Обновление всех стилей UI при смене темы"""
        from ui.styles import theme
        
        # Обновляем QApplication palette для фона окна (делаем это первым)
        app = QApplication.instance()
        if app:
            from app.application import apply_theme as apply_app_theme
            apply_app_theme(app)
        
        # Обновляем title bar (включая текст и иконку)
        if hasattr(self, "title_bar"):
            self.title_bar.apply_theme()
        
        # Обновляем навигационные кнопки
        if hasattr(self, 'btn_nav_profile'):
            self._update_nav_button(self.btn_nav_profile, 
                                   tr("nav.profile"), 
                                   "mdi.account")
        if hasattr(self, 'btn_nav_home'):
            self._update_nav_button(self.btn_nav_home, 
                                   tr("nav.home"), 
                                   "mdi.home")
        if hasattr(self, 'btn_nav_settings'):
            self._update_nav_button(self.btn_nav_settings, 
                                   tr("nav.settings"), 
                                   "mdi.cog")
        
        # Обновляем навигацию
        nav = self.findChild(QWidget, 'nav')
        if nav:
            nav.setStyleSheet(StyleSheet.navigation())
        
        # Обновляем version container
        if hasattr(self, 'version_container'):
            self.version_container.setStyleSheet(f"""
                QWidget {{
                    background-color: {theme.get_color('background_primary')};
                    border: none;
                }}
            """)
        
        # Обновляем страницы через их методы обновления стилей
        if hasattr(self, 'page_home'):
            self._refresh_home_page_styles()
        if hasattr(self, 'page_profile'):
            self._refresh_profile_page_styles()
        if hasattr(self, 'page_settings'):
            self._refresh_settings_page_styles()
        
        # Обновляем информацию о профиле, версии, кнопках (они используют стили)
        self.update_profile_info()
        self.update_version_info()
        self.update_app_version_display()
        self.update_big_button_state()
        self.update_admin_status_label()
        
        # Обновляем главное окно
        self.setStyleSheet(StyleSheet.global_styles())
        
        # Обновляем центральный виджет (фон окна)
        central = self.centralWidget()
        if central:
            central.setStyleSheet(f"""
                QWidget {{
                    background-color: {theme.get_color('background_primary')};
                }}
            """)
            central.update()
        
        # Обновляем tray manager (иконка трея)
        if hasattr(self, 'tray_manager'):
            self._refresh_tray_manager()
        
        # Обновляем LogsWindow если оно открыто
        if hasattr(self, 'page_settings') and hasattr(self.page_settings, '_logs_window'):
            if self.page_settings._logs_window is not None:
                if hasattr(self.page_settings._logs_window, 'apply_theme'):
                    self.page_settings._logs_window.apply_theme()
        
        # Принудительно обновляем все виджеты для перерисовки
        self.update()
        self.repaint()
        if hasattr(self, 'page_home'):
            self.page_home.update()
            self.page_home.repaint()
        if hasattr(self, 'page_profile'):
            self.page_profile.update()
            self.page_profile.repaint()
        if hasattr(self, 'page_settings'):
            self.page_settings.update()
            self.page_settings.repaint()
    
    def _refresh_tray_manager(self):
        """Обновляет tray manager при смене темы"""
        if not hasattr(self, 'tray_manager') or not self.tray_manager.tray_icon:
            return
        
        # Иконка трея не зависит от темы (она статичная), но обновляем tooltip
        from utils.i18n import tr
        self.tray_manager.tray_icon.setToolTip(tr("app.title"))
    
    def _refresh_home_page_styles(self):
        """Обновление стилей главной страницы"""
        if not hasattr(self, 'page_home'):
            return
        from ui.styles import theme
        from utils.icon_helper import icon
        
        # Обновляем кнопки версии
        if hasattr(self.page_home, 'btn_version_warning'):
            error_color = theme.get_color('error')
            self.page_home.btn_version_warning.setIcon(icon("mdi.alert-circle", color=error_color).icon())
            error_hex = error_color.lstrip('#')
            error_r = int(error_hex[0:2], 16)
            error_g = int(error_hex[2:4], 16)
            error_b = int(error_hex[4:6], 16)
            error_hover = f"rgba({error_r}, {error_g}, {error_b}, 0.15)"
            self.page_home.btn_version_warning.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 50%;
                    padding: 4px;
                }}
                QPushButton:hover {{
                    background-color: {error_hover};
                }}
            """)
        
        if hasattr(self.page_home, 'btn_version_update'):
            accent_color = theme.get_color('accent')
            self.page_home.btn_version_update.setIcon(icon("mdi.download", color=accent_color).icon())
            accent_light = theme.get_color('accent_light')
            self.page_home.btn_version_update.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 50%;
                    padding: 4px;
                }}
                QPushButton:hover {{
                    background-color: {accent_light};
                }}
            """)
        
        # Обновляем заголовки
        from ui.styles import StyleSheet
        from PyQt5.QtWidgets import QLabel
        
        # Находим все элементы на странице и обновляем их
        # Заголовок профиля
        if hasattr(self.page_home, 'profile_title'):
            self.page_home.profile_title.setStyleSheet(StyleSheet.label(variant="default", size="large"))
        
        # Заголовок версии (version_title)
        if hasattr(self.page_home, 'version_title'):
            self.page_home.version_title.setStyleSheet(StyleSheet.label(variant="default", size="large"))
        
        # Обновляем все заголовки карточек (version_title и другие) по их стилю
        # Ищем все QLabel с жирным шрифтом размером >= 13 как заголовки карточек
        processed_labels = set()
        if hasattr(self.page_home, 'lbl_version'):
            processed_labels.add(self.page_home.lbl_version)
        if hasattr(self.page_home, 'lbl_profile'):
            processed_labels.add(self.page_home.lbl_profile)
        if hasattr(self.page_home, 'lbl_admin_status'):
            processed_labels.add(self.page_home.lbl_admin_status)
        if hasattr(self.page_home, 'lbl_update_info'):
            processed_labels.add(self.page_home.lbl_update_info)
        
        for label in self.page_home.findChildren(QLabel):
            if label in processed_labels:
                continue
            # Обновляем заголовки карточек (жирный шрифт размером >= 13)
            font = label.font()
            if font.bold() and font.pointSize() >= 13:
                label.setStyleSheet(StyleSheet.label(variant="default", size="large"))
                label.update()
        
        # Лейбл версии (базовый стиль, подробнее обновится в update_version_info)
        if hasattr(self.page_home, 'lbl_version'):
            # Базовый стиль будет переопределен в update_version_info
            pass
        
        # Лейбл профиля (базовый стиль, подробнее обновится в update_profile_info)
        if hasattr(self.page_home, 'lbl_profile'):
            # Базовый стиль будет переопределен в update_profile_info
            pass
        
        # Лейбл обновления
        if hasattr(self.page_home, 'lbl_update_info'):
            self.page_home.lbl_update_info.setStyleSheet(StyleSheet.label(variant="warning"))
        
        # Обновляем фон страницы
        self.page_home.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.get_color('background_primary')};
            }}
        """)
        
        # Обновляем все карточки на странице
        self._refresh_cards_on_page(self.page_home)
        
        # Обновляем большую кнопку (big_btn) - стиль обновится через style_big_btn_running
        # которое вызывается в update_big_button_state, но вызываем здесь для надежности
        if hasattr(self.page_home, 'big_btn'):
            # Определяем состояние кнопки
            running = self.proc and self.proc.poll() is None
            self.style_big_btn_running(running)
            
            # Обновляем подложку кнопки (btn_wrapper) если она есть
            # Проверяем оба варианта названия
            if hasattr(self.page_home, 'btn_wrapper'):
                self._apply_big_btn_wrapper_style()
            elif hasattr(self.page_home, 'btn_container'):
                # btn_container прозрачный, но обновляем на всякий случай
                self.page_home.btn_container.setStyleSheet("background-color: transparent; border: none;")
        
        # Принудительно обновляем всю страницу для перерисовки
        self.page_home.update()
        self.page_home.repaint()
    
    def _refresh_profile_page_styles(self):
        """Обновление стилей страницы профилей"""
        if not hasattr(self, 'page_profile'):
            return
        from ui.styles import theme
        from ui.styles import StyleSheet
        
        # Обновляем фон страницы
        self.page_profile.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.get_color('background_primary')};
            }}
        """)
        
        # Обновляем заголовок
        if hasattr(self.page_profile, 'lbl_profile_title'):
            self.page_profile.lbl_profile_title.setStyleSheet(StyleSheet.label(variant="default", size="xlarge"))
        
        # Обновляем список подписок
        if hasattr(self.page_profile, 'sub_list'):
            self.page_profile.sub_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {theme.get_color('background_tertiary')};
                    border: none;
                    border-radius: {theme.get_size('border_radius_medium')}px;
                    padding: {theme.get_size('padding_small')}px;
                    outline: none;
                }}
                QListWidget::item {{
                    background-color: transparent;
                    border-radius: {theme.get_size('border_radius_small')}px;
                    padding: {theme.get_size('padding_medium')}px;
                    margin: 2px;
                }}
                QListWidget::item:hover {{
                    background-color: {theme.get_color('accent_light')};
                }}
                QListWidget::item:selected {{
                    background-color: {theme.get_color('accent_light')};
                    color: {theme.get_color('accent')};
                }}
            """)
        
        # Обновляем кнопки
        button_style = f"""
            QPushButton {{
                background-color: {theme.get_color('background_tertiary')};
                color: {theme.get_color('text_primary')};
                border: 1px solid {theme.get_color('border')};
                border-radius: {theme.get_size('border_radius_medium')}px;
                padding: {theme.get_size('padding_medium')}px {theme.get_size('padding_large')}px;
                font-size: {theme.get_font('size_medium')}px;
                font-weight: {theme.get_font('weight_medium')};
                font-family: {theme.get_font('family')};
            }}
            QPushButton:hover {{
                background-color: {theme.get_color('accent_light')};
                border-color: {theme.get_color('border_hover')};
            }}
            QPushButton:pressed {{
                background-color: {theme.get_color('accent_light_hover')};
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: {theme.get_color('background_secondary')};
                color: {theme.get_color('text_disabled')};
                opacity: 0.5;
            }}
        """
        if hasattr(self.page_profile, 'btn_add_sub'):
            self.page_profile.btn_add_sub.setStyleSheet(button_style)
        if hasattr(self.page_profile, 'btn_del_sub'):
            self.page_profile.btn_del_sub.setStyleSheet(button_style)
        if hasattr(self.page_profile, 'btn_rename_sub'):
            self.page_profile.btn_rename_sub.setStyleSheet(button_style)
        
        # Обновляем все карточки на странице
        self._refresh_cards_on_page(self.page_profile)
        
        # Принудительно обновляем всю страницу для перерисовки
        self.page_profile.update()
        self.page_profile.repaint()
    
    def _refresh_cards_on_page(self, page):
        """Обновляет все CardWidget на странице"""
        from ui.widgets.card import CardWidget
        
        # Находим все карточки на странице
        cards = page.findChildren(CardWidget)
        for card in cards:
            if hasattr(card, 'apply_theme'):
                card.apply_theme()
                # update() уже вызывается в apply_theme, но убедимся что перерисовка происходит
                card.update()
    
    def _refresh_settings_page_styles(self):
        """Обновление стилей страницы настроек"""
        if not hasattr(self, 'page_settings'):
            return
        from ui.styles import theme
        from ui.styles import StyleSheet
        
        # Обновляем фон страницы
        self.page_settings.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.get_color('background_primary')};
            }}
        """)
        
        # Обновляем заголовок
        if hasattr(self.page_settings, 'lbl_settings_title'):
            self.page_settings.lbl_settings_title.setStyleSheet(StyleSheet.label(variant="default", size="xlarge") + """
                QLabel {
                    line-height: 24px;
                    padding: 0px;
                    margin: 0px;
                }
            """)
        
        # Обновляем лейблы
        if hasattr(self.page_settings, 'interval_label'):
            self.page_settings.interval_label.setStyleSheet(StyleSheet.label(variant="secondary"))
        if hasattr(self.page_settings, 'language_label'):
            self.page_settings.language_label.setStyleSheet(StyleSheet.label(variant="secondary"))
        if hasattr(self.page_settings, 'theme_label'):
            self.page_settings.theme_label.setStyleSheet(StyleSheet.label(variant="secondary"))
        
        # Обновляем все чекбоксы
        if hasattr(self.page_settings, 'cb_autostart'):
            self.page_settings.cb_autostart.setStyleSheet(StyleSheet.checkbox())
        if hasattr(self.page_settings, 'cb_run_as_admin'):
            self.page_settings.cb_run_as_admin.setStyleSheet(StyleSheet.checkbox())
        if hasattr(self.page_settings, 'cb_auto_start_singbox'):
            self.page_settings.cb_auto_start_singbox.setStyleSheet(StyleSheet.checkbox())
        if hasattr(self.page_settings, 'cb_minimize_to_tray'):
            self.page_settings.cb_minimize_to_tray.setStyleSheet(StyleSheet.checkbox())
        
        # Обновляем чекбокс allow_multiple (специальный стиль)
        if hasattr(self.page_settings, 'cb_allow_multiple'):
            error_color = theme.get_color('error')
            error_hex = error_color.lstrip('#')
            error_r = int(error_hex[0:2], 16)
            error_g = int(error_hex[2:4], 16)
            error_b = int(error_hex[4:6], 16)
            error_light = f"rgba({error_r}, {error_g}, {error_b}, 0.1)"
            self.page_settings.cb_allow_multiple.setStyleSheet(f"""
                QCheckBox {{
                    color: {error_color};
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                }}
                QCheckBox::indicator {{
                    width: 22px;
                    height: 22px;
                    border-radius: 6px;
                    border: 2px solid {error_color};
                    background-color: {error_light};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {error_color};
                    border-color: {error_color};
                }}
            """)
        
        # Обновляем радиокнопки интервала
        if hasattr(self.page_settings, 'interval_buttons'):
            for radio in self.page_settings.interval_buttons.values():
                radio.setStyleSheet(StyleSheet.checkbox())
        
        # Обновляем комбобоксы
        if hasattr(self.page_settings, 'combo_language'):
            self.page_settings.combo_language.setStyleSheet(StyleSheet.combo_box())
        if hasattr(self.page_settings, 'combo_theme'):
            self.page_settings.combo_theme.setStyleSheet(StyleSheet.combo_box())
        
        # Обновляем кнопку kill_all
        if hasattr(self.page_settings, 'btn_kill_all'):
            self.page_settings.btn_kill_all.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.get_color('error')};
                    color: {theme.get_color('text_primary')};
                    border: none;
                    border-radius: {theme.get_size('border_radius_medium')}px;
                    padding: {theme.get_size('padding_medium')}px {theme.get_size('padding_large')}px;
                    font-size: {theme.get_font('size_medium')}px;
                    font-weight: {theme.get_font('weight_medium')};
                    font-family: {theme.get_font('family')};
                }}
                QPushButton:hover {{
                    background-color: {theme.get_color('error')};
                    opacity: 0.9;
                }}
                QPushButton:pressed {{
                    opacity: 0.9;
                }}
                QPushButton:disabled {{
                    background-color: {theme.get_color('background_secondary')};
                    color: {theme.get_color('text_disabled')};
                    opacity: 0.5;
                }}
            """)
        
        # Обновляем кнопку logs
        if hasattr(self.page_settings, 'btn_open_logs'):
            self.page_settings.btn_open_logs.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.get_color('background_tertiary')};
                    color: {theme.get_color('text_primary')};
                    border: 1px solid {theme.get_color('border')};
                    border-radius: {theme.get_size('border_radius_medium')}px;
                    padding: {theme.get_size('padding_medium')}px {theme.get_size('padding_large')}px;
                    font-size: {theme.get_font('size_medium')}px;
                    font-weight: {theme.get_font('weight_medium')};
                    font-family: {theme.get_font('family')};
                }}
                QPushButton:hover {{
                    background-color: {theme.get_color('accent_light')};
                    border-color: {theme.get_color('border_hover')};
                }}
            """)
        
        # Обновляем все карточки на странице
        self._refresh_cards_on_page(self.page_settings)
        
        # Принудительно обновляем всю страницу для перерисовки
        self.page_settings.update()
        self.page_settings.repaint()
    
    def refresh_ui_texts(self):
        """Обновление всех текстов в интерфейсе после смены языка"""
        # Обновляем заголовок окна
        self.setWindowTitle(tr("app.title"))
        if hasattr(self, "title_bar"):
            self.title_bar.set_title(tr("app.title"))
        
        # Обновляем кнопки навигации
        if hasattr(self, 'btn_nav_profile'):
            self._update_nav_button(self.btn_nav_profile, tr("nav.profile"), "mdi.account")
        if hasattr(self, 'btn_nav_home'):
            self._update_nav_button(self.btn_nav_home, tr("nav.home"), "mdi.home")
        if hasattr(self, 'btn_nav_settings'):
            self._update_nav_button(self.btn_nav_settings, tr("nav.settings"), "mdi.cog")
        
        # Обновляем заголовки страниц
        if hasattr(self, 'page_profile') and hasattr(self.page_profile, 'lbl_profile_title'):
            self.page_profile.lbl_profile_title.setText(tr("profile.title"))
        if hasattr(self, 'page_settings') and hasattr(self.page_settings, 'settings_title'):
            self.page_settings.settings_title.setText(tr("settings.title"))
        if hasattr(self, 'page_home') and hasattr(self.page_home, 'profile_title'):
            self.page_home.profile_title.setText(tr("home.profile"))
        
        # Обновляем кнопки на странице профилей
        if hasattr(self, 'page_profile'):
            if hasattr(self.page_profile, 'btn_add_sub'):
                self.page_profile.btn_add_sub.setText(tr("profile.add"))
            if hasattr(self.page_profile, 'btn_del_sub'):
                self.page_profile.btn_del_sub.setText(tr("profile.delete"))
            if hasattr(self.page_profile, 'btn_rename_sub'):
                self.page_profile.btn_rename_sub.setText(tr("profile.rename"))
        
        # Обновляем настройки
        if hasattr(self, 'page_settings'):
            if hasattr(self.page_settings, 'cb_autostart'):
                self.page_settings.cb_autostart.setText(tr("settings.autostart"))
            if hasattr(self.page_settings, 'cb_run_as_admin'):
                self.page_settings.cb_run_as_admin.setText(tr("settings.run_as_admin"))
            if hasattr(self.page_settings, 'cb_auto_start_singbox'):
                self.page_settings.cb_auto_start_singbox.setText(tr("settings.auto_start_singbox"))
            if hasattr(self.page_settings, 'cb_minimize_to_tray'):
                self.page_settings.cb_minimize_to_tray.setText(tr("settings.minimize_to_tray"))
            if hasattr(self.page_settings, 'btn_kill_all'):
                self.page_settings.btn_kill_all.setText(tr("settings.kill_all"))
        if hasattr(self, 'page_settings') and hasattr(self.page_settings, 'interval_label'):
            self.page_settings.interval_label.setText(tr("settings.auto_update_interval"))
        if hasattr(self, 'language_label'):
            self.language_label.setText(tr("settings.language"))
        
        # Обновляем информацию о профиле и версии
        self.update_profile_info()
        self.update_version_info()
        self.update_app_version_display()
        self.update_big_button_state()
        self.update_admin_status_label()
    
    def _update_nav_button(self, btn: QPushButton, text: str, icon_name: str):
        """Обновляет текст и иконку кнопки навигации"""
        # Структура: QPushButton -> QHBoxLayout -> QWidget (container) -> QVBoxLayout -> QLabel (icon) + QLabel (text)
        layout = btn.layout()
        if not layout:
            return
        
        # Ищем контейнер (QWidget) в layout кнопки
        container = None
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item:
                widget = item.widget()
                if isinstance(widget, QWidget):
                    container = widget
                    break
        
        if not container:
            return
        
        # Ищем layout контейнера
        container_layout = container.layout()
        if not container_layout:
            return
        
        # Определяем цвет в зависимости от состояния кнопки (используем цвета из темы)
        from ui.styles import theme
        color = theme.get_color('accent') if btn.isChecked() else theme.get_color('text_secondary')
        font_weight = "600" if btn.isChecked() else "500"
        
        # Обновляем все QLabel'ы в layout контейнера
        icon_label = None
        text_label = None
        
        for j in range(container_layout.count()):
            item = container_layout.itemAt(j)
            if item:
                label = item.widget()
                if isinstance(label, QLabel):
                    if label.pixmap() is not None:
                        # Это иконка
                        icon_label = label
                    else:
                        # Это текст
                        text_label = label
        
        # Обновляем иконку
        if icon_label:
            icon_label.setPixmap(icon(icon_name, color=color).pixmap(36, 36))
        
        # Обновляем текст
        if text_label:
            text_label.setText(text)
            text_label.setStyleSheet(f"""
                font-size: 14px;
                font-weight: {font_weight};
                background-color: transparent;
                border: none;
                color: {color};
            """)
    
    def on_minimize_to_tray_changed(self, state: int):
        """Изменение настройки сворачивания в трей"""
        enabled = state == Qt.Checked
        
        try:
            # Обновляем настройку в памяти
            self.settings.data["minimize_to_tray"] = enabled
            
            # Динамически показываем/скрываем трей иконку БЕЗ закрытия окна
            if enabled:
                # Включаем трей режим
                if not self.tray_manager.tray_icon:
                    self.tray_manager.setup()
                if self.tray_manager.tray_icon:
                    self.tray_manager.show()
            else:
                # Выключаем трей режим - скрываем иконку и удаляем её
                self.tray_manager.cleanup()
            
            # Сохраняем настройки после всех изменений
            self.settings.save()
            
            # Обновляем поведение закрытия окна в зависимости от настройки
            app = QApplication.instance()
            if app:
                app.setQuitOnLastWindowClosed(not enabled)
            
            self.log(tr("messages.minimize_to_tray_enabled") if enabled else tr("messages.minimize_to_tray_disabled"))
        except Exception as e:
            log_to_file(f"Ошибка при изменении настройки трея: {e}")
            # Восстанавливаем состояние чекбокса при ошибке
            if hasattr(self, 'page_settings') and hasattr(self.page_settings, 'cb_minimize_to_tray'):
                self.page_settings.cb_minimize_to_tray.blockSignals(True)
                self.page_settings.cb_minimize_to_tray.setChecked(not enabled)
                self.page_settings.cb_minimize_to_tray.blockSignals(False)
    
    def kill_all_processes(self):
        """Остановка всех процессов SingBox"""
        # Останавливаем текущий процесс, если он запущен
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None
        
        # Пытаемся убить все процессы sing-box через taskkill
        try:
            # Убиваем процессы sing-box.exe
            subprocess.run(
                ["taskkill", "/F", "/IM", "sing-box.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
        except Exception:
            pass
        
        # Пытаемся убить через psutil, если доступен
        try:
            import psutil
            current_pid = os.getpid()
            exe_name = "sing-box.exe"
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and exe_name.lower() in proc.info['name'].lower():
                        if proc.info['pid'] != current_pid:
                            psutil.Process(proc.info['pid']).kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except ImportError:
            pass
        except Exception:
            pass
    
    def on_kill_all_clicked(self):
        """Обработка нажатия кнопки 'Убить' - полная остановка всех процессов"""
        if show_kill_all_confirm_dialog(
            self,
            tr("messages.kill_all_title"),
            tr("messages.kill_all_confirm")
        ):
            self.log(tr("messages.killing_all"))
            self.kill_all_processes()
            self.update_big_button_state()
            show_kill_all_success_dialog(
                self,
                tr("messages.kill_all_title"),
                tr("messages.kill_all_done")
            )
            # Закрываем приложение после остановки всех процессов
            QApplication.quit()
    
    
    def _handle_new_instance(self):
        """Обработка подключения нового экземпляра приложения"""
        socket = self.local_server.nextPendingConnection()
        if socket:
            # Ждем данные от нового экземпляра
            if socket.waitForReadyRead(1000):
                data = socket.readAll().data()
                
                # Проверяем команду перезапуска
                if data == b"__RESTART__":
                    log_to_file("[Restart] Получена команда перезапуска, ожидаем подтверждения от нового процесса")
                    # Отправляем подтверждение новому процессу, что мы готовы закрыться
                    socket.write(b"__RESTART_ACK__")
                    socket.waitForBytesWritten(1000)
                    socket.flush()
                    socket.disconnectFromServer()
                    socket.close()
                    socket.deleteLater()
                    
                    # Даем время новому процессу захватить mutex, затем закрываемся
                    QTimer.singleShot(500, lambda: self._restart_shutdown())
                    return
                
                # Обычные данные
                socket.disconnectFromServer()
                socket.close()
                socket.deleteLater()
                
                # Обычные аргументы (deep link)
                try:
                    data_str = data.decode('utf-8')
                    if data_str and data_str.strip():
                        args = data_str.strip().split('\n')
                        # Сохраняем аргументы для обработки
                        self._pending_args = args
                        QTimer.singleShot(200, self._process_pending_args)
                    else:
                        self._pending_args = []
                except:
                    self._pending_args = []
                
                # Восстанавливаем окно
                self._restore_window()
            else:
                # Если данных нет, просто восстанавливаем окно
                socket.disconnectFromServer()
                socket.close()
                socket.deleteLater()
                self._restore_window()
    
    def _restart_shutdown(self):
        """Закрытие приложения при перезапуске"""
        from utils.logger import log_to_file
        log_to_file("[Restart] Закрываем старое приложение после подтверждения от нового процесса")
        # Шрифты теперь вшиты в QRC, сброс не требуется
        # Освобождаем mutex только в самом конце
        release_global_mutex()
        QApplication.quit()
    
    def _restore_window(self):
        """Восстановление окна из свернутого состояния"""
        # Снимаем минимизацию и скрытое состояние
        self.showNormal()
        # Устанавливаем активное состояние окна
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.raise_()
        self.activateWindow()
    
    def _process_pending_args(self):
        """Обработка отложенных аргументов от нового экземпляра"""
        if hasattr(self, '_pending_args') and self._pending_args:
            # Временно сохраняем аргументы в sys.argv для обработки deep link
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]] + self._pending_args
            try:
                self.handle_deep_link()
            finally:
                sys.argv = original_argv
            self._pending_args = []
    
    def quit_application(self):
        """Полное закрытие приложения с остановкой всех процессов"""
        self.kill_all_processes()
        self.tray_manager.cleanup()
        if self.local_server:
            self.local_server.close()
            QLocalServer.removeServer("SingBox-UI-Instance")
        # Шрифты теперь вшиты в QRC, сброс не требуется
        release_global_mutex()
        QApplication.quit()
    
    # Логи (делегируются в LogUIManager)
    def load_logs(self):
        """Загрузка логов из singbox.log (важные логи)"""
        self.log_ui_manager.load_logs()
    
    def _load_logs_from_file(self):
        """Загрузка обычных логов из singbox.log (для обратной совместимости)"""
        self.log_ui_manager.load_logs()
    
    def _load_debug_logs_from_file(self):
        """Загрузка debug логов из debug.log (для обратной совместимости)"""
        self.log_ui_manager.load_debug_logs()
    
    def refresh_logs_from_files(self):
        """Обновление логов из файлов (вызывается таймером каждую секунду, если открыта страница настроек)"""
        self.log_ui_manager.refresh_logs(self.stack.currentIndex())

    def cleanup_logs_if_needed(self):
        """Очистка логов раз в сутки (полная очистка файла)"""
        self.log_ui_manager.cleanup_if_needed()
    
    def log(self, msg: str):
        """Логирование в UI панель и в singbox.log (только важные сообщения для пользователя)"""
        # Показываем в UI
        self.log_ui_manager.log_to_ui(msg)
        
        # Записываем в singbox.log (важные логи)
        try:
            from config.paths import LOG_FILE
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            full_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{full_ts}] {msg}"
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except Exception:
            pass  # Игнорируем ошибки записи в файл


    
    def closeEvent(self, event):
        """Закрытие окна"""
        # Если включен трей режим, сворачиваем в трей вместо закрытия
        if self.settings.get("minimize_to_tray", True):
            # Убеждаемся, что трей иконка существует
            if not self.tray_manager.tray_icon:
                self.tray_manager.setup()
            
            if self.tray_manager.tray_icon:
                # Всегда показываем иконку
                self.tray_manager.show()
                
                # Проверяем, что иконка действительно видна
                if not self.tray_manager.is_visible():
                    # Если не видна, пробуем пересоздать
                    self.tray_manager.cleanup()
                    self.tray_manager.setup()
                    if self.tray_manager.tray_icon:
                        self.tray_manager.show()
                
                # Сворачиваем в трей только если иконка видна
                if self.tray_manager.is_visible():
                    event.ignore()
                    self.hide()
                    
                    # Показываем уведомление
                    self.tray_manager.show_message(
                        tr("app.title"),
                        tr("messages.minimized_to_tray"),
                        QSystemTrayIcon.Information,
                        2000
                    )
                    return
        
        # Если трей режим выключен - закрываем приложение нормально
        self.kill_all_processes()
        if hasattr(self, 'local_server') and self.local_server:
            self.local_server.close()
            QLocalServer.removeServer("SingBox-UI-Instance")
        release_global_mutex()
        
        # Даем время на освобождение ресурсов перед закрытием
        # Это помогает избежать предупреждения PyInstaller о временных файлах
        QTimer.singleShot(100, lambda: event.accept())


# apply_dark_theme перенесена в app/application.py
from app.application import create_application

# StartSingBoxThread перенесен в core/singbox_manager.py


if __name__ == "__main__":
    # Устанавливаем глобальный обработчик исключений для PyQt5
    import sys
    def excepthook(exc_type, exc_value, exc_traceback):
        """Глобальный обработчик исключений"""
        if exc_type == KeyboardInterrupt:
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        import traceback
        error_msg = f"[Unhandled Exception] {exc_type.__name__}: {exc_value}\n{traceback.format_exception(exc_type, exc_value, exc_traceback)}"
        try:
            from utils.logger import log_to_file
            log_to_file(error_msg)
        except:
            pass
        
        # Вызываем стандартный обработчик
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = excepthook
    
    try:
        # Создаем папки для логов ДО логирования
        ensure_dirs()
        
        # Создаем приложение с применением темы
        app = create_application()
        
        # Загружаем настройки и принудительно запрещаем несколько экземпляров
        settings = SettingsManager()
        allow_multiple = False
        if settings.get("allow_multiple_processes", True):
            settings.set("allow_multiple_processes", False)
            settings.save()
        
        # Регистрируем/обновляем протоколы при каждом запуске (без лишних логов)
        try:
            register_protocols()
        except Exception:
            pass
    
        # Проверяем флаг --restart
        is_restart = "--restart" in sys.argv
        if is_restart:
            # Удаляем флаг из аргументов
            sys.argv = [a for a in sys.argv if a != "--restart"]
            log_to_file("[Startup] Перезапуск приложения...")
            # Даем время старому процессу завершиться
            time.sleep(1.0)
        
        # Глобальный mutex для одного экземпляра (общий для admin/non-admin)
        mutex_handle, mutex_exists = create_global_mutex()
        
        # Проверка единственного экземпляра приложения через локальный сервер
        server_name = "SingBox-UI-Instance"
        local_server = None
        
        if not allow_multiple:
            # Если глобальный mutex уже существует
            if mutex_exists:
                # При перезапуске закрываем старый процесс через local_server
                if is_restart:
                    socket = QLocalSocket()
                    socket.connectToServer(server_name)
                    if socket.waitForConnected(1000):
                        # Отправляем команду на закрытие
                        socket.write(b"__RESTART__")
                        socket.waitForBytesWritten(1000)
                        socket.flush()
                        
                        # Ждем подтверждения от старого процесса
                        if socket.waitForReadyRead(2000):
                            ack = socket.readAll().data()
                            if ack == b"__RESTART_ACK__":
                                log_to_file("[Restart] Получено подтверждение от старого процесса")
                        
                        socket.disconnectFromServer()
                        socket.close()
                        log_to_file("[Restart] Команда перезапуска отправлена старому процессу")
                    else:
                        log_to_file("[Restart] Не удалось подключиться к старому процессу, продолжаем...")
                    
                    # Освобождаем наш временный mutex
                    release_global_mutex()
                    # Ждем, пока старый процесс закроется и освободит ресурсы
                    # Старый процесс держит mutex до последнего момента
                    mutex_captured = False
                    for attempt in range(30):  # Максимум 3 секунды
                        time.sleep(0.1)
                        mutex_handle_new, mutex_exists_new = create_global_mutex()
                        if not mutex_exists_new:
                            # Старый процесс освободил mutex, мы его захватили
                            mutex_handle = mutex_handle_new
                            mutex_exists = False
                            mutex_captured = True
                            log_to_file(f"[Restart] Mutex захвачен после {attempt + 1} попыток")
                            break
                        # Освобождаем временный mutex для следующей проверки
                        release_global_mutex()
                    
                    if not mutex_captured:
                        # Если не удалось захватить mutex, создаем свой
                        log_to_file("[Restart] Не удалось захватить mutex старого процесса, создаем новый")
                        mutex_handle, mutex_exists = create_global_mutex()
                        mutex_captured = True
                    
                    # Если мы перезапускаемся и захватили mutex, переходим к созданию local_server
                    # Пропускаем все проверки на существующий экземпляр
                    if mutex_captured:
                        log_to_file("[Restart] Mutex захвачен, продолжаем запуск нового процесса")
                        # Устанавливаем mutex_exists в False, чтобы пропустить проверки ниже
                        mutex_exists = False
                        # Переходим к созданию local_server (код ниже)
                
                # Обычный запуск (не перезапуск) - проверяем на существующий экземпляр
                if mutex_exists and not is_restart:
                    # Обычный запуск - передаем аргументы и выходим
                    socket = QLocalSocket()
                    socket.connectToServer(server_name)
                    # Делаем несколько попыток подключения, вдруг сервер освободился
                    connected = False
                    for _ in range(3):
                        if socket.waitForConnected(500):
                            connected = True
                            break
                        QThread.msleep(100)
                    if connected:
                        args = sys.argv[1:] if len(sys.argv) > 1 else []
                        if args:
                            data = '\n'.join(args).encode('utf-8')
                            socket.write(data)
                            socket.waitForBytesWritten(1000)
                            socket.flush()
                        socket.disconnectFromServer()
                        socket.close()
                        log_to_file("[Startup] Другой экземпляр уже запущен (mutex), передаем аргументы и выходим")
                        cleanup_single_instance(server_name, None)
                        sys.exit(0)
                    else:
                        # Экземпляр в другой сессии (admin/non-admin) или сервер ещё не поднялся — выходим, чтобы не плодить процессы
                        log_to_file("[Startup] Глобальный mutex существует, экземпляр в другой сессии или недоступен. Выходим.")
                        cleanup_single_instance(server_name, None)
                        sys.exit(0)

            # Если mutex новый или мы перезапускаемся — создаем локальный сервер
            # При перезапуске пропускаем проверку на существующий сервер, т.к. старый процесс уже закрывается
            if not is_restart:
                socket = QLocalSocket()
                socket.connectToServer(server_name)
                
                if socket.waitForConnected(500):
                    args = sys.argv[1:] if len(sys.argv) > 1 else []
                    if args:
                        data = '\n'.join(args).encode('utf-8')
                        socket.write(data)
                        socket.waitForBytesWritten(1000)
                        socket.flush()
                    socket.disconnectFromServer()
                    socket.close()
                    log_to_file("[Startup] Другой экземпляр уже запущен, передаем аргументы и выходим")
                    cleanup_single_instance(server_name, None)
                    sys.exit(0)
            
            # Удаляем старый сервер если есть (при перезапуске он должен быть удален старым процессом, но на всякий случай)
            QLocalServer.removeServer(server_name)
            
            local_server = QLocalServer()
            if not local_server.listen(server_name):
                error = local_server.errorString()
                log_to_file(f"[Startup Warning] Не удалось запустить локальный сервер: {error}")
                local_server = None
            else:
                log_to_file("[Startup] Локальный сервер запущен успешно")
        
        # Проверяем доступность системного трея
        # НЕ закрываем приложение если трей недоступен - просто не используем его
        tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        # Тема уже применена в create_application()
        
        # Иконка уже установлена в create_application() через IconManager
        # Дополнительно убеждаемся что она установлена
        from utils.icon_manager import set_application_icon
        set_application_icon(app)
        
        log_to_file("[Startup] Создание главного окна...")
        try:
            win = MainWindow()
            # Передаем локальный сервер в MainWindow
            if local_server:
                win.local_server = local_server
                local_server.setParent(win)
                win.local_server.newConnection.connect(win._handle_new_instance)
                log_to_file("[Startup] Локальный сервер подключен к MainWindow")
            log_to_file("[Startup] Главное окно создано успешно")
        except Exception as e:
            import traceback
            error_msg = f"[Startup Error] Ошибка создания главного окна: {e}\n{traceback.format_exc()}"
            log_to_file(error_msg)
            raise
        
        # Устанавливаем ссылку на MainWindow для показа логов из log_to_file в UI при isDebug=True
        try:
            set_main_window(win)
            log_to_file("[Startup] Ссылка на MainWindow установлена")
        except Exception as e:
            log_to_file(f"[Startup Warning] Ошибка установки ссылки на MainWindow: {e}")
        
        # Проверяем настройку run_as_admin при запуске
        try:
            run_as_admin_setting = win.settings.get("run_as_admin", False)
            if run_as_admin_setting and not is_admin():
                log_to_file("[Startup] Настройка 'run_as_admin' включена, но приложение не запущено от админа. Перезапуск...")
                if not restart_application(win, run_as_admin=True):
                    log_to_file("[Startup] Не удалось перезапустить от имени администратора")
        except Exception as e:
            log_to_file(f"[Startup Warning] Ошибка проверки run_as_admin: {e}")
        
        # Устанавливаем поведение закрытия окна в зависимости от настройки трея
        try:
            minimize_to_tray = win.settings.get("minimize_to_tray", True)
            app.setQuitOnLastWindowClosed(not minimize_to_tray)
            log_to_file(f"[Startup] Настройка закрытия окна: minimize_to_tray={minimize_to_tray}")
        except Exception as e:
            log_to_file(f"[Startup Warning] Ошибка настройки закрытия окна: {e}")
        
        # Убеждаемся, что трей показывается сразу после создания окна
        try:
            if win.tray_manager.tray_icon:
                win.tray_manager.show()
                log_to_file("[Startup] Трей иконка показана")
        except Exception as e:
            log_to_file(f"[Startup Warning] Ошибка показа трей иконки: {e}")
        
        log_to_file("[Startup] Показ главного окна...")
        try:
            win.show()
            log_to_file("[Startup] Главное окно показано")
        except Exception as e:
            import traceback
            error_msg = f"[Startup Error] Ошибка показа главного окна: {e}\n{traceback.format_exc()}"
            log_to_file(error_msg)
            raise
        
        log_to_file("[Startup] Запуск главного цикла приложения...")
        try:
            exit_code = app.exec_()
            log_to_file(f"[Startup] Главный цикл завершен с кодом: {exit_code}")
            sys.exit(exit_code)
        except Exception as e:
            import traceback
            error_msg = f"[Startup Error] Ошибка в главном цикле: {e}\n{traceback.format_exc()}"
            log_to_file(error_msg)
            raise
    except Exception as e:
        import traceback
        error_msg = f"[Fatal Error] Критическая ошибка при запуске приложения: {e}\n{traceback.format_exc()}"
        log_to_file(error_msg)
        # Показываем сообщение об ошибке пользователю
        try:
            show_info_dialog(
                None,
                "Ошибка запуска",
                f"Произошла критическая ошибка при запуске приложения:\n\n{str(e)}\n\nПроверьте файл логов: {LOG_FILE}"
            )
        except:
            pass
        sys.exit(1)
    finally:
        try:
            cleanup_single_instance("SingBox-UI-Instance", locals().get("local_server"))
        except Exception:
            pass

