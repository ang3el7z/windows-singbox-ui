from typing import TYPE_CHECKING, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QCheckBox, QComboBox, QTextEdit, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.pages.base_page import BasePage
from ui.widgets import CardWidget
from ui.styles import StyleSheet, theme
from utils.i18n import tr, get_available_languages, get_language_name, get_translator
from utils.theme_manager import get_available_themes, get_theme_name

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
        # Не устанавливаем отступы в основном layout, как в ProfilePage
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build_ui()
    
    def _build_ui(self):
        """Построение UI страницы"""
        # Настройки
        settings_card = CardWidget()
        settings_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(20, 18, 20, 18)
        settings_layout.setSpacing(16)
        
        # Заголовок страницы
        self.settings_title = QLabel(tr("settings.title"))
        self.settings_title.setFont(QFont("Segoe UI Semibold", 16, QFont.Bold))
        self.settings_title.setStyleSheet(StyleSheet.label(variant="default", size="large"))
        settings_layout.addWidget(self.settings_title)
        
        # Регистрируем для адаптивного масштабирования
        if hasattr(self.main_window, 'responsive_scaler'):
            self.main_window.responsive_scaler.register_widget(
                self.settings_title, base_font_size=16
            )
        
        # Интервал автообновления (по образцу языка)
        interval_row = QHBoxLayout()
        interval_row.setSpacing(12)
        self.interval_label = QLabel(tr("settings.auto_update_interval"))
        self.interval_label.setFont(QFont("Segoe UI", 13))
        self.interval_label.setStyleSheet(StyleSheet.label(variant="secondary"))
        self.interval_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        interval_row.addWidget(self.interval_label)
        
        # Регистрируем для адаптивного масштабирования
        if hasattr(self.main_window, 'responsive_scaler'):
            self.main_window.responsive_scaler.register_widget(self.interval_label, base_font_size=13)
        
        self.edit_interval = QLineEdit()
        self.edit_interval.setText(str(self.main_window.settings.get("auto_update_minutes", 90)))
        self.edit_interval.setPlaceholderText("90")
        self.edit_interval.editingFinished.connect(self.main_window.on_interval_changed)
        self.edit_interval.setStyleSheet(StyleSheet.combo_box())  # Используем стиль комбобокса для единообразия
        self.edit_interval.setMinimumWidth(120)
        interval_row.addWidget(self.edit_interval, 1)
        settings_layout.addLayout(interval_row)
        
        # Чекбоксы настроек
        self.cb_autostart = QCheckBox(tr("settings.autostart"))
        self.cb_autostart.setChecked(self.main_window.settings.get("start_with_windows", False))
        self.cb_autostart.stateChanged.connect(self.main_window.on_autostart_changed)
        self.cb_autostart.setFont(QFont("Segoe UI", 13))
        self.cb_autostart.setStyleSheet(StyleSheet.checkbox())
        settings_layout.addWidget(self.cb_autostart)
        
        # Регистрируем для адаптивного масштабирования
        if hasattr(self.main_window, 'responsive_scaler'):
            self.main_window.responsive_scaler.register_widget(self.cb_autostart, base_font_size=13)
        
        self.cb_run_as_admin = QCheckBox(tr("settings.run_as_admin"))
        self.cb_run_as_admin.setChecked(self.main_window.settings.get("run_as_admin", False))
        self.cb_run_as_admin.stateChanged.connect(self.main_window.on_run_as_admin_changed)
        self.cb_run_as_admin.setFont(QFont("Segoe UI", 13))
        self.cb_run_as_admin.setStyleSheet(StyleSheet.checkbox())
        settings_layout.addWidget(self.cb_run_as_admin)
        
        # Регистрируем для адаптивного масштабирования
        if hasattr(self.main_window, 'responsive_scaler'):
            self.main_window.responsive_scaler.register_widget(self.cb_run_as_admin, base_font_size=13)
        
        self.cb_auto_start_singbox = QCheckBox(tr("settings.auto_start_singbox"))
        self.cb_auto_start_singbox.setChecked(self.main_window.settings.get("auto_start_singbox", False))
        self.cb_auto_start_singbox.stateChanged.connect(self.main_window.on_auto_start_singbox_changed)
        self.cb_auto_start_singbox.setFont(QFont("Segoe UI", 13))
        self.cb_auto_start_singbox.setStyleSheet(StyleSheet.checkbox())
        settings_layout.addWidget(self.cb_auto_start_singbox)
        
        # Регистрируем для адаптивного масштабирования
        if hasattr(self.main_window, 'responsive_scaler'):
            self.main_window.responsive_scaler.register_widget(self.cb_auto_start_singbox, base_font_size=13)
        
        self.cb_minimize_to_tray = QCheckBox(tr("settings.minimize_to_tray"))
        self.cb_minimize_to_tray.setChecked(self.main_window.settings.get("minimize_to_tray", True))
        self.cb_minimize_to_tray.stateChanged.connect(self.main_window.on_minimize_to_tray_changed)
        self.cb_minimize_to_tray.setFont(QFont("Segoe UI", 13))
        self.cb_minimize_to_tray.setStyleSheet(StyleSheet.checkbox())
        settings_layout.addWidget(self.cb_minimize_to_tray)
        
        # Регистрируем для адаптивного масштабирования
        if hasattr(self.main_window, 'responsive_scaler'):
            self.main_window.responsive_scaler.register_widget(self.cb_minimize_to_tray, base_font_size=13)
        
        # Дебаг настройка (появляется только в дебаг режиме)
        self.cb_allow_multiple = QCheckBox(tr("settings.allow_multiple_processes"))
        self.cb_allow_multiple.setChecked(self.main_window.settings.get("allow_multiple_processes", True))
        self.cb_allow_multiple.stateChanged.connect(self.main_window.on_allow_multiple_changed)
        self.cb_allow_multiple.setFont(QFont("Segoe UI", 13))
        self.cb_allow_multiple.setStyleSheet(f"""
            QCheckBox {{
                color: {theme.get_color('error')};
                background-color: transparent;
                border: none;
                padding: 0px;
            }}
            QCheckBox::indicator {{
                width: 22px;
                height: 22px;
                border-radius: 6px;
                border: 2px solid {theme.get_color('error')};
                background-color: rgba(255,107,107,0.1);
            }}
            QCheckBox::indicator:checked {{
                background-color: {theme.get_color('error')};
                border-color: {theme.get_color('error')};
            }}
        """)
        self.cb_allow_multiple.setVisible(False)  # Скрыта по умолчанию
        settings_layout.addWidget(self.cb_allow_multiple)
        
        # Выбор языка
        language_row = QHBoxLayout()
        language_row.setSpacing(12)
        self.language_label = QLabel(tr("settings.language"))
        self.language_label.setFont(QFont("Segoe UI", 13))
        self.language_label.setStyleSheet(StyleSheet.label(variant="secondary"))
        self.language_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        language_row.addWidget(self.language_label)
        
        # Регистрируем для адаптивного масштабирования
        if hasattr(self.main_window, 'responsive_scaler'):
            self.main_window.responsive_scaler.register_widget(self.language_label, base_font_size=13)
        
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
        self.combo_language.setMinimumWidth(120)
        language_row.addWidget(self.combo_language, 1)
        settings_layout.addLayout(language_row)
        
        # Выбор темы
        theme_row = QHBoxLayout()
        theme_row.setSpacing(12)
        self.theme_label = QLabel(tr("settings.theme"))
        self.theme_label.setFont(QFont("Segoe UI", 13))
        self.theme_label.setStyleSheet(StyleSheet.label(variant="secondary"))
        self.theme_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        theme_row.addWidget(self.theme_label)
        
        # Регистрируем для адаптивного масштабирования
        if hasattr(self.main_window, 'responsive_scaler'):
            self.main_window.responsive_scaler.register_widget(self.theme_label, base_font_size=13)
        
        self.combo_theme = QComboBox()
        available_themes = get_available_themes()
        current_theme = self.main_window.settings.get("theme", "dark")
        current_language = get_translator().language
        for theme_info in available_themes:
            theme_name = get_theme_name(theme_info["id"], current_language)
            self.combo_theme.addItem(theme_name, theme_info["id"])
            if theme_info["id"] == current_theme:
                self.combo_theme.setCurrentIndex(self.combo_theme.count() - 1)
        self.combo_theme.currentIndexChanged.connect(self.main_window.on_theme_changed)
        self.combo_theme.setStyleSheet(StyleSheet.combo_box())
        self.combo_theme.setMinimumWidth(120)
        theme_row.addWidget(self.combo_theme, 1)
        settings_layout.addLayout(theme_row)
        
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
        
        # Кнопка для открытия окна логов
        logs_button_row = QHBoxLayout()
        logs_button_row.setSpacing(12)
        
        self.btn_open_logs = QPushButton(tr("settings.logs"))
        self.btn_open_logs.setFont(QFont("Segoe UI", 13))
        self.btn_open_logs.setCursor(Qt.PointingHandCursor)
        self.btn_open_logs.clicked.connect(self._open_logs_window)
        self.btn_open_logs.setStyleSheet(f"""
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
        logs_button_row.addWidget(self.btn_open_logs, 1)
        
        self._layout.addLayout(logs_button_row)
        
        # Скрытые текстовые поля для хранения логов (используются окном логов)
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setVisible(False)  # Скрываем, так как логи теперь в отдельном окне
        
        self.debug_logs = QTextEdit()
        self.debug_logs.setReadOnly(True)
        self.debug_logs.setVisible(False)  # Скрываем, так как логи теперь в отдельном окне
        
        # Дебаг логи теперь в отдельном окне, здесь только скрытое поле для хранения
        self._logs_window = None  # Ссылка на окно логов
        
        # Инициализируем видимость дебаг элементов
        self.update_debug_logs_visibility()
    
    def load_logs(self):
        """Загрузка логов в QTextEdit"""
        self.main_window.log_ui_manager.load_logs(self.logs)
    
    def load_debug_logs(self):
        """Загрузка дебаг логов в QTextEdit"""
        self.main_window.log_ui_manager.load_debug_logs(self.debug_logs)
    
    def update_debug_logs_visibility(self):
        """Обновляет видимость дебаг элементов на основе настройки isDebug"""
        is_debug = self.main_window.settings.get("isDebug", False)
        # Показываем/скрываем дебаг настройку в обычных настройках
        if hasattr(self, 'cb_allow_multiple'):
            self.cb_allow_multiple.setVisible(is_debug)
        if is_debug:
            self.load_debug_logs()
    
    def _open_logs_window(self, mode="logs"):
        """Открывает окно с логами"""
        if not hasattr(self, '_logs_window') or self._logs_window is None:
            from ui.widgets.logs_window import LogsWindow
            self._logs_window = LogsWindow(self.main_window, self)
            self._logs_window.finished.connect(lambda: setattr(self, '_logs_window', None))
        
        # Переключаем режим если нужно
        if mode == "debug":
            self._logs_window._switch_mode("debug")
        
        # Загружаем логи перед показом
        self.load_logs()
        if hasattr(self, 'debug_logs'):
            self.load_debug_logs()
        
        self._logs_window.show()
        self._logs_window.raise_()
        self._logs_window.activateWindow()
