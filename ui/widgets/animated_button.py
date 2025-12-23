"""Анимированная кнопка Start/Stop"""
from typing import Optional
from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QSize
from PyQt5.QtGui import QPainter, QPen, QColor
from ui.styles import theme


class AnimatedStartButton(QPushButton):
    """Анимированная кнопка Start/Stop с вращающейся обводкой"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._rotation_angle = 0
        self._is_running = False
        self._is_animating = False
        
        # Анимация вращения
        self.rotation_animation = QPropertyAnimation(self, b"rotation_angle")
        self.rotation_animation.setDuration(2000)  # 2 секунды на полный оборот
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setLoopCount(-1)  # Бесконечный цикл
        self.rotation_animation.setEasingCurve(QEasingCurve.Linear)
    
    def get_rotation_angle(self) -> float:
        """Получить угол вращения"""
        return self._rotation_angle
    
    def set_rotation_angle(self, angle: float):
        """Установить угол вращения"""
        self._rotation_angle = angle
        self.update()
    
    rotation_angle = pyqtProperty(float, get_rotation_angle, set_rotation_angle)
    
    def start_animation(self):
        """Запустить анимацию вращения"""
        if not self._is_animating:
            self._is_animating = True
            self.rotation_animation.start()
    
    def stop_animation(self):
        """Остановить анимацию вращения"""
        if self._is_animating:
            self._is_animating = False
            self.rotation_animation.stop()
            self._rotation_angle = 0
            self.update()
    
    def set_running(self, running: bool):
        """Установить состояние запуска"""
        self._is_running = running
        if running:
            self.start_animation()
        else:
            self.stop_animation()
    
    def paintEvent(self, event):
        """Переопределяем отрисовку для добавления вращающейся обводки"""
        super().paintEvent(event)
        
        if self._is_animating and self._is_running:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Получаем размеры кнопки
            rect = self.rect()
            center_x = rect.width() / 2
            center_y = rect.height() / 2
            radius = min(rect.width(), rect.height()) / 2 - 5
            
            # Создаем перо для обводки
            pen = QPen()
            pen.setWidth(3)
            pen.setColor(QColor(theme.get_color('accent')))
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            # Рисуем дугу (обводку)
            start_angle = int(self._rotation_angle * 16)  # Qt использует 1/16 градуса
            span_angle = 270 * 16  # 270 градусов дуги
            
            painter.drawArc(
                int(center_x - radius),
                int(center_y - radius),
                int(radius * 2),
                int(radius * 2),
                start_angle,
                span_angle
            )
            
            painter.end()

