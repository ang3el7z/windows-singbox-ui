"""Базовый класс для диалогов"""
from enum import Enum
from typing import Optional, Tuple, Callable
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.styles import StyleSheet, theme
from utils.i18n import tr


class DialogType(Enum):
    """Типы диалогов"""
    INFO = "info"  # Информационный (одна кнопка OK)
    CONFIRM = "confirm"  # Подтверждение (Yes/No)
    WARNING = "warning"  # Предупреждение (Yes/No с красной кнопкой)
    SUCCESS = "success"  # Успех (одна кнопка OK зеленого цвета)


def create_dialog(
    parent,
    title: str,
    message: str,
    dialog_type: DialogType = DialogType.INFO,
    min_width: int = 400,
    yes_text: Optional[str] = None,
    no_text: Optional[str] = None,
    ok_text: Optional[str] = None
) -> QDialog:
    """
    Создает универсальный диалог
    
    Args:
        parent: Родительский виджет
        title: Заголовок диалога
        message: Сообщение
        dialog_type: Тип диалога
        min_width: Минимальная ширина
        yes_text: Текст кнопки Yes (для confirm/warning)
        no_text: Текст кнопки No (для confirm/warning)
        ok_text: Текст кнопки OK (для info/success)
    
    Returns:
        Созданный диалог
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(min_width)
    dialog.setModal(True)
    
    # Стили диалога
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
            border: none;
        }}
    """)
    
    layout = QVBoxLayout(dialog)
    layout.setSpacing(20)
    layout.setContentsMargins(24, 24, 24, 24)
    
    # Заголовок
    title_label = QLabel(title)
    title_label.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
    title_label.setStyleSheet(StyleSheet.label(variant="default", size="xlarge") + "margin-bottom: 8px;")
    layout.addWidget(title_label)
    
    # Сообщение
    message_label = QLabel(message)
    message_label.setWordWrap(True)
    message_label.setFont(QFont("Segoe UI", 13))
    message_label.setStyleSheet(StyleSheet.label(variant="secondary") + "margin-bottom: 8px;")
    layout.addWidget(message_label)
    
    # Кнопки
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(12)
    
    if dialog_type in (DialogType.CONFIRM, DialogType.WARNING):
        # Кнопки Yes/No
        btn_no = QPushButton(no_text or tr("download.cancel"))
        btn_no.setObjectName("btnNo")
        btn_no.setCursor(Qt.PointingHandCursor)
        from ui.styles.constants import COLORS
        btn_no.setStyleSheet(f"""
            QPushButton#btnNo {{
                background-color: rgba(255,255,255,0.05);
                color: {COLORS['text_secondary']};
            }}
            QPushButton#btnNo:hover {{
                background-color: rgba(255,255,255,0.1);
            }}
        """)
        btn_no.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_no)
        
        from ui.styles.constants import COLORS
        yes_color = COLORS['error'] if dialog_type == DialogType.WARNING else COLORS['accent']
        btn_yes = QPushButton(yes_text or (tr("messages.kill_all_yes") if dialog_type == DialogType.WARNING else tr("messages.restart_yes")))
        btn_yes.setObjectName("btnYes")
        btn_yes.setCursor(Qt.PointingHandCursor)
        btn_yes.setDefault(True)
        btn_yes.setStyleSheet(f"""
            QPushButton#btnYes {{
                background-color: {yes_color};
                color: {'#ffffff' if dialog_type == DialogType.WARNING else '#020617'};
            }}
            QPushButton#btnYes:hover {{
                background-color: {'#ff8787' if dialog_type == DialogType.WARNING else '#5fffe3'};
            }}
        """)
        btn_yes.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_yes)
    else:
        # Кнопка OK
        btn_ok = QPushButton(ok_text or tr("messages.ok"))
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setDefault(True)
        from ui.styles.constants import COLORS
        ok_color = COLORS['success'] if dialog_type == DialogType.SUCCESS else COLORS['accent']
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {ok_color};
                color: #020617;
            }}
            QPushButton:hover {{
                background-color: #5fffe3;
            }}
        """)
        btn_ok.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_ok)
    
    layout.addLayout(btn_layout)
    
    return dialog

