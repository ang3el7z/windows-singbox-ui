"""Менеджер подписок"""
import json
import requests
from config.paths import SUB_FILE, CONFIG_FILE


class SubscriptionManager:
    """Управление подписками"""
    
    def __init__(self):
        self.data = {"subscriptions": []}
        self.load_or_init()
    
    def load_or_init(self):
        """Загружает подписки из файла или создает пустой список"""
        if SUB_FILE.exists():
            try:
                content = SUB_FILE.read_text(encoding="utf-8")
                if content.strip():  # Проверяем что файл не пустой
                    self.data = json.loads(content)
                    return
            except Exception as e:
                print(f"Ошибка загрузки подписок: {e}")
        # Если файла нет или он пустой - создаем пустой список подписок
        self.data = {"subscriptions": []}
        self.save()
    
    def save(self):
        """Сохраняет подписки в файл"""
        # Убеждаемся что папка существует
        SUB_FILE.parent.mkdir(parents=True, exist_ok=True)
        SUB_FILE.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"Подписки сохранены в: {SUB_FILE}")
    
    def list_names(self):
        """Возвращает список названий подписок"""
        return [s.get("name", "no-name") for s in self.data.get("subscriptions", [])]
    
    def get(self, index: int):
        """Получить подписку по индексу"""
        subs = self.data.get("subscriptions", [])
        if 0 <= index < len(subs):
            return subs[index]
        return None
    
    def add(self, name: str, url: str):
        """Добавить новую подписку"""
        self.data.setdefault("subscriptions", []).append({"name": name, "url": url})
        self.save()
    
    def remove(self, index: int):
        """Удалить подписку по индексу"""
        subs = self.data.get("subscriptions", [])
        if 0 <= index < len(subs):
            subs.pop(index)
            self.save()
    
    def download_config(self, index: int) -> bool:
        """Скачать конфиг из подписки"""
        sub = self.get(index)
        if not sub:
            return False
        url = sub["url"]
        try:
            # Убеждаемся что папка существует
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            
            # Проверяем что это валидный JSON
            try:
                content = r.content
                # Пробуем декодировать как текст для проверки JSON
                text_content = content.decode('utf-8')
                import json
                json.loads(text_content)  # Проверка валидности JSON
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                print(f"Ошибка валидации конфига: {e}")
                # Все равно сохраняем, может быть это не JSON
                pass
            
            # Сохраняем конфиг
            CONFIG_FILE.write_bytes(content)
            print(f"Конфиг сохранен в: {CONFIG_FILE}")
            print(f"Размер файла: {CONFIG_FILE.stat().st_size} байт")
            return True
        except Exception as e:
            print(f"download_config error: {e}")
            return False

