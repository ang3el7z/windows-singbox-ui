"""Менеджер профилей"""
import json
import requests
from urllib.parse import urlparse
from typing import Optional, Dict, Any
from config.paths import PROFILE_FILE, CONFIG_FILE

# Импортируем log_to_file если доступен
try:
    from utils.logger import log_to_file
except ImportError:
    # Если модуль еще не загружен, используем простой print
    def log_to_file(msg: str, log_file=None):
        print(msg)


class SubscriptionManager:
    """Управление профилями (подписки и готовые конфиги)"""
    
    PROFILE_TYPE_SUBSCRIPTION = "subscription"
    PROFILE_TYPE_CONFIG = "config"
    
    def __init__(self):
        self.data = {"profiles": []}
        self.load_or_init()
    
    def load_or_init(self):
        """Загружает профили из файла или создает пустой список"""
        if PROFILE_FILE.exists():
            try:
                content = PROFILE_FILE.read_text(encoding="utf-8")
                if content.strip():  # Проверяем что файл не пустой
                    self.data = json.loads(content)
                    # Миграция со старого формата (если есть)
                    if "subscriptions" in self.data and "profiles" not in self.data:
                        # Конвертируем старые подписки в новый формат
                        old_subs = self.data.get("subscriptions", [])
                        self.data["profiles"] = [
                            {
                                "name": sub.get("name", "no-name"),
                                "type": self.PROFILE_TYPE_SUBSCRIPTION,
                                "url": sub.get("url", "")
                            }
                            for sub in old_subs
                        ]
                        del self.data["subscriptions"]
                        self.save()
                    return
            except Exception as e:
                log_to_file(f"Ошибка загрузки профилей: {e}")
        # Если файла нет или он пустой - создаем пустой список профилей
        self.data = {"profiles": []}
        self.save()
    
    def save(self):
        """Сохраняет профили в файл"""
        # Убеждаемся что папка существует
        PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
        PROFILE_FILE.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        log_to_file(f"Профили сохранены в: {PROFILE_FILE}")
    
    def list_names(self):
        """Возвращает список названий профилей"""
        return [p.get("name", "no-name") for p in self.data.get("profiles", [])]
    
    def get(self, index: int) -> Optional[Dict[str, Any]]:
        """Получить профиль по индексу"""
        profiles = self.data.get("profiles", [])
        if 0 <= index < len(profiles):
            return profiles[index]
        return None
    
    def get_profile_type(self, index: int) -> Optional[str]:
        """Получить тип профиля по индексу"""
        profile = self.get(index)
        if profile:
            return profile.get("type", self.PROFILE_TYPE_SUBSCRIPTION)
        return None
    
    def is_subscription(self, index: int) -> bool:
        """Проверить, является ли профиль подпиской"""
        return self.get_profile_type(index) == self.PROFILE_TYPE_SUBSCRIPTION
    
    def add_subscription(self, name: str, url: str):
        """Добавить новую подписку"""
        self.data.setdefault("profiles", []).append({
            "name": name,
            "type": self.PROFILE_TYPE_SUBSCRIPTION,
            "url": url
        })
        self.save()
    
    def add_config(self, name: str, config_data: Dict[str, Any]):
        """Добавить готовый конфиг"""
        self.data.setdefault("profiles", []).append({
            "name": name,
            "type": self.PROFILE_TYPE_CONFIG,
            "config": config_data
        })
        self.save()
    
    def add(self, name: str, url: str = None, config: Dict[str, Any] = None):
        """Добавить профиль (универсальный метод для обратной совместимости)"""
        if url:
            self.add_subscription(name, url)
        elif config:
            self.add_config(name, config)
        else:
            raise ValueError("Необходимо указать либо url, либо config")
    
    def remove(self, index: int):
        """Удалить профиль по индексу"""
        profiles = self.data.get("profiles", [])
        if 0 <= index < len(profiles):
            profiles.pop(index)
            self.save()
    
    def update_profile(self, index: int, name: str = None, profile_type: str = None, url: str = None, config: Dict[str, Any] = None):
        """Обновить профиль по индексу"""
        profile = self.get(index)
        if not profile:
            return False
        
        if name is not None:
            profile["name"] = name
        
        if profile_type is not None:
            profile["type"] = profile_type
            # При смене типа очищаем неактуальные поля
            if profile_type == self.PROFILE_TYPE_SUBSCRIPTION:
                profile.pop("config", None)
                if url is not None:
                    profile["url"] = url
            elif profile_type == self.PROFILE_TYPE_CONFIG:
                profile.pop("url", None)
                if config is not None:
                    profile["config"] = config
        else:
            # Если тип не меняется, обновляем соответствующие поля
            if profile.get("type") == self.PROFILE_TYPE_SUBSCRIPTION and url is not None:
                profile["url"] = url
            elif profile.get("type") == self.PROFILE_TYPE_CONFIG and config is not None:
                profile["config"] = config
        
        self.save()
        return True
    
    def download_config(self, index: int) -> bool:
        """Скачать конфиг из подписки (только для типа subscription)"""
        profile = self.get(index)
        if not profile:
            return False
        
        profile_type = profile.get("type", self.PROFILE_TYPE_SUBSCRIPTION)
        if profile_type != self.PROFILE_TYPE_SUBSCRIPTION:
            log_to_file(f"download_config: профиль не является подпиской (тип: {profile_type})")
            return False
        
        url = profile.get("url")
        
        # Проверяем и нормализуем URL
        if not url:
            return False
        
        # Убеждаемся что URL абсолютный
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            log_to_file(f"download_config error: URL не является абсолютным: {url}")
            return False
        
        try:
            # Убеждаемся что папка существует
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            
            # Проверяем что это валидный JSON и форматируем его
            try:
                content = r.content
                # Пробуем декодировать как текст для проверки JSON
                text_content = content.decode('utf-8')
                # Парсим JSON для проверки валидности
                config_data = json.loads(text_content)
                # Форматируем JSON с отступами для красивого отображения
                formatted_content = json.dumps(config_data, ensure_ascii=False, indent=2)
                # Сохраняем отформатированный конфиг
                CONFIG_FILE.write_text(formatted_content, encoding='utf-8')
                log_to_file(f"Конфиг сохранен в: {CONFIG_FILE}")
                log_to_file(f"Размер файла: {CONFIG_FILE.stat().st_size} байт")
                return True
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                log_to_file(f"Ошибка валидации конфига: {e}")
                # Если JSON невалидный, сохраняем как есть (может быть это не JSON)
                CONFIG_FILE.write_bytes(content)
                log_to_file(f"Конфиг сохранен в: {CONFIG_FILE} (без форматирования)")
                log_to_file(f"Размер файла: {CONFIG_FILE.stat().st_size} байт")
                return True
        except Exception as e:
            log_to_file(f"download_config error: {e}")
            return False
    
    def apply_config(self, index: int) -> bool:
        """Применить конфиг профиля (для готовых конфигов)"""
        profile = self.get(index)
        if not profile:
            return False
        
        profile_type = profile.get("type", self.PROFILE_TYPE_SUBSCRIPTION)
        if profile_type == self.PROFILE_TYPE_CONFIG:
            # Для готового конфига - сохраняем его напрямую
            config_data = profile.get("config")
            if not config_data:
                log_to_file("apply_config: конфиг не найден в профиле")
                return False
            
            try:
                CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
                formatted_content = json.dumps(config_data, ensure_ascii=False, indent=2)
                CONFIG_FILE.write_text(formatted_content, encoding='utf-8')
                log_to_file(f"Конфиг применен из профиля: {CONFIG_FILE}")
                return True
            except Exception as e:
                log_to_file(f"apply_config error: {e}")
                return False
        elif profile_type == self.PROFILE_TYPE_SUBSCRIPTION:
            # Для подписки - скачиваем конфиг
            return self.download_config(index)
        else:
            log_to_file(f"apply_config: неизвестный тип профиля: {profile_type}")
            return False
