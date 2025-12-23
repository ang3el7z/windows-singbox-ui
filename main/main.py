"""Главный файл приложения SingBox-UI"""
import sys
import subprocess
import ctypes
import os
import zipfile
import shutil
import tempfile
import time
from pathlib import Path


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

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QTextEdit, QStackedWidget,
    QSpinBox, QCheckBox, QInputDialog, QMessageBox, QDialog, QProgressBar,
    QLineEdit, QSystemTrayIcon, QMenu, QAction, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSharedMemory
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
import qtawesome as qta

# Импорты новых UI компонентов
from ui.widgets import CardWidget, NavButton
from ui.styles import StyleSheet, theme
from ui.tray_manager import TrayManager

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
from core.protocol import register_protocols, is_admin, restart_as_admin
from core.singbox_manager import StartSingBoxThread
from workers.init_worker import InitOperationsWorker
from workers.version_worker import CheckVersionWorker, CheckAppVersionWorker
from ui.dialogs.language_dialog import show_language_selection_dialog
from ui.dialogs.confirm_dialog import show_restart_admin_dialog, show_kill_all_confirm_dialog
from ui.dialogs.info_dialog import show_kill_all_success_dialog
import requests
from datetime import datetime
from utils.logger import log_to_file, set_main_window


def load_icon_with_logging(context: str = "window") -> QIcon:
    """
    Загружает иконку приложения из самого exe файла (встроена в ресурсы при сборке).
    Это 100% рабочий вариант - иконка всегда встроена в exe через PyInstaller.
    
    Args:
        context: Контекст загрузки ("window" или "app") для логирования
    """
    log_to_file(f"[Icon {context}] Начало загрузки иконки")
    
    if getattr(sys, 'frozen', False):
        # В собранном приложении - извлекаем иконку из самого exe
        exe_path = Path(sys.executable)
        log_to_file(f"[Icon {context}] Извлечение иконки из exe: {exe_path}")
        icon = QIcon(str(exe_path))
        
        if not icon.isNull():
            log_to_file(f"[Icon {context}] ✓ Успешно загружена иконка из exe")
            return icon
        else:
            log_to_file(f"[Icon {context}] ✗ Не удалось извлечь иконку из exe")
            return QIcon()
    else:
        # В режиме разработки - загружаем из папки icons
        root = Path(__file__).parent.parent
        icon_path = root / "icons" / "icon.ico"
        
        if not icon_path.exists():
            icon_path = root / "icons" / "icon.png"
        
        if icon_path.exists():
            log_to_file(f"[Icon {context}] Загрузка иконки из: {icon_path}")
            icon = QIcon(str(icon_path))
            
            if not icon.isNull():
                log_to_file(f"[Icon {context}] ✓ Успешно загружена иконка")
                return icon
        
        log_to_file(f"[Icon {context}] ✗ Иконка не найдена в режиме разработки")
        return QIcon()


