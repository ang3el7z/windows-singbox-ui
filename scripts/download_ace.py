"""Скрипт для скачивания Ace Editor"""
import urllib.request
import json
from pathlib import Path
import sys

# Путь к папке для Ace Editor
ACE_DIR = Path(__file__).parent.parent / "resources" / "web" / "ace"
ACE_DIR.mkdir(parents=True, exist_ok=True)

# URL для скачивания Ace Editor (используем unpkg CDN для стабильности)
ACE_VERSION = "1.23.4"
BASE_URL = f"https://cdn.jsdelivr.net/npm/ace-builds@{ACE_VERSION}/src-min-noconflict"

# Файлы для скачивания
FILES_TO_DOWNLOAD = [
    ("ace.js", "ace.js"),
    ("mode-json5.js", "mode-json5.js"),
    ("theme-monokai.js", "theme-monokai.js"),
    # Дополнительные полезные файлы
    ("worker-json.js", "worker-json.js"),  # Воркер для валидации JSON в реальном времени
    ("ext-language_tools.js", "ext-language_tools.js"),  # Автодополнение и подсказки
]

def download_file(url: str, filepath: Path):
    """Скачивает файл по URL"""
    print(f"Скачиваю {filepath.name}...")
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"[OK] {filepath.name} скачан успешно")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка при скачивании {filepath.name}: {e}")
        return False

def main():
    """Основная функция"""
    print("Скачивание Ace Editor...")
    print(f"Версия: {ACE_VERSION}")
    print(f"Папка: {ACE_DIR}")
    print()
    
    success_count = 0
    for filename, local_name in FILES_TO_DOWNLOAD:
        url = f"{BASE_URL}/{filename}"
        filepath = ACE_DIR / local_name
        
        if download_file(url, filepath):
            success_count += 1
        print()
    
    if success_count == len(FILES_TO_DOWNLOAD):
        print(f"[OK] Все файлы скачаны успешно в {ACE_DIR}")
        return 0
    else:
        print(f"[ERROR] Скачано только {success_count} из {len(FILES_TO_DOWNLOAD)} файлов")
        return 1

if __name__ == "__main__":
    sys.exit(main())

