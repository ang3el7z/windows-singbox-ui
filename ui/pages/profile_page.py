"""Страница профилей"""
from typing import TYPE_CHECKING, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import qtawesome as qta
from ui.pages.base_page import BasePage
from ui.widgets import CardWidget
from ui.styles import StyleSheet
from utils.i18n import tr

if TYPE_CHECKING:
    from main import MainWindow


class ProfilePage(BasePage):
    """Страница управления профилями"""
    
    def __init__(self, main_window: 'MainWindow', parent: Optional[QWidget] = None):
        """
        Инициализация страницы профилей
        
        Args:
            main_window: Ссылка на главное окно для доступа к методам
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.main_window = main_window
        self._build_ui()
    
    def _build_ui(self):
        """Построение UI страницы"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        
        # Заголовок
        self.lbl_profile_title = QLabel(tr("profile.title"))
        self.lbl_profile_title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        self.lbl_profile_title.setStyleSheet(StyleSheet.label(variant="default", size="xlarge"))
        layout.addWidget(self.lbl_profile_title)
        
        # Список подписок
        self.sub_list = QListWidget()
        self.sub_list.currentRowChanged.connect(self.main_window.on_sub_changed)
        self.sub_list.setStyleSheet(StyleSheet.list_widget())
        layout.addWidget(self.sub_list, 1)
        
        # Кнопки управления
        btn_row = QHBoxLayout()
        self.btn_add_sub = QPushButton(qta.icon("mdi.plus"), tr("profile.add"))
        self.btn_del_sub = QPushButton(qta.icon("mdi.delete"), tr("profile.delete"))
        self.btn_rename_sub = QPushButton(qta.icon("mdi.rename-box"), tr("profile.rename"))
        self.btn_test_sub = QPushButton(qta.icon("mdi.network"), tr("profile.test"))
        
        for b in (self.btn_add_sub, self.btn_del_sub, self.btn_rename_sub, self.btn_test_sub):
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(StyleSheet.button(variant="secondary", size="medium"))
            btn_row.addWidget(b)
        
        self.btn_add_sub.clicked.connect(self.main_window.on_add_sub)
        self.btn_del_sub.clicked.connect(self.main_window.on_del_sub)
        self.btn_rename_sub.clicked.connect(self.main_window.on_rename_sub)
        self.btn_test_sub.clicked.connect(self.main_window.on_test_sub)
        
        layout.addLayout(btn_row)
        self._layout.addWidget(card)
    
    def refresh_subscriptions(self):
        """Обновление списка подписок"""
        saved_index = self.main_window.current_sub_index
        self.sub_list.clear()
        for name in self.main_window.subs.list_names():
            self.sub_list.addItem(name)
        if self.sub_list.count() > 0:
            if 0 <= saved_index < self.sub_list.count():
                self.sub_list.setCurrentRow(saved_index)
                self.main_window.current_sub_index = saved_index
            else:
                self.sub_list.setCurrentRow(0)
                self.main_window.current_sub_index = 0
        else:
            self.main_window.current_sub_index = -1

