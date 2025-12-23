"""Инициализация и настройка QApplication"""
from typing import Optional
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
import sys
from ui.styles import StyleSheet, theme


def create_application() -> QApplication:
    """
    Создает и настраивает QApplication
    
    Returns:
        Настроенный экземпляр QApplication
    """
    app = QApplication(sys.argv)
    app.setApplicationName("SingBox-UI")
    apply_dark_theme(app)
    return app


def apply_dark_theme(app: QApplication) -> None:
    """
    Применение темной темы к приложению
    
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
    palette.setColor(QPalette.HighlightedText, QColor("#000000"))
    app.setPalette(palette)
    
    # Используем новую систему стилей
    app.setStyleSheet(StyleSheet.global_styles())

