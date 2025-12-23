"""Утилиты для адаптивного дизайна"""
from typing import Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QSize


class ResponsiveHelper:
    """Помощник для адаптивного дизайна"""
    
    # Базовые размеры (для разрешения 420x780 - минимальный размер окна)
    BASE_WIDTH = 420
    BASE_HEIGHT = 780
    
    @staticmethod
    def get_scale_factor(widget: QWidget) -> float:
        """
        Получить коэффициент масштабирования на основе размера виджета
        
        Args:
            widget: Виджет для расчета масштаба
            
        Returns:
            Коэффициент масштабирования (1.0 для базового размера)
        """
        if not widget:
            return 1.0
        
        size = widget.size()
        if size.width() == 0 or size.height() == 0:
            return 1.0
        
        # Используем минимальную сторону для масштабирования
        width_scale = size.width() / ResponsiveHelper.BASE_WIDTH
        height_scale = size.height() / ResponsiveHelper.BASE_HEIGHT
        
        # Используем среднее значение для более плавного масштабирования
        scale = (width_scale + height_scale) / 2.0
        
        # Ограничиваем масштаб (не меньше 0.8, не больше 1.5)
        scale = max(0.8, min(1.5, scale))
        
        return scale
    
    @staticmethod
    def scale_size(base_size: int, scale: float) -> int:
        """
        Масштабировать размер
        
        Args:
            base_size: Базовый размер
            scale: Коэффициент масштабирования
            
        Returns:
            Масштабированный размер
        """
        return int(base_size * scale)
    
    @staticmethod
    def scale_font_size(base_size: int, scale: float) -> int:
        """
        Масштабировать размер шрифта
        
        Args:
            base_size: Базовый размер шрифта
            scale: Коэффициент масштабирования
            
        Returns:
            Масштабированный размер шрифта
        """
        return max(10, int(base_size * scale))  # Минимум 10px


def get_scale_factor(widget: QWidget) -> float:
    """Получить коэффициент масштабирования"""
    return ResponsiveHelper.get_scale_factor(widget)


def scale_size(base_size: int, scale: float) -> int:
    """Масштабировать размер"""
    return ResponsiveHelper.scale_size(base_size, scale)


def scale_font_size(base_size: int, scale: float) -> int:
    """Масштабировать размер шрифта"""
    return ResponsiveHelper.scale_font_size(base_size, scale)

