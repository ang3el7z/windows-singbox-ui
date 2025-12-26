"""Утилиты для анимаций"""
from typing import Optional
from PyQt5.QtWidgets import QWidget, QStackedWidget
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, Qt, QAbstractAnimation, QPoint


class PageTransitionAnimation:
    """Анимация перехода между страницами"""
    
    @staticmethod
    def slide_transition(stack: QStackedWidget, new_index: int, duration: int = 300):
        """
        Анимация слайда при переходе между страницами
        
        Args:
            stack: QStackedWidget со страницами
            new_index: Индекс новой страницы
            duration: Длительность анимации в миллисекундах
        """
        if not stack or new_index < 0 or new_index >= stack.count():
            stack.setCurrentIndex(new_index)
            return
        
        old_index = stack.currentIndex()
        if old_index == new_index:
            return
        
        # Получаем виджеты
        old_widget = stack.widget(old_index)
        new_widget = stack.widget(new_index)
        
        if not old_widget or not new_widget:
            stack.setCurrentIndex(new_index)
            return
        
        # Определяем направление анимации
        direction = 1 if new_index > old_index else -1
        
        # Показываем новую страницу
        stack.setCurrentIndex(new_index)
        
        # Создаем анимации
        old_animation = QPropertyAnimation(old_widget, b"pos")
        new_animation = QPropertyAnimation(new_widget, b"pos")
        
        # Начальные и конечные позиции
        width = stack.width()
        
        old_animation.setDuration(duration)
        old_animation.setStartValue(old_widget.pos())
        old_animation.setEndValue(old_widget.pos() - QPoint(direction * width, 0))
        old_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        new_widget.move(direction * width, 0)
        new_animation.setDuration(duration)
        new_animation.setStartValue(new_widget.pos())
        new_animation.setEndValue(QPoint(0, 0))
        new_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Запускаем анимации
        old_animation.start(QAbstractAnimation.DeleteWhenStopped)
        new_animation.start(QAbstractAnimation.DeleteWhenStopped)


class FadeAnimation:
    """Анимация затухания"""
    
    @staticmethod
    def fade_in(widget: QWidget, duration: int = 200):
        """
        Анимация появления виджета
        
        Args:
            widget: Виджет для анимации
            duration: Длительность анимации в миллисекундах
        """
        if not widget:
            return
        
        widget.setWindowOpacity(0.0)
        widget.show()
        
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start(QAbstractAnimation.DeleteWhenStopped)
    
    @staticmethod
    def fade_out(widget: QWidget, duration: int = 200):
        """
        Анимация исчезновения виджета
        
        Args:
            widget: Виджет для анимации
            duration: Длительность анимации в миллисекундах
        """
        if not widget:
            return
        
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.finished.connect(widget.hide)
        animation.start(QAbstractAnimation.DeleteWhenStopped)

