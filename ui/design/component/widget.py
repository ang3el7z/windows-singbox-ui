"""Виджет - компонент из дизайн-системы"""
from typing import Optional
from PyQt5.QtWidgets import QWidget
from ui.styles import theme


class Container(QWidget):
    """Контейнер с применением стилей из дизайн-системы"""
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        background_color: Optional[str] = None
    ):
        """
        Инициализация контейнера
        
        Args:
            parent: Родительский виджет
            background_color: Цвет фона (если не указан, используется background_primary)
        """
        super().__init__(parent)
        bg_color = background_color or theme.get_color('background_primary')
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: none;
            }}
        """)

