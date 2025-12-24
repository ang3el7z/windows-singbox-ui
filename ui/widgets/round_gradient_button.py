"""Круглая кнопка с градиентом и тенью"""
from typing import Optional
from PyQt5.QtWidgets import QPushButton, QGraphicsDropShadowEffect, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QRadialGradient, QBrush
from ui.styles import theme


class GradientWidget(QWidget):
    """Виджет для отображения градиента под кнопкой"""
    
    def __init__(self, size: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.gradient_color = theme.get_color('accent')
        self.bg_color = theme.get_color('background_secondary')
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Пропускаем события мыши через градиент
    
    def update_gradient_color(self, color: str):
        """Обновляет цвет градиента"""
        self.gradient_color = color
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # Градиент
        gradient = QRadialGradient(
            rect.center(),
            rect.width() / 2
        )
        gradient.setColorAt(0.0, QColor(self.gradient_color))
        gradient.setColorAt(1.0, QColor(self.bg_color))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(rect)


class RoundGradientButton(QPushButton):
    """Круглая кнопка с градиентом под ней"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(150, 150)
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setStyleSheet("border: none; background: transparent;")
        
        # Тень
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(32)
        self.shadow.setOffset(0, 6)
        self._update_shadow_color()
        self.setGraphicsEffect(self.shadow)
        
        # Цвет текста
        self.text_color = theme.get_color('text_secondary')
    
    def _update_shadow_color(self):
        """Обновляет цвет тени из темы"""
        accent = theme.get_color('accent')
        # Преобразуем hex в rgba для прозрачности
        accent_rgb = QColor(accent)
        accent_rgb.setAlpha(180)
        self.shadow.setColor(accent_rgb)
    
    def update_style(self, gradient_color: Optional[str] = None, text_color: Optional[str] = None, shadow_color: Optional[str] = None):
        """Обновляет стиль кнопки"""
        if text_color:
            self.text_color = text_color
        if shadow_color:
            shadow_rgb = QColor(shadow_color)
            shadow_rgb.setAlpha(180)
            self.shadow.setColor(shadow_rgb)
        self.update()  # Перерисовываем кнопку
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # Только текст (градиент теперь под кнопкой)
        painter.setPen(QColor(self.text_color))
        font = painter.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.text())

