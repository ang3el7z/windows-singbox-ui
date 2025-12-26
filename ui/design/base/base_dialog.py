"""Базовый диалог - компонент из дизайн-системы"""
from typing import Optional
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from ui.styles import StyleSheet
from .base_title_bar import BaseTitleBar


class BaseDialog(QDialog):
    """Базовый диалог из дизайн-системы с TitleBar"""
    
    def __init__(self, parent: Optional[QWidget] = None, title: str = ""):
        """
        Инициализация базового диалога
        
        Args:
            parent: Родительский виджет
            title: Заголовок диалога (для TitleBar)
        """
        super().__init__(parent)
        
        # Фреймлесс-режим для кастомного TitleBar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window | Qt.Dialog)
        self.setModal(True)
        
        # Стили из дизайн-системы
        self.setStyleSheet(StyleSheet.dialog())
        
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # TitleBar из компонентов
        self.title_bar = BaseTitleBar(self)
        self.title_bar.set_title(title)
        main_layout.addWidget(self.title_bar)
        
        # Content widget для содержимого (должен быть заполнен в наследниках)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.addWidget(self.content_widget, 1)
    
    def set_title(self, title: str):
        """Устанавливает заголовок в TitleBar"""
        self.title_bar.set_title(title)
        self.setWindowTitle(title)

