"""Список - компонент из дизайн-системы"""
from typing import Optional
from PyQt5.QtWidgets import QListWidget, QWidget
from PyQt5.QtCore import Qt
from ui.styles import StyleSheet, theme


class ListWidget(QListWidget):
    """Список с применением стилей из дизайн-системы"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Инициализация списка
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Используем кастомные стили для списка внутри карточки
        self.setStyleSheet(f"""
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

