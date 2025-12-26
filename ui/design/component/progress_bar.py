"""Прогресс-бар - компонент из дизайн-системы"""
from typing import Optional
from PyQt5.QtWidgets import QProgressBar, QWidget
from ui.styles import StyleSheet


class ProgressBar(QProgressBar):
    """Прогресс-бар с применением стилей из дизайн-системы"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Инициализация прогресс-бара
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.progress_bar())

