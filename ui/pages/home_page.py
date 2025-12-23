"""Главная страница"""
from typing import TYPE_CHECKING, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import qtawesome as qta
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
        self.btn_version_warning.clicked.connect(self.main_window.show_download_dialog)
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
        self.btn_version_update.clicked.connect(self.main_window.show_download_dialog)
        self.btn_version_update.hide()
        version_row.addWidget(self.btn_version_update)
        
        version_row.addStretch()
        version_layout.addLayout(version_row)
        
        # Label для сообщения об обновлении
        self.lbl_update_info = QLabel()
        self.lbl_update_info.setFont(QFont("Segoe UI", 11))
        self.lbl_update_info.setStyleSheet(StyleSheet.label(variant="warning"))
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
        self.lbl_admin_status.setFont(QFont("Segoe UI", 11))
        self.lbl_admin_status.setAlignment(Qt.AlignCenter)
        self.lbl_admin_status.mousePressEvent = self.main_window.admin_status_mouse_press
        # Используем StyleSheet.label как базовый стиль, аналогично lbl_update_info
        self.lbl_admin_status.setStyleSheet(StyleSheet.label(variant="warning"))
        self.main_window.update_admin_status_label()
        admin_info_layout.addWidget(self.lbl_admin_status)
        
        self._layout.addWidget(admin_info_card)
        
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
        self.main_window.style_big_btn_running(False)
        self.big_btn.clicked.connect(self.main_window.on_big_button)
        self.big_btn.setCursor(Qt.PointingHandCursor)
        wrapper_layout.addWidget(self.big_btn)
        
        btn_layout.addWidget(self.btn_wrapper, alignment=Qt.AlignCenter)
        
        self._layout.addWidget(btn_container)
        self._layout.addStretch()

