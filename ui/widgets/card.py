"""Универсальный виджет карточки"""
from typing import Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from ui.styles import StyleSheet


class CardWidget(QWidget):
    """
    Универсальная карточка с единым стилем
    
    Args:
        parent: Родительский виджет
        radius: Радиус скругления (опционально)
    """
    
    def __init__(self, parent: Optional[QWidget] = None, radius: Optional[int] = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.card(radius))

