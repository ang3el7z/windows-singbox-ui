"""Текстовое поле - компонент из дизайн-системы"""
from typing import Optional
from PyQt5.QtWidgets import QTextEdit, QWidget
from ui.styles import StyleSheet


class TextEdit(QTextEdit):
    """Текстовое поле с применением стилей из дизайн-системы"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Инициализация текстового поля
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.text_edit())

