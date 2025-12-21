"""Главный файл приложения SingBox-UI"""
__version__ = "1.1.0"  # Версия приложения

import sys
import subprocess
import ctypes
import os
import zipfile
import shutil
import tempfile
import time
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QTextEdit, QStackedWidget,
    QSpinBox, QCheckBox, QInputDialog, QMessageBox, QDialog, QProgressBar,
    QLineEdit, QSystemTrayIcon, QMenu, QAction, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSharedMemory
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
import qtawesome as qta

# Импорты из архитектуры проекта
from config.paths import (
    ensure_dirs, CORE_EXE, CONFIG_FILE, LOG_FILE, CORE_DIR
)
from managers.settings import SettingsManager
from managers.subscriptions import SubscriptionManager
from utils.i18n import tr, set_language, get_available_languages, get_language_name, Translator
from utils.singbox import get_singbox_version, get_latest_version, compare_versions, get_app_latest_version
from core.downloader import DownloadThread
import requests
from datetime import datetime
from utils.logger import log_to_file, set_main_window


def register_protocols():
    """Регистрация протоколов sing-box:// и singbox-ui:// в Windows (без прав админа)"""
    if sys.platform != "win32":
        return False
    
    try:
        import winreg
        protocols = ["sing-box", "singbox-ui"]
        
        # Получаем путь к exe файлу
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = sys.executable
            script_path = Path(__file__).parent / "main.py"
            exe_path = f'"{exe_path}" "{script_path}"'
        
        for protocol in protocols:
            key_path = f"Software\\Classes\\{protocol}"
            
            # Создаем ключ протокола
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"URL:{protocol} Protocol")
                winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            # Создаем ключ для команды по умолчанию
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\shell\\open\\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{exe_path}" "%1"')
        
        return True
    except Exception as e:
        log_to_file(f"[Protocol Registration] Ошибка регистрации протокола: {e}")
        return False


