"""
Скрипт для извлечения кодов символов иконок из qtawesome.
Запустите этот скрипт, чтобы получить правильные коды для icon_helper.py
"""
import sys
from PyQt5.QtWidgets import QApplication
import qtawesome as qta

# Создаем QApplication для работы qtawesome
app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()

# Список используемых иконок
ICONS_TO_EXTRACT = [
    "mdi.plus",
    "mdi.delete",
    "mdi.rename-box",
    "mdi.alert-circle",
    "mdi.download",
    "mdi.window-minimize",
    "mdi.close",
    "mdi.home",
    "mdi.account",
    "mdi.cog",
]

print("Коды символов для Material Design Icons:\n")
print("MDI_ICONS = {")

for icon_name in ICONS_TO_EXTRACT:
    try:
        # Получаем информацию об иконке через внутренний API qtawesome
        from qtawesome.iconic_font import _resource
        if not _resource:
            qta._init()
        
        # Получаем код символа через charmap
        charmap = qta._charmap
        if not charmap:
            # Пробуем другой способ
            icon_obj = qta.icon(icon_name)
            # Получаем pixmap и извлекаем символ
            pixmap = icon_obj.pixmap(16, 16)
            # Пробуем получить через _resource
            try:
                font_data = qta._resource
                if font_data:
                    # Ищем в charmap
                    for key, value in charmap.items():
                        if key == icon_name:
                            char_code = value
                            break
                    else:
                        # Пробуем через iconic_font
                        from qtawesome.iconic_font import IconicFont
                        iconic = IconicFont('mdi', 'materialdesignicons5-webfont-5.9.55.ttf', charmap={})
                        char_code = iconic.charmap.get(icon_name.replace('mdi.', ''), '')
            except:
                char_code = ''
        else:
            char_code = charmap.get(icon_name, '')
        
        if char_code:
            # Получаем Unicode код
            unicode_code = ord(char_code) if isinstance(char_code, str) else char_code
            # Для Private Use Area (U+F0000+) используем формат \U
            if unicode_code >= 0xF0000:
                hex_code = f"\\U{unicode_code:08x}"
            else:
                hex_code = f"\\u{unicode_code:04x}"
            
            # Выводим в формате для копирования в MDI_ICONS
            icon_short = icon_name.split(".")[-1]
            print(f'    "{icon_name}": "{hex_code}",  # {icon_short} (U+{unicode_code:06X})')
        else:
            print(f'    # "{icon_name}": ERROR - не удалось найти код символа')
    except Exception as e:
        print(f'    # "{icon_name}": ERROR - {e}')

print("}")

# Также выводим информацию о шрифте
print("\n\nИнформация о шрифте:")
try:
    icon = qta.icon("mdi.plus")
    font = icon.font
    print(f"Font family: {font.family()}")
    print(f"Font style: {font.styleName()}")
except Exception as e:
    print(f"Ошибка получения информации о шрифте: {e}")

