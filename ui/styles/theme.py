"""Класс темы приложения"""
from typing import Dict, Optional, Any
from .constants import FONTS, SIZES, TRANSITIONS
from utils.theme_manager import get_theme_manager


class Theme:
    """Централизованное управление темой приложения"""
    
    def __init__(self) -> None:
        """Инициализация темы с копированием констант"""
        self.theme_manager = get_theme_manager()
        self.fonts: Dict[str, Any] = FONTS.copy()
        self.sizes: Dict[str, int] = SIZES.copy()
        self.transitions: Dict[str, str] = TRANSITIONS.copy()
    
    def get_color(self, name: str) -> str:
        """
        Получить цвет по имени
        
        Args:
            name: Имя цвета из темы
            
        Returns:
            Цвет в формате hex или rgba
        """
        return self.theme_manager.get_color(name)
    
    def get_font(self, name: str) -> Optional[Any]:
        """
        Получить параметр шрифта по имени
        
        Args:
            name: Имя параметра шрифта
            
        Returns:
            Значение параметра или None
        """
        return self.fonts.get(name)
    
    def get_size(self, name: str) -> int:
        """
        Получить размер по имени
        
        Args:
            name: Имя размера
            
        Returns:
            Размер в пикселях
        """
        return self.sizes.get(name, 0)
    
    def get_transition(self, name: str) -> str:
        """
        Получить время перехода по имени
        
        Args:
            name: Имя перехода (fast, medium, slow)
            
        Returns:
            Время перехода в миллисекундах
        """
        return self.transitions.get(name, '250ms')
    
    def reload_theme(self):
        """Перезагружает тему из менеджера"""
        self.theme_manager = get_theme_manager()


# Глобальный экземпляр темы
theme = Theme()

