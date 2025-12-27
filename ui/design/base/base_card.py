"""Базовая карточка - компонент из дизайн-системы"""
from typing import Optional
from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPalette
from ui.styles import theme


class BaseCard(QWidget):
    """
    Универсальная карточка с единым стилем из дизайн-системы
    
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
        # Карточки должны расширяться
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Параметры темы (инициализация)
        self._radius = radius or theme.get_size('border_radius_large')
        self.apply_theme()
    
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

    def apply_theme(self):
        """Пере-применяет цвета/радиус под текущую тему"""
        self._bg_color = theme.get_color('background_secondary')
        self._radius = self._radius or theme.get_size('border_radius_large')
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(self._bg_color))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
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
        # Обновляем виджет чтобы перерисовать paintEvent
        self.update()




