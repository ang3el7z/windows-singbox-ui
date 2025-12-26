"""Менеджер тем приложения"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from config.paths import THEMES_DIR


class ThemeFileNotFoundError(Exception):
    """Исключение, возникающее при отсутствии файла темы"""
    pass

# Импортируем log_to_file если доступен
try:
    from utils.logger import log_to_file
except ImportError:
    def log_to_file(msg: str, log_file=None):
        print(msg)


class ThemeManager:
    """Класс для работы с темами приложения"""
    
    def __init__(self, theme_name: str = "dark"):
        self.theme_name = theme_name
        self.themes: Dict[str, Any] = {}
        self.current_theme: Dict[str, Any] = {}
        self.load_themes()
        self.set_theme(theme_name)
    
    def load_themes(self):
        """Загружает все темы из папки themes"""
        themes_dir = THEMES_DIR
        
        if not themes_dir.exists():
            log_to_file(f"Папка тем не найдена: {themes_dir}")
            return
        
        for theme_file in themes_dir.glob("*.json"):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                    theme_id = theme_file.stem
                    self.themes[theme_id] = theme_data
                    log_to_file(f"Тема загружена: {theme_id}")
            except Exception as e:
                log_to_file(f"Ошибка загрузки темы {theme_file}: {e}")
    
    def set_theme(self, theme_name: str):
        """Устанавливает тему"""
        if theme_name in self.themes:
            self.theme_name = theme_name
            self.current_theme = self.themes[theme_name]
            log_to_file(f"Тема установлена: {theme_name}")
        else:
            log_to_file(f"Тема не найдена: {theme_name}, пробуем использовать dark")
            if "dark" in self.themes:
                self.theme_name = "dark"
                self.current_theme = self.themes["dark"]
            else:
                raise ThemeFileNotFoundError(
                    f"Файл темы не найден. Запрошенная тема '{theme_name}' не существует, "
                    f"и резервная тема 'dark' также отсутствует. "
                    f"Проверьте наличие файлов тем в директории: {THEMES_DIR}"
                )
    
    def get_color(self, name: str) -> str:
        """
        Получает цвет по имени
        
        Args:
            name: Имя цвета
            
        Returns:
            Цвет в формате hex или rgba
        """
        colors = self.current_theme.get("colors", {})
        return colors.get(name, "#000000")
    
    def get_available_themes(self) -> List[Dict[str, Any]]:
        """Возвращает список доступных тем (только активные)"""
        themes = []
        for theme_id, theme_data in self.themes.items():
            if theme_data.get("isActive", True):
                themes.append({
                    "id": theme_id,
                    "name": theme_data.get("_theme_name", theme_id),
                    "name_ru": theme_data.get("_theme_name_ru", theme_id)
                })
        return sorted(themes, key=lambda x: x["id"])
    
    def get_theme_name(self, theme_id: str, language: str = "en") -> str:
        """Возвращает название темы по ID"""
        if theme_id in self.themes:
            if language == "ru":
                return self.themes[theme_id].get("_theme_name_ru", self.themes[theme_id].get("_theme_name", theme_id))
            else:
                return self.themes[theme_id].get("_theme_name", theme_id)
        return theme_id


# Глобальный экземпляр менеджера тем
_theme_manager = ThemeManager()


def get_theme_manager() -> ThemeManager:
    """Возвращает экземпляр менеджера тем"""
    return _theme_manager


def set_theme(theme_name: str):
    """Устанавливает тему"""
    _theme_manager.set_theme(theme_name)


def get_color(name: str) -> str:
    """Получает цвет текущей темы по имени"""
    return _theme_manager.get_color(name)


def get_available_themes() -> List[Dict[str, Any]]:
    """Возвращает список доступных тем"""
    return _theme_manager.get_available_themes()


def get_theme_name(theme_id: str, language: str = "en") -> str:
    """Возвращает название темы"""
    return _theme_manager.get_theme_name(theme_id, language)

