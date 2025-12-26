"""Вариации кнопок - используют дизайн-систему"""
from typing import Optional
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap, QRadialGradient, QBrush
from utils.icon_helper import icon
from ui.styles import StyleSheet, theme


class Button(QPushButton):
    """Универсальная кнопка с применением стилей из дизайн-системы"""
    
    def __init__(
        self,
        text: str = "",
        parent: Optional[QWidget] = None,
        variant: str = "default",
        size: str = "medium",
        full_width: bool = False
    ):
        """
        Инициализация кнопки
        
        Args:
            text: Текст кнопки
            parent: Родительский виджет
            variant: Вариант кнопки (default, primary, secondary, danger)
            size: Размер (small, medium, large)
            full_width: Занимать всю ширину
        """
        super().__init__(text, parent)
        self._variant = variant
        self._size = size
        self._full_width = full_width
        self.setCursor(Qt.PointingHandCursor)
        self.apply_style()
    
    def apply_style(self):
        """Применяет стиль кнопки из дизайн-системы"""
        self.setStyleSheet(StyleSheet.button(
            variant=self._variant,
            size=self._size,
            full_width=self._full_width
        ))
    
    def set_variant(self, variant: str):
        """Устанавливает вариант кнопки"""
        self._variant = variant
        self.apply_style()
    
    def set_size(self, size: str):
        """Устанавливает размер кнопки"""
        self._size = size
        self.apply_style()


class NavButton(QPushButton):
    """Кнопка навигации с иконкой и текстом"""
    
    def __init__(self, text: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name  # Сохраняем имя иконки
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # Контейнер для содержимого
        container = QWidget()
        container.setStyleSheet("background-color: transparent; border: none;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(10)
        
        # Иконка
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        icon_color = theme.get_color('text_secondary')
        self.icon_label.setPixmap(icon(icon_name, color=icon_color).pixmap(36, 36))
        self.icon_label.setStyleSheet("background-color: transparent; border: none;")
        
        # Текст
        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet(StyleSheet.label(variant="secondary", size="medium"))
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        container.setLayout(layout)
        
        # Основной layout кнопки
        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addWidget(container)
        
        # Подключаем изменение состояния
        self.toggled.connect(self._update_style)
    
    def _update_style(self, checked: bool):
        """Обновляет стиль при изменении состояния"""
        color = theme.get_color('accent') if checked else theme.get_color('text_secondary')
        self.icon_label.setPixmap(
            icon(self.icon_name, color=color).pixmap(36, 36)
        )
        
        weight = theme.get_font('weight_semibold') if checked else theme.get_font('weight_medium')
        self.text_label.setStyleSheet(f"""
            font-size: {theme.get_font('size_medium')}px;
            font-weight: {weight};
            background-color: transparent;
            border: none;
            color: {color};
        """)
    
    def setIconName(self, icon_name: str):
        """Устанавливает имя иконки"""
        self.icon_name = icon_name
        self._update_style(self.isChecked())
    
    def setText(self, text: str):
        """Устанавливает текст"""
        self.text_label.setText(text)


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
