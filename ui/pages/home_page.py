"""Главная страница"""
from typing import TYPE_CHECKING, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from utils.icon_helper import icon
from ui.pages.base_page import BasePage
from ui.design import CardWidget
from ui.design.component import Label, Button
from ui.styles import StyleSheet, theme
from utils.i18n import tr

if TYPE_CHECKING:
    from main import MainWindow


class HomePage(BasePage):
    """Главная страница приложения"""
    
    def __init__(self, main_window: 'MainWindow', parent: Optional[QWidget] = None):
        """
        Инициализация главной страницы
        
        Args:
            main_window: Ссылка на главное окно
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.main_window = main_window
        self._layout.setContentsMargins(16, 20, 16, 20)
        self._layout.setSpacing(12)
        self._build_ui()
    
    def _build_ui(self):
        """Построение UI страницы"""
        # Карточка версии
        version_card = CardWidget()
        version_layout = QVBoxLayout(version_card)
        version_layout.setContentsMargins(20, 18, 20, 18)
        version_layout.setSpacing(10)
        
        self.version_title = Label(tr("home.version"), variant="default", size="large")
        self.version_title.setFont(QFont("Segoe UI Semibold", 13, QFont.Bold))
        version_layout.addWidget(self.version_title)
        
        version_row = QHBoxLayout()
        version_row.setSpacing(10)
        
        self.lbl_version = Label(variant="secondary")
        self.lbl_version.setFont(QFont("Segoe UI", 12))
        # Версия ядра не кликабельна (дебаг режим активируется только через версию приложения)
        version_row.addWidget(self.lbl_version)
        
        self.btn_version_warning = Button()
        error_color = theme.get_color('error')
        self.btn_version_warning.setIcon(icon("mdi.alert-circle", color=error_color).icon())
        self.btn_version_warning.setMinimumSize(24, 24)
        self.btn_version_warning.setMaximumSize(32, 32)
        self.btn_version_warning.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        # Используем error цвет с прозрачностью для hover (можно улучшить, добавив error_light в темы)
        error_hex = error_color.lstrip('#')
        error_r = int(error_hex[0:2], 16)
        error_g = int(error_hex[2:4], 16)
        error_b = int(error_hex[4:6], 16)
        error_hover = f"rgba({error_r}, {error_g}, {error_b}, 0.15)"
        self.btn_version_warning.setStyleSheet(f"""
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
        self.btn_version_warning.clicked.connect(self.main_window.show_download_dialog)
        self.btn_version_warning.hide()
        version_row.addWidget(self.btn_version_warning)
        
        self.btn_version_update = Button()
        warning_color = theme.get_color('warning')
        self.btn_version_update.setIcon(icon("mdi.download", color=warning_color).icon())
        self.btn_version_update.setMinimumSize(24, 24)
        self.btn_version_update.setMaximumSize(32, 32)
        self.btn_version_update.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        warning_hex = warning_color.lstrip('#')
        warning_r = int(warning_hex[0:2], 16)
        warning_g = int(warning_hex[2:4], 16)
        warning_b = int(warning_hex[4:6], 16)
        warning_light = f"rgba({warning_r}, {warning_g}, {warning_b}, 0.15)"
        self.btn_version_update.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 50%;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {warning_light};
            }}
        """)
        # Обработчик клика для обновления ядра
        def on_core_update_clicked():
            from utils.singbox import get_singbox_version
            from config.paths import CORE_EXE
            
            # Если стрелочка показывается, значит есть обновление
            # Получаем текущую версию и показываем диалог обновления
            if CORE_EXE.exists():
                current_version = get_singbox_version()
                if current_version and self.main_window.cached_latest_version:
                    # Есть обновление - показываем диалог с версиями
                    self.main_window.show_download_dialog(
                        is_update=True,
                        current_version=current_version,
                        latest_version=self.main_window.cached_latest_version
                    )
                    return
            
            # Если ядра нет - показываем диалог установки
            if not CORE_EXE.exists():
                self.main_window.show_download_dialog()
                return
            
            # Если версии не определены - показываем обычный диалог
            self.main_window.show_download_dialog()
        
        self.btn_version_update.clicked.connect(on_core_update_clicked)
        self.btn_version_update.hide()
        version_row.addWidget(self.btn_version_update)
        
        version_row.addStretch()
        version_layout.addLayout(version_row)
        
        # Label для сообщения об обновлении
        self.lbl_update_info = Label(variant="warning")
        self.lbl_update_info.setFont(QFont("Segoe UI", 11))
        self.lbl_update_info.setCursor(Qt.PointingHandCursor)
        self.lbl_update_info.hide()
        version_layout.addWidget(self.lbl_update_info)
        
        self._layout.addWidget(version_card)
        
        # Карточка профиля
        profile_card = CardWidget()
        profile_layout = QVBoxLayout(profile_card)
        profile_layout.setContentsMargins(20, 18, 20, 18)
        profile_layout.setSpacing(10)
        
        self.profile_title = Label(tr("home.profile"), variant="default", size="large")
        self.profile_title.setFont(QFont("Segoe UI Semibold", 13, QFont.Bold))
        profile_layout.addWidget(self.profile_title)
        
        self.lbl_profile = Label(tr("home.not_selected"), variant="secondary")
        self.lbl_profile.setFont(QFont("Segoe UI", 12))
        profile_layout.addWidget(self.lbl_profile)
        
        self._layout.addWidget(profile_card)
        
        # Кнопка Start/Stop
        from ui.design.component import Container
        self.btn_container = Container()
        self.btn_container.setStyleSheet("background-color: transparent; border: none;")
        btn_layout = QVBoxLayout(self.btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setAlignment(Qt.AlignCenter)
        
        self.big_btn = Button(tr("home.button_start"))
        # Фиксированный размер кнопки (круглая)
        button_size = 160
        self.big_btn.setFixedSize(button_size, button_size)
        self.main_window.style_big_btn_running(False)
        self.big_btn.clicked.connect(self.main_window.on_big_button)
        
        btn_layout.addWidget(self.big_btn, 1, alignment=Qt.AlignCenter)
        
        # Скрываем кнопку по умолчанию - она будет показана через update_big_button_state
        # когда будет выбран профиль или если singbox запущен
        self.btn_container.hide()
        
        self._layout.addWidget(self.btn_container, 1)
    

