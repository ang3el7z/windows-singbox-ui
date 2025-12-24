"""Диалог выбора языка"""
from typing import Optional
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
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
    dialog.setWindowTitle(tr("language_dialog.title"))
    dialog.setMinimumWidth(400)
    dialog.setModal(True)
    
    # Стили диалога через дизайн-систему
    dialog.setStyleSheet(StyleSheet.dialog() + f"""
        QPushButton {{
            border: 2px solid {theme.get_color('accent')};
            background-color: transparent;
            color: {theme.get_color('accent')};
            margin: 4px;
        }}
        QPushButton:hover {{
            background-color: {theme.get_color('accent_light')};
        }}
        QPushButton:default {{
            background-color: {theme.get_color('accent')};
            color: {theme.get_color('background_primary')};
        }}
    """)
    
    layout = QVBoxLayout(dialog)
    layout.setSpacing(20)
    layout.setContentsMargins(24, 24, 24, 24)
    
    # Заголовок
    title_label = QLabel(tr("language_dialog.title"))
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
    
    # Кнопка OK (справа)
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()  # Растяжка слева
    btn_ok = QPushButton(tr("language_dialog.ok"))
    btn_ok.setCursor(Qt.PointingHandCursor)
    btn_ok.setDefault(True)
    btn_ok.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
    btn_ok.clicked.connect(dialog.accept)
    btn_layout.addWidget(btn_ok)
    layout.addLayout(btn_layout)
    
    if dialog.exec_() == QDialog.Accepted:
        return selected_language[0]
    return "en"  # Fallback на английский

