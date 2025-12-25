"""Диалог добавления подписки"""
from typing import Optional, Tuple
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.styles import StyleSheet, theme
from ui.widgets import TitleBar
from ui.dialogs.base_dialog import create_dialog, DialogType
from utils.i18n import tr


def show_add_subscription_dialog(parent: QWidget) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Показывает диалог добавления подписки с двумя полями ввода
    
    Args:
        parent: Родительский виджет
    
    Returns:
        Кортеж (name, url, был ли нажат OK)
    """
    dialog = QDialog(parent)
    # Фреймлесс-режим, чтобы отрисовывать собственный статус-бар
    dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Window | Qt.Dialog)
    dialog.setWindowTitle(tr("profile.add_subscription"))
    dialog.setMinimumWidth(420)
    dialog.setModal(True)
    
    # Стили диалога через дизайн-систему
    dialog.setStyleSheet(StyleSheet.dialog() + StyleSheet.input())
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    
    # Собственный статус-бар в стиле приложения
    title_bar = TitleBar(dialog)
    title_bar.set_title(tr("profile.add_subscription"))
    layout.addWidget(title_bar)
    
    # Внутренний layout для содержимого
    content_layout = QVBoxLayout()
    content_layout.setSpacing(20)
    content_layout.setContentsMargins(24, 24, 24, 24)
    
    # Заголовок
    title_label = QLabel(tr("profile.add_subscription"))
    title_label.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
    title_label.setStyleSheet(StyleSheet.label(variant="default", size="xlarge") + "margin-bottom: 8px;")
    content_layout.addWidget(title_label)
    
    # Название
    name_label = QLabel(tr("profile.name"))
    name_label.setStyleSheet(StyleSheet.label(variant="default", size="medium") + "margin-top: 8px;")
    content_layout.addWidget(name_label)
    
    name_input = QLineEdit()
    name_input.setPlaceholderText(tr("profile.name"))
    name_input.setStyleSheet(StyleSheet.input())
    content_layout.addWidget(name_input)
    
    # URL
    url_label = QLabel(tr("profile.url"))
    url_label.setStyleSheet(StyleSheet.label(variant="default", size="medium") + "margin-top: 8px;")
    content_layout.addWidget(url_label)
    
    url_input = QLineEdit()
    url_input.setPlaceholderText("https://...")
    url_input.setStyleSheet(StyleSheet.input())
    content_layout.addWidget(url_input)
    
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
    
    # Кнопка добавления справа
    btn_add = QPushButton(tr("profile.add"))
    btn_add.setCursor(Qt.PointingHandCursor)
    btn_add.setDefault(True)
    btn_add.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
    
    def on_add_clicked():
        name = name_input.text().strip()
        url = url_input.text().strip()
        if name and url:
            dialog.accept()
        else:
            # Показываем диалог ошибки через дизайн-систему
            from ui.dialogs.info_dialog import show_info_dialog
            show_info_dialog(dialog, tr("profile.add_subscription"), tr("profile.fill_all_fields"))
    
    btn_add.clicked.connect(on_add_clicked)
    btn_layout.addWidget(btn_add)
    
    content_layout.addLayout(btn_layout)
    
    # Добавляем content_layout в основной layout
    content_widget = QWidget()
    content_widget.setLayout(content_layout)
    layout.addWidget(content_widget, 1)
    
    # Фокус на первое поле
    name_input.setFocus()
    
    # Обработка Enter для подтверждения
    def on_enter():
        if name_input.text().strip() and url_input.text().strip():
            on_add_clicked()
    
    name_input.returnPressed.connect(lambda: url_input.setFocus())
    url_input.returnPressed.connect(on_enter)
    
    result = dialog.exec_()
    if result == QDialog.Accepted:
        name = name_input.text().strip()
        url = url_input.text().strip()
        if name and url:
            return name, url, True
    return None, None, False

