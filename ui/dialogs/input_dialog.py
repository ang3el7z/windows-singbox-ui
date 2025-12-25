"""Диалог ввода текста"""
from typing import Optional, Tuple
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.styles import StyleSheet, theme
from ui.widgets import TitleBar
from utils.i18n import tr


def show_input_dialog(
    parent: QWidget,
    title: str,
    message: str,
    text: str = "",
    min_width: int = 400
) -> Tuple[str, bool]:
    """
    Показывает диалог ввода текста
    
    Args:
        parent: Родительский виджет
        title: Заголовок диалога
        message: Сообщение/подсказка
        text: Начальный текст
        min_width: Минимальная ширина диалога
    
    Returns:
        Кортеж (введенный текст, был ли нажат OK)
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
    
    # Поле ввода
    input_field = QLineEdit()
    input_field.setText(text)
    input_field.selectAll()  # Выделяем весь текст для удобства редактирования
    input_field.setStyleSheet(StyleSheet.input())
    input_field.setMinimumHeight(40)
    content_layout.addWidget(input_field)
    
    # Кнопки
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(12)
    
    # Кнопка отмены слева
    btn_cancel = QPushButton(tr("download.cancel"))
    btn_cancel.setCursor(Qt.PointingHandCursor)
    btn_cancel.setStyleSheet(StyleSheet.dialog_button(variant="cancel"))
    btn_cancel.clicked.connect(dialog.reject)
    btn_layout.addWidget(btn_cancel)
    
    # Растяжка между кнопками
    btn_layout.addStretch()
    
    # Кнопка OK справа
    btn_ok = QPushButton(tr("messages.ok"))
    btn_ok.setCursor(Qt.PointingHandCursor)
    btn_ok.setDefault(True)
    btn_ok.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
    btn_ok.clicked.connect(dialog.accept)
    btn_layout.addWidget(btn_ok)
    
    content_layout.addLayout(btn_layout)
    
    # Добавляем content_layout в основной layout
    content_widget = QWidget()
    content_widget.setLayout(content_layout)
    layout.addWidget(content_widget, 1)
    
    # Фокус на поле ввода
    input_field.setFocus()
    
    # Обработка Enter для подтверждения
    def on_enter():
        if input_field.text().strip():
            dialog.accept()
    
    input_field.returnPressed.connect(on_enter)
    
    result = dialog.exec_()
    if result == QDialog.Accepted:
        return input_field.text().strip(), True
    return "", False

