"""Извлекает коды символов из charmap файла qtawesome"""
import json
from pathlib import Path

# Находим charmap файл
try:
    import qtawesome
    qt_path = Path(qtawesome.__file__).parent
    fonts_path = qt_path / 'fonts'
    charmap_file = fonts_path / 'materialdesignicons5-webfont-charmap-5.9.55.json'
    
    if not charmap_file.exists():
        charmap_file = fonts_path / 'materialdesignicons6-webfont-charmap-6.9.96.json'
    
    data = json.loads(charmap_file.read_text())
    
    # Иконки, которые используются в проекте
    icons = {
        'plus': 'plus',
        'delete': 'delete',
        'rename-box': 'rename-box',
        'alert-circle': 'alert-circle',
        'download': 'download',
        'window-minimize': 'window-minimize',
        'close': 'close',
        'home': 'home',
        'account': 'account',
        'cog': 'cog',
    }
    
    print("MDI_ICONS = {")
    for icon_key, icon_name in icons.items():
        if icon_name in data:
            hex_code = data[icon_name]
            unicode_code = int(hex_code, 16)
            # Для Private Use Area используем \U
            if unicode_code >= 0xF0000:
                escape_code = f"\\U{unicode_code:08x}"
            else:
                escape_code = f"\\u{unicode_code:04x}"
            print(f'    "mdi.{icon_key}": "{escape_code}",  # {icon_name} (U+{unicode_code:06X})')
        else:
            print(f'    # "mdi.{icon_key}": NOT FOUND - {icon_name}')
    print("}")
    
    # Копируем шрифт
    font_file = fonts_path / 'materialdesignicons5-webfont-5.9.55.ttf'
    if not font_file.exists():
        font_file = fonts_path / 'materialdesignicons6-webfont-6.9.96.ttf'
    
    if font_file.exists():
        target_dir = Path('resources/fonts')
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / font_file.name
        import shutil
        shutil.copy2(font_file, target_file)
        print(f"\n[OK] Font copied: {target_file}")
    else:
        print("\n[ERROR] Font not found")
        
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()

