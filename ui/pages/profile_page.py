"""Страница профилей"""
from typing import TYPE_CHECKING, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.pages.base_page import BasePage
from ui.widgets import CardWidget
from ui.styles import StyleSheet, theme
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
        layout.setSpacing(16)
        
        # Заголовок
        self.lbl_profile_title = QLabel(tr("profile.title"))
        self.lbl_profile_title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        self.lbl_profile_title.setStyleSheet(StyleSheet.label(variant="default", size="xlarge"))
        layout.addWidget(self.lbl_profile_title)
        
        # Список подписок (без обводки, внутри карточки)
        self.sub_list = QListWidget()
        self.sub_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sub_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sub_list.currentRowChanged.connect(self.main_window.on_sub_changed)
        # Убираем обводку у списка, оставляем только фон
        self.sub_list.setStyleSheet(f"""
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
        layout.addWidget(self.sub_list, 1)
        
        # Кнопки управления (без отдельных подложек, просто кнопки)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_add_sub = QPushButton(tr("profile.add"))
        self.btn_del_sub = QPushButton(tr("profile.delete"))
        self.btn_rename_sub = QPushButton(tr("profile.rename"))
        
        # Стиль кнопок без подложек, просто с фоном и границей
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
                text-align: center;
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
        
        for b in (self.btn_add_sub, self.btn_del_sub, self.btn_rename_sub):
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(button_style)
            btn_row.addWidget(b, 1)
        
        self.btn_add_sub.clicked.connect(self.main_window.on_add_sub)
        self.btn_del_sub.clicked.connect(self.main_window.on_del_sub)
        self.btn_rename_sub.clicked.connect(self.main_window.on_rename_sub)
        
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

