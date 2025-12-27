"""Страница профилей"""
from typing import TYPE_CHECKING, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.pages.base_page import BasePage
from ui.design import CardWidget
from ui.design.component import ListWidget, Button, Label
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
        self.lbl_profile_title = Label(tr("profile.title"), variant="default", size="xlarge")
        self.lbl_profile_title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        layout.addWidget(self.lbl_profile_title)
        
        # Список подписок (без обводки, внутри карточки)
        self.sub_list = ListWidget()
        self.sub_list.currentRowChanged.connect(self.main_window.on_sub_changed)
        layout.addWidget(self.sub_list, 1)
        
        # Кнопки управления (без отдельных подложек, просто кнопки)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_add_sub = Button(tr("profile.add"), variant="secondary")
        self.btn_del_sub = Button(tr("profile.delete"), variant="secondary")
        self.btn_rename_sub = Button(tr("profile.rename"), variant="secondary")
        
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
            b.setStyleSheet(button_style)
            btn_row.addWidget(b, 1)
        
        self.btn_add_sub.clicked.connect(self.main_window.on_add_sub)
        self.btn_del_sub.clicked.connect(self.main_window.on_del_sub)
        self.btn_rename_sub.clicked.connect(self.main_window.on_rename_sub)
        
        layout.addLayout(btn_row)
        self._layout.addWidget(card)
    
    def refresh_subscriptions(self):
        """Обновление списка профилей с визуальным различием типов"""
        saved_index = self.main_window.current_sub_index
        self.sub_list.clear()
        
        from utils.icon_helper import icon
        from managers.subscriptions import SubscriptionManager
        
        profiles = self.main_window.subs.data.get("profiles", [])
        for i, profile in enumerate(profiles):
            name = profile.get("name", "no-name")
            profile_type = profile.get("type", SubscriptionManager.PROFILE_TYPE_SUBSCRIPTION)
            
            # Создаем элемент списка с иконкой типа
            item = QListWidgetItem(name)
            
            if profile_type == SubscriptionManager.PROFILE_TYPE_SUBSCRIPTION:
                # Подписка - иконка обновления
                icon_item = icon("mdi.sync", color=theme.get_color('accent'))
            else:
                # Готовый конфиг - иконка файла
                icon_item = icon("mdi.file-document", color=theme.get_color('text_secondary'))
            
            if icon_item:
                item.setIcon(icon_item.icon())
            
            self.sub_list.addItem(item)
        
        if self.sub_list.count() > 0:
            if 0 <= saved_index < self.sub_list.count():
                self.sub_list.setCurrentRow(saved_index)
                self.main_window.current_sub_index = saved_index
            else:
                # Если сохраненный индекс невалидный, выбираем первый профиль
                self.sub_list.setCurrentRow(0)
                self.main_window.current_sub_index = 0
                # Сохраняем исправленный индекс в настройках
                self.main_window.settings.set("current_sub_index", 0)
        else:
            self.main_window.current_sub_index = -1
            # Сохраняем -1 если профилей нет
            self.main_window.settings.set("current_sub_index", -1)

