from typing import TYPE_CHECKING, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.pages.base_page import BasePage
from ui.design import CardWidget
from ui.design.component import Label, CheckBox, ComboBox, TextEdit, Button
from ui.styles import StyleSheet, theme
from utils.i18n import tr, get_available_languages, get_language_name, get_translator
from utils.theme_manager import get_available_themes, get_theme_name

if TYPE_CHECKING:
    from main import MainWindow




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
        # Убираем отступы из базового layout для настроек
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(16)
        self._build_ui()
    
    def _build_ui(self):
        """Построение UI страницы"""
        # Настройки
        settings_card = CardWidget()
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(20, 12, 20, 18)
        settings_layout.setSpacing(16)
        
        # Заголовок страницы (внутри карточки)
        self.lbl_settings_title = Label(tr("settings.title"), variant="default", size="xlarge")
        self.lbl_settings_title.setFont(QFont("Segoe UI Semibold", 20, QFont.Bold))
        self.lbl_settings_title.setStyleSheet(self.lbl_settings_title.styleSheet() + """
            QLabel {
                line-height: 24px;
                padding: 0px;
                margin: 0px;
            }
        """)
        self.lbl_settings_title.setFixedHeight(28)
        settings_layout.addWidget(self.lbl_settings_title)
        
        # Интервал автообновления (текст сверху, кнопки снизу)
        # Создаем виджет-контейнер вместо layout для контроля размера
        interval_widget = QWidget()
        # Убираем фон у виджета - делаем прозрачным
        interval_widget.setStyleSheet("background-color: transparent;")
        interval_container = QVBoxLayout(interval_widget)
        interval_container.setSpacing(8)
        interval_container.setContentsMargins(0, 0, 0, 0)  # Убираем лишние отступы
        
        self.interval_label = Label(tr("settings.auto_update_interval"), variant="secondary")
        self.interval_label.setFont(QFont("Segoe UI", 13))
        interval_container.addWidget(self.interval_label)
        
        # Кнопки для выбора интервала (в одну линию под текстом)
        interval_buttons_row = QHBoxLayout()
        interval_buttons_row.setSpacing(12)
        interval_buttons_row.setContentsMargins(0, 0, 0, 0)  # Убираем лишние отступы
        
        self.interval_buttons = {}
        interval_values = [30, 60, 90, 120, 180]  # Добавлен интервал 180 после 120
        current_interval = self.main_window.settings.get("auto_update_minutes", 90)
        
        for value in interval_values:
            radio = CheckBox(str(value))
            radio.setFont(QFont("Segoe UI", 12))
            radio.setChecked(value == current_interval)
            # Используем lambda с правильным захватом значения
            def make_handler(v):
                return lambda checked: self._on_interval_radio_toggled(v) if checked else None
            radio.toggled.connect(make_handler(value))
            self.interval_buttons[value] = radio
            interval_buttons_row.addWidget(radio)
        
        interval_buttons_row.addStretch()
        interval_container.addLayout(interval_buttons_row)
        # Виджет не будет растягиваться по высоте
        interval_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        settings_layout.addWidget(interval_widget)
        
        # Чекбоксы настроек (без дополнительных отступов)
        self.cb_autostart = CheckBox(tr("settings.autostart"))
        self.cb_autostart.setChecked(self.main_window.settings.get("start_with_windows", False))
        self.cb_autostart.stateChanged.connect(self.main_window.on_autostart_changed)
        self.cb_autostart.setFont(QFont("Segoe UI", 13))
        settings_layout.addWidget(self.cb_autostart)
        
        self.cb_auto_start_singbox = CheckBox(tr("settings.auto_start_singbox"))
        self.cb_auto_start_singbox.setChecked(self.main_window.settings.get("auto_start_singbox", False))
        self.cb_auto_start_singbox.stateChanged.connect(self.main_window.on_auto_start_singbox_changed)
        self.cb_auto_start_singbox.setFont(QFont("Segoe UI", 13))
        settings_layout.addWidget(self.cb_auto_start_singbox)
        
        self.cb_minimize_to_tray = CheckBox(tr("settings.minimize_to_tray"))
        self.cb_minimize_to_tray.setChecked(self.main_window.settings.get("minimize_to_tray", True))
        self.cb_minimize_to_tray.stateChanged.connect(self.main_window.on_minimize_to_tray_changed)
        self.cb_minimize_to_tray.setFont(QFont("Segoe UI", 13))
        settings_layout.addWidget(self.cb_minimize_to_tray)
        
        # Выбор языка
        language_row = QHBoxLayout()
        language_row.setSpacing(12)
        self.language_label = Label(tr("settings.language"), variant="secondary")
        self.language_label.setFont(QFont("Segoe UI", 13))
        language_row.addWidget(self.language_label)
        
        self.combo_language = ComboBox()
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
        # Убеждаемся, что комбобокс разблокирован при инициализации
        self.combo_language.setEnabled(True)
        language_row.addWidget(self.combo_language, 1)
        settings_layout.addLayout(language_row)
        
        # Выбор темы
        theme_row = QHBoxLayout()
        theme_row.setSpacing(12)
        self.theme_label = Label(tr("settings.theme"), variant="secondary")
        self.theme_label.setFont(QFont("Segoe UI", 13))
        theme_row.addWidget(self.theme_label)
        
        self.combo_theme = ComboBox()
        available_themes = get_available_themes()
        current_theme = self.main_window.settings.get("theme", "dark")
        current_language = get_translator().language
        for theme_info in available_themes:
            theme_name = get_theme_name(theme_info["id"], current_language)
            self.combo_theme.addItem(theme_name, theme_info["id"])
            if theme_info["id"] == current_theme:
                self.combo_theme.setCurrentIndex(self.combo_theme.count() - 1)
        self.combo_theme.currentIndexChanged.connect(self.main_window.on_theme_changed)
        # Убеждаемся, что комбобокс разблокирован при инициализации
        self.combo_theme.setEnabled(True)
        theme_row.addWidget(self.combo_theme, 1)
        settings_layout.addLayout(theme_row)
        
        # Кнопка "Убить" для полной остановки всех процессов (без отдельной подложки, просто кнопка)
        self.btn_kill_all = Button(tr("settings.kill_all"), variant="danger")
        self.btn_kill_all.setFont(QFont("Segoe UI", 13))
        self.btn_kill_all.clicked.connect(self.main_window.on_kill_all_clicked)
        settings_layout.addWidget(self.btn_kill_all)
        
        self._layout.addWidget(settings_card)
        
        # Кнопка для открытия окна логов
        logs_button_row = QHBoxLayout()
        logs_button_row.setSpacing(12)
        
        self.btn_open_logs = Button(tr("settings.logs"), variant="secondary")
        self.btn_open_logs.setFont(QFont("Segoe UI", 13))
        self.btn_open_logs.clicked.connect(self._open_logs_window)
        logs_button_row.addWidget(self.btn_open_logs, 1)
        
        self._layout.addLayout(logs_button_row)
        
        # Скрытые текстовые поля для хранения логов (используются окном логов)
        self.logs = TextEdit()
        self.logs.setReadOnly(True)
        self.logs.setVisible(False)  # Скрываем, так как логи теперь в отдельном окне
        
        # Дебаг логи выводятся вместе с обычными, отдельное поле не нужно
        self._logs_window = None  # Ссылка на окно логов
    
    def load_logs(self):
        """Загрузка логов в QTextEdit"""
        self.main_window.log_ui_manager.load_logs(self.logs)
    
    def _on_interval_radio_toggled(self, value: int):
        """Обработка изменения интервала через радиокнопки"""
        # Снимаем выделение с других радиокнопок
        for v, radio in self.interval_buttons.items():
            if v != value:
                radio.blockSignals(True)
                radio.setChecked(False)
                radio.blockSignals(False)
        
        # Вызываем обработчик из main_window
        if hasattr(self.main_window, 'on_interval_changed'):
            self.main_window.settings.set("auto_update_minutes", value)
            self.main_window.on_interval_changed_from_radio(value)
    
    def _open_logs_window(self, mode="logs"):
        """Открывает окно с логами"""
        try:
            # Если окно уже открыто, просто активируем его
            if self._logs_window is not None:
                self._logs_window.raise_()
                self._logs_window.activateWindow()
                if self._logs_window.isMinimized():
                    self._logs_window.showNormal()
                return
            
            # Всегда создаем новое окно при нажатии кнопки (как диалоги)
            from ui.design.component import LogsWindow
            # Создаем окно БЕЗ parent, чтобы оно было полностью независимым
            # Используем None в качестве parent, чтобы окно не было привязано к главному окну
            logs_window = LogsWindow(self.main_window, parent=None)
            
            # Переключаем режим если нужно
            if mode == "debug":
                logs_window._switch_mode("debug")
            
            # Загружаем логи перед показом
            self.load_logs()
            
            # Сохраняем ссылку ПЕРЕД показом, чтобы окно не было уничтожено
            self._logs_window = logs_window
            # Подключаем сигнал закрытия для очистки ссылки
            logs_window.finished.connect(self._on_logs_window_closed)
            
            # Устанавливаем позицию окна относительно главного окна
            main_geometry = self.main_window.geometry()
            logs_window.move(
                main_geometry.x() + (main_geometry.width() - logs_window.width()) // 2,
                main_geometry.y() + (main_geometry.height() - logs_window.height()) // 2
            )
            
            # Показываем окно (немодальное) - используем show() как для обычных окон
            # Убеждаемся, что окно видимо и активировано
            logs_window.setAttribute(Qt.WA_ShowWithoutActivating, False)
            logs_window.show()
            
            # Обрабатываем события, чтобы окно успело отобразиться
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            logs_window.raise_()
            logs_window.activateWindow()
            # Дополнительно убеждаемся, что окно на переднем плане
            if logs_window.isMinimized():
                logs_window.showNormal()
            logs_window.setFocus()
            
            # Принудительно обновляем окно
            logs_window.update()
            QApplication.processEvents()
        except Exception as e:
            # В случае ошибки выводим в консоль для отладки
            import traceback
            import sys
            print(f"Error opening logs window: {e}", file=sys.stderr)
            traceback.print_exc()
            # Очищаем ссылку в случае ошибки
            self._logs_window = None
    
    def _on_logs_window_closed(self):
        """Обработчик закрытия окна логов"""
        self._logs_window = None