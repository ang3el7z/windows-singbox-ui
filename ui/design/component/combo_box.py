"""Комбобокс - компонент из дизайн-системы"""
from typing import Optional
from PyQt5.QtWidgets import QComboBox, QWidget
from ui.styles import StyleSheet


class ComboBox(QComboBox):
    """Комбобокс с применением стилей из дизайн-системы"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Инициализация комбобокса
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.combo_box())

