"""Система локализации"""
import json
import sys
from pathlib import Path
from typing import Dict, Any
from config.paths import LOCALES_DIR

# Импортируем log_to_file если доступен
try:
    from utils.logger import log_to_file
except ImportError:
    # Если модуль еще не загружен, используем простой print
    def log_to_file(msg: str, log_file=None):
        print(msg)


class Translator:
    """Класс для работы с локализацией"""
    
    def __init__(self, language: str = "ru"):
        self.language = language
        self.translations: Dict[str, Any] = {}
        self.load_translations()
    
    def load_translations(self):
        """Загружает переводы из файла"""
        # Используем LOCALES_DIR из config.paths (теперь это data/locales)
        locale_file = LOCALES_DIR / f"{self.language}.json"
        
        # Для обратной совместимости проверяем старые пути
        if not locale_file.exists() and getattr(sys, 'frozen', False):
            exe_path = Path(sys.executable)
            if exe_path.parent.name == '_internal':
                exe_dir = exe_path.parent.parent
            else:
                exe_dir = exe_path.parent
            # Проверяем старый путь рядом с exe
            old_locale_file = exe_dir / "locales" / f"{self.language}.json"
            if old_locale_file.exists():
                locale_file = old_locale_file
        
        if locale_file.exists():
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                log_to_file(f"Локализация загружена: {locale_file}")
            except Exception as e:
                log_to_file(f"Ошибка загрузки локализации: {e}")
                # Загружаем русский как fallback
                if self.language != "ru":
                    self.load_fallback()
        else:
            log_to_file(f"Файл локализации не найден: {locale_file}")
            self.load_fallback()
    
    def load_fallback(self):
        """Загружает русский язык как fallback"""
        locale_file = LOCALES_DIR / "ru.json"
        
        # Для обратной совместимости проверяем старые пути
        if not locale_file.exists() and getattr(sys, 'frozen', False):
            exe_path = Path(sys.executable)
            if exe_path.parent.name == '_internal':
                exe_dir = exe_path.parent.parent
            else:
                exe_dir = exe_path.parent
            old_locale_file = exe_dir / "locales" / "ru.json"
            if old_locale_file.exists():
                locale_file = old_locale_file
        
        if locale_file.exists():
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            except Exception:
                self.translations = {}
    
    def set_language(self, language: str):
        """Устанавливает язык"""
        self.language = language
        self.load_translations()
    
    def tr(self, key: str, **kwargs) -> str:
        """
        Получает перевод по ключу
        
        Args:
            key: Ключ в формате "section.key" (например, "home.version")
            **kwargs: Параметры для форматирования строки
        
        Returns:
            Переведенная строка
        """
        keys = key.split('.')
        value = self.translations
        
        try:
            for k in keys:
                value = value[k]
            
            if isinstance(value, str):
                return value.format(**kwargs) if kwargs else value
            return str(value)
        except (KeyError, TypeError):
            # Если ключ не найден, возвращаем сам ключ
            return key
    
    def get_available_languages(self) -> list:
        """Возвращает список доступных языков"""
        languages = []
        # Используем LOCALES_DIR из config.paths (теперь это data/locales)
        locales_path = LOCALES_DIR
        
        # Для обратной совместимости проверяем старые пути
        if not locales_path.exists() and getattr(sys, 'frozen', False):
            exe_path = Path(sys.executable)
            if exe_path.parent.name == '_internal':
                exe_dir = exe_path.parent.parent
            else:
                exe_dir = exe_path.parent
            old_locales_path = exe_dir / "locales"
            if old_locales_path.exists():
                locales_path = old_locales_path
        
        # Ищем все json файлы в папке locales
        if locales_path.exists():
            for file in locales_path.glob("*.json"):
                lang = file.stem
                languages.append(lang)
        
        return sorted(languages) if languages else ["en"]  # Fallback на английский


# Глобальный экземпляр переводчика
_translator = Translator()


def tr(key: str, **kwargs) -> str:
    """Глобальная функция для перевода"""
    return _translator.tr(key, **kwargs)


def set_language(language: str):
    """Устанавливает язык"""
    _translator.set_language(language)


def get_translator() -> Translator:
    """Возвращает экземпляр переводчика"""
    return _translator


def get_available_languages() -> list:
    """Возвращает список доступных языков из папки locales"""
    return _translator.get_available_languages()


def get_language_name(lang_code: str) -> str:
    """Возвращает название языка по коду"""
    names = {
        "en": "English",
        "ru": "Русский",
        "es": "Español",
        "fr": "Français",
        "de": "Deutsch",
        "zh": "中文",
        "ja": "日本語",
        "ko": "한국어",
    }
    return names.get(lang_code, lang_code.upper())

