"""Вариации окон - используют базовые компоненты из design"""
from typing import Optional
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from ui.styles import StyleSheet, theme
from ui.design import CardWidget, TitleBar
from ui.design.component.button import Button
from ui.design.component.text_edit import TextEdit
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
        
        # Фреймлесс-режим, чтобы убрать системный статус-бар
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        
        self.setWindowTitle(tr("settings.logs"))
        self.setMinimumSize(600, 500)
        self.resize(800, 600)
        
        # Устанавливаем стиль окна через дизайн-систему
        self.setStyleSheet(StyleSheet.dialog())
        
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Собственный статус-бар в стиле приложения (без текста)
        self.title_bar = TitleBar(self)
        self.title_bar.set_title("")  # Пустой текст
        layout.addWidget(self.title_bar)
        
        # Внутренний layout для содержимого
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)
        
        # Кнопки переключения режима
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)
        
        self.btn_logs = Button(tr("settings.logs"), variant="secondary")
        self.btn_logs.setCheckable(True)
        self.btn_logs.setChecked(True)
        self.btn_logs.clicked.connect(lambda: self._switch_mode("logs"))
        buttons_row.addWidget(self.btn_logs)
        
        self.btn_debug_logs = Button(tr("settings.debug_logs"), variant="secondary")
        self.btn_debug_logs.setCheckable(True)
        self.btn_debug_logs.clicked.connect(lambda: self._switch_mode("debug"))
        buttons_row.addWidget(self.btn_debug_logs)
        
        buttons_row.addStretch()
        content_layout.addLayout(buttons_row)
        
        # Карточка с логами
        logs_card = CardWidget(self)
        logs_card_layout = QVBoxLayout(logs_card)
        logs_card_layout.setContentsMargins(16, 16, 16, 16)
        logs_card_layout.setSpacing(8)
        
        self.logs_text = TextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Consolas", 10))
        # Переопределяем стиль для логов (с фоном background_primary вместо background_secondary)
        self.logs_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.get_color('background_primary')};
                color: {theme.get_color('text_primary')};
                border: none;
                border-radius: {theme.get_size('border_radius_medium')}px;
                padding: 8px;
            }}
        """)
        logs_card_layout.addWidget(self.logs_text)
        
        content_layout.addWidget(logs_card, 1)
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget, 1)
    
    def _switch_mode(self, mode: str):
        """Переключение режима отображения логов"""
        if mode == self.current_mode:
            return
        
        self.current_mode = mode
        self.btn_logs.setChecked(mode == "logs")
        self.btn_debug_logs.setChecked(mode == "debug")
        self._update_logs()
    
    def _update_logs(self):
        """Обновление логов"""
        is_debug = self.main_window.settings.get("isDebug", False)
        self.btn_debug_logs.setVisible(is_debug)
        
        # Логика для скрытия/показа кнопки "Logs"
        if is_debug:
            self.btn_logs.setVisible(True)
        else:
            self.btn_logs.setVisible(False)
            self.btn_logs.setChecked(True)
            self.current_mode = "logs"
        
        if self.current_mode == "logs":
            logs = self.main_window.log_ui_manager.get_logs()
        else:
            logs = self.main_window.log_ui_manager.get_debug_logs()
        
        # Сохраняем позицию скролла
        scrollbar = self.logs_text.verticalScrollBar()
        old_position = scrollbar.value()
        is_at_bottom = (scrollbar.maximum() - old_position) < 50  # Порог 50px
        
        # Обновляем текст
        self.logs_text.setPlainText(logs)
        
        # Восстанавливаем позицию скролла
        if self.autoscroll_enabled or is_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
            self.user_has_scrolled = False
        else:
            scrollbar.setValue(old_position)
    
    def _on_scroll(self, value):
        """Обработка скролла пользователем"""
        scrollbar = self.logs_text.verticalScrollBar()
        max_value = scrollbar.maximum()
        
        # Если пользователь прокрутил вверх, отключаем автоскролл
        if value < max_value - 50:
            if self.autoscroll_enabled:
                self.autoscroll_enabled = False
                self.user_has_scrolled = True
                # Запускаем таймер для возврата автоскролла через 30 секунд
                self.autoscroll_reset_timer.start(30000)
        else:
            # Если пользователь прокрутил вниз до конца, включаем автоскролл
            if not self.autoscroll_enabled and value >= max_value - 5:
                self.autoscroll_enabled = True
                self.user_has_scrolled = False
                self.autoscroll_reset_timer.stop()
    
    def _re_enable_autoscroll(self):
        """Пере-включает автоскролл через 30 секунд после ручного скролла"""
        if self.user_has_scrolled:
            self.autoscroll_enabled = True
            self.user_has_scrolled = False
            scrollbar = self.logs_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.update_timer.stop()
        self.autoscroll_reset_timer.stop()
        super().closeEvent(event)