# register_protocols, is_admin, restart_as_admin перенесены в core/protocol.py
# Все диалоги перенесены в ui/dialogs/


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        # Сначала создаем папки
        ensure_dirs()
        
        # Инициализируем менеджеры
        self.settings = SettingsManager()
        self.subs = SubscriptionManager()
        
        # Инициализируем менеджеры UI
        self.tray_manager = TrayManager(self)
        self.log_ui_manager = LogUIManager(self)
        self.deep_link_handler = DeepLinkHandler(self)
        
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
        self.logs_click_count = 0  # Счетчик кликов по заголовку логов для дебаг меню
        self.debug_section_visible = False  # Флаг видимости дебаг секции

        self.setWindowTitle(tr("app.title"))
        self.setMinimumSize(420, 780)

        # Устанавливаем иконку окна
        window_icon = load_icon_with_logging("window")
        if not window_icon.isNull():
            self.setWindowIcon(window_icon)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Стек страниц
        self.stack = QStackedWidget()
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
        nav.setFixedHeight(110)
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
        version_container = QWidget()
        version_container.setFixedHeight(30)
        version_layout = QHBoxLayout(version_container)
        version_layout.setContentsMargins(16, 0, 16, 0)
        version_layout.setAlignment(Qt.AlignCenter)
        
        self.lbl_app_version = QLabel()
        self.lbl_app_version.setFont(QFont("Segoe UI", 10))
        self.lbl_app_version.setStyleSheet(StyleSheet.label(variant="secondary", size="medium"))
        self.lbl_app_version.setAlignment(Qt.AlignCenter)
        version_layout.addWidget(self.lbl_app_version)
        
        from ui.styles import theme
        version_container.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.get_color('background_primary')};
                border: none;
            }}
        """)
        
        root.addWidget(version_container)
        root.addWidget(nav)

        # Инициализация
        # Проверяем права администратора
        self.is_admin = is_admin()
        
        # Выносим тяжелые операции в потоки, чтобы не блокировать UI
        QTimer.singleShot(0, self._init_async_operations)
        
        # Обновляем UI элементы, которые не требуют данных
        if hasattr(self, 'lbl_admin_status'):
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
        
        if running_sub and selected_sub:
            if self.running_sub_index == self.current_sub_index:
                self.page_home.lbl_profile.setText(tr("home.current_profile", name=running_sub.get("name", tr("profile.unknown"))))
                self.page_home.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
            else:
                text = f"{tr('home.current_profile', name=running_sub.get('name', tr('profile.unknown')))}\n    {tr('home.selected_profile', name=selected_sub.get('name', tr('profile.unknown')))}"
                self.page_home.lbl_profile.setText(text)
                self.page_home.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
        elif running_sub:
            self.page_home.lbl_profile.setText(tr("home.current_profile", name=running_sub.get("name", tr("profile.unknown"))))
            self.page_home.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
        elif selected_sub:
            self.page_home.lbl_profile.setText(tr("home.selected_profile", name=selected_sub.get("name", tr("profile.unknown"))))
            self.page_home.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
        else:
            self.page_home.lbl_profile.setText(tr("home.profile_not_selected_click"))
            self.page_home.lbl_profile.setStyleSheet("color: #9ca3af; background-color: transparent; border: none; padding: 0px; cursor: pointer;")
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
        if current_version:
            self.page_home.lbl_version.setText(tr("home.installed", version=current_version))
            self.page_home.lbl_version.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px;")
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
                    if hasattr(self.page_home, 'btn_version_update'):
                        self.page_home.btn_version_update.show()
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

    # UI helpers (устаревшие методы, оставлены для обратной совместимости)
    def make_nav_button(self, text: str, icon_name: str) -> QPushButton:
        """Создает кнопку навигации (использует новый NavButton)"""
        return NavButton(text, icon_name)

    def build_card(self) -> QWidget:
        """Создает карточку (использует новый CardWidget)"""
        return CardWidget()

    # Страницы перенесены в ui/pages/ - ProfilePage, HomePage, SettingsPage

    # Навигация
    def switch_page(self, index: int):
        """Переключение страниц"""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate([self.btn_nav_profile, self.btn_nav_home, self.btn_nav_settings]):
            btn.setChecked(i == index)
        if index == 2:  # Settings page
            # Загружаем логи при открытии страницы
            if hasattr(self, 'page_settings'):
                self.page_settings.load_logs()
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
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("profile.add_subscription"))
        dialog.setMinimumWidth(420)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0b0f1a;
            }
            QLabel {
                color: #e5e9ff;
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QLineEdit {
                background-color: #1a1f2e;
                color: #e5e9ff;
                border: 1px solid rgba(0,245,212,0.2);
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00f5d4;
                background-color: #1f2937;
            }
            QPushButton {
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                border: none;
            }
            QPushButton#btnAdd {
                background-color: #00f5d4;
                color: #020617;
            }
            QPushButton#btnAdd:hover {
                background-color: #5fffe3;
            }
            QPushButton#btnCancel {
                background-color: rgba(255,255,255,0.05);
                color: #9ca3af;
            }
            QPushButton#btnCancel:hover {
                background-color: rgba(255,255,255,0.1);
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Заголовок
        title_label = QLabel(tr("profile.add_subscription"))
        title_label.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 8px;")
        layout.addWidget(title_label)
        
        # Название
        name_label = QLabel(tr("profile.name"))
        name_label.setStyleSheet("margin-top: 8px;")
        layout.addWidget(name_label)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText(tr("profile.name"))
        layout.addWidget(name_input)
        
        # URL
        url_label = QLabel(tr("profile.url"))
        url_label.setStyleSheet("margin-top: 8px;")
        layout.addWidget(url_label)
        
        url_input = QLineEdit()
        url_input.setPlaceholderText("https://...")
        layout.addWidget(url_input)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        btn_cancel = QPushButton(tr("download.cancel"))
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_add = QPushButton(tr("profile.add"))
        btn_add.setObjectName("btnAdd")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setDefault(True)
        
        def on_add_clicked():
            name = name_input.text().strip()
            url = url_input.text().strip()
            if name and url:
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
                dialog.accept()
            else:
                QMessageBox.warning(dialog, tr("profile.add_subscription"), tr("profile.fill_all_fields"))
        
        btn_add.clicked.connect(on_add_clicked)
        btn_layout.addWidget(btn_add)
        
        layout.addLayout(btn_layout)
        
        # Фокус на первое поле
        name_input.setFocus()
        
        if dialog.exec_() == QDialog.Accepted:
            pass  # Уже обработано в on_add_clicked

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
        new_name, ok = QInputDialog.getText(
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
        # Отключаем кнопку на время теста
        if hasattr(self.page_profile, 'btn_test_sub'):
            self.page_profile.btn_test_sub.setEnabled(False)
            self.page_profile.btn_test_sub.setText(tr("profile.test") + "...")
        
        try:
            ok = self.subs.download_config(row)
            if ok:
                self.log(tr("profile.test_success"))
                # Показываем успешное сообщение более заметно
                msg = QMessageBox(self)
                msg.setWindowTitle(tr("profile.test"))
                msg.setText(tr("profile.test_success"))
                msg.setInformativeText(f"Subscription '{sub_name}' works correctly. Config downloaded successfully.")
                msg.setIcon(QMessageBox.Information)
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #0b0f1a;
                    }
                    QLabel {
                        color: #e5e9ff;
                    }
                    QPushButton {
                        background-color: #1a1f2e;
                        color: #00f5d4;
                        border: 2px solid #00f5d4;
                        border-radius: 8px;
                        padding: 8px 16px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: rgba(0,245,212,0.1);
                    }
                """)
                msg.exec_()
            else:
                self.log(tr("profile.test_error"))
                # Показываем ошибку более заметно
                msg = QMessageBox(self)
                msg.setWindowTitle(tr("profile.test"))
                msg.setText(tr("profile.test_error"))
                msg.setInformativeText(f"Failed to download config from subscription '{sub_name}'. Please check the URL.")
                msg.setIcon(QMessageBox.Warning)
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #0b0f1a;
                    }
                    QLabel {
                        color: #e5e9ff;
                    }
                    QPushButton {
                        background-color: #1a1f2e;
                        color: #00f5d4;
                        border: 2px solid #00f5d4;
                        border-radius: 8px;
                        padding: 8px 16px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: rgba(0,245,212,0.1);
                    }
                """)
                msg.exec_()
        finally:
            # Восстанавливаем кнопку
            if hasattr(self, 'page_profile') and hasattr(self.page_profile, 'btn_test_sub'):
                self.page_profile.btn_test_sub.setEnabled(True)
                self.page_profile.btn_test_sub.setText(tr("profile.test"))
    
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
                    if hasattr(self.page_home, 'btn_version_update'):
                        self.page_home.btn_version_update.show()
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
                # Делаем кликабельным для открытия диалога обновления
                if not hasattr(self.lbl_app_version, '_click_handler'):
                    self.lbl_app_version.mousePressEvent = lambda e: self.show_app_update_dialog() if e.button() == Qt.LeftButton else None
                    self.lbl_app_version._click_handler = True
            else:
                # Нет обновления
                self.lbl_app_version.setText(tr("app.version", version=self.app_version))
                self.lbl_app_version.setStyleSheet(StyleSheet.label(variant="secondary"))
                if hasattr(self.lbl_app_version, '_click_handler'):
                    self.lbl_app_version.mousePressEvent = None
                    delattr(self.lbl_app_version, '_click_handler')
        else:
            # Показываем текущую версию
            self.lbl_app_version.setText(tr("app.version", version=self.app_version))
            self.lbl_app_version.setStyleSheet("color: #64748b; background-color: transparent; border: none; padding: 0px;")
            if hasattr(self.lbl_app_version, '_click_handler'):
                self.lbl_app_version.mousePressEvent = None
                delattr(self.lbl_app_version, '_click_handler')
    
    
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
            QMessageBox.warning(self, tr("app.update_error_title"), f"updater.exe not found at {updater_exe}")
            return
        
        log_to_file(f"[App Update] Starting updater.exe with version: {self.cached_app_latest_version}")
        
        # Запускаем updater.exe с версией
        try:
            subprocess.Popen(
                [str(updater_exe), self.cached_app_latest_version],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            # Даем время на запуск updater
            time.sleep(1)
            
            # Закрываем приложение - updater сам все сделает
            self.log(tr("app.update_complete"))
            QApplication.quit()
        except Exception as e:
            log_to_file(f"[App Update] Error starting updater: {e}")
            QMessageBox.warning(self, tr("app.update_error_title"), f"Error starting updater: {e}")
    
    def update_profile_info(self):
        """Обновление информации о профиле"""
        if not hasattr(self, 'page_home') or not hasattr(self.page_home, 'lbl_profile'):
            return
        running = self.proc and self.proc.poll() is None
        running_sub = None
        selected_sub = None
        
        # Получаем запущенный профиль
        if running and self.running_sub_index >= 0 and self.sub_list.count() > 0:
            running_sub = self.subs.get(self.running_sub_index)
        
        # Получаем выбранный профиль
        if self.current_sub_index >= 0 and self.sub_list.count() > 0:
            selected_sub = self.subs.get(self.current_sub_index)
        
        # Формируем текст
        if running_sub and selected_sub:
            if self.running_sub_index == self.current_sub_index:
                # Профили совпадают
                self.page_home.lbl_profile.setText(tr("home.current_profile", name=running_sub.get("name", tr("profile.unknown"))))
                self.page_home.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
            else:
                # Профили разные - добавляем отступ для второй строки
                text = f"{tr('home.current_profile', name=running_sub.get('name', tr('profile.unknown')))}\n    {tr('home.selected_profile', name=selected_sub.get('name', tr('profile.unknown')))}"
                self.page_home.lbl_profile.setText(text)
                self.page_home.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
        elif running_sub:
            # Только запущенный профиль
            self.page_home.lbl_profile.setText(tr("home.current_profile", name=running_sub.get("name", tr("profile.unknown"))))
            self.page_home.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
        elif selected_sub:
            # Только выбранный профиль
            self.page_home.lbl_profile.setText(tr("home.selected_profile", name=selected_sub.get("name", tr("profile.unknown"))))
            self.page_home.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
        else:
            # Нет профиля
            self.page_home.lbl_profile.setText(tr("home.profile_not_selected_click"))
            self.page_home.lbl_profile.setStyleSheet("color: #9ca3af; background-color: transparent; border: none; padding: 0px; cursor: pointer;")
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
        if is_admin():
            self.page_home.lbl_admin_status.setText(tr("home.admin_running"))
            self.page_home.lbl_admin_status.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px;")
            self.page_home.lbl_admin_status.setCursor(Qt.ArrowCursor)
        else:
            self.page_home.lbl_admin_status.setText(tr("home.admin_not_running"))
            self.page_home.lbl_admin_status.setStyleSheet("color: #ffa500; background-color: transparent; border: none; padding: 0px; text-decoration: underline;")
            self.page_home.lbl_admin_status.setCursor(Qt.PointingHandCursor)
    
    def admin_status_mouse_press(self, event):
        """Обработка клика по надписи о правах администратора"""
        if not is_admin():
            if show_restart_admin_dialog(
                self,
                tr("messages.admin_required_title"),
                tr("messages.restart_as_admin_question")
            ):
                if restart_as_admin():
                    self.close()
                else:
                    self.log(tr("messages.admin_restart_failed"))
        else:
            event.ignore()
    
    def handle_deep_link(self):
        """Обработка deep link для импорта подписки (поддержка sing-box:// и singbox-ui://)"""
        self.deep_link_handler.handle()
    
    def show_download_dialog(self):
        """Диалог загрузки SingBox"""
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("download.title"))
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0b0f1a;
            }
            QLabel {
                color: #e5e9ff;
            }
            QPushButton {
                background-color: #00f5d4;
                color: #020617;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                border: none;
            }
            QPushButton:hover {
                background-color: #5fffe3;
            }
            QPushButton:disabled {
                background-color: #475569;
                color: #94a3b8;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel(tr("download.not_installed"))
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)
        
        info = QLabel(tr("download.description"))
        info.setWordWrap(True)
        layout.addWidget(info)
        
        self.download_progress = QProgressBar()
        self.download_progress.setRange(0, 100)
        self.download_progress.setValue(0)
        self.download_progress.hide()
        layout.addWidget(self.download_progress)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton(tr("download.cancel"))
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_download = QPushButton(tr("download.download"))
        btn_download.clicked.connect(lambda: self.start_download(dialog, btn_download))
        btn_layout.addWidget(btn_download)
        
        layout.addLayout(btn_layout)
        
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
            QMessageBox.information(dialog, tr("download.success"), message)
            dialog.accept()
            self.update_version_info()
        else:
            QMessageBox.warning(dialog, tr("download.error"), message)
            btn_download.setEnabled(True)
            btn_download.setText(tr("download.download"))
    
    # Кнопка Start/Stop
    def style_big_btn_running(self, running: bool):
        """Стиль большой кнопки"""
        if not hasattr(self, 'page_home'):
            return
        # Проверяем, нужно ли показать "Сменить" (оранжевый цвет)
        is_change_mode = (running and 
                         self.running_sub_index != self.current_sub_index and 
                         self.current_sub_index >= 0)
        
        # Обновляем подложку
        if hasattr(self.page_home, 'btn_wrapper'):
            if running:
                if is_change_mode:
                    # Оранжевый для режима "Сменить"
                    border_color = "rgba(255,165,0,0.5)"  # Оранжевый
                else:
                    # Красный для режима "Остановить"
                    border_color = "rgba(255,107,107,0.5)"
                self.page_home.btn_wrapper.setStyleSheet(f"""
                    QWidget {{
                        background-color: #1a1f2e;
                        border-radius: 110px;
                        border: 2px solid {border_color};
                    }}
                """)
            else:
                self.page_home.btn_wrapper.setStyleSheet("""
                    QWidget {
                        background-color: #1a1f2e;
                        border-radius: 110px;
                        border: 2px solid rgba(0,245,212,0.5);
                    }
                """)
        
        if running:
            # Текст кнопки устанавливается в update_big_button_state, здесь только стиль
            if is_change_mode:
                # Оранжевый стиль для кнопки "Сменить"
                self.page_home.big_btn.setStyleSheet("""
                    QPushButton {
                        border-radius: 100px;
                        background-color: #1a1f2e;
                        color: #ffa500;
                        font-size: 28px;
                        font-weight: 700;
                        font-family: 'Segoe UI', sans-serif;
                        border: 2px solid #ffa500;
                    }
                    QPushButton:hover {
                        background-color: rgba(255,165,0,0.1);
                        border: 2px solid #ffb733;
                    }
                    QPushButton:disabled {
                        background-color: #475569;
                        color: #94a3b8;
                        border: 2px solid #475569;
                    }
                """)
            else:
                # Красный стиль для кнопки "Остановить"
                self.page_home.big_btn.setStyleSheet("""
                    QPushButton {
                        border-radius: 100px;
                        background-color: #1a1f2e;
                        color: #ff6b6b;
                        font-size: 28px;
                        font-weight: 700;
                        font-family: 'Segoe UI', sans-serif;
                        border: 2px solid #ff6b6b;
                    }
                    QPushButton:hover {
                        background-color: rgba(255,107,107,0.1);
                        border: 2px solid #ff8787;
                    }
                    QPushButton:disabled {
                        background-color: #475569;
                        color: #94a3b8;
                        border: 2px solid #475569;
                    }
                """)
        else:
            # Текст кнопки устанавливается в update_big_button_state, здесь только стиль
            self.page_home.big_btn.setStyleSheet("""
                QPushButton {
                    border-radius: 100px;
                    background-color: #1a1f2e;
                    color: #00f5d4;
                    font-size: 28px;
                    font-weight: 700;
                    font-family: 'Segoe UI', sans-serif;
                    border: 2px solid #00f5d4;
                }
                QPushButton:hover {
                    background-color: rgba(0,245,212,0.1);
                    border: 2px solid #5fffe3;
                }
                QPushButton:disabled {
                    background-color: #475569;
                    color: #94a3b8;
                    border: 2px solid #475569;
                }
            """)

    def update_big_button_state(self):
        """Обновление состояния большой кнопки"""
        if not hasattr(self, 'page_home') or not hasattr(self.page_home, 'big_btn'):
            return
        core_ok = CORE_EXE.exists()
        running = self.proc and self.proc.poll() is None
        
        if running:
            # Если запущен - кнопка всегда активна (можно остановить)
            self.page_home.big_btn.setEnabled(core_ok)
            # Проверяем, совпадает ли выбранный профиль с запущенным
            if self.running_sub_index != self.current_sub_index and self.current_sub_index >= 0:
                # Выбран другой профиль - показываем "Сменить"
                self.page_home.big_btn.setText(tr("home.button_change"))
            else:
                # Профили совпадают или не выбран - показываем "Остановить"
                self.page_home.big_btn.setText(tr("home.button_stop"))
        else:
            # Если не запущен - нужен выбранный профиль
            has_sub = False
            if hasattr(self, 'page_profile') and hasattr(self.page_profile, 'sub_list'):
                has_sub = self.page_profile.sub_list.count() > 0 and self.current_sub_index >= 0
            self.page_home.big_btn.setEnabled(core_ok and has_sub)
            self.page_home.big_btn.setText(tr("home.button_start"))
        
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
                if restart_as_admin():
                    self.close()
                    return
                else:
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
                if restart_as_admin():
                    # Закрываем текущее приложение
                    self.close()
                    return
                else:
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
        """Изменение интервала автообновления"""
        if not hasattr(self, 'page_settings') or not hasattr(self.page_settings, 'edit_interval'):
            return
        try:
            value = int(self.page_settings.edit_interval.text())
            if 5 <= value <= 1440:
                self.settings.set("auto_update_minutes", value)
                self.update_timer.start(value * 60 * 1000)
                self.log(tr("messages.interval_changed", value=value))
            else:
                # Восстанавливаем значение если вне диапазона
                self.page_settings.edit_interval.setText(str(self.settings.get("auto_update_minutes", 90)))
        except ValueError:
            # Восстанавливаем значение если не число
            self.page_settings.edit_interval.setText(str(self.settings.get("auto_update_minutes", 90)))
    
    def on_logs_title_clicked(self):
        """Обработка клика по заголовку логов для показа дебаг меню"""
        if not hasattr(self, 'page_settings'):
            return
        self.logs_click_count += 1
        if self.logs_click_count >= 6:
            self.debug_section_visible = not self.debug_section_visible
            if hasattr(self.page_settings, 'debug_card'):
                self.page_settings.debug_card.setVisible(self.debug_section_visible)
            self.logs_click_count = 0  # Сбрасываем счетчик
            
            # Переключаем настройку isDebug
            current_debug = self.settings.get("isDebug", False)
            new_debug = not current_debug
            self.settings.set("isDebug", new_debug)
            
            # Автоматически обновляем видимость debug логов на основе isDebug
            self._update_debug_logs_visibility()
            
            if self.debug_section_visible:
                log_to_file(f"Debug меню активировано (isDebug: {new_debug})")
            else:
                log_to_file(f"Debug меню скрыто (isDebug: {new_debug})")
    
    def _update_debug_logs_visibility(self):
        """Обновляет видимость debug логов на основе настройки isDebug"""
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
                if restart_as_admin():
                    self.close()
                    return
                else:
                    self.log(tr("messages.admin_restart_failed"))
                    # Восстанавливаем состояние чекбокса при ошибке
                    if hasattr(self, 'page_settings') and hasattr(self.page_settings, 'cb_run_as_admin'):
                        self.page_settings.cb_run_as_admin.blockSignals(True)
                        self.page_settings.cb_run_as_admin.setChecked(False)
                        self.settings.set("run_as_admin", False)
                        self.page_settings.cb_run_as_admin.blockSignals(False)
        elif not enabled and is_admin():
            # Если выключили галочку, но приложение запущено от админа
            # Предлагаем перезапустить без прав админа
            if show_restart_admin_dialog(
                self,
                tr("messages.restart_required_title"),
                "Для применения настройки 'Запускать от имени администратора' требуется перезапустить приложение.\n\nПерезапустить сейчас?"
            ):
                # Перезапускаем без прав админа
                try:
                    exe_path = sys.executable
                    work_dir = str(Path(exe_path).parent)
                    # Запускаем новый процесс без прав админа
                    result = ctypes.windll.shell32.ShellExecuteW(
                        None, "open", exe_path, "", work_dir, 1
                    )
                    if result > 32:
                        app = QApplication.instance()
                        if app:
                            QTimer.singleShot(2000, lambda: app.quit() if app else None)
                        self.close()
                        return
                except Exception as e:
                    log_to_file(f"Ошибка перезапуска без прав админа: {e}")
        
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
    
    def refresh_ui_texts(self):
        """Обновление всех текстов в интерфейсе после смены языка"""
        # Обновляем заголовок окна
        self.setWindowTitle(tr("app.title"))
        
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
            if hasattr(self.page_profile, 'btn_test_sub'):
                self.page_profile.btn_test_sub.setText(tr("profile.test"))
        
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
        if hasattr(self, 'label_interval'):
            self.label_interval.setText(tr("settings.auto_update_interval"))
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
        
        # Определяем цвет в зависимости от состояния кнопки
        color = "#00f5d4" if btn.isChecked() else "#64748b"
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
            icon_label.setPixmap(qta.icon(icon_name, color=color).pixmap(36, 36))
        
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
    
    def quit_application(self):
        """Полное закрытие приложения с остановкой всех процессов"""
        self.kill_all_processes()
        self.tray_manager.cleanup()
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
        event.accept()


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
        
        # Загружаем настройки для проверки разрешения нескольких процессов
        settings = SettingsManager()
        allow_multiple = settings.get("allow_multiple_processes", True)
        
        # Регистрируем/обновляем протоколы при каждом запуске (без лишних логов)
        try:
            register_protocols()
        except Exception:
            pass
    
        # Проверка единственного экземпляра приложения (только если не разрешены несколько процессов)
        shared_memory = QSharedMemory("SingBox-UI-Instance")
        if not allow_multiple and shared_memory.attach():
            # Приложение уже запущено - проверяем, что процесс действительно работает
            try:
                import psutil
                exe_name = Path(sys.executable).name
                current_pid = os.getpid()
                found_process = False
                
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        if proc.info['name'] and exe_name.lower() in proc.info['name'].lower():
                            if proc.info['pid'] != current_pid:
                                # Проверяем, что процесс действительно работает
                                if proc.is_running():
                                    found_process = True
                                    break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                
                if found_process:
                    # Процесс работает, пытаемся активировать окно
                    try:
                        import win32gui
                        import win32con
                        
                        def enum_windows_callback(hwnd, windows):
                            # Проверяем все окна, не только видимые (включая свернутые в трей)
                            window_text = win32gui.GetWindowText(hwnd)
                            if "SingBox-UI" in window_text:
                                # Проверяем, что это действительно наше окно
                                class_name = win32gui.GetClassName(hwnd)
                                if "QWidget" in class_name or "Qt5QWindow" in class_name or "MainWindow" in class_name:
                                    windows.append(hwnd)
                            return True
                        
                        windows = []
                        win32gui.EnumWindows(enum_windows_callback, windows)
                        
                        if windows:
                            hwnd = windows[0]
                            # Восстанавливаем окно (даже если оно скрыто)
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                            # Активируем окно
                            win32gui.SetForegroundWindow(hwnd)
                            win32gui.BringWindowToTop(hwnd)
                            # Отправляем сообщение для активации
                            win32gui.SetActiveWindow(hwnd)
                    except ImportError:
                        try:
                            user32 = ctypes.windll.user32
                            def enum_windows_proc(hwnd, lParam):
                                # Проверяем все окна, не только видимые
                                length = user32.GetWindowTextLengthW(hwnd)
                                if length > 0:
                                    buffer = ctypes.create_unicode_buffer(length + 1)
                                    user32.GetWindowTextW(hwnd, buffer, length + 1)
                                    if "SingBox-UI" in buffer.value:
                                        # Восстанавливаем и показываем окно
                                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                                        user32.ShowWindow(hwnd, 5)  # SW_SHOW
                                        user32.SetForegroundWindow(hwnd)
                                        user32.BringWindowToTop(hwnd)
                                        user32.SetActiveWindow(hwnd)
                                return True
                            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
                            user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    
                    sys.exit(0)
                else:
                    # Процесс не найден, но shared memory существует - освобождаем и продолжаем
                    shared_memory.detach()
            except ImportError:
                # Если psutil не доступен, просто пытаемся активировать окно
                try:
                    import win32gui
                    import win32con
                    def enum_windows_callback(hwnd, windows):
                        if win32gui.IsWindowVisible(hwnd):
                            window_text = win32gui.GetWindowText(hwnd)
                            if "SingBox-UI" in window_text:
                                windows.append(hwnd)
                        return True
                    windows = []
                    win32gui.EnumWindows(enum_windows_callback, windows)
                    if windows:
                        hwnd = windows[0]
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                        win32gui.BringWindowToTop(hwnd)
                        sys.exit(0)
                except Exception:
                    pass
        
        # Создаем shared memory для этого экземпляра (только если не разрешены несколько процессов)
        if not allow_multiple:
            if not shared_memory.create(1):
                # Если не удалось создать, возможно старый экземпляр завис - пробуем еще раз
                try:
                    shared_memory.detach()
                    if not shared_memory.create(1):
                        sys.exit(0)
                except Exception:
                    sys.exit(0)
        
        # Проверяем доступность системного трея
        # НЕ закрываем приложение если трей недоступен - просто не используем его
        tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        # Тема уже применена в create_application()
        
        # Устанавливаем иконку приложения для QApplication (чтобы Windows показывала её в заголовке)
        app_icon = load_icon_with_logging("app")
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
        
        log_to_file("[Startup] Создание главного окна...")
        try:
            win = MainWindow()
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
                if restart_as_admin():
                    sys.exit(0)
                else:
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
            QMessageBox.critical(
                None,
                "Ошибка запуска",
                f"Произошла критическая ошибка при запуске приложения:\n\n{str(e)}\n\nПроверьте файл логов: {LOG_FILE}"
            )
        except:
            pass
        sys.exit(1)

