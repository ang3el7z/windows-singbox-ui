"""Инициализация и настройка QApplication"""
from typing import Optional
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
import sys
import ctypes
from ui.styles import StyleSheet, theme
from utils.icon_manager import set_application_icon
from utils.theme_manager import set_theme, get_theme_manager
from managers.settings import SettingsManager

# Импортируем ресурсы (QRC) для доступа к шрифтам
try:
    import scripts.resources_rc  # noqa: F401
except ImportError:
    pass  # resources_rc может отсутствовать в режиме разработки

# Инициализируем icon_helper для загрузки шрифта
from utils.icon_helper import IconHelper


def create_application() -> QApplication:
    """
    Создает и настраивает QApplication
    
    Returns:
        Настроенный экземпляр QApplication
    """
    app = QApplication(sys.argv)
    app.setApplicationName("SingBox-UI")
    
    # Загружаем шрифт Material Design Icons из QRC
    # Это нужно сделать до создания UI элементов
    IconHelper._ensure_font_loaded()
    
    # Устанавливаем иконку приложения (важно для Windows - иконка в таскбаре)
    set_application_icon(app)
    
    # Устанавливаем AppUserModelID для Windows (чтобы иконка не сбрасывалась)
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ang3el.SingBox-UI")
        except Exception:
            pass  # Игнорируем ошибки, если не удалось установить
    
    # Загружаем настройки и применяем тему
    settings = SettingsManager()
    theme_name = settings.get("theme", "dark")
    set_theme(theme_name)
    theme.reload_theme()
    
    apply_theme(app)
    return app


def apply_theme(app: QApplication) -> None:
    """
    Применение темы к приложению
    
    Args:
        app: Экземпляр QApplication
    """
    app.setStyle("Fusion")
    palette = QPalette()
    text = QColor(theme.get_color('text_primary'))
    accent = QColor(theme.get_color('accent'))

    palette.setColor(QPalette.Window, QColor(theme.get_color('background_primary')))
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, QColor(theme.get_color('background_secondary')))
    palette.setColor(QPalette.AlternateBase, QColor(theme.get_color('background_secondary')))
    palette.setColor(QPalette.ToolTipBase, QColor(theme.get_color('background_secondary')))
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, QColor(theme.get_color('background_secondary')))
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.BrightText, QColor(theme.get_color('error')))
    palette.setColor(QPalette.Highlight, accent)
    # Используем цвет текста из темы для выделенного текста
    # Для темной темы - темный фон, для светлой - светлый
    bg_primary = QColor(theme.get_color('background_primary'))
    palette.setColor(QPalette.HighlightedText, bg_primary)
    app.setPalette(palette)
    
    # Используем новую систему стилей
    app.setStyleSheet(StyleSheet.global_styles())


def apply_dark_theme(app: QApplication) -> None:
    """
    Применение темной темы к приложению (для обратной совместимости)
    
    Args:
        app: Экземпляр QApplication
    """
    apply_theme(app)

