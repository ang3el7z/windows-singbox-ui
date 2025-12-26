"""Вариации лейблов - используют дизайн-систему"""
from typing import Optional
from PyQt5.QtWidgets import QLabel, QWidget
from ui.styles import StyleSheet


class Label(QLabel):
    """Универсальный лейбл с применением стилей из дизайн-системы"""
    
    def __init__(
        self,
        text: str = "",
        parent: Optional[QWidget] = None,
        variant: str = "default",
        size: str = "medium"
    ):
        """
        Инициализация лейбла
        
        Args:
            text: Текст лейбла
            parent: Родительский виджет
            variant: Вариант (default, primary, secondary, success, error, warning)
            size: Размер (small, medium, large, xlarge)
        """
        super().__init__(text, parent)
        self._variant = variant
        self._size = size
        self.apply_style()
    
    def apply_style(self):
        """Применяет стиль лейбла из дизайн-системы"""
        self.setStyleSheet(StyleSheet.label(
            variant=self._variant,
            size=self._size
        ))
    
    def set_variant(self, variant: str):
        """Устанавливает вариант лейбла"""
        self._variant = variant
        self.apply_style()
    
    def set_size(self, size: str):
        """Устанавливает размер лейбла"""
        self._size = size
        self.apply_style()


class VersionLabel(QLabel):
    """Лейбл версии с поддержкой различных состояний"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = "default"  # default, installed, not_installed, update_available
    
    def set_installed(self, version: str):
        """Устанавливает состояние 'установлено'"""
        self._state = "installed"
        self.setText(version)
        self.setStyleSheet(StyleSheet.label(variant="primary"))
    
    def set_not_installed(self):
        """Устанавливает состояние 'не установлено'"""
        self._state = "not_installed"
        self.setStyleSheet(StyleSheet.label(variant="error"))
    
    def set_update_available(self, version: str):
        """Устанавливает состояние 'доступно обновление'"""
        self._state = "update_available"
        self.setText(version)
        self.setStyleSheet(StyleSheet.label(variant="warning"))
