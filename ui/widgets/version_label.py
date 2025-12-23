"""Виджет для отображения версии с состояниями"""
from PyQt5.QtWidgets import QLabel
from ui.styles import StyleSheet


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

