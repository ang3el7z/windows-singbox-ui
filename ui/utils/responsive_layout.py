"""Утилиты для адаптивного layout"""
from typing import Optional
from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import QSize, Qt


class ResponsiveLayoutHelper:
    """Помощник для создания адаптивных layout'ов"""
    
    # Базовые размеры (для разрешения 420x780 - минимальный размер окна)
    BASE_WIDTH = 420
    BASE_HEIGHT = 780
    
    @staticmethod
    def setup_responsive_widget(widget: QWidget, min_width: int = None, min_height: int = None):
        """
        Настраивает виджет для адаптивного поведения
        
        Args:
            widget: Виджет для настройки
            min_width: Минимальная ширина (опционально)
            min_height: Минимальная высота (опционально)
        """
        if min_width:
            widget.setMinimumWidth(min_width)
        if min_height:
            widget.setMinimumHeight(min_height)
        
        # Используем Expanding для горизонтали и вертикали
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    @staticmethod
    def setup_responsive_button(widget: QWidget, min_size: int = None):
        """
        Настраивает кнопку для адаптивного поведения
        
        Args:
            widget: Кнопка для настройки
            min_size: Минимальный размер (опционально)
        """
        if min_size:
            widget.setMinimumSize(min_size, min_size)
        
        # Кнопки должны расширяться, но не слишком сильно
        widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
    
    @staticmethod
    def calculate_button_size(window_width: int, window_height: int) -> int:
        """
        Вычисляет размер кнопки на основе размера окна
        
        Args:
            window_width: Ширина окна
            window_height: Высота окна
            
        Returns:
            Размер кнопки в пикселях
        """
        # Базовый размер кнопки для минимального окна
        base_button_size = 200
        
        # Используем минимальную сторону для масштабирования
        min_dimension = min(window_width, window_height)
        
        # Масштабируем относительно базового размера
        # Для окна 420x780 кнопка будет 200px
        # Для большего окна кнопка будет пропорционально больше
        scale = min_dimension / ResponsiveLayoutHelper.BASE_HEIGHT
        
        # Ограничиваем масштаб (не меньше 0.8, не больше 1.5)
        scale = max(0.8, min(1.5, scale))
        
        button_size = int(base_button_size * scale)
        
        # Ограничиваем размер кнопки (не меньше 160px, не больше 300px)
        return max(160, min(300, button_size))

