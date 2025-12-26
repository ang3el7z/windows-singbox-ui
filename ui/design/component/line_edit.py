"""Поле ввода - компонент из дизайн-системы"""
from typing import Optional
from PyQt5.QtWidgets import QLineEdit, QWidget
from ui.styles import StyleSheet


class LineEdit(QLineEdit):
    """Поле ввода с применением стилей из дизайн-системы"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Инициализация поля ввода
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.input())