def is_admin():
    """Проверка, запущено ли приложение от имени администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def restart_as_admin():
    """Перезапуск приложения от имени администратора"""
    if is_admin():
        return False

    try:
        exe_path = sys.executable  # PyInstaller: это ваш .exe
        # Передаем рабочий каталог, чтобы новый процесс запускался в правильной директории
        work_dir = str(Path(exe_path).parent)
        
        # Запускаем новый процесс от имени администратора
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe_path, "", work_dir, 1  # SW_SHOWNORMAL = 1
        )
        
        # ShellExecuteW возвращает значение > 32 при успехе
        if result <= 32:
            log_to_file(f"[Admin Restart] Ошибка запуска от имени администратора: код {result}")
            return False

        log_to_file(f"[Admin Restart] Новый процесс запущен от имени администратора, PID должен быть > 32: {result}")
        
        # Даем больше времени новому процессу запуститься перед закрытием старого
        # Это важно для корректной работы QSharedMemory и трея
        app = QApplication.instance()
        if app:
            # Используем QTimer чтобы не блокировать UI поток
            # Увеличиваем задержку до 2 секунд, чтобы новый процесс успел полностью запуститься
            QTimer.singleShot(2000, lambda: app.quit() if app else None)
        return True
    except Exception as e:
        import traceback
        error_msg = f"[Admin Restart] Исключение при перезапуске: {e}\n{traceback.format_exc()}"
        log_to_file(error_msg)
        return False

def show_restart_admin_dialog(parent, title, message):
    """Кастомный диалог для перезапуска от имени администратора"""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(400)
    dialog.setModal(True)
    dialog.setStyleSheet("""
        QDialog {
            background-color: #0b0f1a;
            border-radius: 12px;
        }
        QLabel {
            color: #e5e9ff;
            background-color: transparent;
            border: none;
        }
        QPushButton {
            border-radius: 12px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            border: none;
        }
        QPushButton#btnYes {
            background-color: #00f5d4;
            color: #020617;
        }
        QPushButton#btnYes:hover {
            background-color: #5fffe3;
        }
        QPushButton#btnNo {
            background-color: rgba(255,255,255,0.05);
            color: #9ca3af;
        }
        QPushButton#btnNo:hover {
            background-color: rgba(255,255,255,0.1);
        }
    """)
    
    layout = QVBoxLayout(dialog)
    layout.setSpacing(20)
    layout.setContentsMargins(24, 24, 24, 24)
    
    # Иконка и заголовок
    title_label = QLabel(title)
    title_label.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
    title_label.setStyleSheet("color: #ffffff; margin-bottom: 8px;")
    layout.addWidget(title_label)
    
    # Сообщение
    message_label = QLabel(message)
    message_label.setWordWrap(True)
    message_label.setFont(QFont("Segoe UI", 13))
    message_label.setStyleSheet("color: #9ca3af; margin-bottom: 8px;")
    layout.addWidget(message_label)
    
    # Кнопки
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(12)
    
    btn_no = QPushButton(tr("download.cancel"))
    btn_no.setObjectName("btnNo")
    btn_no.setCursor(Qt.PointingHandCursor)
    btn_no.clicked.connect(dialog.reject)
    btn_layout.addWidget(btn_no)
    
    btn_yes = QPushButton(tr("messages.restart_yes"))
    btn_yes.setObjectName("btnYes")
    btn_yes.setCursor(Qt.PointingHandCursor)
    btn_yes.setDefault(True)
    btn_yes.clicked.connect(dialog.accept)
    btn_layout.addWidget(btn_yes)
    
    layout.addLayout(btn_layout)
    
    return dialog.exec_() == QDialog.Accepted


def show_kill_all_confirm_dialog(parent, title, message):
    """Кастомный диалог для подтверждения остановки всех процессов"""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(450)
    dialog.setModal(True)
    dialog.setStyleSheet("""
        QDialog {
            background-color: #0b0f1a;
            border-radius: 12px;
        }
        QLabel {
            color: #e5e9ff;
            background-color: transparent;
            border: none;
        }
        QPushButton {
            border-radius: 12px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            border: none;
        }
        QPushButton#btnYes {
            background-color: #ff6b6b;
            color: #ffffff;
        }
        QPushButton#btnYes:hover {
            background-color: #ff8787;
        }
        QPushButton#btnNo {
            background-color: rgba(255,255,255,0.05);
            color: #9ca3af;
        }
        QPushButton#btnNo:hover {
            background-color: rgba(255,255,255,0.1);
        }
    """)
    
    layout = QVBoxLayout(dialog)
    layout.setSpacing(20)
    layout.setContentsMargins(24, 24, 24, 24)
    
    # Иконка и заголовок
    title_label = QLabel(title)
    title_label.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
    title_label.setStyleSheet("color: #ffffff; margin-bottom: 8px;")
    layout.addWidget(title_label)
    
    # Сообщение
    message_label = QLabel(message)
    message_label.setWordWrap(True)
    message_label.setFont(QFont("Segoe UI", 13))
    message_label.setStyleSheet("color: #9ca3af; margin-bottom: 8px;")
    layout.addWidget(message_label)
    
    # Кнопки
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(12)
    
    btn_no = QPushButton(tr("download.cancel"))
    btn_no.setObjectName("btnNo")
    btn_no.setCursor(Qt.PointingHandCursor)
    btn_no.clicked.connect(dialog.reject)
    btn_layout.addWidget(btn_no)
    
    btn_yes = QPushButton(tr("messages.kill_all_yes"))
    btn_yes.setObjectName("btnYes")
    btn_yes.setCursor(Qt.PointingHandCursor)
    btn_yes.setDefault(True)
    btn_yes.clicked.connect(dialog.accept)
    btn_layout.addWidget(btn_yes)
    
    layout.addLayout(btn_layout)
    
    return dialog.exec_() == QDialog.Accepted


def show_language_selection_dialog(parent) -> str:
    """Диалог выбора языка при первом запуске"""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Select Language / Выберите язык")
    dialog.setMinimumWidth(400)
    dialog.setModal(True)
    dialog.setStyleSheet("""
        QDialog {
            background-color: #0b0f1a;
            border-radius: 12px;
        }
        QLabel {
            color: #e5e9ff;
            background-color: transparent;
            border: none;
        }
        QPushButton {
            border-radius: 12px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            border: 2px solid #00f5d4;
            background-color: transparent;
            color: #00f5d4;
            margin: 4px;
        }
        QPushButton:hover {
            background-color: rgba(0,245,212,0.1);
        }
        QPushButton:default {
            background-color: #00f5d4;
            color: #020617;
        }
    """)
    
    layout = QVBoxLayout(dialog)
    layout.setSpacing(20)
    layout.setContentsMargins(24, 24, 24, 24)
    
    # Заголовок
    title_label = QLabel("Select Language / Выберите язык")
    title_label.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
    title_label.setStyleSheet("color: #ffffff; margin-bottom: 8px;")
    layout.addWidget(title_label)
    
    # Список языков
    available_languages = get_available_languages()
    selected_language = ["en"]  # Используем список для изменения в lambda
    
    def select_language(lang_code):
        selected_language[0] = lang_code
        dialog.accept()
    
    for lang_code in available_languages:
        lang_name = get_language_name(lang_code)
        btn = QPushButton(lang_name)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda checked, l=lang_code: select_language(l))
        layout.addWidget(btn)
    
    # Кнопка OK (используем английский по умолчанию)
    btn_ok = QPushButton("OK")
    btn_ok.setCursor(Qt.PointingHandCursor)
    btn_ok.setDefault(True)
    btn_ok.clicked.connect(dialog.accept)
    layout.addWidget(btn_ok)
    
    if dialog.exec_() == QDialog.Accepted:
        return selected_language[0]
    return "en"  # Fallback на английский


def show_kill_all_success_dialog(parent, title, message):
    """Кастомный диалог для уведомления об успешной остановке процессов"""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(400)
    dialog.setModal(True)
    dialog.setStyleSheet("""
        QDialog {
            background-color: #0b0f1a;
            border-radius: 12px;
        }
        QLabel {
            color: #e5e9ff;
            background-color: transparent;
            border: none;
        }
        QPushButton {
            border-radius: 12px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            border: none;
            background-color: #00f5d4;
            color: #020617;
        }
        QPushButton:hover {
            background-color: #5fffe3;
        }
    """)
    
    layout = QVBoxLayout(dialog)
    layout.setSpacing(20)
    layout.setContentsMargins(24, 24, 24, 24)
    
    # Иконка и заголовок
    title_label = QLabel(title)
    title_label.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
    title_label.setStyleSheet("color: #ffffff; margin-bottom: 8px;")
    layout.addWidget(title_label)
    
    # Сообщение
    message_label = QLabel(message)
    message_label.setWordWrap(True)
    message_label.setFont(QFont("Segoe UI", 13))
    message_label.setStyleSheet("color: #9ca3af; margin-bottom: 8px;")
    layout.addWidget(message_label)
    
    # Кнопка OK
    btn_ok = QPushButton(tr("messages.ok"))
    btn_ok.setCursor(Qt.PointingHandCursor)
    btn_ok.setDefault(True)
    btn_ok.clicked.connect(dialog.accept)
    layout.addWidget(btn_ok)
    
    return dialog.exec_() == QDialog.Accepted


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        # Сначала создаем папки
        ensure_dirs()
        
        # Инициализируем менеджеры
        self.settings = SettingsManager()
        self.subs = SubscriptionManager()
        
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
        window_icon = QIcon()
        if getattr(sys, 'frozen', False):
            # В frozen режиме (PyInstaller) используем sys._MEIPASS для доступа к ресурсам
            base_path = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
            
            # Пробуем загрузить иконку из временной папки PyInstaller
            icon_path = base_path / "icon.ico"
            if icon_path.exists():
                window_icon = QIcon(str(icon_path))
            
            # Если не нашли .ico, пробуем .png
            if window_icon.isNull():
                icon_path = base_path / "icon.png"
                if icon_path.exists():
                    window_icon = QIcon(str(icon_path))
            
            # Если не нашли в _MEIPASS, пробуем рядом с exe
            if window_icon.isNull():
                exe_path = Path(sys.executable)
                icon_path = exe_path.parent / "icon.ico"
                if icon_path.exists():
                    window_icon = QIcon(str(icon_path))
                else:
                    icon_path = exe_path.parent / "icon.png"
                    if icon_path.exists():
                        window_icon = QIcon(str(icon_path))
            
            # Если не нашли, пробуем извлечь из exe
            if window_icon.isNull():
                exe_path = Path(sys.executable)
                window_icon = QIcon(str(exe_path))
        else:
            # В режиме разработки используем icon.ico или icon.png
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                window_icon = QIcon(str(icon_path))
            else:
                icon_path = Path(__file__).parent / "icon.png"
                if icon_path.exists():
                    window_icon = QIcon(str(icon_path))
        
        # Устанавливаем иконку окна только если она загрузилась
        if not window_icon.isNull():
            self.setWindowIcon(window_icon)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Стек страниц
        self.stack = QStackedWidget()
        self.page_profile = self.build_profile_page()
        self.page_home = self.build_home_page()
        self.page_settings = self.build_settings_page()
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
        
        self.btn_nav_profile = self.make_nav_button(tr("nav.profile"), "mdi.account")
        self.btn_nav_home = self.make_nav_button(tr("nav.home"), "mdi.home")
        self.btn_nav_settings = self.make_nav_button(tr("nav.settings"), "mdi.cog")

        for i, btn in enumerate([self.btn_nav_profile, self.btn_nav_home, self.btn_nav_settings]):
            btn.clicked.connect(lambda _, idx=i: self.switch_page(idx))
            nav_layout.addWidget(btn, 1)

        self.btn_nav_home.setChecked(True)

        nav.setStyleSheet("""
            QWidget {
                background-color: #0f1419;
                border: none;
            }
            QPushButton {
                color: #64748b;
                font-size: 14px;
                font-weight: 500;
                padding: 32px 8px;
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: rgba(0,245,212,0.06);
            }
            QPushButton:checked {
                color: #00f5d4;
                font-weight: 600;
                background-color: transparent;
            }
            QLabel {
                color: inherit;
                background-color: transparent;
                border: none;
            }
        """)

        root.addWidget(self.stack, 1)
        
        # Версия приложения над навигацией
        version_container = QWidget()
        version_container.setFixedHeight(30)
        version_layout = QHBoxLayout(version_container)
        version_layout.setContentsMargins(16, 0, 16, 0)
        version_layout.setAlignment(Qt.AlignCenter)
        
        self.lbl_app_version = QLabel()
        self.lbl_app_version.setFont(QFont("Segoe UI", 10))
        self.lbl_app_version.setStyleSheet("color: #64748b; background-color: transparent; border: none; padding: 0px;")
        self.lbl_app_version.setAlignment(Qt.AlignCenter)
        version_layout.addWidget(self.lbl_app_version)
        
        version_container.setStyleSheet("""
            QWidget {
                background-color: #0f1419;
                border: none;
            }
        """)
        
        root.addWidget(version_container)
        root.addWidget(nav)

        # Инициализация
        # Проверяем права администратора
        self.is_admin = is_admin()
        if not self.is_admin:
            log_to_file("[Admin Check] Приложение запущено без прав администратора")
        
        self.refresh_subscriptions_ui()
        self.update_version_info()
        self.update_profile_info()
        self.update_app_version_display()
        # Проверяем обновления приложения при запуске
        QTimer.singleShot(2000, self.check_app_update_once)
        
        # Очистка логов раз в сутки
        self.cleanup_logs_if_needed()
        
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
            self.setup_tray()
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.show()
        
        # Таймеры
        # Проверка версии только при запуске, не периодически
        self.update_info_timer = QTimer(self)
        self.update_info_timer.timeout.connect(self.update_profile_info)
        self.update_info_timer.start(5000)  # Обновление профиля каждые 5 секунд
        
        # Проверка версии один раз при запуске
        QTimer.singleShot(1000, self.check_version_once)
        
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

    # UI helpers
    def make_nav_button(self, text: str, icon_name: str) -> QPushButton:
        """Создает кнопку навигации"""
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(10)
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setPixmap(qta.icon(icon_name, color="#64748b").pixmap(36, 36))
        icon_label.setStyleSheet("background-color: transparent; border: none;")
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 500;
            background-color: transparent;
            border: none;
            color: #64748b;
        """)
        container = QWidget()
        container.setStyleSheet("background-color: transparent; border: none;")
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        container.setLayout(layout)
        h = QHBoxLayout(btn)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(container)
        
        def update_icon(checked):
            color = "#00f5d4" if checked else "#64748b"
            icon_label.setPixmap(qta.icon(icon_name, color=color).pixmap(36, 36))
            text_label.setStyleSheet(f"""
                font-size: 14px;
                font-weight: {'600' if checked else '500'};
                background-color: transparent;
                border: none;
                color: {color};
            """)
        
        btn.toggled.connect(update_icon)
        return btn

    def build_card(self) -> QWidget:
        """Создает карточку"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #1a1f2e;
                border-radius: 16px;
                border: none;
            }
        """)
        return card

    # Страницы (упрощенные версии - полный код будет в следующих итерациях)
    def build_profile_page(self):
        """Страница профилей"""
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(16, 16, 16, 16)

        card = self.build_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        
        self.lbl_profile_title = QLabel(tr("profile.title"))
        self.lbl_profile_title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        self.lbl_profile_title.setStyleSheet("color: #ffffff; background-color: transparent; border: none; padding: 0px;")
        layout.addWidget(self.lbl_profile_title)

        self.sub_list = QListWidget()
        self.sub_list.currentRowChanged.connect(self.on_sub_changed)
        self.sub_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #e5e9ff;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                padding: 14px 12px;
                border: none;
                border-radius: 12px;
                margin: 4px 0px;
            }
            QListWidget::item:hover {
                background-color: rgba(255,255,255,0.05);
            }
            QListWidget::item:selected {
                background-color: rgba(0,245,212,0.15);
                color: #00f5d4;
            }
        """)
        layout.addWidget(self.sub_list, 1)

        btn_row = QHBoxLayout()
        self.btn_add_sub = QPushButton(qta.icon("mdi.plus"), tr("profile.add"))
        self.btn_del_sub = QPushButton(qta.icon("mdi.delete"), tr("profile.delete"))
        self.btn_rename_sub = QPushButton(qta.icon("mdi.rename-box"), tr("profile.rename"))
        self.btn_test_sub = QPushButton(qta.icon("mdi.network"), tr("profile.test"))

        for b in (self.btn_add_sub, self.btn_del_sub, self.btn_rename_sub, self.btn_test_sub):
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0,245,212,0.1);
                    color: #00f5d4;
                    border-radius: 12px;
                    padding: 12px 20px;
                    border: none;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: rgba(0,245,212,0.2);
                }
            """)
            btn_row.addWidget(b)

        self.btn_add_sub.clicked.connect(self.on_add_sub)
        self.btn_del_sub.clicked.connect(self.on_del_sub)
        self.btn_rename_sub.clicked.connect(self.on_rename_sub)
        self.btn_test_sub.clicked.connect(self.on_test_sub)

        layout.addLayout(btn_row)
        outer.addWidget(card)
        return w

    def build_home_page(self):
        """Страница главная"""
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(16, 20, 16, 20)
        outer.setSpacing(12)
        
        # Карточка версии
        version_card = self.build_card()
        version_layout = QVBoxLayout(version_card)
        version_layout.setContentsMargins(20, 18, 20, 18)
        version_layout.setSpacing(10)
        
        version_title = QLabel(tr("home.version"))
        version_title.setFont(QFont("Segoe UI Semibold", 13, QFont.Bold))
        version_title.setStyleSheet("color: #ffffff; background-color: transparent; border: none; padding: 0px;")
        version_layout.addWidget(version_title)
        
        version_row = QHBoxLayout()
        version_row.setSpacing(10)
        
        self.lbl_version = QLabel()
        self.lbl_version.setFont(QFont("Segoe UI", 12))
        self.lbl_version.setStyleSheet("color: #9ca3af; background-color: transparent; border: none; padding: 0px;")
        version_row.addWidget(self.lbl_version)
        
        self.btn_version_warning = QPushButton()
        self.btn_version_warning.setIcon(qta.icon("mdi.alert-circle", color="#ff6b6b"))
        self.btn_version_warning.setFixedSize(28, 28)
        self.btn_version_warning.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 14px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 107, 107, 0.15);
            }
        """)
        self.btn_version_warning.setCursor(Qt.PointingHandCursor)
        self.btn_version_warning.clicked.connect(self.show_download_dialog)
        self.btn_version_warning.hide()
        version_row.addWidget(self.btn_version_warning)
        
        self.btn_version_update = QPushButton()
        self.btn_version_update.setIcon(qta.icon("mdi.download", color="#00f5d4"))
        self.btn_version_update.setFixedSize(28, 28)
        self.btn_version_update.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 14px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(0, 245, 212, 0.15);
            }
        """)
        self.btn_version_update.setCursor(Qt.PointingHandCursor)
        self.btn_version_update.clicked.connect(self.show_download_dialog)
        self.btn_version_update.hide()
        version_row.addWidget(self.btn_version_update)
        
        version_row.addStretch()
        version_layout.addLayout(version_row)
        
        # Label для сообщения об обновлении (показывается под текущей версией)
        self.lbl_update_info = QLabel()
        self.lbl_update_info.setFont(QFont("Segoe UI", 11))
        self.lbl_update_info.setStyleSheet("color: #ffa500; background-color: transparent; border: none; padding: 0px;")
        self.lbl_update_info.hide()
        version_layout.addWidget(self.lbl_update_info)
        
        outer.addWidget(version_card)
        
        # Карточка профиля
        profile_card = self.build_card()
        profile_layout = QVBoxLayout(profile_card)
        profile_layout.setContentsMargins(20, 18, 20, 18)
        profile_layout.setSpacing(10)
        
        self.profile_title = QLabel(tr("home.profile"))
        self.profile_title.setFont(QFont("Segoe UI Semibold", 13, QFont.Bold))
        self.profile_title.setStyleSheet("color: #ffffff; background-color: transparent; border: none; padding: 0px;")
        profile_layout.addWidget(self.profile_title)
        
        self.lbl_profile = QLabel(tr("home.not_selected"))
        self.lbl_profile.setFont(QFont("Segoe UI", 12))
        self.lbl_profile.setStyleSheet("color: #9ca3af; background-color: transparent; border: none; padding: 0px;")
        profile_layout.addWidget(self.lbl_profile)
        
        outer.addWidget(profile_card)
        
        # Информация о правах администратора
        admin_info_card = self.build_card()
        admin_info_layout = QVBoxLayout(admin_info_card)
        admin_info_layout.setContentsMargins(20, 12, 20, 12)
        admin_info_layout.setSpacing(0)
        
        self.lbl_admin_status = QLabel()
        # Используем такой же шрифт как у других элементов
        self.lbl_admin_status.setFont(QFont("Segoe UI", 10))
        self.lbl_admin_status.setAlignment(Qt.AlignCenter)
        self.lbl_admin_status.mousePressEvent = self.admin_status_mouse_press
        self.update_admin_status_label()
        admin_info_layout.addWidget(self.lbl_admin_status)
        
        outer.addWidget(admin_info_card)
        
        # Кнопка Start/Stop
        btn_container = QWidget()
        btn_container.setStyleSheet("background-color: transparent; border: none;")
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 30, 0, 30)
        btn_layout.setAlignment(Qt.AlignCenter)
        
        # Подложка для кнопки
        self.btn_wrapper = QWidget()
        self.btn_wrapper.setFixedSize(220, 220)
        self.btn_wrapper.setStyleSheet("""
            QWidget {
                background-color: #1a1f2e;
                border-radius: 110px;
                border: 2px solid rgba(0,245,212,0.3);
            }
        """)
        wrapper_layout = QVBoxLayout(self.btn_wrapper)
        wrapper_layout.setContentsMargins(10, 10, 10, 10)
        wrapper_layout.setAlignment(Qt.AlignCenter)
        
        self.big_btn = QPushButton(tr("home.button_start"))
        self.big_btn.setFixedSize(200, 200)
        self.style_big_btn_running(False)
        self.big_btn.clicked.connect(self.on_big_button)
        self.big_btn.setCursor(Qt.PointingHandCursor)
        wrapper_layout.addWidget(self.big_btn)
        
        btn_layout.addWidget(self.btn_wrapper, alignment=Qt.AlignCenter)
        
        outer.addWidget(btn_container)
        outer.addStretch()
        
        return w

    def build_settings_page(self):
        """Страница настроек"""
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)
        
        # Настройки
        settings_card = self.build_card()
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(20, 16, 20, 16)
        settings_layout.setSpacing(16)
        
        self.settings_title = QLabel(tr("settings.title"))
        self.settings_title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        self.settings_title.setStyleSheet("color: #ffffff; background-color: transparent; border: none; padding: 0px;")
        settings_layout.addWidget(self.settings_title)

        row = QHBoxLayout()
        row.setSpacing(12)
        row_label = QLabel(tr("settings.auto_update_interval"))
        row_label.setFont(QFont("Segoe UI", 13))
        row_label.setStyleSheet("color: #e5e9ff; background-color: transparent; border: none; padding: 0px;")
        row.addWidget(row_label)
        self.edit_interval = QLineEdit()
        self.edit_interval.setText(str(self.settings.get("auto_update_minutes", 90)))
        self.edit_interval.setPlaceholderText("90")
        self.edit_interval.editingFinished.connect(self.on_interval_changed)
        self.edit_interval.setStyleSheet("""
            QLineEdit {
                background-color: rgba(0,245,212,0.1);
                color: #00f5d4;
                border-radius: 12px;
                padding: 10px 14px;
                border: none;
                font-size: 13px;
                font-weight: 500;
            }
            QLineEdit:focus {
                background-color: rgba(0,245,212,0.15);
                border: 1px solid rgba(0,245,212,0.3);
            }
        """)
        row.addWidget(self.edit_interval)
        settings_layout.addLayout(row)

        self.cb_autostart = QCheckBox(tr("settings.autostart"))
        self.cb_autostart.setChecked(self.settings.get("start_with_windows", False))
        self.cb_autostart.stateChanged.connect(self.on_autostart_changed)
        self.cb_autostart.setFont(QFont("Segoe UI", 13))
        self.cb_autostart.setStyleSheet("""
            QCheckBox {
                color: #e5e9ff;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 6px;
                border: 2px solid #475569;
                background-color: rgba(0,245,212,0.1);
            }
            QCheckBox::indicator:checked {
                background-color: #00f5d4;
                border-color: #00f5d4;
            }
        """)
        settings_layout.addWidget(self.cb_autostart)
        
        self.cb_run_as_admin = QCheckBox(tr("settings.run_as_admin"))
        self.cb_run_as_admin.setChecked(self.settings.get("run_as_admin", False))
        self.cb_run_as_admin.stateChanged.connect(self.on_run_as_admin_changed)
        self.cb_run_as_admin.setFont(QFont("Segoe UI", 13))
        self.cb_run_as_admin.setStyleSheet("""
            QCheckBox {
                color: #e5e9ff;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 6px;
                border: 2px solid #475569;
                background-color: rgba(0,245,212,0.1);
            }
            QCheckBox::indicator:checked {
                background-color: #00f5d4;
                border-color: #00f5d4;
            }
        """)
        settings_layout.addWidget(self.cb_run_as_admin)
        
        self.cb_auto_start_singbox = QCheckBox(tr("settings.auto_start_singbox"))
        self.cb_auto_start_singbox.setChecked(self.settings.get("auto_start_singbox", False))
        self.cb_auto_start_singbox.stateChanged.connect(self.on_auto_start_singbox_changed)
        self.cb_auto_start_singbox.setFont(QFont("Segoe UI", 13))
        self.cb_auto_start_singbox.setStyleSheet("""
            QCheckBox {
                color: #e5e9ff;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 6px;
                border: 2px solid #475569;
                background-color: rgba(0,245,212,0.1);
            }
            QCheckBox::indicator:checked {
                background-color: #00f5d4;
                border-color: #00f5d4;
            }
        """)
        settings_layout.addWidget(self.cb_auto_start_singbox)
        
        self.cb_minimize_to_tray = QCheckBox(tr("settings.minimize_to_tray"))
        self.cb_minimize_to_tray.setChecked(self.settings.get("minimize_to_tray", True))
        self.cb_minimize_to_tray.stateChanged.connect(self.on_minimize_to_tray_changed)
        self.cb_minimize_to_tray.setFont(QFont("Segoe UI", 13))
        self.cb_minimize_to_tray.setStyleSheet("""
            QCheckBox {
                color: #e5e9ff;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 6px;
                border: 2px solid #475569;
                background-color: rgba(0,245,212,0.1);
            }
            QCheckBox::indicator:checked {
                background-color: #00f5d4;
                border-color: #00f5d4;
            }
        """)
        settings_layout.addWidget(self.cb_minimize_to_tray)
        
        # Выбор языка
        language_row = QHBoxLayout()
        language_row.setSpacing(12)
        self.language_label = QLabel(tr("settings.language"))
        self.language_label.setFont(QFont("Segoe UI", 13))
        self.language_label.setStyleSheet("color: #e5e9ff; background-color: transparent; border: none; padding: 0px;")
        language_row.addWidget(self.language_label)
        
        self.combo_language = QComboBox()
        available_languages = get_available_languages()
        current_language = self.settings.get("language", "")
        if not current_language:
            current_language = "en"  # Fallback на английский если не выбран
        for lang_code in available_languages:
            lang_name = get_language_name(lang_code)
            self.combo_language.addItem(lang_name, lang_code)
            if lang_code == current_language:
                self.combo_language.setCurrentIndex(self.combo_language.count() - 1)
        self.combo_language.currentIndexChanged.connect(self.on_language_changed)
        self.combo_language.setStyleSheet("""
            QComboBox {
                background-color: rgba(0,245,212,0.1);
                color: #00f5d4;
                border-radius: 12px;
                padding: 10px 14px;
                border: none;
                font-size: 13px;
                font-weight: 500;
            }
            QComboBox:hover {
                background-color: rgba(0,245,212,0.15);
            }
            QComboBox:focus {
                background-color: rgba(0,245,212,0.15);
                border: 1px solid rgba(0,245,212,0.3);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #00f5d4;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #151a24;
                color: #e5e9ff;
                border: 1px solid #00f5d4;
                border-radius: 8px;
                selection-background-color: rgba(0,245,212,0.2);
            }
        """)
        language_row.addWidget(self.combo_language)
        settings_layout.addLayout(language_row)
        
        # Кнопка "Убить" для полной остановки всех процессов
        self.btn_kill_all = QPushButton(tr("settings.kill_all"))
        self.btn_kill_all.setFont(QFont("Segoe UI", 13))
        self.btn_kill_all.setCursor(Qt.PointingHandCursor)
        self.btn_kill_all.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 107, 107, 0.15);
                color: #ff6b6b;
                border-radius: 12px;
                padding: 12px 20px;
                border: 2px solid #ff6b6b;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 107, 107, 0.25);
                border-color: #ff5252;
            }
        """)
        self.btn_kill_all.clicked.connect(self.on_kill_all_clicked)
        settings_layout.addWidget(self.btn_kill_all)
        
        outer.addWidget(settings_card)
        
        # Логи
        logs_card = self.build_card()
        logs_layout = QVBoxLayout(logs_card)
        logs_layout.setContentsMargins(20, 16, 20, 16)
        logs_layout.setSpacing(12)
        
        # Создаем класс для обработки кликов
        class ClickableLabel(QLabel):
            def __init__(self, parent, callback):
                super().__init__()
                self.parent_window = parent
                self.callback = callback
                self.setCursor(Qt.PointingHandCursor)
            
            def mousePressEvent(self, event):
                if event.button() == Qt.LeftButton:
                    self.callback()
                super().mousePressEvent(event)
        
        clickable_logs_title = ClickableLabel(self, self.on_logs_title_clicked)
        clickable_logs_title.setText(tr("settings.logs"))
        clickable_logs_title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        clickable_logs_title.setStyleSheet("color: #ffffff; background-color: transparent; border: none; padding: 0px;")
        logs_layout.addWidget(clickable_logs_title)
        
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0,245,212,0.05);
                color: #e5e9ff;
                border-radius: 16px;
                padding: 16px;
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        logs_layout.addWidget(self.logs, 1)
        self.load_logs()
        
        # Debug логи (скрыты по умолчанию, показываются только при isDebug=True)
        debug_logs_title = QLabel("Debug Logs")
        debug_logs_title.setFont(QFont("Segoe UI Semibold", 16, QFont.Bold))
        debug_logs_title.setStyleSheet("color: #ff6b6b; background-color: transparent; border: none; padding: 0px;")
        self.debug_logs_title = debug_logs_title
        logs_layout.addWidget(debug_logs_title)
        debug_logs_title.setVisible(False)
        
        self.debug_logs = QTextEdit()
        self.debug_logs.setReadOnly(True)
        self.debug_logs.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 107, 107, 0.05);
                color: #ff6b6b;
                border-radius: 16px;
                padding: 16px;
                border: 2px solid rgba(255, 107, 107, 0.2);
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        logs_layout.addWidget(self.debug_logs, 1)
        self.debug_logs.setVisible(False)
        
        # Видимость debug логов зависит от настройки isDebug (обновляется автоматически)
        self._update_debug_logs_visibility()
        
        outer.addWidget(logs_card, 1)
        
        # Дебаг секция (скрыта по умолчанию, появляется снизу после логов)
        self.debug_card = self.build_card()
        self.debug_layout = QVBoxLayout(self.debug_card)
        self.debug_layout.setContentsMargins(20, 16, 20, 16)
        self.debug_layout.setSpacing(16)
        
        debug_title = QLabel("Debug Settings")
        debug_title.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
        debug_title.setStyleSheet("color: #ff6b6b; background-color: transparent; border: none; padding: 0px;")
        self.debug_layout.addWidget(debug_title)
        
        self.cb_allow_multiple = QCheckBox("Разрешить несколько процессов одновременно")
        self.cb_allow_multiple.setChecked(self.settings.get("allow_multiple_processes", True))
        self.cb_allow_multiple.stateChanged.connect(self.on_allow_multiple_changed)
        self.cb_allow_multiple.setFont(QFont("Segoe UI", 13))
        self.cb_allow_multiple.setStyleSheet("""
            QCheckBox {
                color: #e5e9ff;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 6px;
                border: 2px solid #475569;
                background-color: rgba(255,107,107,0.1);
            }
            QCheckBox::indicator:checked {
                background-color: #ff6b6b;
                border-color: #ff6b6b;
            }
        """)
        self.debug_layout.addWidget(self.cb_allow_multiple)
        
        self.debug_card.setVisible(False)
        outer.addWidget(self.debug_card)
        return w

    # Навигация
    def switch_page(self, index: int):
        """Переключение страниц"""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate([self.btn_nav_profile, self.btn_nav_home, self.btn_nav_settings]):
            btn.setChecked(i == index)
        if index == 2:  # Settings page
            # Загружаем логи при открытии страницы
            self.load_logs()
            # Загружаем debug логи если включен debug режим
            is_debug = self.settings.get("isDebug", False)
            if is_debug and hasattr(self, 'debug_logs'):
                self._load_debug_logs_from_file()

    # Подписки
    def refresh_subscriptions_ui(self):
        """Обновление списка подписок"""
        saved_index = self.current_sub_index
        self.sub_list.clear()
        for name in self.subs.list_names():
            self.sub_list.addItem(name)
        if self.sub_list.count() > 0:
            # Проверяем, что сохраненный индекс валидный
            if 0 <= saved_index < self.sub_list.count():
                self.sub_list.setCurrentRow(saved_index)
                self.current_sub_index = saved_index
            else:
                # Если индекс невалидный, выбираем первый элемент
                self.sub_list.setCurrentRow(0)
                self.current_sub_index = 0
        else:
            self.current_sub_index = -1

    def on_sub_changed(self, row: int):
        """Изменение выбранной подписки"""
        # Проверяем, что список не пустой и индекс валидный
        if row < 0 or self.sub_list.count() == 0:
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
                if saved_index >= 0 and saved_index < self.sub_list.count():
                    self.sub_list.setCurrentRow(saved_index)
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
        row = self.sub_list.currentRow()
        if row < 0 or self.sub_list.count() == 0:
            return
        if row >= self.sub_list.count():
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
        row = self.sub_list.currentRow()
        if row < 0 or self.sub_list.count() == 0:
            return
        if row >= self.sub_list.count():
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
            if self.sub_list.count() > 0 and 0 <= row < self.sub_list.count():
                self.sub_list.setCurrentRow(row)
                self.current_sub_index = row
            self.log(tr("profile.renamed", old_name=old_name, new_name=new_name.strip()))
    
    def on_test_sub(self):
        """Тест подписки"""
        row = self.sub_list.currentRow()
        if row < 0 or self.sub_list.count() == 0:
            self.log(tr("profile.select_for_test"))
            return
        if row >= self.sub_list.count():
            return
        
        # Получаем название подписки для отображения
        sub = self.subs.get(row)
        sub_name = sub.get("name", "Unknown") if sub else "Unknown"
        
        self.log(tr("profile.test_loading"))
        # Отключаем кнопку на время теста
        self.btn_test_sub.setEnabled(False)
        self.btn_test_sub.setText(tr("profile.test") + "...")
        
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
            self.btn_test_sub.setEnabled(True)
            self.btn_test_sub.setText(tr("profile.test"))
    
    def _log_version_debug(self, msg: str):
        """Логирование версий в debug логи"""
        log_to_file(msg)
    
    def check_version_once(self):
        """Проверка версии один раз при запуске или по таймеру повторной попытки"""
        version = get_singbox_version()
        if version:
            # Всегда показываем текущую версию
            self.lbl_version.setText(tr("home.installed", version=version))
            self.lbl_version.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px;")
            self.btn_version_warning.hide()
            
            # Проверяем наличие обновлений
            latest_version = get_latest_version()
            if latest_version:
                # Успешно получили версию
                self.cached_latest_version = latest_version
                self.version_check_failed_count = 0
                self.version_checked = True
                # Останавливаем таймер повторных попыток если был запущен
                if self.version_check_retry_timer:
                    self.version_check_retry_timer.stop()
                    self.version_check_retry_timer = None
                self.version_check_retry_delay = 5 * 60 * 1000  # Сбрасываем задержку
                
                self._log_version_debug(f"[Version Check] Текущая версия: {version}, Последняя версия: {latest_version}")
                comparison = compare_versions(version, latest_version)
                self._log_version_debug(f"[Version Check] Сравнение: {comparison} (< 0 означает что текущая старше)")
                
                if comparison < 0:  # Текущая версия старше
                    # Показываем сообщение об обновлении под текущей версией
                    self.lbl_update_info.setText(tr("home.update_available", version=latest_version))
                    self.lbl_update_info.show()
                    self.btn_version_update.show()
                    self._log_version_debug(f"[Version Check] Показано обновление: {latest_version}")
                else:
                    # Версия актуальна, скрываем сообщение об обновлении
                    self.lbl_update_info.hide()
                    self.btn_version_update.hide()
                    self._log_version_debug(f"[Version Check] Версия актуальна: {version}")
            else:
                # Не удалось получить версию
                self.version_check_failed_count += 1
                self._log_version_debug(f"[Version Check] Не удалось получить последнюю версию (попытка {self.version_check_failed_count})")
                
                # Используем кэш если есть
                if self.cached_latest_version:
                    latest_version = self.cached_latest_version
                    comparison = compare_versions(version, latest_version)
                    if comparison < 0:
                        self.lbl_update_info.setText(tr("home.update_available", version=latest_version))
                        self.lbl_update_info.show()
                        self.btn_version_update.show()
                    else:
                        self.lbl_update_info.hide()
                        self.btn_version_update.hide()
                else:
                    self.lbl_update_info.hide()
                    self.btn_version_update.hide()
                
                # Планируем повторную попытку с экспоненциальной задержкой
                if not self.version_check_retry_timer:
                    self.version_check_retry_timer = QTimer(self)
                    self.version_check_retry_timer.timeout.connect(self.check_version_once)
                
                # Экспоненциальная задержка: 5 мин, 15 мин, 30 мин, затем каждые 60 мин
                if self.version_check_failed_count == 1:
                    delay = 5 * 60 * 1000  # 5 минут
                elif self.version_check_failed_count == 2:
                    delay = 15 * 60 * 1000  # 15 минут
                elif self.version_check_failed_count == 3:
                    delay = 30 * 60 * 1000  # 30 минут
                else:
                    delay = 60 * 60 * 1000  # 60 минут
                
                self.version_check_retry_delay = delay
                self.version_check_retry_timer.start(delay)
                self._log_version_debug(f"[Version Check] Следующая попытка через {delay // 60000} минут")
        else:
            self._log_version_debug("[Version Check] SingBox не установлен")
            self.lbl_version.setText(tr("home.not_installed"))
            self.lbl_version.setStyleSheet("color: #ff6b6b; background-color: transparent; border: none; padding: 0px;")
            self.lbl_update_info.hide()
            self.btn_version_warning.show()
            self.btn_version_update.hide()
    
    # Версия и профиль
    def update_version_info(self):
        """Обновление информации о версии (только UI, без проверки)"""
        version = get_singbox_version()
        if version:
            # Всегда показываем текущую версию
            self.lbl_version.setText(tr("home.installed", version=version))
            self.lbl_version.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px;")
            self.btn_version_warning.hide()
            
            # Используем кэшированную версию если есть
            if self.cached_latest_version:
                comparison = compare_versions(version, self.cached_latest_version)
                if comparison < 0:
                    self.lbl_update_info.setText(tr("home.update_available", version=self.cached_latest_version))
                    self.lbl_update_info.show()
                    self.btn_version_update.show()
                else:
                    self.lbl_update_info.hide()
                    self.btn_version_update.hide()
            else:
                self.lbl_update_info.hide()
                self.btn_version_update.hide()
        else:
            self.lbl_version.setText(tr("home.not_installed"))
            self.lbl_version.setStyleSheet("color: #ff6b6b; background-color: transparent; border: none; padding: 0px;")
            self.lbl_update_info.hide()
            self.btn_version_warning.show()
            self.btn_version_update.hide()
    
    def update_app_version_display(self):
        """Обновление отображения версии приложения"""
        if self.cached_app_latest_version:
            comparison = compare_versions(self.app_version, self.cached_app_latest_version)
            if comparison < 0:
                # Есть обновление
                self.lbl_app_version.setText(tr("app.update_available", version=self.cached_app_latest_version))
                self.lbl_app_version.setStyleSheet("color: #ffa500; background-color: transparent; border: none; padding: 0px; cursor: pointer;")
                # Делаем кликабельным для открытия диалога обновления
                if not hasattr(self.lbl_app_version, '_click_handler'):
                    self.lbl_app_version.mousePressEvent = lambda e: self.show_app_update_dialog() if e.button() == Qt.LeftButton else None
                    self.lbl_app_version._click_handler = True
            else:
                # Нет обновления
                self.lbl_app_version.setText(tr("app.version", version=self.app_version))
                self.lbl_app_version.setStyleSheet("color: #64748b; background-color: transparent; border: none; padding: 0px;")
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
    
    def check_app_update_once(self):
        """Проверка обновлений приложения один раз при запуске"""
        if self.app_update_checked:
            return
        
        try:
            latest_version = get_app_latest_version()
            if latest_version:
                self.cached_app_latest_version = latest_version
                self.app_update_checked = True
                log_to_file(f"[App Update Check] Текущая версия: {self.app_version}, Последняя версия: {latest_version}")
                
                comparison = compare_versions(self.app_version, latest_version)
                if comparison < 0:
                    # Есть обновление - обновляем отображение, но не показываем диалог автоматически
                    log_to_file(f"[App Update Check] Доступно обновление: {latest_version}")
                    # Пользователь сам нажмет на версию, если захочет обновиться
                
                self.update_app_version_display()
            else:
                log_to_file("[App Update Check] Не удалось получить последнюю версию приложения")
                self.update_app_version_display()
        except Exception as e:
            log_to_file(f"[App Update Check] Ошибка при проверке обновлений: {e}")
            self.update_app_version_display()
    
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
                self.lbl_profile.setText(tr("home.current_profile", name=running_sub.get("name", "Неизвестно")))
                self.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
            else:
                # Профили разные - добавляем отступ для второй строки
                text = f"{tr('home.current_profile', name=running_sub.get('name', 'Неизвестно'))}\n    {tr('home.selected_profile', name=selected_sub.get('name', 'Неизвестно'))}"
                self.lbl_profile.setText(text)
                self.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
        elif running_sub:
            # Только запущенный профиль
            self.lbl_profile.setText(tr("home.current_profile", name=running_sub.get("name", "Неизвестно")))
            self.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
        elif selected_sub:
            # Только выбранный профиль
            self.lbl_profile.setText(tr("home.selected_profile", name=selected_sub.get("name", "Неизвестно")))
            self.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px; padding-left: 4px;")
        else:
            # Нет профиля
            self.lbl_profile.setText(tr("home.profile_not_selected_click"))
            self.lbl_profile.setStyleSheet("color: #9ca3af; background-color: transparent; border: none; padding: 0px; cursor: pointer;")
            # Делаем кликабельным для перехода в профили
            # Сохраняем оригинальный mousePressEvent если он есть
            if not hasattr(self.lbl_profile, '_original_mousePressEvent'):
                self.lbl_profile._original_mousePressEvent = self.lbl_profile.mousePressEvent
            
            def handle_click(event):
                if event.button() == Qt.LeftButton:
                    self.switch_page(0)  # Переход на страницу профилей (индекс 0)
                else:
                    # Вызываем оригинальный обработчик для других кнопок
                    if hasattr(self.lbl_profile, '_original_mousePressEvent') and self.lbl_profile._original_mousePressEvent:
                        self.lbl_profile._original_mousePressEvent(event)
            
            self.lbl_profile.mousePressEvent = handle_click
    
    def update_admin_status_label(self):
        """Обновление надписи о правах администратора"""
        if is_admin():
            self.lbl_admin_status.setText(tr("home.admin_running"))
            self.lbl_admin_status.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px;")
            self.lbl_admin_status.setCursor(Qt.ArrowCursor)
        else:
            self.lbl_admin_status.setText(tr("home.admin_not_running"))
            self.lbl_admin_status.setStyleSheet("color: #ffa500; background-color: transparent; border: none; padding: 0px; text-decoration: underline;")
            self.lbl_admin_status.setCursor(Qt.PointingHandCursor)
    
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
        # Проверяем аргументы командной строки
        args = sys.argv[1:] if len(sys.argv) > 1 else []
        
        if not args:
            return
        
        for arg in args:
            # Проверяем, является ли аргумент URL
            if arg.startswith('http://') or arg.startswith('https://') or arg.startswith('sing-box://') or arg.startswith('singbox-ui://'):
                # Убираем префикс протокола если есть
                url = arg
                if url.startswith('sing-box://'):
                    # Убираем протокол sing-box://
                    url = url.replace('sing-box://', '', 1)
                    # Если после протокола нет http:// или https://, добавляем https://
                    if not url.startswith('http://') and not url.startswith('https://'):
                        url = 'https://' + url
                elif url.startswith('singbox-ui://'):
                    # Убираем протокол singbox-ui://
                    url = url.replace('singbox-ui://', '', 1)
                    # Если после протокола нет http:// или https://, добавляем https://
                    if not url.startswith('http://') and not url.startswith('https://'):
                        url = 'https://' + url
                
                # Извлекаем имя из URL (можно использовать часть URL или параметры)
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(url)
                
                # Пытаемся извлечь имя из фрагмента или параметров
                name = None
                if parsed.fragment:
                    # Пытаемся извлечь имя из фрагмента (например, [tg_5818132224]_ang3el_(cdn_1))
                    fragment = parsed.fragment
                    # Убираем квадратные скобки и другие символы
                    if '_' in fragment:
                        parts = fragment.split('_')
                        if len(parts) > 1:
                            name = '_'.join(parts[1:])  # Берем все после первого подчеркивания
                            # Убираем скобки и другие символы
                            name = name.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
                
                # Если имя не найдено, используем домен или путь
                if not name or len(name) < 3:
                    if parsed.netloc:
                        name = parsed.netloc.split('.')[0] if '.' in parsed.netloc else parsed.netloc
                    elif parsed.path:
                        name = parsed.path.split('/')[-1] if '/' in parsed.path else parsed.path
                    else:
                        name = "Imported Subscription"
                
                # Ограничиваем длину имени
                if len(name) > 50:
                    name = name[:50]
                
                # Проверяем, нет ли уже такой подписки
                existing_urls = [s.get("url", "") for s in self.subs.data.get("subscriptions", [])]
                if url in existing_urls:
                    self.log(tr("messages.subscription_already_exists"))
                    QMessageBox.information(
                        self,
                        tr("messages.subscription_exists_title"),
                        tr("messages.subscription_exists_text")
                    )
                    return
                
                # Добавляем подписку
                try:
                    self.subs.add(name, url)
                    self.refresh_subscriptions_ui()
                    self.log(tr("profile.added", name=name))
                    
                    # Показываем уведомление
                    QMessageBox.information(
                        self,
                        tr("messages.subscription_imported_title"),
                        tr("messages.subscription_imported_text", name=name)
                    )
                    
                    # Переключаемся на страницу профилей
                    self.switch_page(0)
                except Exception as e:
                    self.log(tr("messages.subscription_import_error", error=str(e)))
                    QMessageBox.warning(
                        self,
                        tr("messages.subscription_import_error_title"),
                        tr("messages.subscription_import_error_text", error=str(e))
                    )
                break  # Обрабатываем только первый URL
    
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
        # Проверяем, нужно ли показать "Сменить" (оранжевый цвет)
        is_change_mode = (running and 
                         self.running_sub_index != self.current_sub_index and 
                         self.current_sub_index >= 0)
        
        # Обновляем подложку
        if hasattr(self, 'btn_wrapper'):
            if running:
                if is_change_mode:
                    # Оранжевый для режима "Сменить"
                    border_color = "rgba(255,165,0,0.5)"  # Оранжевый
                else:
                    # Красный для режима "Остановить"
                    border_color = "rgba(255,107,107,0.5)"
                self.btn_wrapper.setStyleSheet(f"""
                    QWidget {{
                        background-color: #1a1f2e;
                        border-radius: 110px;
                        border: 2px solid {border_color};
                    }}
                """)
            else:
                self.btn_wrapper.setStyleSheet("""
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
                self.big_btn.setStyleSheet("""
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
                self.big_btn.setStyleSheet("""
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
            self.big_btn.setStyleSheet("""
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
        core_ok = CORE_EXE.exists()
        running = self.proc and self.proc.poll() is None
        
        if running:
            # Если запущен - кнопка всегда активна (можно остановить)
            self.big_btn.setEnabled(core_ok)
            # Проверяем, совпадает ли выбранный профиль с запущенным
            if self.running_sub_index != self.current_sub_index and self.current_sub_index >= 0:
                # Выбран другой профиль - показываем "Сменить"
                self.big_btn.setText(tr("home.button_change"))
            else:
                # Профили совпадают или не выбран - показываем "Остановить"
                self.big_btn.setText(tr("home.button_stop"))
        else:
            # Если не запущен - нужен выбранный профиль
            has_sub = self.sub_list.count() > 0 and self.current_sub_index >= 0
            self.big_btn.setEnabled(core_ok and has_sub)
            self.big_btn.setText(tr("home.button_start"))
        
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
        if self.current_sub_index < 0 or self.sub_list.count() == 0:
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
        self.big_btn.setEnabled(False)
        
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
        if self.current_sub_index < 0 or self.sub_list.count() == 0:
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
        try:
            value = int(self.edit_interval.text())
            if 5 <= value <= 1440:
                self.settings.set("auto_update_minutes", value)
                self.update_timer.start(value * 60 * 1000)
                self.log(tr("messages.interval_changed", value=value))
            else:
                # Восстанавливаем значение если вне диапазона
                self.edit_interval.setText(str(self.settings.get("auto_update_minutes", 90)))
        except ValueError:
            # Восстанавливаем значение если не число
            self.edit_interval.setText(str(self.settings.get("auto_update_minutes", 90)))
    
    def on_logs_title_clicked(self):
        """Обработка клика по заголовку логов для показа дебаг меню"""
        self.logs_click_count += 1
        if self.logs_click_count >= 6:
            self.debug_section_visible = not self.debug_section_visible
            self.debug_card.setVisible(self.debug_section_visible)
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
        if hasattr(self, 'debug_logs_title') and hasattr(self, 'debug_logs'):
            is_debug = self.settings.get("isDebug", False)
            self.debug_logs_title.setVisible(is_debug)
            self.debug_logs.setVisible(is_debug)
    
    def on_allow_multiple_changed(self, state: int):
        """Изменение настройки разрешения нескольких процессов"""
        enabled = state == Qt.Checked
        try:
            self.settings.set("allow_multiple_processes", enabled)
            log_to_file(f"Разрешение нескольких процессов: {'включено' if enabled else 'выключено'}")
        except Exception as e:
            log_to_file(f"Ошибка при изменении настройки нескольких процессов: {e}")
            # Восстанавливаем состояние чекбокса при ошибке
            self.cb_allow_multiple.blockSignals(True)
            self.cb_allow_multiple.setChecked(not enabled)
            self.cb_allow_multiple.blockSignals(False)

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
            self.cb_autostart.blockSignals(True)
            self.cb_autostart.setChecked(not enabled)
            self.cb_autostart.blockSignals(False)
    
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
                    self.cb_run_as_admin.blockSignals(True)
                    self.cb_run_as_admin.setChecked(False)
                    self.settings.set("run_as_admin", False)
                    self.cb_run_as_admin.blockSignals(False)
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
            self.cb_auto_start_singbox.blockSignals(True)
            self.cb_auto_start_singbox.setChecked(not enabled)
            self.cb_auto_start_singbox.blockSignals(False)
    
    def on_language_changed(self, index: int):
        """Обработка изменения языка"""
        if index >= 0:
            lang_code = self.combo_language.itemData(index)
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
        if hasattr(self, 'lbl_profile_title'):
            self.lbl_profile_title.setText(tr("profile.title"))
        if hasattr(self, 'settings_title'):
            self.settings_title.setText(tr("settings.title"))
        if hasattr(self, 'profile_title'):
            self.profile_title.setText(tr("home.profile"))
        
        # Обновляем кнопки на странице профилей
        if hasattr(self, 'btn_add_sub'):
            self.btn_add_sub.setText(tr("profile.add"))
        if hasattr(self, 'btn_del_sub'):
            self.btn_del_sub.setText(tr("profile.delete"))
        if hasattr(self, 'btn_rename_sub'):
            self.btn_rename_sub.setText(tr("profile.rename"))
        if hasattr(self, 'btn_test_sub'):
            self.btn_test_sub.setText(tr("profile.test"))
        
        # Обновляем настройки
        if hasattr(self, 'cb_autostart'):
            self.cb_autostart.setText(tr("settings.autostart"))
        if hasattr(self, 'cb_run_as_admin'):
            self.cb_run_as_admin.setText(tr("settings.run_as_admin"))
        if hasattr(self, 'cb_auto_start_singbox'):
            self.cb_auto_start_singbox.setText(tr("settings.auto_start_singbox"))
        if hasattr(self, 'cb_minimize_to_tray'):
            self.cb_minimize_to_tray.setText(tr("settings.minimize_to_tray"))
        if hasattr(self, 'btn_kill_all'):
            self.btn_kill_all.setText(tr("settings.kill_all"))
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
                if not hasattr(self, 'tray_icon') or not self.tray_icon:
                    self.setup_tray()
                if self.tray_icon:
                    self.tray_icon.show()
            else:
                # Выключаем трей режим - скрываем иконку и удаляем её
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.hide()
                    self.tray_icon.deleteLater()
                    self.tray_icon = None
            
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
            self.cb_minimize_to_tray.blockSignals(True)
            self.cb_minimize_to_tray.setChecked(not enabled)
            self.cb_minimize_to_tray.blockSignals(False)
    
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
    
    def setup_tray(self):
        """Настройка системного трея"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # Создаем иконку для трея
        tray_icon = QIcon()
        if getattr(sys, 'frozen', False):
            # В frozen режиме (PyInstaller) используем sys._MEIPASS для доступа к ресурсам
            base_path = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
            
            # Пробуем загрузить иконку из временной папки PyInstaller
            icon_path = base_path / "icon.ico"
            if icon_path.exists():
                tray_icon = QIcon(str(icon_path))
            
            # Если не нашли .ico, пробуем .png
            if tray_icon.isNull():
                icon_path = base_path / "icon.png"
                if icon_path.exists():
                    tray_icon = QIcon(str(icon_path))
            
            # Если не нашли в _MEIPASS, пробуем рядом с exe
            if tray_icon.isNull():
                exe_path = Path(sys.executable)
                icon_path = exe_path.parent / "icon.ico"
                if icon_path.exists():
                    tray_icon = QIcon(str(icon_path))
                else:
                    icon_path = exe_path.parent / "icon.png"
                    if icon_path.exists():
                        tray_icon = QIcon(str(icon_path))
            
            # Если не нашли, пробуем извлечь из exe
            if tray_icon.isNull():
                exe_path = Path(sys.executable)
                tray_icon = QIcon(str(exe_path))
        else:
            # В режиме разработки используем иконку окна или ищем icon.png/icon.ico
            tray_icon = self.windowIcon()
            if tray_icon.isNull():
                icon_path = Path(__file__).parent / "icon.ico"
                if icon_path.exists():
                    tray_icon = QIcon(str(icon_path))
                else:
                    icon_path = Path(__file__).parent / "icon.png"
                    if icon_path.exists():
                        tray_icon = QIcon(str(icon_path))
        
        self.tray_icon = QSystemTrayIcon(self)
        # Если иконка не найдена, используем системную иконку вместо пустой
        if tray_icon.isNull():
            from PyQt5.QtWidgets import QStyle
            tray_icon = QApplication.instance().style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(tray_icon)
        self.tray_icon.setToolTip(tr("app.title"))
        
        # Создаем контекстное меню для трея
        tray_menu = QMenu(self)
        
        # Действие "Открыть"
        show_action = QAction(tr("tray.show"), self)
        show_action.triggered.connect(self.show)
        show_action.triggered.connect(self.raise_)
        show_action.triggered.connect(self.activateWindow)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # Действие "Закрыть"
        quit_action = QAction(tr("tray.quit"), self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Обработка клика по иконке трея
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Показываем иконку в трее
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """Обработка активации иконки трея"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def quit_application(self):
        """Полное закрытие приложения с остановкой всех процессов"""
        self.kill_all_processes()
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()
    
    # Логи
    def load_logs(self):
        """Загрузка логов из singbox.log (важные логи)"""
        self._load_logs_from_file()
    
    def _load_logs_from_file(self):
        """Загрузка обычных логов из singbox.log"""
        if LOG_FILE.exists():
            try:
                with LOG_FILE.open("r", encoding="utf-8") as f:
                    content = f.read()
                    # Преобразуем формат из файла [2024-01-01 12:00:00] в формат UI [12:00:00]
                    import re
                    lines = content.split('\n')
                    formatted_lines = []
                    for line in lines:
                        # Ищем паттерн [YYYY-MM-DD HH:MM:SS] и заменяем на [HH:MM:SS]
                        line = re.sub(r'\[\d{4}-\d{2}-\d{2} (\d{2}:\d{2}:\d{2})\]', r'[\1]', line)
                        if line.strip():  # Пропускаем пустые строки
                            formatted_lines.append(line)
                    formatted_content = '\n'.join(formatted_lines)
                    self.logs.setPlainText(formatted_content)
                    cursor = self.logs.textCursor()
                    cursor.movePosition(cursor.End)
                    self.logs.setTextCursor(cursor)
            except Exception:
                pass
    
    def _load_debug_logs_from_file(self):
        """Загрузка debug логов из debug.log"""
        from config.paths import DEBUG_LOG_FILE
        if DEBUG_LOG_FILE.exists():
            try:
                with DEBUG_LOG_FILE.open("r", encoding="utf-8") as f:
                    content = f.read()
                    # Преобразуем формат из файла [2024-01-01 12:00:00] в формат UI [12:00:00]
                    import re
                    lines = content.split('\n')
                    formatted_lines = []
                    for line in lines:
                        # Ищем паттерн [YYYY-MM-DD HH:MM:SS] и заменяем на [HH:MM:SS]
                        line = re.sub(r'\[\d{4}-\d{2}-\d{2} (\d{2}:\d{2}:\d{2})\]', r'[\1]', line)
                        if line.strip():  # Пропускаем пустые строки
                            formatted_lines.append(line)
                    formatted_content = '\n'.join(formatted_lines)
                    self.debug_logs.setPlainText(formatted_content)
                    cursor = self.debug_logs.textCursor()
                    cursor.movePosition(cursor.End)
                    self.debug_logs.setTextCursor(cursor)
            except Exception:
                pass
    
    def refresh_logs_from_files(self):
        """Обновление логов из файлов (вызывается таймером каждую секунду, если открыта страница настроек)"""
        # Обновляем только если открыта страница настроек (index 2)
        if self.stack.currentIndex() == 2:
            # Всегда обновляем обычные логи
            self._load_logs_from_file()
            
            # Обновляем debug логи только если включен debug режим
            is_debug = self.settings.get("isDebug", False)
            if is_debug and hasattr(self, 'debug_logs'):
                self._load_debug_logs_from_file()

    def cleanup_logs_if_needed(self):
        """Очистка логов раз в сутки (полная очистка файла)"""
        try:
            last_cleanup = self.settings.get("last_log_cleanup", None)
            now = datetime.now()
            
            if last_cleanup:
                # Парсим дату последней очистки
                try:
                    last_date = datetime.fromisoformat(last_cleanup)
                    # Проверяем, прошло ли больше суток
                    time_diff = now - last_date
                    if time_diff.total_seconds() < 24 * 60 * 60:  # Меньше 24 часов
                        return  # Еще не прошло сутки
                except (ValueError, TypeError):
                    # Если дата некорректная, считаем что нужно очистить
                    pass
            
            # Полностью очищаем оба файла логов (singbox.log и singbox-debug.log)
            from config.paths import DEBUG_LOG_FILE
            if LOG_FILE.exists():
                try:
                    # Получаем размер файла для информации
                    file_size = LOG_FILE.stat().st_size
                    # Полностью очищаем файл
                    LOG_FILE.write_text("", encoding="utf-8")
                    self._log_version_debug(f"[Log Cleanup] singbox.log очищен (было {file_size} байт)")
                except Exception as e:
                    self._log_version_debug(f"[Log Cleanup] Ошибка при очистке singbox.log: {e}")
            
            if DEBUG_LOG_FILE.exists():
                try:
                    # Получаем размер файла для информации
                    file_size = DEBUG_LOG_FILE.stat().st_size
                    # Полностью очищаем файл
                    DEBUG_LOG_FILE.write_text("", encoding="utf-8")
                    self._log_version_debug(f"[Log Cleanup] debug.log очищен (было {file_size} байт)")
                except Exception as e:
                    self._log_version_debug(f"[Log Cleanup] Ошибка при очистке debug.log: {e}")
            
            # Сохраняем дату последней очистки
            self.settings.data["last_log_cleanup"] = now.isoformat()
            self.settings.save()
        except Exception as e:
            # Не критично, просто логируем
            log_to_file(f"[Log Cleanup] Ошибка: {e}")
    
    def log(self, msg: str):
        """Логирование в UI панель и в singbox.log (только важные сообщения для пользователя)"""
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        
        # Всегда показываем в UI (это для пользователя - только важные сообщения)
        if hasattr(self, 'logs'):
            self.logs.append(line)
            cursor = self.logs.textCursor()
            cursor.movePosition(cursor.End)
            self.logs.setTextCursor(cursor)
        
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
            if not hasattr(self, 'tray_icon') or not self.tray_icon:
                self.setup_tray()
            
            if self.tray_icon:
                # Всегда показываем иконку
                self.tray_icon.show()
                
                # Проверяем, что иконка действительно видна
                if not self.tray_icon.isVisible():
                    # Если не видна, пробуем пересоздать
                    self.tray_icon.hide()
                    self.setup_tray()
                    if self.tray_icon:
                        self.tray_icon.show()
                
                # Сворачиваем в трей только если иконка видна
                if self.tray_icon.isVisible():
                    event.ignore()
                    self.hide()
                    
                    # Показываем уведомление
                    self.tray_icon.showMessage(
                        tr("app.title"),
                        tr("messages.minimized_to_tray"),
                        QSystemTrayIcon.Information,
                        2000
                    )
                    return
        
        # Если трей режим выключен - закрываем приложение нормально
        self.kill_all_processes()
        event.accept()


def apply_dark_theme(app: QApplication):
    """Применение темной темы"""
    app.setStyle("Fusion")
    palette = QPalette()
    bg = QColor("#0b0f1a")
    card = QColor("#151a24")
    text = QColor("#f5f7ff")
    accent = QColor("#00f5d4")

    palette.setColor(QPalette.Window, QColor("#0f1419"))
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, QColor("#1a1f2e"))
    palette.setColor(QPalette.AlternateBase, QColor("#1a1f2e"))
    palette.setColor(QPalette.ToolTipBase, QColor("#1a1f2e"))
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, QColor("#1a1f2e"))
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.BrightText, QColor("#ff6b6b"))
    palette.setColor(QPalette.Highlight, accent)
    palette.setColor(QPalette.HighlightedText, QColor("#000000"))
    app.setPalette(palette)
    
    app.setStyleSheet("""
        QWidget {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        QLabel {
            background-color: transparent;
            border: none;
        }
        QPushButton {
            background-color: transparent;
            border: none;
        }
        QListWidget {
            outline: none;
        }
        QSpinBox {
            outline: none;
        }
        QTextEdit {
            outline: none;
        }
    """)




class StartSingBoxThread(QThread):
    """Поток для запуска SingBox без блокировки UI"""
    finished = pyqtSignal(object)  # subprocess.Popen
    error = pyqtSignal(str)
    
    def __init__(self, core_exe, config_file, core_dir):
        super().__init__()
        self.core_exe = core_exe
        self.config_file = config_file
        self.core_dir = core_dir
    
    def run(self):
        try:
            # Скрываем окно консоли
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            proc = subprocess.Popen(
                [str(self.core_exe), "run", "-c", str(self.config_file)],
                stdout=subprocess.DEVNULL,  # Перенаправляем в /dev/null чтобы не блокировать
                stderr=subprocess.DEVNULL,  # Перенаправляем в /dev/null чтобы не блокировать
                cwd=str(self.core_dir),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            
            # Небольшая задержка, чтобы процесс успел запуститься
            import time
            time.sleep(0.2)
            
            # Проверяем, что процесс все еще запущен
            if proc.poll() is None:
                # Процесс запущен успешно
                self.finished.emit(proc)
            else:
                # Процесс завершился сразу после запуска
                returncode = proc.returncode if proc.returncode is not None else -1
                self.error.emit(f"Процесс завершился сразу после запуска с кодом {returncode}")
        except Exception as e:
            self.error.emit(str(e))


if __name__ == "__main__":
    try:
        # Создаем папки для логов ДО логирования
        ensure_dirs()
        
        log_to_file(f"[Startup] Запуск приложения, PID: {os.getpid()}")
        log_to_file(f"[Startup] Запущено от имени администратора: {is_admin()}")
        log_to_file(f"[Startup] Путь к исполняемому файлу: {sys.executable}")
        log_to_file(f"[Startup] Рабочий каталог: {os.getcwd()}")
        
        app = QApplication(sys.argv)
        app.setApplicationName("SingBox-UI")
        
        # Загружаем настройки для проверки разрешения нескольких процессов
        settings = SettingsManager()
        allow_multiple = settings.get("allow_multiple_processes", True)
        log_to_file(f"[Startup] Разрешено несколько процессов: {allow_multiple}")
        
        # Регистрируем протоколы при первом запуске (если еще не зарегистрированы)
        try:
            import winreg
            protocol_registered = False
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\singbox-ui"):
                    protocol_registered = True
            except FileNotFoundError:
                pass
            
            if not protocol_registered:
                log_to_file("[Startup] Регистрация протоколов sing-box:// и singbox-ui://...")
                if register_protocols():
                    log_to_file("[Startup] Протоколы успешно зарегистрированы")
                else:
                    log_to_file("[Startup] Не удалось зарегистрировать протоколы")
        except Exception as e:
            log_to_file(f"[Startup] Ошибка при проверке/регистрации протоколов: {e}")
    
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
        if not tray_available:
            log_to_file("[Startup] Предупреждение: Системный трей недоступен на этой системе.")
        
        log_to_file("[Startup] Применение темы...")
        apply_dark_theme(app)
        
        # Устанавливаем иконку приложения для QApplication (чтобы Windows показывала её в заголовке)
        if getattr(sys, 'frozen', False):
            base_path = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
            icon_path = base_path / "icon.ico"
            if not icon_path.exists():
                icon_path = base_path / "icon.png"
            if not icon_path.exists():
                exe_path = Path(sys.executable)
                icon_path = exe_path.parent / "icon.ico"
                if not icon_path.exists():
                    icon_path = exe_path.parent / "icon.png"
            if icon_path.exists():
                app_icon = QIcon(str(icon_path))
                if not app_icon.isNull():
                    app.setWindowIcon(app_icon)
        else:
            icon_path = Path(__file__).parent / "icon.ico"
            if not icon_path.exists():
                icon_path = Path(__file__).parent / "icon.png"
            if icon_path.exists():
                app_icon = QIcon(str(icon_path))
                if not app_icon.isNull():
                    app.setWindowIcon(app_icon)
        
        log_to_file("[Startup] Создание главного окна...")
        win = MainWindow()
        
        # Устанавливаем ссылку на MainWindow для показа логов из log_to_file в UI при isDebug=True
        set_main_window(win)
        
        # Проверяем настройку run_as_admin при запуске
        run_as_admin_setting = win.settings.get("run_as_admin", False)
        if run_as_admin_setting and not is_admin():
            log_to_file("[Startup] Настройка 'run_as_admin' включена, но приложение не запущено от админа. Перезапуск...")
            if restart_as_admin():
                sys.exit(0)
            else:
                log_to_file("[Startup] Не удалось перезапустить от имени администратора")
        
        # Устанавливаем поведение закрытия окна в зависимости от настройки трея
        minimize_to_tray = win.settings.get("minimize_to_tray", True)
        app.setQuitOnLastWindowClosed(not minimize_to_tray)
        
        # Убеждаемся, что трей показывается сразу после создания окна
        # Проверяем оба варианта имени на случай, если где-то используется другое имя
        if hasattr(win, 'tray_icon') and win.tray_icon:
            win.tray_icon.show()
        elif hasattr(win, 'trayicon') and win.trayicon:
            win.trayicon.show()
        
        log_to_file("[Startup] Показ главного окна...")
        win.show()
        log_to_file("[Startup] Запуск главного цикла приложения...")
        sys.exit(app.exec_())
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

