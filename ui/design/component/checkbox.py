"""Чекбокс - компонент из дизайн-системы"""
from typing import Optional
from PyQt5.QtWidgets import QCheckBox, QWidget
from ui.styles import StyleSheet


class CheckBox(QCheckBox):
    """Чекбокс с применением стилей из дизайн-системы"""
    
    def __init__(
        self,
        text: str = "",
        parent: Optional[QWidget] = None
    ):
        """
        Инициализация чекбокса
        
        Args:
            text: Текст чекбокса
            parent: Родительский виджет
        """
        super().__init__(text, parent)
        self.setStyleSheet(StyleSheet.checkbox())

