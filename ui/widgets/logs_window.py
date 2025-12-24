"""Окно для отображения логов"""
from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from ui.styles import StyleSheet, theme
from ui.widgets import CardWidget
from utils.i18n import tr


class LogsWindow(QDialog):
    """Окно для отображения логов и дебаг логов"""
    
    def __init__(self, main_window, parent=None):
        """
        Инициализация окна логов
        
        Args:
            main_window: Ссылка на главное окно
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.main_window = main_window
        self.current_mode = "logs"  # "logs" или "debug"
        
        # Флаг для автоскролла
        self.autoscroll_enabled = True
        self.user_has_scrolled = False
        
        self.setWindowTitle(tr("settings.logs"))
        self.setMinimumSize(600, 500)
        self.resize(800, 600)
        
        # Устанавливаем стиль окна
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.get_color('background_primary')};
            }}
        """)
        
        self._build_ui()
        
        # Таймер для обновления логов
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_logs)
        self.update_timer.start(500)  # Обновление каждые 500мс
        
        # Таймер для возврата автоскролла через 30 секунд
        self.autoscroll_reset_timer = QTimer(self)
        self.autoscroll_reset_timer.timeout.connect(self._re_enable_autoscroll)
        self.autoscroll_reset_timer.setSingleShot(True)
        
        # Подключаем обработчик скролла
        self.logs_text.verticalScrollBar().valueChanged.connect(self._on_scroll)
        
        # Загружаем логи при открытии
        self._update_logs()
    
    def _build_ui(self):
        """Построение UI окна"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Кнопки переключения режима
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)
        
        self.btn_logs = QPushButton(tr("settings.logs"))
        self.btn_logs.setCheckable(True)
        self.btn_logs.setChecked(True)
        self.btn_logs.clicked.connect(lambda: self._switch_mode("logs"))
        self.btn_logs.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.get_color('background_tertiary')};
                color: {theme.get_color('text_primary')};
                border: 1px solid {theme.get_color('border')};
                border-radius: {theme.get_size('border_radius_medium')}px;
                padding: {theme.get_size('padding_medium')}px {theme.get_size('padding_large')}px;
                font-size: {theme.get_font('size_medium')}px;
                font-weight: {theme.get_font('weight_medium')};
                font-family: {theme.get_font('family')};
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {theme.get_color('accent_light')};
                border-color: {theme.get_color('border_hover')};
            }}
            QPushButton:checked {{
                background-color: {theme.get_color('accent')};
                color: #ffffff;
                border-color: {theme.get_color('accent')};
            }}
        """)
        buttons_row.addWidget(self.btn_logs, 1)
        
        self.btn_debug_logs = QPushButton("Debug Logs")
        self.btn_debug_logs.setCheckable(True)
        self.btn_debug_logs.clicked.connect(lambda: self._switch_mode("debug"))
        self.btn_debug_logs.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.get_color('background_tertiary')};
                color: {theme.get_color('error')};
                border: 1px solid rgba(255, 107, 107, 0.3);
                border-radius: {theme.get_size('border_radius_medium')}px;
                padding: {theme.get_size('padding_medium')}px {theme.get_size('padding_large')}px;
                font-size: {theme.get_font('size_medium')}px;
                font-weight: {theme.get_font('weight_medium')};
                font-family: {theme.get_font('family')};
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 107, 107, 0.1);
                border-color: rgba(255, 107, 107, 0.5);
            }}
            QPushButton:checked {{
                background-color: {theme.get_color('error')};
                color: #ffffff;
                border-color: {theme.get_color('error')};
            }}
        """)
        # Кнопка дебаг логов видна только если isDebug=True
        is_debug = self.main_window.settings.get("isDebug", False)
        self.btn_debug_logs.setVisible(is_debug)
        buttons_row.addWidget(self.btn_debug_logs, 1)
        
        layout.addLayout(buttons_row)
        
        # Область для логов
        logs_card = CardWidget()
        logs_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        logs_layout = QVBoxLayout(logs_card)
        logs_layout.setContentsMargins(16, 16, 16, 16)
        logs_layout.setSpacing(0)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet(StyleSheet.text_edit())
        self.logs_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        logs_layout.addWidget(self.logs_text)
        
        layout.addWidget(logs_card, 1)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.get_color('background_tertiary')};
                color: {theme.get_color('text_primary')};
                border: 1px solid {theme.get_color('border')};
                border-radius: {theme.get_size('border_radius_medium')}px;
                padding: {theme.get_size('padding_medium')}px {theme.get_size('padding_large')}px;
                font-size: {theme.get_font('size_medium')}px;
                font-weight: {theme.get_font('weight_medium')};
                font-family: {theme.get_font('family')};
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {theme.get_color('accent_light')};
                border-color: {theme.get_color('border_hover')};
            }}
        """)
        layout.addWidget(close_btn)
    
    def _switch_mode(self, mode: str):
        """Переключение режима отображения логов"""
        self.current_mode = mode
        self.btn_logs.setChecked(mode == "logs")
        self.btn_debug_logs.setChecked(mode == "debug")
        self._update_logs()
    
    def _update_logs(self):
        """Обновление содержимого логов"""
        # Проверяем, включен ли дебаг режим
        is_debug = self.main_window.settings.get("isDebug", False)
        
        # Обновляем видимость кнопки дебаг логов
        self.btn_debug_logs.setVisible(is_debug)
        
        if self.current_mode == "logs":
            # Загружаем обычные логи
            if hasattr(self.main_window, 'page_settings'):
                logs_content = self.main_window.page_settings.logs.toPlainText()
                self.logs_text.setPlainText(logs_content)
                self.logs_text.setStyleSheet(StyleSheet.text_edit())
        else:
            # Загружаем дебаг логи только если isDebug=True
            if is_debug and hasattr(self.main_window, 'page_settings'):
                debug_logs_content = self.main_window.page_settings.debug_logs.toPlainText()
                self.logs_text.setPlainText(debug_logs_content)
                self.logs_text.setStyleSheet(f"""
                    QTextEdit {{
                        background-color: rgba(255, 107, 107, 0.05);
                        color: {theme.get_color('error')};
                        border-radius: {theme.get_size('border_radius_large')}px;
                        padding: {theme.get_size('padding_large')}px;
                        border: 2px solid rgba(255, 107, 107, 0.2);
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 10px;
                        outline: none;
                    }}
                """)
            else:
                # Если дебаг режим выключен, показываем сообщение
                self.logs_text.setPlainText("Debug mode is disabled. Click on the version 6 times to enable debug mode.")
                self.logs_text.setStyleSheet(StyleSheet.text_edit())
        
        # Проверяем позицию скролла и прокручиваем вниз если нужно
        scrollbar = self.logs_text.verticalScrollBar()
        max_value = scrollbar.maximum()
        current_value = scrollbar.value()
        is_at_bottom = current_value >= max_value - 5
        
        # Если пользователь внизу, включаем автоскролл (на случай если он был выключен таймером)
        if is_at_bottom:
            self.autoscroll_enabled = True
            self.user_has_scrolled = False
            self.autoscroll_reset_timer.stop()
        
        # Прокручиваем вниз только если автоскролл включен
        if self.autoscroll_enabled:
            scrollbar.setValue(max_value)
    
    def _on_scroll(self, value):
        """Обработка скролла пользователем"""
        scrollbar = self.logs_text.verticalScrollBar()
        max_value = scrollbar.maximum()
        
        # Определяем, находится ли пользователь внизу (с небольшим допуском в 5 пикселей)
        is_at_bottom = value >= max_value - 5
        
        if is_at_bottom:
            # Если пользователь прокрутил до самого низа, включаем автоскролл
            self.autoscroll_enabled = True
            self.user_has_scrolled = False
            self.autoscroll_reset_timer.stop()
        else:
            # Если пользователь прокрутил вверх, выключаем автоскролл
            if not self.user_has_scrolled:
                self.user_has_scrolled = True
                self.autoscroll_enabled = False
            
            # Сбрасываем и перезапускаем таймер на 30 секунд
            self.autoscroll_reset_timer.stop()
            self.autoscroll_reset_timer.start(30000)  # 30 секунд
    
    def _re_enable_autoscroll(self):
        """Перевключает автоскролл после истечения таймера"""
        scrollbar = self.logs_text.verticalScrollBar()
        max_value = scrollbar.maximum()
        current_value = scrollbar.value()
        
        # Проверяем, находится ли пользователь внизу
        is_at_bottom = current_value >= max_value - 5
        
        if is_at_bottom:
            self.autoscroll_enabled = True
            self.user_has_scrolled = False
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.update_timer.stop()
        self.autoscroll_reset_timer.stop()
        super().closeEvent(event)

