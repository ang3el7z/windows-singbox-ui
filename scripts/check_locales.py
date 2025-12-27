"""Скрипт для проверки используемых ключей локализации"""
import json
import re
from pathlib import Path
from typing import Set, Dict

def find_used_keys() -> Set[str]:
    """Находит все используемые ключи локализации в коде"""
    used_keys = set()
    
    # Ищем все .py файлы
    for py_file in Path('.').rglob('*.py'):
        if py_file.is_file() and 'check_locales.py' not in str(py_file):
            try:
                content = py_file.read_text(encoding='utf-8')
                # Ищем tr("key") или tr('key')
                matches = re.findall(r'tr\(["\']([^"\']+)["\']', content)
                used_keys.update(matches)
            except Exception:
                pass
    
    return used_keys

def load_locale_keys(locale_file: Path) -> Dict:
    """Загружает все ключи из файла локализации"""
    try:
        with open(locale_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def get_all_keys(data: Dict, prefix: str = "") -> Set[str]:
    """Рекурсивно получает все ключи из словаря"""
    keys = set()
    for key, value in data.items():
        if key.startswith('_'):
            continue  # Пропускаем служебные ключи
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys.update(get_all_keys(value, full_key))
        else:
            keys.add(full_key)
    return keys

def main():
    locales_dir = Path('locales')
    used_keys = find_used_keys()
    
    print(f"Найдено {len(used_keys)} используемых ключей")
    print("\nПроверка файлов локализации...\n")
    
    for locale_file in locales_dir.glob('*.json'):
        print(f"\n{locale_file.name}:")
        locale_data = load_locale_keys(locale_file)
        all_keys = get_all_keys(locale_data)
        
        unused_keys = all_keys - used_keys
        missing_keys = used_keys - all_keys
        
        if unused_keys:
            print(f"  Неиспользуемые ключи ({len(unused_keys)}):")
            for key in sorted(unused_keys):
                print(f"    - {key}")
        
        if missing_keys:
            print(f"  Отсутствующие ключи ({len(missing_keys)}):")
            for key in sorted(missing_keys):
                print(f"    - {key}")
        
        if not unused_keys and not missing_keys:
            print("  ✓ Все ключи используются")

if __name__ == '__main__':
    main()







