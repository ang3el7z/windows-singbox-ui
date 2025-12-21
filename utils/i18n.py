"""Система локализации"""
import json
import sys
from pathlib import Path
from typing import Dict, Any
from config.paths import LOCALES_DIR


class Translator:
    """Класс для работы с локализацией"""
    
    def __init__(self, language: str = "ru"):
        self.language = language
        self.translations: Dict[str, Any] = {}
        self.load_translations()
    
    def load_translations(self):
        """Загружает переводы из файла"""
        # Сначала проверяем папку рядом с exe (для собранного приложения)
        if getattr(sys, 'frozen', False):
            # Запущено как exe - локали должны быть рядом с exe
            exe_path = Path(sys.executable)
            # Если exe в _internal, берем родительскую папку
            if exe_path.parent.name == '_internal':
                exe_dir = exe_path.parent.parent
            else:
                exe_dir = exe_path.parent
            # Сначала проверяем в корне папки проекта
            locale_file = exe_dir / "locales" / f"{self.language}.json"
            # Если нет, проверяем в _internal/locales
            if not locale_file.exists():
                locale_file = exe_dir / "_internal" / "locales" / f"{self.language}.json"
        else:
            # Запущено как скрипт - используем LOCALES_DIR
            locale_file = LOCALES_DIR / f"{self.language}.json"
        
        if locale_file.exists():
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                print(f"Локализация загружена: {locale_file}")
            except Exception as e:
                print(f"Ошибка загрузки локализации: {e}")
                # Загружаем русский как fallback
                if self.language != "ru":
                    self.load_fallback()
        else:
            print(f"Файл локализации не найден: {locale_file}")
            self.load_fallback()
    
    def load_fallback(self):
        """Загружает русский язык как fallback"""
        if getattr(sys, 'frozen', False):
            exe_path = Path(sys.executable)
            if exe_path.parent.name == '_internal':
                exe_dir = exe_path.parent.parent
            else:
                exe_dir = exe_path.parent
            locale_file = exe_dir / "locales" / "ru.json"
            if not locale_file.exists():
                locale_file = exe_dir / "_internal" / "locales" / "ru.json"
        else:
            locale_file = LOCALES_DIR / "ru.json"
        
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
        for file in LOCALES_DIR.glob("*.json"):
            lang = file.stem
            languages.append(lang)
        return sorted(languages)


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

