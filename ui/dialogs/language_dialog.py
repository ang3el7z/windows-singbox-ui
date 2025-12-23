"""Диалог выбора языка"""
from typing import Optional
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.styles import StyleSheet, theme
from utils.i18n import get_available_languages, get_language_name, tr


def show_language_selection_dialog(parent: Optional[QWidget] = None) -> str:
    """
    Диалог выбора языка при первом запуске
    
    Args:
        parent: Родительский виджет
    
    Returns:
        Код выбранного языка
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle("Select Language / Выберите язык")
    dialog.setMinimumWidth(400)
    dialog.setModal(True)
    from ui.styles.constants import COLORS, SIZES, FONTS
    dialog.setStyleSheet(f"""
        QDialog {{
            background-color: {COLORS['background_primary']};
            border-radius: {SIZES['border_radius_medium']}px;
        }}
        QLabel {{
            color: {COLORS['text_primary']};
            background-color: transparent;
            border: none;
        }}
        QPushButton {{
            border-radius: {SIZES['border_radius_medium']}px;
            padding: {SIZES['padding_medium']}px {SIZES['padding_large']}px;
            font-size: {FONTS['size_medium']}px;
            font-weight: {FONTS['weight_semibold']};
            border: 2px solid {COLORS['accent']};
            background-color: transparent;
            color: {COLORS['accent']};
            margin: 4px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['accent_light']};
        }}
        QPushButton:default {{
            background-color: {COLORS['accent']};
            color: {COLORS['background_primary']};
        }}
    """)
    
    layout = QVBoxLayout(dialog)
    layout.setSpacing(20)
    layout.setContentsMargins(24, 24, 24, 24)
    
    # Заголовок
    title_label = QLabel("Select Language / Выберите язык")
    title_label.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
    title_label.setStyleSheet(StyleSheet.label(variant="default", size="xlarge") + "margin-bottom: 8px;")
    layout.addWidget(title_label)
    
    # Список языков
    available_languages = get_available_languages()
    selected_language = ["en"]  # Используем список для изменения в lambda
    
    def select_language(lang_code: str) -> None:
        selected_language[0] = lang_code
        dialog.accept()
    
    for lang_code in available_languages:
        lang_name = get_language_name(lang_code)
        btn = QPushButton(lang_name)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda checked, l=lang_code: select_language(l))
        layout.addWidget(btn)
    
    # Кнопка OK
    btn_ok = QPushButton("OK")
    btn_ok.setCursor(Qt.PointingHandCursor)
    btn_ok.setDefault(True)
    btn_ok.clicked.connect(dialog.accept)
    layout.addWidget(btn_ok)
    
    if dialog.exec_() == QDialog.Accepted:
        return selected_language[0]
    return "en"  # Fallback на английский

