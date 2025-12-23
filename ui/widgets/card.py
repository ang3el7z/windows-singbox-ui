"""Универсальный виджет карточки"""
from typing import Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPalette
from ui.styles import StyleSheet, theme


class CardWidget(QWidget):
    """
    Универсальная карточка с единым стилем
    
    Args:
        parent: Родительский виджет
        radius: Радиус скругления (опционально)
    """
    
    def __init__(self, parent: Optional[QWidget] = None, radius: Optional[int] = None) -> None:
        super().__init__(parent)
        # Устанавливаем имя объекта для применения стилей
        self.setObjectName("CardWidget")
        # Убеждаемся, что виджет имеет минимальный размер
        self.setMinimumHeight(1)
        
        # Сохраняем параметры для отрисовки
        self._bg_color = theme.get_color('background_secondary')
        self._radius = radius or theme.get_size('border_radius_large')
        
        # Устанавливаем явный фон через палитру
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(self._bg_color))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        # Устанавливаем стиль
        card_style = f"""
        CardWidget {{
            background-color: {self._bg_color};
            border-radius: {self._radius}px;
            border: none;
            min-height: 1px;
        }}
        QWidget#CardWidget {{
            background-color: {self._bg_color};
            border-radius: {self._radius}px;
            border: none;
        }}
        """
        self.setStyleSheet(card_style)
    
    def paintEvent(self, event):
        """Переопределяем paintEvent для гарантированного отображения фона"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Рисуем фон с закругленными углами
        rect = self.rect()
        painter.setBrush(QColor(self._bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self._radius, self._radius)
        
        super().paintEvent(event)

