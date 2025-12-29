"""Менеджер настроек приложения"""
import json
from config.paths import SETTINGS_FILE

# Импортируем log_to_file если доступен
try:
    from utils.logger import log_to_file
except ImportError:
    # Если модуль еще не загружен, используем простой print
    def log_to_file(msg: str, log_file=None):
        print(msg)


class SettingsManager:
    """Управление настройками приложения"""
    
    def __init__(self):
        self.data = {
            "auto_update_minutes": 90,
            "start_with_windows": False,
            "auto_start_singbox": False,  # Автозапуск sing-box при запуске приложения
            "minimize_to_tray": True,  # Сворачивать в трей (по умолчанию включено)
            "language": "",  # Пустая строка означает, что язык не выбран
            "current_sub_index": -1,  # Индекс выбранного профиля (-1 означает, что профиль не выбран)
        }
        self.load()
    
    def load(self):
        """Загружает настройки из файла"""
        if SETTINGS_FILE.exists():
            try:
                self.data.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
            except Exception:
                pass
    
    def save(self):
        """Сохраняет настройки в файл"""
        # Убеждаемся что папка существует
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        log_to_file(f"Настройки сохранены в: {SETTINGS_FILE}")
    
    def get(self, key: str, default=None):
        """Получить значение настройки"""
        return self.data.get(key, default)
    
    def set(self, key: str, value):
        """Установить значение настройки"""
        self.data[key] = value
        self.save()

