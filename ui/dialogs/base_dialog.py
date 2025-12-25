"""Базовый класс для диалогов"""
from enum import Enum
from typing import Optional, Tuple, Callable
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.styles import StyleSheet, theme
from ui.widgets import TitleBar
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
    # Фреймлесс-режим, чтобы убрать системный статус-бар
    dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Window | Qt.Dialog)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(min_width)
    dialog.setModal(True)
    
    # Стили диалога через дизайн-систему
    dialog.setStyleSheet(StyleSheet.dialog())
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    
    # Собственный статус-бар в стиле приложения
    title_bar = TitleBar(dialog)
    title_bar.set_title(title)  # Устанавливаем title в TitleBar
    layout.addWidget(title_bar)
    
    # Внутренний layout для содержимого
    content_layout = QVBoxLayout()
    content_layout.setSpacing(20)
    content_layout.setContentsMargins(24, 24, 24, 24)
    
    # Заголовок
    title_label = QLabel(title)
    title_label.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
    title_label.setStyleSheet(StyleSheet.label(variant="default", size="xlarge") + "margin-bottom: 8px;")
    content_layout.addWidget(title_label)
    
    # Сообщение
    message_label = QLabel(message)
    message_label.setWordWrap(True)
    message_label.setFont(QFont("Segoe UI", 13))
    message_label.setStyleSheet(StyleSheet.label(variant="secondary") + "margin-bottom: 8px;")
    content_layout.addWidget(message_label)
    
    # Кнопки
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(12)
    
    if dialog_type in (DialogType.CONFIRM, DialogType.WARNING):
        # Кнопки: отмена слева, согласие справа
        btn_no = QPushButton(no_text or tr("download.cancel"))
        btn_no.setObjectName("btnNo")
        btn_no.setCursor(Qt.PointingHandCursor)
        btn_no.setStyleSheet(StyleSheet.dialog_button(variant="cancel"))
        btn_no.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_no)
        
        # Растяжка между кнопками
        btn_layout.addStretch()
        
        # Кнопка согласия справа
        btn_yes = QPushButton(yes_text or (tr("messages.kill_all_yes") if dialog_type == DialogType.WARNING else tr("messages.restart_yes")))
        btn_yes.setObjectName("btnYes")
        btn_yes.setCursor(Qt.PointingHandCursor)
        btn_yes.setDefault(True)
        if dialog_type == DialogType.WARNING:
            btn_yes.setStyleSheet(StyleSheet.dialog_button(variant="warning"))
        else:
            btn_yes.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
        btn_yes.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_yes)
    else:
        # Кнопка OK (справа)
        btn_ok = QPushButton(ok_text or tr("messages.ok"))
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setDefault(True)
        if dialog_type == DialogType.SUCCESS:
            btn_ok.setStyleSheet(StyleSheet.dialog_button(variant="success"))
        else:
            btn_ok.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
        btn_ok.clicked.connect(dialog.accept)
        # Добавляем растяжку слева, чтобы кнопка была справа
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
    
    content_layout.addLayout(btn_layout)
    
    # Добавляем content_layout в основной layout
    content_widget = QWidget()
    content_widget.setLayout(content_layout)
    layout.addWidget(content_widget, 1)
    
    return dialog

