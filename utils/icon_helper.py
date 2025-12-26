"""
Простой хелпер для работы с иконками из встроенных шрифтов.
Заменяет qtawesome, работает через Qt Resource System (QRC).
"""
from typing import Optional
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap, QPainter, QIcon, QColor
from PyQt5.QtCore import Qt

# Коды символов Material Design Icons (mdi)
# Извлечены из qtawesome charmap файла
MDI_ICONS = {
    "mdi.plus": "\U000f0415",  # plus (U+0F0415)
    "mdi.delete": "\U000f01b4",  # delete (U+0F01B4)
    "mdi.rename-box": "\U000f0455",  # rename-box (U+0F0455)
    "mdi.alert-circle": "\U000f0028",  # alert-circle (U+0F0028)
    "mdi.download": "\U000f01da",  # download (U+0F01DA)
    "mdi.window-minimize": "\U000f05b0",  # window-minimize (U+0F05B0)
    "mdi.close": "\U000f0156",  # close (U+0F0156)
    "mdi.home": "\U000f02dc",  # home (U+0F02DC)
    "mdi.account": "\U000f0004",  # account (U+0F0004)
    "mdi.cog": "\U000f0493",  # cog (U+0F0493)
}

# Имя шрифта Material Design Icons
MDI_FONT_NAME = "Material Design Icons"


class IconHelper:
    """Хелпер для работы с иконками из встроенных шрифтов"""
    
    _font_loaded = False
    _font_id = -1
    
    @classmethod
    def _ensure_font_loaded(cls):
        """Загружает шрифт из QRC, если еще не загружен"""
        if cls._font_loaded:
            return
        
        # Пытаемся загрузить шрифт из QRC
        font_paths = [
            ":/fonts/materialdesignicons5-webfont-5.9.55.ttf",
            ":/fonts/materialdesignicons6-webfont-6.9.96.ttf",
            ":/fonts/materialdesignicons-webfont.ttf",
        ]
        
        for font_path in font_paths:
            cls._font_id = QFontDatabase.addApplicationFont(font_path)
            if cls._font_id != -1:
                # Получаем имя шрифта из загруженного шрифта
                families = QFontDatabase.applicationFontFamilies(cls._font_id)
                if families:
                    # Обновляем имя шрифта
                    global MDI_FONT_NAME
                    MDI_FONT_NAME = families[0]
                break
        
        cls._font_loaded = True
        
        if cls._font_id == -1:
            # Если шрифт не загружен, это не критично - просто не будет иконок
            pass
    
    @classmethod
    def icon(cls, icon_name: str, color: Optional[str] = None, size: int = 16) -> 'IconObject':
        """
        Создает иконку из шрифта
        
        Args:
            icon_name: Имя иконки (например, "mdi.plus")
            color: Цвет иконки в формате "#RRGGBB" или "rgb(r,g,b)"
            size: Размер иконки в пикселях
            
        Returns:
            Объект IconObject с методами pixmap() и icon()
        """
        cls._ensure_font_loaded()
        
        # Получаем код символа
        char_code = MDI_ICONS.get(icon_name, "")
        if not char_code:
            # Если иконка не найдена, возвращаем пустую иконку
            return IconObject("", size, color)
        
        return IconObject(char_code, size, color)


class IconObject:
    """Объект иконки с методами для получения QPixmap и QIcon"""
    
    def __init__(self, char_code: str, size: int, color: Optional[str] = None):
        self.char_code = char_code
        self.size = size
        self.color = color or "#000000"
    
    def pixmap(self, width: Optional[int] = None, height: Optional[int] = None) -> QPixmap:
        """
        Создает QPixmap с иконкой
        
        Args:
            width: Ширина (если не указана, используется self.size)
            height: Высота (если не указана, используется self.size)
            
        Returns:
            QPixmap с иконкой
        """
        if not self.char_code:
            # Возвращаем пустой pixmap
            w = width or self.size
            h = height or self.size
            pixmap = QPixmap(w, h)
            pixmap.fill(Qt.transparent)
            return pixmap
        
        w = width or self.size
        h = height or self.size
        
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Создаем шрифт
        font = QFont(MDI_FONT_NAME)
        # Размер шрифта немного меньше размера pixmap для отступов
        font_size = min(w, h) - 4
        if font_size < 1:
            font_size = 1
        font.setPixelSize(font_size)
        
        painter.setFont(font)
        
        # Парсим цвет
        color = self._parse_color(self.color)
        painter.setPen(color)
        
        # Декодируем Unicode код символа
        try:
            # Если это escape-последовательность, декодируем её
            if self.char_code.startswith("\\"):
                # Для \U нужно использовать правильное декодирование
                if self.char_code.startswith("\\U"):
                    # \U000f0415 -> chr(0xf0415)
                    hex_code = self.char_code[2:]
                    unicode_code = int(hex_code, 16)
                    char = chr(unicode_code)
                elif self.char_code.startswith("\\u"):
                    # \u0415 -> chr(0x0415)
                    hex_code = self.char_code[2:]
                    unicode_code = int(hex_code, 16)
                    char = chr(unicode_code)
                else:
                    char = self.char_code.encode().decode('unicode_escape')
            else:
                char = self.char_code
        except Exception:
            char = self.char_code
        
        # Рисуем символ по центру
        painter.drawText(pixmap.rect(), Qt.AlignCenter, char)
        painter.end()
        
        return pixmap
    
    def icon(self) -> QIcon:
        """
        Создает QIcon с иконкой
        
        Returns:
            QIcon с иконкой
        """
        return QIcon(self.pixmap())
    
    @staticmethod
    def _parse_color(color_str: str) -> QColor:
        """Парсит строку цвета в QColor"""
        if color_str.startswith("#"):
            return QColor(color_str)
        elif color_str.startswith("rgb"):
            # Простой парсинг rgb(r,g,b)
            import re
            match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", color_str)
            if match:
                r, g, b = map(int, match.groups())
                return QColor(r, g, b)
        return QColor(color_str)


# Функция для обратной совместимости с qtawesome
def icon(icon_name: str, color: Optional[str] = None) -> IconObject:
    """
    Создает иконку (совместимо с qtawesome.icon)
    
    Args:
        icon_name: Имя иконки (например, "mdi.plus")
        color: Цвет иконки
        
    Returns:
        IconObject с методами pixmap() и icon()
    """
    return IconHelper.icon(icon_name, color)

