"""Главный файл приложения SingBox-UI"""
import sys
import subprocess
import ctypes
import os
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QTextEdit, QStackedWidget,
    QSpinBox, QCheckBox, QInputDialog, QMessageBox, QDialog, QProgressBar,
    QLineEdit, QSystemTrayIcon, QMenu, QAction
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
from utils.i18n import tr, set_language
from utils.singbox import get_singbox_version, get_latest_version, compare_versions
from core.downloader import DownloadThread


def is_admin():
    """Проверка, запущено ли приложение от имени администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def restart_as_admin():
    """Перезапуск приложения от имени администратора"""
    if is_admin():
        return False  # Уже запущено от имени администратора
    
    try:
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = sys.executable
        
        # Сначала запускаем новый процесс от имени администратора
        # Используем ShellExecute для запуска от имени администратора
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe_path, "", None, 1
        )
        
        # Проверяем результат (если > 32, то успешно)
        if result > 32:
            # Даем время на запуск нового процесса
            import time
            time.sleep(1.0)
            
            # Теперь убиваем старые процессы (кроме нового)
            try:
                import psutil
                current_pid = os.getpid()
                exe_name = Path(exe_path).name
                
                # Получаем список всех процессов с таким именем
                pids_to_kill = []
                for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                    try:
                        if proc.info['name'] and exe_name.lower() in proc.info['name'].lower():
                            if proc.info['pid'] != current_pid:
                                # Проверяем время создания - если процесс старше 2 секунд, убиваем
                                if proc.info.get('create_time', 0) < time.time() - 2:
                                    pids_to_kill.append(proc.info['pid'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Убиваем старые процессы
                for pid in pids_to_kill:
                    try:
                        proc = psutil.Process(pid)
                        proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except ImportError:
                # Если psutil не доступен, используем taskkill с задержкой
                import time
                time.sleep(0.5)
                try:
                    exe_name = Path(sys.executable).name
                    subprocess.run(
                        ["taskkill", "/F", "/IM", exe_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=3
                    )
                except Exception:
                    pass
            
            return True
        else:
            return False
    except Exception as e:
        # Ошибка перезапуска от имени администратора
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


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        # Сначала создаем папки
        ensure_dirs()
        
        # Инициализируем менеджеры
        self.settings = SettingsManager()
        self.subs = SubscriptionManager()
        
        # Устанавливаем язык из настроек
        language = self.settings.get("language", "ru")
        set_language(language)

        self.proc: subprocess.Popen | None = None
        self.current_sub_index: int = 0
        self.cached_latest_version = None  # Кэш последней версии
        self.version_check_failed_count = 0  # Счетчик неудачных проверок

        self.setWindowTitle(tr("app.title"))
        self.setMinimumSize(420, 780)

        # Устанавливаем иконку окна
        if getattr(sys, 'frozen', False):
            # Запущено как exe - используем иконку из exe файла
            exe_path = Path(sys.executable)
            self.setWindowIcon(QIcon(str(exe_path)))
        else:
            # Запущено как скрипт - используем icon.png если есть
            icon_path = Path(__file__).parent / "icon.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))

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
        root.addWidget(nav)

        # Инициализация
        # Проверяем права администратора
        self.is_admin = is_admin()
        if not self.is_admin:
            print("[Admin Check] Приложение запущено без прав администратора")
        
        self.refresh_subscriptions_ui()
        self.update_version_info()
        self.update_profile_info()
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
        self.update_info_timer = QTimer(self)
        self.update_info_timer.timeout.connect(self.update_version_info)
        self.update_info_timer.timeout.connect(self.update_profile_info)
        self.update_info_timer.start(5000)
        
        self.proc_timer = QTimer(self)
        self.proc_timer.timeout.connect(self.poll_process)
        self.proc_timer.start(700)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.auto_update_config)
        self.update_timer.start(self.settings.get("auto_update_minutes", 90) * 60 * 1000)

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
        
        title = QLabel(tr("profile.title"))
        title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        title.setStyleSheet("color: #ffffff; background-color: transparent; border: none; padding: 0px;")
        layout.addWidget(title)

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
        self.btn_test_sub = QPushButton(qta.icon("mdi.network"), tr("profile.test"))

        for b in (self.btn_add_sub, self.btn_del_sub, self.btn_test_sub):
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
        
        profile_title = QLabel(tr("home.profile"))
        profile_title.setFont(QFont("Segoe UI Semibold", 13, QFont.Bold))
        profile_title.setStyleSheet("color: #ffffff; background-color: transparent; border: none; padding: 0px;")
        profile_layout.addWidget(profile_title)
        
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
        
        self.lbl_state = QLabel(tr("home.state_stopped"))
        self.lbl_state.setAlignment(Qt.AlignCenter)
        self.lbl_state.setFont(QFont("Segoe UI", 14))
        self.lbl_state.setStyleSheet("color: #9ca3af; background-color: transparent; border: none; margin-top: 16px; padding: 0px;")
        btn_layout.addWidget(self.lbl_state)
        
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
        
        title = QLabel(tr("settings.title"))
        title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        title.setStyleSheet("color: #ffffff; background-color: transparent; border: none; padding: 0px;")
        settings_layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(12)
        row_label = QLabel(tr("settings.auto_update_interval"))
        row_label.setFont(QFont("Segoe UI", 13))
        row_label.setStyleSheet("color: #e5e9ff; background-color: transparent; border: none; padding: 0px;")
        row.addWidget(row_label)
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(5, 1440)
        self.spin_interval.setValue(self.settings.get("auto_update_minutes", 90))
        self.spin_interval.valueChanged.connect(self.on_interval_changed)
        self.spin_interval.setStyleSheet("""
            QSpinBox {
                background-color: rgba(0,245,212,0.1);
                color: #00f5d4;
                border-radius: 12px;
                padding: 10px 14px;
                border: none;
                font-size: 13px;
                font-weight: 500;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 24px;
                height: 20px;
                border-left: 1px solid rgba(0,245,212,0.2);
                border-top-right-radius: 12px;
                background-color: rgba(0,245,212,0.15);
            }
            QSpinBox::up-button:hover {
                background-color: rgba(0,245,212,0.25);
            }
            QSpinBox::up-button:pressed {
                background-color: rgba(0,245,212,0.35);
            }
            QSpinBox::up-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 6px solid #00f5d4;
                margin: 2px;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 24px;
                height: 20px;
                border-left: 1px solid rgba(0,245,212,0.2);
                border-bottom-right-radius: 12px;
                background-color: rgba(0,245,212,0.15);
            }
            QSpinBox::down-button:hover {
                background-color: rgba(0,245,212,0.25);
            }
            QSpinBox::down-button:pressed {
                background-color: rgba(0,245,212,0.35);
            }
            QSpinBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #00f5d4;
                margin: 2px;
            }
        """)
        row.addWidget(self.spin_interval)
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
        
        logs_title = QLabel(tr("settings.logs"))
        logs_title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        logs_title.setStyleSheet("color: #ffffff; background-color: transparent; border: none; padding: 0px;")
        logs_layout.addWidget(logs_title)
        
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
        
        outer.addWidget(logs_card, 1)
        return w

    # Навигация
    def switch_page(self, index: int):
        """Переключение страниц"""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate([self.btn_nav_profile, self.btn_nav_home, self.btn_nav_settings]):
            btn.setChecked(i == index)
        if index == 2:  # Settings page
            self.load_logs()

    # Подписки
    def refresh_subscriptions_ui(self):
        """Обновление списка подписок"""
        self.sub_list.clear()
        for name in self.subs.list_names():
            self.sub_list.addItem(name)
        if self.sub_list.count() > 0:
            self.sub_list.setCurrentRow(self.current_sub_index)
        else:
            self.current_sub_index = -1

    def on_sub_changed(self, row: int):
        """Изменение выбранной подписки"""
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
                self.subs.add(name, url)
                self.refresh_subscriptions_ui()
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
        if row < 0:
            return
        sub = self.subs.get(row)
        if not sub:
            return
        if QMessageBox.question(self, tr("profile.delete_question"),
                                tr("profile.delete_confirm", name=sub['name']),
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.subs.remove(row)
            self.refresh_subscriptions_ui()
            self.log(tr("profile.removed", name=sub['name']))

    def on_test_sub(self):
        """Тест подписки"""
        row = self.sub_list.currentRow()
        if row < 0:
            self.log(tr("profile.select_for_test"))
            return
        self.log(tr("profile.test_loading"))
        ok = self.subs.download_config(row)
        if ok:
            self.log(tr("profile.test_success"))
        else:
            self.log(tr("profile.test_error"))
    
    # Версия и профиль
    def update_version_info(self):
        """Обновление информации о версии"""
        version = get_singbox_version()
        if version:
            # Всегда показываем текущую версию
            self.lbl_version.setText(tr("home.installed", version=version))
            self.lbl_version.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px;")
            self.btn_version_warning.hide()
            
            # Проверяем наличие обновлений
            # Используем кэш если проверка не удалась несколько раз подряд
            latest_version = None
            if self.version_check_failed_count < 3:
                latest_version = get_latest_version()
                if latest_version:
                    self.cached_latest_version = latest_version
                    self.version_check_failed_count = 0
                else:
                    self.version_check_failed_count += 1
                    # Используем кэш если есть
                    if self.cached_latest_version:
                        latest_version = self.cached_latest_version
            else:
                # Используем кэш после нескольких неудачных попыток
                if self.cached_latest_version:
                    latest_version = self.cached_latest_version
            
            if latest_version:
                print(f"[Version Check] Текущая версия: {version}, Последняя версия: {latest_version}")
                comparison = compare_versions(version, latest_version)
                print(f"[Version Check] Сравнение: {comparison} (< 0 означает что текущая старше)")
                if comparison < 0:  # Текущая версия старше
                    # Показываем сообщение об обновлении под текущей версией
                    self.lbl_update_info.setText(tr("home.update_available", version=latest_version))
                    self.lbl_update_info.show()
                    self.btn_version_update.show()
                    print(f"[Version Check] Показано обновление: {latest_version}")
                else:
                    # Версия актуальна, скрываем сообщение об обновлении
                    self.lbl_update_info.hide()
                    self.btn_version_update.hide()
                    print(f"[Version Check] Версия актуальна: {version}")
            else:
                # Не удалось проверить обновления
                print(f"[Version Check] Не удалось получить последнюю версию, показываем текущую: {version}")
                self.lbl_update_info.hide()
                self.btn_version_update.hide()
        else:
            print("[Version Check] SingBox не установлен")
            self.lbl_version.setText(tr("home.not_installed"))
            self.lbl_version.setStyleSheet("color: #ff6b6b; background-color: transparent; border: none; padding: 0px;")
            self.lbl_update_info.hide()
            self.btn_version_warning.show()
            self.btn_version_update.hide()
    
    def update_profile_info(self):
        """Обновление информации о профиле"""
        if self.current_sub_index >= 0:
            sub = self.subs.get(self.current_sub_index)
            if sub:
                self.lbl_profile.setText(sub.get("name", "Неизвестно"))
                self.lbl_profile.setStyleSheet("color: #00f5d4; background-color: transparent; border: none; padding: 0px;")
            else:
                self.lbl_profile.setText(tr("home.not_selected"))
                self.lbl_profile.setStyleSheet("color: #9ca3af; background-color: transparent; border: none; padding: 0px;")
        else:
            self.lbl_profile.setText(tr("home.not_selected"))
            self.lbl_profile.setStyleSheet("color: #9ca3af; background-color: transparent; border: none; padding: 0px;")
    
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
        # Обновляем подложку
        if hasattr(self, 'btn_wrapper'):
            if running:
                self.btn_wrapper.setStyleSheet("""
                    QWidget {
                        background-color: #1a1f2e;
                        border-radius: 110px;
                        border: 2px solid rgba(255,107,107,0.5);
                    }
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
            self.big_btn.setText(tr("home.button_stop"))
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
            self.big_btn.setText(tr("home.button_start"))
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
        has_sub = self.sub_list.count() > 0 and self.current_sub_index >= 0
        self.big_btn.setEnabled(core_ok and has_sub)
        running = self.proc and self.proc.poll() is None
        self.style_big_btn_running(bool(running))
        self.lbl_state.setText(tr("home.state_running") if running else tr("home.state_stopped"))

    def on_big_button(self):
        """Обработка нажатия большой кнопки"""
        if self.proc and self.proc.poll() is None:
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
        if self.current_sub_index < 0:
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
        
        self.log(tr("messages.downloading_config"))
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
            self.log(tr("messages.started_success"))
        else:
            # Процесс завершился сразу после запуска
            if proc:
                code = proc.returncode if proc.returncode is not None else -1
                self.log(tr("messages.stopped", code=code))
            self.proc = None
        self.update_big_button_state()
    
    def on_singbox_start_error(self, error_msg):
        """Обработка ошибки запуска SingBox"""
        self.log(tr("messages.start_error", error=error_msg))
        self.proc = None
        self.update_big_button_state()

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
        self.update_big_button_state()

    def auto_update_config(self):
        """Автообновление конфига"""
        if self.current_sub_index < 0:
            return
        self.log(tr("messages.auto_update"))
        ok = self.subs.download_config(self.current_sub_index)
        if not ok:
            self.log(tr("messages.auto_update_error"))
            return
        if self.proc and self.proc.poll() is None:
            self.log(tr("messages.auto_update_restart"))
            self.stop_singbox()
            self.start_singbox()
        else:
            self.log(tr("messages.auto_update_not_running"))

    def poll_process(self):
        """Опрос процесса - проверяем, не завершился ли процесс"""
        if self.proc and self.proc.poll() is not None:
            code = self.proc.returncode
            self.log(tr("messages.stopped", code=code))
            self.proc = None
            self.update_big_button_state()

    # Настройки
    def on_interval_changed(self, value: int):
        """Изменение интервала автообновления"""
        self.settings.set("auto_update_minutes", value)
        self.update_timer.start(value * 60 * 1000)
        self.log(tr("messages.interval_changed", value=value))

    def set_autostart(self, enabled: bool):
        """Установка автозапуска"""
        import winreg
        run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "SingBox-UI"

        if getattr(sys, "frozen", False):
            exe_path = sys.executable
        else:
            exe_path = str((Path(__file__).parent / "run_dev.bat").resolve())
        
        run_as_admin = self.settings.get("run_as_admin", False)

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_ALL_ACCESS) as key:
                if enabled:
                    if run_as_admin:
                        # Используем PowerShell для запуска от имени администратора
                        ps_command = f'powershell -Command "Start-Process -FilePath \\"{exe_path}\\" -Verb RunAs"'
                        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, ps_command)
                    else:
                        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                    except FileNotFoundError:
                        pass
        except OSError as e:
            self.log(tr("messages.autostart_error", error=str(e)))

    def on_autostart_changed(self, state: int):
        """Изменение автозапуска"""
        enabled = state == Qt.Checked
        self.settings.set("start_with_windows", enabled)
        self.set_autostart(enabled)
        self.log(tr("messages.autostart_enabled") if enabled else tr("messages.autostart_disabled"))
    
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
        
        self.log(tr("messages.run_as_admin_enabled") if enabled else tr("messages.run_as_admin_disabled"))
    
    def on_auto_start_singbox_changed(self, state: int):
        """Изменение настройки автозапуска sing-box при запуске приложения"""
        enabled = state == Qt.Checked
        self.settings.set("auto_start_singbox", enabled)
        self.log(tr("messages.auto_start_singbox_enabled") if enabled else tr("messages.auto_start_singbox_disabled"))
    
    def on_minimize_to_tray_changed(self, state: int):
        """Изменение настройки сворачивания в трей"""
        enabled = state == Qt.Checked
        self.settings.set("minimize_to_tray", enabled)
        self.log(tr("messages.minimize_to_tray_enabled") if enabled else tr("messages.minimize_to_tray_disabled"))
        
        # Динамически показываем/скрываем трей иконку
        if enabled:
            # Включаем трей режим
            if not hasattr(self, 'tray_icon') or not self.tray_icon:
                self.setup_tray()
            if self.tray_icon:
                self.tray_icon.show()
        else:
            # Выключаем трей режим
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.hide()
    
    def on_kill_all_clicked(self):
        """Обработка нажатия кнопки 'Убить' - полная остановка всех процессов"""
        reply = QMessageBox.question(
            self,
            tr("messages.kill_all_title"),
            tr("messages.kill_all_confirm"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.log(tr("messages.killing_all"))
            self.kill_all_processes()
            self.update_big_button_state()
            QMessageBox.information(
                self,
                tr("messages.kill_all_title"),
                tr("messages.kill_all_done")
            )
    
    def setup_tray(self):
        """Настройка системного трея"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # Создаем иконку для трея
        tray_icon = QIcon()
        if getattr(sys, 'frozen', False):
            # В frozen режиме используем иконку из exe файла
            exe_path = Path(sys.executable)
            tray_icon = QIcon(str(exe_path))
            # Если иконка не загрузилась из exe, пробуем загрузить из icon.ico рядом с exe
            if tray_icon.isNull():
                icon_path = exe_path.parent / "icon.ico"
                if icon_path.exists():
                    tray_icon = QIcon(str(icon_path))
                else:
                    icon_path = exe_path.parent / "icon.png"
                    if icon_path.exists():
                        tray_icon = QIcon(str(icon_path))
        else:
            # В режиме разработки используем иконку окна или ищем icon.png
            tray_icon = self.windowIcon()
            if tray_icon.isNull():
                icon_path = Path(__file__).parent / "icon.png"
                if icon_path.exists():
                    tray_icon = QIcon(str(icon_path))
                else:
                    icon_path = Path(__file__).parent / "icon.ico"
                    if icon_path.exists():
                        tray_icon = QIcon(str(icon_path))
        
        self.tray_icon = QSystemTrayIcon(self)
        # Всегда устанавливаем иконку, даже если она пустая (система покажет дефолтную)
        self.tray_icon.setIcon(tray_icon if not tray_icon.isNull() else QIcon())
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
        """Загрузка логов"""
        if LOG_FILE.exists():
            try:
                with LOG_FILE.open("r", encoding="utf-8") as f:
                    content = f.read()
                    self.logs.setPlainText(content)
                    cursor = self.logs.textCursor()
                    cursor.movePosition(cursor.End)
                    self.logs.setTextCursor(cursor)
            except Exception:
                pass

    def log(self, msg: str):
        """Логирование"""
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        
        if hasattr(self, 'logs'):
            self.logs.append(line)
            cursor = self.logs.textCursor()
            cursor.movePosition(cursor.End)
            self.logs.setTextCursor(cursor)
        
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            print(f"Ошибка записи в лог файл: {e}")

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
                
                event.ignore()
                self.hide()
                
                # Показываем уведомление только если иконка видна
                if self.tray_icon.isVisible():
                    self.tray_icon.showMessage(
                        tr("app.title"),
                        tr("messages.minimized_to_tray"),
                        QSystemTrayIcon.Information,
                        2000
                    )
                return
        
        # Если трей режим выключен или пользователь хочет закрыть - убиваем все процессы
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
    app = QApplication(sys.argv)
    app.setApplicationName("SingBox-UI")
    
    # Проверка единственного экземпляра приложения
    shared_memory = QSharedMemory("SingBox-UI-Instance")
    if shared_memory.attach():
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
    
    # Создаем shared memory для этого экземпляра
    if not shared_memory.create(1):
        # Если не удалось создать, возможно старый экземпляр завис - пробуем еще раз
        try:
            shared_memory.detach()
            if not shared_memory.create(1):
                sys.exit(0)
        except Exception:
            sys.exit(0)
    
    # Проверяем доступность системного трея
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None,
            "Ошибка",
            "Системный трей недоступен на этой системе."
        )
        sys.exit(1)
    
    # Не закрываем приложение при закрытии последнего окна, если трей включен
    app.setQuitOnLastWindowClosed(False)
    
    apply_dark_theme(app)
    win = MainWindow()
    
    # Убеждаемся, что трей показывается сразу после создания окна
    if hasattr(win, 'tray_icon') and win.tray_icon:
        win.tray_icon.show()
    
    win.show()
    sys.exit(app.exec_())

