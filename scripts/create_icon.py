"""Скрипт для создания иконки из SVG"""
try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    # Создаем изображение 256x256 с черным фоном
    size = 256
    img = Image.new('RGB', (size, size), color='#000000')
    draw = ImageDraw.Draw(img)
    
    # Пытаемся использовать системный шрифт
    try:
        # Windows
        font_path = "C:/Windows/Fonts/arialbd.ttf"
        if not os.path.exists(font_path):
            font_path = "C:/Windows/Fonts/calibrib.ttf"
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 180)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Рисуем букву S
    text = "S"
    # Получаем размеры текста
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Центрируем текст
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 20  # Немного выше центра
    
    draw.text((x, y), text, fill='#00f5d4', font=font)
    
    # Сохраняем как ICO с несколькими размерами (Windows требует все размеры)
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = []
    for s in sizes:
        resized = img.resize(s, Image.Resampling.LANCZOS)
        images.append(resized)
    
    # Сохраняем как ICO с правильными размерами
    # Windows требует все размеры в одном файле
    from PIL import Image
    # Создаем ICO файл с несколькими размерами
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icon_images = []
    for s in icon_sizes:
        resized = img.resize(s, Image.Resampling.LANCZOS)
        icon_images.append(resized)
    
    # Определяем путь для сохранения (в папку icons/)
    from pathlib import Path
    script_dir = Path(__file__).parent.parent
    icons_dir = script_dir / 'icons'
    icons_dir.mkdir(exist_ok=True)
    
    # Сохраняем ICO с указанием всех размеров
    icon_path = icons_dir / 'icon.ico'
    icon_images[0].save(str(icon_path), format='ICO', sizes=[(img.width, img.height) for img in icon_images])
    print(f"Иконка создана: {icon_path}")
    print(f"Размеры в иконке: {[(img.width, img.height) for img in icon_images]}")
    
    # Также сохраняем PNG для использования в приложении
    png_path = icons_dir / 'icon.png'
    img.save(str(png_path))
    print(f"PNG иконка создана: {png_path}")
    
except ImportError:
    print("Pillow не установлен. Устанавливаю...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    print("Перезапустите скрипт")
except Exception as e:
    print(f"Ошибка: {e}")

