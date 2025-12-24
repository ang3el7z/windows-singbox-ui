"""Главная страница"""
from typing import TYPE_CHECKING, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from utils.icon_helper import icon
from ui.pages.base_page import BasePage
from ui.widgets import CardWidget
from ui.styles import StyleSheet
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
        
        version_title = QLabel(tr("home.version"))
        version_title.setFont(QFont("Segoe UI Semibold", 13, QFont.Bold))
        version_title.setStyleSheet(StyleSheet.label(variant="default", size="large"))
        version_layout.addWidget(version_title)
        
        version_row = QHBoxLayout()
        version_row.setSpacing(10)
        
        self.lbl_version = QLabel()
        self.lbl_version.setFont(QFont("Segoe UI", 12))
        self.lbl_version.setStyleSheet(StyleSheet.label(variant="secondary"))
        # Делаем версию кликабельной для активации дебаг режима
        self.lbl_version.setCursor(Qt.PointingHandCursor)
        self.lbl_version.mousePressEvent = self.main_window.on_version_clicked
        version_row.addWidget(self.lbl_version)
        
        self.btn_version_warning = QPushButton()
        self.btn_version_warning.setIcon(icon("mdi.alert-circle", color="#ff6b6b").icon())
        self.btn_version_warning.setMinimumSize(24, 24)
        self.btn_version_warning.setMaximumSize(32, 32)
        self.btn_version_warning.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.btn_version_warning.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 50%;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 107, 107, 0.15);
            }
        """)
        self.btn_version_warning.setCursor(Qt.PointingHandCursor)
        self.btn_version_warning.clicked.connect(self.main_window.show_download_dialog)
        self.btn_version_warning.hide()
        version_row.addWidget(self.btn_version_warning)
        
        self.btn_version_update = QPushButton()
        self.btn_version_update.setIcon(icon("mdi.download", color="#00f5d4").icon())
        self.btn_version_update.setMinimumSize(24, 24)
        self.btn_version_update.setMaximumSize(32, 32)
        self.btn_version_update.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.btn_version_update.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 50%;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(0, 245, 212, 0.15);
            }
        """)
        self.btn_version_update.setCursor(Qt.PointingHandCursor)
        self.btn_version_update.clicked.connect(self.main_window.show_download_dialog)
        self.btn_version_update.hide()
        version_row.addWidget(self.btn_version_update)
        
        version_row.addStretch()
        version_layout.addLayout(version_row)
        
        # Label для сообщения об обновлении
        self.lbl_update_info = QLabel()
        self.lbl_update_info.setFont(QFont("Segoe UI", 11))
        self.lbl_update_info.setStyleSheet(StyleSheet.label(variant="warning"))
        self.lbl_update_info.setCursor(Qt.PointingHandCursor)
        self.lbl_update_info.hide()
        version_layout.addWidget(self.lbl_update_info)
        
        self._layout.addWidget(version_card)
        
        # Карточка профиля
        profile_card = CardWidget()
        profile_layout = QVBoxLayout(profile_card)
        profile_layout.setContentsMargins(20, 18, 20, 18)
        profile_layout.setSpacing(10)
        
        self.profile_title = QLabel(tr("home.profile"))
        self.profile_title.setFont(QFont("Segoe UI Semibold", 13, QFont.Bold))
        self.profile_title.setStyleSheet(StyleSheet.label(variant="default", size="large"))
        profile_layout.addWidget(self.profile_title)
        
        self.lbl_profile = QLabel(tr("home.not_selected"))
        self.lbl_profile.setFont(QFont("Segoe UI", 12))
        self.lbl_profile.setStyleSheet(StyleSheet.label(variant="secondary"))
        profile_layout.addWidget(self.lbl_profile)
        
        self._layout.addWidget(profile_card)
        
        # Информация о правах администратора (на подложке, текст должен быть виден)
        admin_info_card = CardWidget()
        admin_info_layout = QVBoxLayout(admin_info_card)
        admin_info_layout.setContentsMargins(20, 16, 20, 16)
        admin_info_layout.setSpacing(0)
        
        self.lbl_admin_status = QLabel()
        # Уменьшаем шрифт на ~2 пункта (было 11)
        self.lbl_admin_status.setFont(QFont("Segoe UI", 10))
        self.lbl_admin_status.setAlignment(Qt.AlignCenter)
        self.lbl_admin_status.mousePressEvent = self.main_window.admin_status_mouse_press
        # Устанавливаем начальный стиль с цветом из темы
        from ui.styles import theme
        from core.protocol import is_admin
        if is_admin():
            initial_color = theme.get_color('accent')
        else:
            initial_color = theme.get_color('warning')
        self.lbl_admin_status.setStyleSheet(f"color: {initial_color}; background-color: transparent; border: none; padding: 0px;")
        # Обновляем текст и стиль
        self.main_window.update_admin_status_label()
        admin_info_layout.addWidget(self.lbl_admin_status)
        
        self._layout.addWidget(admin_info_card)
        
        # Кнопка Start/Stop
        self.btn_container = QWidget()
        self.btn_container.setStyleSheet("background-color: transparent; border: none;")
        btn_layout = QVBoxLayout(self.btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setAlignment(Qt.AlignCenter)
        
        self.big_btn = QPushButton(tr("home.button_start"))
        # Фиксированный размер кнопки (круглая)
        button_size = 160
        self.big_btn.setFixedSize(button_size, button_size)
        self.main_window.style_big_btn_running(False)
        self.big_btn.clicked.connect(self.main_window.on_big_button)
        self.big_btn.setCursor(Qt.PointingHandCursor)
        
        btn_layout.addWidget(self.big_btn, 1, alignment=Qt.AlignCenter)
        
        # Скрываем кнопку по умолчанию - она будет показана через update_big_button_state
        # когда будет выбран профиль или если singbox запущен
        self.btn_container.hide()
        
        self._layout.addWidget(self.btn_container, 1)
    

