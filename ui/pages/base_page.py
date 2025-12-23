"""Базовый класс для всех страниц"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from ui.widgets import CardWidget
from ui.styles import StyleSheet


class BasePage(QWidget):
    """Базовый класс для всех страниц приложения"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Устанавливаем явный фон страницы
        from ui.styles import theme
        from PyQt5.QtWidgets import QSizePolicy
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.get_color('background_primary')};
            }}
        """)
        # Страницы должны расширяться
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(16)
    
    def add_card(self, title: str = None) -> CardWidget:
        """Добавляет карточку на страницу"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        
        if title:
            from PyQt5.QtWidgets import QLabel
            from PyQt5.QtGui import QFont
            title_label = QLabel(title)
            title_label.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
            title_label.setStyleSheet(StyleSheet.label(variant="default", size="xlarge"))
            layout.addWidget(title_label)
        
        self._layout.addWidget(card)
        return card

