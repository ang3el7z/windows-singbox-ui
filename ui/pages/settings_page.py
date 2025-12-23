from typing import TYPE_CHECKING, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QCheckBox, QComboBox, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.pages.base_page import BasePage
from ui.widgets import CardWidget
from ui.styles import StyleSheet, theme
from utils.i18n import tr, get_available_languages, get_language_name

if TYPE_CHECKING:
    from main import MainWindow


class ClickableLabel(QLabel):
    """Кликабельный лейбл для заголовка логов"""
    def __init__(self, parent, callback):
        super().__init__()
        self.parent_window = parent
        self.callback = callback
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.callback()
        super().mousePressEvent(event)


class SettingsPage(BasePage):
    """Страница настроек приложения"""
    
    def __init__(self, main_window: 'MainWindow', parent: Optional[QWidget] = None):
        """
        Инициализация страницы настроек
        
        Args:
            main_window: Ссылка на главное окно
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.main_window = main_window
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(16)
        self._build_ui()
    
    def _build_ui(self):
        """Построение UI страницы"""
        # Настройки
        settings_card = CardWidget()
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(20, 16, 20, 16)
        settings_layout.setSpacing(16)
        
        self.settings_title = QLabel(tr("settings.title"))
        self.settings_title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        self.settings_title.setStyleSheet(StyleSheet.label(variant="default", size="xlarge"))
        settings_layout.addWidget(self.settings_title)
        
        # Интервал автообновления
        row = QHBoxLayout()
        row.setSpacing(12)
        row_label = QLabel(tr("settings.auto_update_interval"))
        row_label.setFont(QFont("Segoe UI", 13))
        row_label.setStyleSheet(StyleSheet.label(variant="secondary"))
        row.addWidget(row_label)
        self.edit_interval = QLineEdit()
        self.edit_interval.setText(str(self.main_window.settings.get("auto_update_minutes", 90)))
        self.edit_interval.setPlaceholderText("90")
        self.edit_interval.editingFinished.connect(self.main_window.on_interval_changed)
        self.edit_interval.setStyleSheet(StyleSheet.input())
        row.addWidget(self.edit_interval)
        settings_layout.addLayout(row)
        
        # Чекбоксы настроек
        self.cb_autostart = QCheckBox(tr("settings.autostart"))
        self.cb_autostart.setChecked(self.main_window.settings.get("start_with_windows", False))
        self.cb_autostart.stateChanged.connect(self.main_window.on_autostart_changed)
        self.cb_autostart.setFont(QFont("Segoe UI", 13))
        self.cb_autostart.setStyleSheet(StyleSheet.checkbox())
        settings_layout.addWidget(self.cb_autostart)
        
        self.cb_run_as_admin = QCheckBox(tr("settings.run_as_admin"))
        self.cb_run_as_admin.setChecked(self.main_window.settings.get("run_as_admin", False))
        self.cb_run_as_admin.stateChanged.connect(self.main_window.on_run_as_admin_changed)
        self.cb_run_as_admin.setFont(QFont("Segoe UI", 13))
        self.cb_run_as_admin.setStyleSheet(StyleSheet.checkbox())
        settings_layout.addWidget(self.cb_run_as_admin)
        
        self.cb_auto_start_singbox = QCheckBox(tr("settings.auto_start_singbox"))
        self.cb_auto_start_singbox.setChecked(self.main_window.settings.get("auto_start_singbox", False))
        self.cb_auto_start_singbox.stateChanged.connect(self.main_window.on_auto_start_singbox_changed)
        self.cb_auto_start_singbox.setFont(QFont("Segoe UI", 13))
        self.cb_auto_start_singbox.setStyleSheet(StyleSheet.checkbox())
        settings_layout.addWidget(self.cb_auto_start_singbox)
        
        self.cb_minimize_to_tray = QCheckBox(tr("settings.minimize_to_tray"))
        self.cb_minimize_to_tray.setChecked(self.main_window.settings.get("minimize_to_tray", True))
        self.cb_minimize_to_tray.stateChanged.connect(self.main_window.on_minimize_to_tray_changed)
        self.cb_minimize_to_tray.setFont(QFont("Segoe UI", 13))
        self.cb_minimize_to_tray.setStyleSheet(StyleSheet.checkbox())
        settings_layout.addWidget(self.cb_minimize_to_tray)
        
        # Выбор языка
        language_row = QHBoxLayout()
        language_row.setSpacing(12)
        self.language_label = QLabel(tr("settings.language"))
        self.language_label.setFont(QFont("Segoe UI", 13))
        self.language_label.setStyleSheet(StyleSheet.label(variant="secondary"))
        language_row.addWidget(self.language_label)
        
        self.combo_language = QComboBox()
        available_languages = get_available_languages()
        current_language = self.main_window.settings.get("language", "")
        if not current_language:
            current_language = "en"  # Fallback на английский если не выбран
        for lang_code in available_languages:
            lang_name = get_language_name(lang_code)
            self.combo_language.addItem(lang_name, lang_code)
            if lang_code == current_language:
                self.combo_language.setCurrentIndex(self.combo_language.count() - 1)
        self.combo_language.currentIndexChanged.connect(self.main_window.on_language_changed)
        self.combo_language.setStyleSheet(StyleSheet.combo_box())
        language_row.addWidget(self.combo_language)
        settings_layout.addLayout(language_row)
        
        # Кнопка "Убить" для полной остановки всех процессов (без отдельной подложки, просто кнопка)
        self.btn_kill_all = QPushButton(tr("settings.kill_all"))
        self.btn_kill_all.setFont(QFont("Segoe UI", 13))
        self.btn_kill_all.setCursor(Qt.PointingHandCursor)
        # Кнопка внутри карточки, без отдельной подложки
        # Добавляем минимальные размеры для адаптивности
        self.btn_kill_all.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.get_color('error')};
                color: #ffffff;
                border: none;
                border-radius: {theme.get_size('border_radius_medium')}px;
                padding: {theme.get_size('padding_medium')}px {theme.get_size('padding_large')}px;
                font-size: {theme.get_font('size_medium')}px;
                font-weight: {theme.get_font('weight_medium')};
                font-family: {theme.get_font('family')};
                min-width: 100px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #ff5252;
            }}
            QPushButton:pressed {{
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: {theme.get_color('background_secondary')};
                color: {theme.get_color('text_disabled')};
                opacity: 0.5;
            }}
        """)
        self.btn_kill_all.setMinimumSize(100, 36)
        self.btn_kill_all.clicked.connect(self.main_window.on_kill_all_clicked)
        settings_layout.addWidget(self.btn_kill_all)
        
        self._layout.addWidget(settings_card)
        
        # Логи
        logs_card = CardWidget()
        logs_layout = QVBoxLayout(logs_card)
        logs_layout.setContentsMargins(20, 16, 20, 16)
        logs_layout.setSpacing(12)
        
        clickable_logs_title = ClickableLabel(self, self.main_window.on_logs_title_clicked)
        clickable_logs_title.setText(tr("settings.logs"))
        clickable_logs_title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        clickable_logs_title.setStyleSheet(StyleSheet.label(variant="default", size="xlarge"))
        logs_layout.addWidget(clickable_logs_title)
        
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setStyleSheet(StyleSheet.text_edit())
        logs_layout.addWidget(self.logs, 1)
        # Логи загружаются при активации страницы через switch_page
        
        self._layout.addWidget(logs_card, 1)
        
        # Дебаг секция (скрыта по умолчанию, появляется снизу после логов)
        # Включает дебаг настройки и дебаг логи на одной подложке
        self.debug_card = CardWidget()
        self.debug_layout = QVBoxLayout(self.debug_card)
        self.debug_layout.setContentsMargins(20, 16, 20, 16)
        self.debug_layout.setSpacing(16)
        
        debug_title = QLabel(tr("settings.debug_title"))
        debug_title.setFont(QFont("Segoe UI Semibold", 18, QFont.Bold))
        debug_title.setStyleSheet(StyleSheet.label(variant="error", size="large"))
        self.debug_layout.addWidget(debug_title)
        
        self.cb_allow_multiple = QCheckBox(tr("settings.allow_multiple_processes"))
        self.cb_allow_multiple.setChecked(self.main_window.settings.get("allow_multiple_processes", True))
        self.cb_allow_multiple.stateChanged.connect(self.main_window.on_allow_multiple_changed)
        self.cb_allow_multiple.setFont(QFont("Segoe UI", 13))
        self.cb_allow_multiple.setStyleSheet("""
            QCheckBox {
                color: #e5e9ff;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 6px;
                border: 2px solid #475569;
                background-color: rgba(255,107,107,0.1);
            }
            QCheckBox::indicator:checked {
                background-color: #ff6b6b;
                border-color: #ff6b6b;
            }
        """)
        self.debug_layout.addWidget(self.cb_allow_multiple)
        
        # Debug логи (в дебаг секции, под дебаг настройками)
        debug_logs_title = QLabel("Debug Logs")
        debug_logs_title.setFont(QFont("Segoe UI Semibold", 16, QFont.Bold))
        debug_logs_title.setStyleSheet(StyleSheet.label(variant="error", size="large"))
        self.debug_logs_title = debug_logs_title
        self.debug_layout.addWidget(debug_logs_title)
        debug_logs_title.setVisible(False)
        
        self.debug_logs = QTextEdit()
        self.debug_logs.setReadOnly(True)
        self.debug_logs.setStyleSheet(f"""
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
        self.debug_layout.addWidget(self.debug_logs, 1)
        self.debug_logs.setVisible(False)
        
        self.debug_card.setVisible(False)
        self._layout.addWidget(self.debug_card)
        
        # Инициализируем видимость дебаг логов
        self.main_window._update_debug_logs_visibility()
    
    def load_logs(self):
        """Загрузка логов в QTextEdit"""
        self.main_window.log_ui_manager.load_logs(self.logs)
    
    def load_debug_logs(self):
        """Загрузка дебаг логов в QTextEdit"""
        self.main_window.log_ui_manager.load_debug_logs(self.debug_logs)
    
    def update_debug_logs_visibility(self):
        """Обновляет видимость всей дебаг секции на основе настройки isDebug"""
        is_debug = self.main_window.settings.get("isDebug", False)
        # Вся дебаг секция (debug_card, debug_logs_title, debug_logs) видима только если isDebug=True
        self.debug_card.setVisible(is_debug)
        self.debug_logs_title.setVisible(is_debug)
        self.debug_logs.setVisible(is_debug)
        if is_debug:
            self.load_debug_logs()
