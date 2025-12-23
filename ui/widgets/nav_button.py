"""Кнопка навигации с иконкой"""
from PyQt5.QtWidgets import QPushButton, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import qtawesome as qta
from ui.styles import StyleSheet


class NavButton(QPushButton):
    """Кнопка навигации с иконкой и текстом"""
    
    def __init__(self, text: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name  # Сохраняем имя иконки
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # Контейнер для содержимого
        container = QWidget()
        container.setStyleSheet("background-color: transparent; border: none;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(10)
        
        # Иконка
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setPixmap(qta.icon(icon_name, color="#64748b").pixmap(36, 36))
        self.icon_label.setStyleSheet("background-color: transparent; border: none;")
        
        # Текст
        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet(StyleSheet.label(variant="secondary", size="medium"))
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        container.setLayout(layout)
        
        # Основной layout кнопки
        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addWidget(container)
        
        # Подключаем изменение состояния
        self.toggled.connect(self._update_style)
    
    def _update_style(self, checked: bool):
        """Обновляет стиль при изменении состояния"""
        from ui.styles import theme
        
        color = theme.get_color('accent') if checked else theme.get_color('text_secondary')
        self.icon_label.setPixmap(
            qta.icon(self.icon_name, color=color).pixmap(36, 36)
        )
        
        weight = theme.get_font('weight_semibold') if checked else theme.get_font('weight_medium')
        self.text_label.setStyleSheet(f"""
            font-size: {theme.get_font('size_medium')}px;
            font-weight: {weight};
            background-color: transparent;
            border: none;
            color: {color};
        """)
    
    def setIconName(self, icon_name: str):
        """Устанавливает имя иконки"""
        self.icon_name = icon_name
        self._update_style(self.isChecked())
    
    def setText(self, text: str):
        """Устанавливает текст"""
        self.text_label.setText(text)

