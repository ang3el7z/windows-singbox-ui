"""Все вариации диалогов - используют BaseDialog из design"""
from enum import Enum
from typing import Optional, Tuple, Callable, Dict, Any
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QProgressBar, QFileDialog, QVBoxLayout
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont
from ui.styles import StyleSheet, theme
from ui.design.base.base_dialog import BaseDialog
from ui.design.component.button import Button
from ui.design.component.label import Label
from ui.design.component.line_edit import LineEdit
from ui.design.component.progress_bar import ProgressBar
from ui.design.component.combo_box import ComboBox
from utils.i18n import tr, get_available_languages, get_language_name
from config.paths import SOURCE_RESOURCES_DIR
import json
import sys
import base64
from pathlib import Path

# Импортируем ресурсы Qt
try:
    import scripts.resources_rc  # noqa: F401 - для регистрации Qt ресурсов
except ImportError:
    pass


def get_ace_editor_content(filename: str) -> str:
    """Получает содержимое файла Ace Editor из Qt ресурсов или файловой системы"""
    from PyQt5.QtCore import QFile
    
    # Пытаемся загрузить из Qt ресурсов (qrc://web/ace/filename)
    resource_path = f":/web/ace/{filename}"
    qfile = QFile(resource_path)
    
    if qfile.exists():
        if qfile.open(QFile.ReadOnly | QFile.Text):
            content = qfile.readAll().data().decode('utf-8')
            qfile.close()
            return content
    
    # Fallback: загружаем из файловой системы (для разработки)
    source_ace_file = SOURCE_RESOURCES_DIR / "web" / "ace" / filename
    if source_ace_file.exists():
        try:
            with source_ace_file.open('r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            pass
    
    # Если не найдено, возвращаем пустую строку (приложение должно работать, но без Ace Editor)
    return ""


class DialogType(Enum):
    """Типы диалогов"""
    INFO = "info"  # Информационный (одна кнопка OK)
    CONFIRM = "confirm"  # Подтверждение (Yes/No)
    WARNING = "warning"  # Предупреждение (Yes/No с красной кнопкой)
    SUCCESS = "success"  # Успех (одна кнопка OK зеленого цвета)


def _create_dialog(
    parent,
    title: str,
    message: str,
    dialog_type: DialogType = DialogType.INFO,
    min_width: int = 400,
    yes_text: Optional[str] = None,
    no_text: Optional[str] = None,
    ok_text: Optional[str] = None
) -> BaseDialog:
    """
    Создает универсальный диалог используя BaseDialog из design
    
    Args:
        parent: Родительский виджет
        title: Заголовок диалога (отображается в TitleBar)
        message: Сообщение
        dialog_type: Тип диалога
        min_width: Минимальная ширина
        yes_text: Текст кнопки Yes (для confirm/warning)
        no_text: Текст кнопки No (для confirm/warning)
        ok_text: Текст кнопки OK (для info/success)
    
    Returns:
        Созданный диалог (BaseDialog из design)
    """
    # Используем BaseDialog из design (использует дизайн-систему)
    dialog = BaseDialog(parent, title)
    dialog.setMinimumWidth(min_width)
    
    # Сообщение (заголовок уже в TitleBar)
    message_label = Label(message, variant="secondary")
    message_label.setWordWrap(True)
    message_label.setFont(QFont("Segoe UI", 13))
    message_label.setStyleSheet(message_label.styleSheet() + "margin-bottom: 8px;")
    dialog.content_layout.addWidget(message_label)
    
    # Кнопки (используем компоненты из дизайн-системы)
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(12)
    
    if dialog_type in (DialogType.CONFIRM, DialogType.WARNING):
        # Кнопки: отмена слева, согласие справа
        btn_no = Button(no_text or tr("download.cancel"), variant="default")
        btn_no.setObjectName("btnNo")
        btn_no.setStyleSheet(StyleSheet.dialog_button(variant="cancel"))
        btn_no.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_no)
        
        # Растяжка между кнопками
        btn_layout.addStretch()
        
        # Кнопка согласия справа
        yes_btn_text = yes_text or (tr("messages.kill_all_yes") if dialog_type == DialogType.WARNING else tr("messages.restart_yes"))
        btn_yes = Button(yes_btn_text, variant="default")
        btn_yes.setObjectName("btnYes")
        btn_yes.setDefault(True)
        if dialog_type == DialogType.WARNING:
            btn_yes.setStyleSheet(StyleSheet.dialog_button(variant="warning"))
        else:
            btn_yes.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
        btn_yes.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_yes)
    else:
        # Кнопка OK (справа)
        btn_ok = Button(ok_text or tr("messages.ok"), variant="default")
        btn_ok.setDefault(True)
        if dialog_type == DialogType.SUCCESS:
            btn_ok.setStyleSheet(StyleSheet.dialog_button(variant="success"))
        else:
            btn_ok.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
        btn_ok.clicked.connect(dialog.accept)
        # Добавляем растяжку слева, чтобы кнопка была справа
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
    
    dialog.content_layout.addLayout(btn_layout)
    
    return dialog


def show_info_dialog(
    parent: QWidget,
    title: str,
    message: str,
    ok_text: Optional[str] = None,
    success: bool = False
) -> bool:
    """
    Показывает информационный диалог
    
    Args:
        parent: Родительский виджет
        title: Заголовок
        message: Сообщение
        ok_text: Текст кнопки OK
        success: Если True, использует зеленую кнопку (для успешных действий)
    
    Returns:
        True если пользователь нажал OK
    """
    dialog_type = DialogType.SUCCESS if success else DialogType.INFO
    dialog = _create_dialog(parent, title, message, dialog_type, ok_text=ok_text or tr("messages.ok"))
    return dialog.exec_() == BaseDialog.Accepted


def show_confirm_dialog(
    parent: QWidget,
    title: str,
    message: str,
    yes_text: Optional[str] = None,
    no_text: Optional[str] = None,
    warning: bool = False
) -> bool:
    """
    Показывает диалог подтверждения
    
    Args:
        parent: Родительский виджет
        title: Заголовок
        message: Сообщение
        yes_text: Текст кнопки Yes
        no_text: Текст кнопки No
        warning: Если True, использует красную кнопку (для опасных действий)
    
    Returns:
        True если пользователь нажал Yes
    """
    dialog_type = DialogType.WARNING if warning else DialogType.CONFIRM
    dialog = _create_dialog(parent, title, message, dialog_type, yes_text=yes_text, no_text=no_text)
    return dialog.exec_() == BaseDialog.Accepted


def show_input_dialog(
    parent: QWidget,
    title: str,
    message: str,
    text: str = "",
    min_width: int = 400
) -> Tuple[str, bool]:
    """
    Показывает диалог ввода текста
    
    Args:
        parent: Родительский виджет
        title: Заголовок диалога (отображается в TitleBar)
        message: Сообщение/подсказка
        text: Начальный текст
        min_width: Минимальная ширина диалога
    
    Returns:
        Кортеж (введенный текст, был ли нажат OK)
    """
    # Используем BaseDialog из design (использует дизайн-систему)
    dialog = BaseDialog(parent, title)
    dialog.setMinimumWidth(min_width)
    
    # Сообщение (заголовок уже в TitleBar)
    message_label = Label(message, variant="secondary")
    message_label.setWordWrap(True)
    message_label.setFont(QFont("Segoe UI", 13))
    message_label.setStyleSheet(message_label.styleSheet() + "margin-bottom: 8px;")
    dialog.content_layout.addWidget(message_label)
    
    # Поле ввода (использует компоненты из дизайн-системы)
    input_field = LineEdit()
    input_field.setText(text)
    input_field.selectAll()
    input_field.setMinimumHeight(40)
    dialog.content_layout.addWidget(input_field)
    
    # Кнопки (используют компоненты из дизайн-системы)
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(12)
    
    btn_cancel = Button(tr("download.cancel"), variant="default")
    btn_cancel.setStyleSheet(StyleSheet.dialog_button(variant="cancel"))
    btn_cancel.clicked.connect(dialog.reject)
    btn_layout.addWidget(btn_cancel)
    
    btn_layout.addStretch()
    
    btn_ok = Button(tr("messages.ok"), variant="default")
    btn_ok.setDefault(True)
    btn_ok.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
    btn_ok.clicked.connect(dialog.accept)
    btn_layout.addWidget(btn_ok)
    
    dialog.content_layout.addLayout(btn_layout)
    
    input_field.setFocus()
    
    def on_enter():
        if input_field.text().strip():
            dialog.accept()
    
    input_field.returnPressed.connect(on_enter)
    
    result = dialog.exec_()
    if result == BaseDialog.Accepted:
        return input_field.text().strip(), True
    return "", False


def show_language_selection_dialog(parent: Optional[QWidget] = None) -> str:
    """
    Диалог выбора языка при первом запуске
    
    Args:
        parent: Родительский виджет
    
    Returns:
        Код выбранного языка
    """
    dialog = BaseDialog(parent, tr("language_dialog.title"))
    dialog.setMinimumWidth(400)
    
    # Добавляем стили для кнопок языков
    dialog.setStyleSheet(dialog.styleSheet() + f"""
        QPushButton {{
            border: 2px solid {theme.get_color('accent')};
            background-color: transparent;
            color: {theme.get_color('accent')};
            margin: 4px;
        }}
        QPushButton:hover {{
            background-color: {theme.get_color('accent_light')};
        }}
        QPushButton:default {{
            background-color: {theme.get_color('accent')};
            color: {theme.get_color('background_primary')};
        }}
    """)
    
    # Убираем дублирование заголовка - он уже в TitleBar
    
    available_languages = get_available_languages()
    selected_language = ["en"]
    
    def select_language(lang_code: str) -> None:
        selected_language[0] = lang_code
        dialog.accept()
    
    for lang_code in available_languages:
        lang_name = get_language_name(lang_code)
        btn = Button(lang_name, variant="default")
        btn.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {theme.get_color('accent')};
                background-color: transparent;
                color: {theme.get_color('accent')};
                margin: 4px;
            }}
            QPushButton:hover {{
                background-color: {theme.get_color('accent_light')};
            }}
            QPushButton:default {{
                background-color: {theme.get_color('accent')};
                color: {theme.get_color('background_primary')};
            }}
        """)
        btn.clicked.connect(lambda checked, l=lang_code: select_language(l))
        dialog.content_layout.addWidget(btn)
    
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    btn_ok = Button(tr("language_dialog.ok"), variant="default")
    btn_ok.setDefault(True)
    btn_ok.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
    btn_ok.clicked.connect(dialog.accept)
    btn_layout.addWidget(btn_ok)
    dialog.content_layout.addLayout(btn_layout)
    
    if dialog.exec_() == BaseDialog.Accepted:
        return selected_language[0]
    return "en"


def show_add_profile_dialog(parent: QWidget) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]], Optional[str], bool]:
    """
    Показывает диалог добавления профиля с выбором типа (подписка или конфиг)
    Для конфига используется Ace Editor для вставки содержимого
    
    Args:
        parent: Родительский виджет
    
    Returns:
        Кортеж (name, url, config, profile_type, был ли нажат OK)
        Для подписки: (name, url, None, "subscription", ok)
        Для конфига: (name, None, config_dict, "config", ok)
    """
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        HAS_WEBENGINE = True
    except ImportError:
        HAS_WEBENGINE = False
        from PyQt5.QtWidgets import QTextEdit
    
    dialog = BaseDialog(parent, tr("profile.add_profile_dialog_title"))
    dialog.setMinimumWidth(600)
    dialog.setMinimumHeight(500)
    
    dialog.setStyleSheet(dialog.styleSheet() + StyleSheet.input())
    
    # Тип профиля
    type_label = Label(tr("profile.type"), variant="default", size="medium")
    type_label.setStyleSheet(type_label.styleSheet() + "margin-top: 8px;")
    dialog.content_layout.addWidget(type_label)
    
    type_combo = ComboBox()
    type_combo.addItem(tr("profile.type_subscription"), "subscription")
    type_combo.addItem(tr("profile.type_config"), "config")
    dialog.content_layout.addWidget(type_combo)
    
    # Название
    name_label = Label(tr("profile.name"), variant="default", size="medium")
    name_label.setStyleSheet(name_label.styleSheet() + "margin-top: 8px;")
    dialog.content_layout.addWidget(name_label)
    
    name_input = LineEdit()
    name_input.setPlaceholderText(tr("profile.name"))
    dialog.content_layout.addWidget(name_input)
    
    # URL (для подписки)
    url_label = Label(tr("profile.url"), variant="default", size="medium")
    url_label.setStyleSheet(url_label.styleSheet() + "margin-top: 8px;")
    dialog.content_layout.addWidget(url_label)
    
    url_input = LineEdit()
    url_input.setPlaceholderText("https://...")
    dialog.content_layout.addWidget(url_input)
    
    # Редактор конфига (для config типа)
    config_label = Label(tr("profile.config_content"), variant="default", size="medium")
    config_label.setStyleSheet(config_label.styleSheet() + "margin-top: 8px;")
    dialog.content_layout.addWidget(config_label)
    
    # Контейнер для редактора конфига
    config_container = QWidget()
    config_layout = QVBoxLayout(config_container)
    config_layout.setContentsMargins(0, 0, 0, 0)
    config_layout.setSpacing(0)
    
    editor_content = {"value": ""}
    
    if HAS_WEBENGINE:
        config_editor = QWebEngineView()
        config_editor.setMinimumHeight(300)
        
        # Пустой JSON для начала
        initial_json = "{\n  \n}"
        editor_content["value"] = initial_json
        config_json_escaped = json.dumps(initial_json)
        
        # Получаем содержимое файлов Ace Editor из Qt ресурсов
        ace_js_content = get_ace_editor_content("ace.js")
        mode_json5_content = get_ace_editor_content("mode-json5.js")
        theme_monokai_content = get_ace_editor_content("theme-monokai.js")
        worker_json_content = get_ace_editor_content("worker-json.js")
        ext_language_tools_content = get_ace_editor_content("ext-language_tools.js")
        
        # Экранируем JS код для вставки в HTML (заменяем </script> на <\/script>)
        def escape_js_for_html(js_code: str) -> str:
            return js_code.replace("</script>", "<\\/script>")
        
        # Создаем data URL для worker (Ace Editor требует URL для worker)
        worker_data_url = ""
        if worker_json_content:
            worker_json_encoded = base64.b64encode(worker_json_content.encode('utf-8')).decode('utf-8')
            worker_data_url = f"data:text/javascript;base64,{worker_json_encoded}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Ace Editor</title>
            <script type="text/javascript">{escape_js_for_html(ace_js_content)}</script>
            <script type="text/javascript">{escape_js_for_html(mode_json5_content)}</script>
            <script type="text/javascript">{escape_js_for_html(theme_monokai_content)}</script>
            <script type="text/javascript">{escape_js_for_html(ext_language_tools_content)}</script>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: {theme.get_color('background_primary')};
                    color: {theme.get_color('text_primary')};
                }}
                #editor {{
                    width: 100%;
                    height: 100%;
                }}
            </style>
        </head>
        <body>
            <div id="editor"></div>
            <script>
                var editor = ace.edit("editor");
                editor.setTheme("ace/theme/monokai");
                editor.session.setMode("ace/mode/json5");
                editor.setValue({config_json_escaped});
                editor.setOptions({{
                    fontSize: 14,
                    tabSize: 2,
                    useSoftTabs: true,
                    wrap: true,
                    enableBasicAutocompletion: true,
                    enableSnippets: true,
                    enableLiveAutocompletion: true
                }});
                
                // Настраиваем воркер для валидации JSON
                editor.session.setUseWorker(true);
                editor.session.setWorkerUrl("{worker_data_url}");
                
                editor.on("change", function() {{
                    window.editorValue = editor.getValue();
                }});
                
                window.editorValue = editor.getValue();
                
                window.getEditorValue = function() {{
                    return window.editorValue || editor.getValue();
                }};
            </script>
        </body>
        </html>
        """
        
        config_editor.setHtml(html_content)
        config_layout.addWidget(config_editor)
    else:
        config_editor = QTextEdit()
        config_editor.setMinimumHeight(300)
        config_editor.setPlainText("{\n  \n}")
        config_editor.setFont(QFont("Consolas", 10))
        config_layout.addWidget(config_editor)
    
    config_container.setLayout(config_layout)
    dialog.content_layout.addWidget(config_container, 1)
    
    def get_config_content():
        if HAS_WEBENGINE:
            result_container = {"value": None, "ready": False}
            
            def callback(value):
                result_container["value"] = value
                result_container["ready"] = True
            
            config_editor.page().runJavaScript("window.getEditorValue()", callback)
            
            from PyQt5.QtCore import QTimer, QEventLoop
            loop = QEventLoop()
            timer = QTimer()
            timer.timeout.connect(loop.quit)
            timer.setSingleShot(True)
            timer.start(1000)
            
            check_timer = QTimer()
            def check_ready():
                if result_container["ready"]:
                    loop.quit()
            check_timer.timeout.connect(check_ready)
            check_timer.start(50)
            
            loop.exec_()
            timer.stop()
            check_timer.stop()
            
            if result_container["value"] is not None:
                editor_content["value"] = result_container["value"]
                return result_container["value"]
            return editor_content["value"] if editor_content["value"] else ""
        else:
            text = config_editor.toPlainText()
            editor_content["value"] = text
            return text
    
    def on_type_changed(index: int):
        """Обработка изменения типа профиля"""
        profile_type = type_combo.itemData(index)
        if profile_type == "subscription":
            url_label.show()
            url_input.show()
            config_label.hide()
            config_container.hide()
        else:  # config
            url_label.hide()
            url_input.hide()
            config_label.show()
            config_container.show()
    
    type_combo.currentIndexChanged.connect(on_type_changed)
    
    # Инициализация: показываем поля для подписки
    on_type_changed(0)
    
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(12)
    
    btn_cancel = Button(tr("download.cancel"), variant="default")
    btn_cancel.setStyleSheet(StyleSheet.dialog_button(variant="cancel"))
    btn_cancel.clicked.connect(dialog.reject)
    btn_layout.addWidget(btn_cancel)
    
    btn_layout.addStretch()
    
    btn_add = Button(tr("profile.add"), variant="default")
    btn_add.setDefault(True)
    btn_add.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
    
    def on_add_clicked():
        name = name_input.text().strip()
        profile_type = type_combo.currentData()
        
        if not name:
            show_info_dialog(dialog, tr("profile.add_profile_dialog_title"), tr("profile.fill_all_fields"))
            return
        
        if profile_type == "subscription":
            url = url_input.text().strip()
            if not url:
                show_info_dialog(dialog, tr("profile.add_profile_dialog_title"), tr("profile.fill_all_fields"))
                return
            dialog.accept()
        else:  # config
            try:
                config_text = get_config_content()
                if not config_text or config_text.strip() == "" or config_text.strip() == "{}":
                    show_info_dialog(dialog, tr("profile.add_profile_dialog_title"), tr("profile.load_config_first"))
                    return
                # Парсим JSON5/JSON
                try:
                    import json5
                    config_data = json5.loads(config_text)
                except ImportError:
                    config_data = json.loads(config_text)
                dialog._config_data = config_data
                dialog.accept()
            except Exception as e:
                show_info_dialog(dialog, tr("profile.add_profile_dialog_title"), tr("profile.invalid_json") + f": {str(e)}")
    
    btn_add.clicked.connect(on_add_clicked)
    btn_layout.addWidget(btn_add)
    
    dialog.content_layout.addLayout(btn_layout)
    
    name_input.setFocus()
    
    result = dialog.exec_()
    if result == BaseDialog.Accepted:
        name = name_input.text().strip()
        profile_type = type_combo.currentData()
        
        if profile_type == "subscription":
            url = url_input.text().strip()
            if name and url:
                return name, url, None, "subscription", True
        else:  # config
            config = getattr(dialog, '_config_data', None)
            if not config:
                try:
                    config_text = get_config_content()
                    if config_text:
                        try:
                            import json5
                            config = json5.loads(config_text)
                        except ImportError:
                            config = json.loads(config_text)
                except:
                    pass
            if name and config:
                return name, None, config, "config", True
    
    return None, None, None, None, False


def show_add_subscription_dialog(parent: QWidget) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Показывает диалог добавления подписки (для обратной совместимости)
    
    Args:
        parent: Родительский виджет
    
    Returns:
        Кортеж (name, url, был ли нажат OK)
    """
    name, url, _, profile_type, ok = show_add_profile_dialog(parent)
    if ok and profile_type == "subscription":
        return name, url, True
    return None, None, False


class DownloadDialog(BaseDialog):
    """Диалог загрузки SingBox с прогресс-баром"""
    
    def __init__(self, parent: QWidget, on_download_callback: Callable[['DownloadDialog'], None], message: str = None):
        """
        Инициализация диалога загрузки
        
        Args:
            parent: Родительский виджет
            on_download_callback: Функция-коллбэк для запуска загрузки (принимает dialog)
            message: Кастомное сообщение (если None, используется стандартное)
        """
        super().__init__(parent, tr("download.title"))
        self.on_download_callback = on_download_callback
        self.download_thread = None
        
        self.setMinimumWidth(400)
        self.setStyleSheet(self.styleSheet() + StyleSheet.progress_bar())
        self.content_layout.setSpacing(16)
        
        # Убираем дублирование заголовка - он уже в TitleBar
        info_text = message if message else tr("download.description")
        info = Label(info_text, variant="secondary", size="medium")
        info.setWordWrap(True)
        self.content_layout.addWidget(info)
        
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.content_layout.addWidget(self.progress_bar)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.btn_cancel = Button(tr("download.cancel"), variant="default")
        self.btn_cancel.setStyleSheet(StyleSheet.dialog_button(variant="cancel"))
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        btn_layout.addStretch()
        
        self.btn_download = Button(tr("download.download"), variant="default")
        self.btn_download.setDefault(True)
        self.btn_download.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
        self.btn_download.clicked.connect(self._on_download_clicked)
        btn_layout.addWidget(self.btn_download)
        
        self.content_layout.addLayout(btn_layout)
    
    def _on_download_clicked(self):
        """Обработка нажатия кнопки загрузки"""
        self.btn_download.setEnabled(False)
        self.btn_download.setText(tr("download.downloading"))
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.on_download_callback(self)
    
    def on_download_finished(self, success: bool, message: str):
        """Обработка завершения загрузки"""
        self.progress_bar.hide()
        if success:
            show_info_dialog(self, tr("download.success"), message, success=True)
            self.accept()
        else:
            show_info_dialog(self, tr("download.error"), message)
            self.btn_download.setEnabled(True)
            self.btn_download.setText(tr("download.download"))


def show_kill_all_confirm_dialog(parent: QWidget, title: str, message: str) -> bool:
    """Диалог для подтверждения остановки всех процессов"""
    return show_confirm_dialog(
        parent, title, message,
        yes_text=tr("messages.kill_all_yes"),
        no_text=tr("download.cancel"),
        warning=True
    )


def show_kill_all_success_dialog(parent: QWidget, title: str, message: str) -> bool:
    """Диалог для уведомления об успешной остановке процессов"""
    return show_info_dialog(parent, title, message, success=True)


def show_edit_profile_dialog(parent: QWidget, profile: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]], Optional[str], bool]:
    """
    Показывает диалог редактирования профиля
    
    Args:
        parent: Родительский виджет
        profile: Словарь с данными профиля (name, type, url или config)
    
    Returns:
        Кортеж (name, url, config, profile_type, был ли нажат OK)
        Для подписки: (name, url, None, "subscription", ok)
        Для конфига: (name, None, config_dict, "config", ok)
    """
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        from PyQt5.QtCore import QUrl
        HAS_WEBENGINE = True
    except ImportError:
        HAS_WEBENGINE = False
        # Fallback на QTextEdit если WebEngine недоступен
        from PyQt5.QtWidgets import QTextEdit
    
    from managers.subscriptions import SubscriptionManager
    
    dialog = BaseDialog(parent, tr("profile.edit_profile_dialog_title"))
    dialog.setMinimumWidth(600)
    dialog.setMinimumHeight(500)
    
    dialog.setStyleSheet(dialog.styleSheet() + StyleSheet.input())
    
    # Тип профиля
    type_label = Label(tr("profile.type"), variant="default", size="medium")
    type_label.setStyleSheet(type_label.styleSheet() + "margin-top: 8px;")
    dialog.content_layout.addWidget(type_label)
    
    type_combo = ComboBox()
    type_combo.addItem(tr("profile.type_subscription"), "subscription")
    type_combo.addItem(tr("profile.type_config"), "config")
    
    # Устанавливаем текущий тип
    current_type = profile.get("type", SubscriptionManager.PROFILE_TYPE_SUBSCRIPTION)
    if current_type == SubscriptionManager.PROFILE_TYPE_SUBSCRIPTION:
        type_combo.setCurrentIndex(0)
    else:
        type_combo.setCurrentIndex(1)
    
    dialog.content_layout.addWidget(type_combo)
    
    # Название
    name_label = Label(tr("profile.name"), variant="default", size="medium")
    name_label.setStyleSheet(name_label.styleSheet() + "margin-top: 8px;")
    dialog.content_layout.addWidget(name_label)
    
    name_input = LineEdit()
    name_input.setText(profile.get("name", ""))
    dialog.content_layout.addWidget(name_input)
    
    # URL (для подписки)
    url_label = Label(tr("profile.url"), variant="default", size="medium")
    url_label.setStyleSheet(url_label.styleSheet() + "margin-top: 8px;")
    dialog.content_layout.addWidget(url_label)
    
    url_input = LineEdit()
    url_input.setText(profile.get("url", ""))
    url_input.setPlaceholderText("https://...")
    dialog.content_layout.addWidget(url_input)
    
    # Редактор конфига (для config типа)
    config_label = Label(tr("profile.config_content"), variant="default", size="medium")
    config_label.setStyleSheet(config_label.styleSheet() + "margin-top: 8px;")
    dialog.content_layout.addWidget(config_label)
    
    # Контейнер для редактора конфига
    config_container = QWidget()
    config_layout = QVBoxLayout(config_container)
    config_layout.setContentsMargins(0, 0, 0, 0)
    config_layout.setSpacing(0)
    
    # Переменная для хранения содержимого редактора
    editor_content = {"value": ""}
    
    if HAS_WEBENGINE:
        # Используем Ace Editor через QWebEngineView
        config_editor = QWebEngineView()
        config_editor.setMinimumHeight(300)
        
        # Получаем текущий конфиг
        current_config = profile.get("config", {})
        config_json = json.dumps(current_config, ensure_ascii=False, indent=2)
        editor_content["value"] = config_json
        
        # Экранируем JSON для вставки в JavaScript
        config_json_escaped = json.dumps(config_json)
        
        # Получаем содержимое файлов Ace Editor из Qt ресурсов
        ace_js_content = get_ace_editor_content("ace.js")
        mode_json5_content = get_ace_editor_content("mode-json5.js")
        theme_monokai_content = get_ace_editor_content("theme-monokai.js")
        worker_json_content = get_ace_editor_content("worker-json.js")
        ext_language_tools_content = get_ace_editor_content("ext-language_tools.js")
        
        # Экранируем JS код для вставки в HTML (заменяем </script> на <\/script>)
        def escape_js_for_html(js_code: str) -> str:
            return js_code.replace("</script>", "<\\/script>")
        
        # Создаем data URL для worker (Ace Editor требует URL для worker)
        worker_data_url = ""
        if worker_json_content:
            worker_json_encoded = base64.b64encode(worker_json_content.encode('utf-8')).decode('utf-8')
            worker_data_url = f"data:text/javascript;base64,{worker_json_encoded}"
        
        # Создаем HTML с Ace Editor
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Ace Editor</title>
            <script type="text/javascript">{escape_js_for_html(ace_js_content)}</script>
            <script type="text/javascript">{escape_js_for_html(mode_json5_content)}</script>
            <script type="text/javascript">{escape_js_for_html(theme_monokai_content)}</script>
            <script type="text/javascript">{escape_js_for_html(ext_language_tools_content)}</script>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: {theme.get_color('background_primary')};
                    color: {theme.get_color('text_primary')};
                }}
                #editor {{
                    width: 100%;
                    height: 100%;
                }}
            </style>
        </head>
        <body>
            <div id="editor"></div>
            <script>
                var editor = ace.edit("editor");
                editor.setTheme("ace/theme/monokai");
                editor.session.setMode("ace/mode/json5");
                editor.setValue({config_json_escaped});
                editor.setOptions({{
                    fontSize: 14,
                    tabSize: 2,
                    useSoftTabs: true,
                    wrap: true,
                    enableBasicAutocompletion: true,
                    enableSnippets: true,
                    enableLiveAutocompletion: true
                }});
                
                // Настраиваем воркер для валидации JSON
                editor.session.setUseWorker(true);
                editor.session.setWorkerUrl("{worker_data_url}");
                
                // Сохраняем значение при каждом изменении
                editor.on("change", function() {{
                    window.editorValue = editor.getValue();
                }});
                
                // Инициализируем значение
                window.editorValue = editor.getValue();
                
                // Функция для получения содержимого
                window.getEditorValue = function() {{
                    return window.editorValue || editor.getValue();
                }};
            </script>
        </body>
        </html>
        """
        
        config_editor.setHtml(html_content)
        config_layout.addWidget(config_editor)
    else:
        # Fallback на QTextEdit
        from PyQt5.QtWidgets import QTextEdit
        config_editor = QTextEdit()
        config_editor.setMinimumHeight(300)
        current_config = profile.get("config", {})
        config_json = json.dumps(current_config, ensure_ascii=False, indent=2)
        config_editor.setPlainText(config_json)
        config_editor.setFont(QFont("Consolas", 10))
        config_layout.addWidget(config_editor)
    
    config_container.setLayout(config_layout)
    dialog.content_layout.addWidget(config_container, 1)
    
    # Функция для получения содержимого редактора
    def get_config_content():
        if HAS_WEBENGINE:
            # Используем JavaScript для получения содержимого
            # Сохраняем результат в переменную через JavaScript
            result_container = {"value": None, "ready": False}
            
            def callback(value):
                result_container["value"] = value
                result_container["ready"] = True
            
            # Получаем значение из редактора
            config_editor.page().runJavaScript("window.getEditorValue()", callback)
            
            # Ждем результат с таймаутом (максимум 1 секунда)
            from PyQt5.QtCore import QTimer, QEventLoop
            loop = QEventLoop()
            timer = QTimer()
            timer.timeout.connect(loop.quit)
            timer.setSingleShot(True)
            timer.start(1000)  # Даем время на выполнение JS
            
            # Проверяем каждые 50мс, готов ли результат
            check_timer = QTimer()
            def check_ready():
                if result_container["ready"]:
                    loop.quit()
            check_timer.timeout.connect(check_ready)
            check_timer.start(50)
            
            loop.exec_()
            timer.stop()
            check_timer.stop()
            
            if result_container["value"] is not None:
                editor_content["value"] = result_container["value"]
                return result_container["value"]
            # Fallback на сохраненное значение
            return editor_content["value"] if editor_content["value"] else ""
        else:
            text = config_editor.toPlainText()
            editor_content["value"] = text
            return text
    
    def on_type_changed(index: int):
        """Обработка изменения типа профиля"""
        profile_type = type_combo.itemData(index)
        if profile_type == "subscription":
            url_label.show()
            url_input.show()
            config_label.hide()
            config_container.hide()
        else:  # config
            url_label.hide()
            url_input.hide()
            config_label.show()
            config_container.show()
    
    type_combo.currentIndexChanged.connect(on_type_changed)
    
    # Инициализация: показываем поля в зависимости от типа
    if current_type == SubscriptionManager.PROFILE_TYPE_SUBSCRIPTION:
        on_type_changed(0)
    else:
        on_type_changed(1)
    
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(12)
    
    btn_cancel = Button(tr("download.cancel"), variant="default")
    btn_cancel.setStyleSheet(StyleSheet.dialog_button(variant="cancel"))
    btn_cancel.clicked.connect(dialog.reject)
    btn_layout.addWidget(btn_cancel)
    
    btn_layout.addStretch()
    
    btn_save = Button(tr("messages.ok"), variant="default")
    btn_save.setDefault(True)
    btn_save.setStyleSheet(StyleSheet.dialog_button(variant="confirm"))
    
    def on_save_clicked():
        name = name_input.text().strip()
        profile_type = type_combo.currentData()
        
        if not name:
            show_info_dialog(dialog, tr("profile.edit_profile_dialog_title"), tr("profile.fill_all_fields"))
            return
        
        if profile_type == "subscription":
            url = url_input.text().strip()
            if not url:
                show_info_dialog(dialog, tr("profile.edit_profile_dialog_title"), tr("profile.fill_all_fields"))
                return
            dialog.accept()
        else:  # config
            try:
                config_text = get_config_content()
                if not config_text:
                    show_info_dialog(dialog, tr("profile.edit_profile_dialog_title"), tr("profile.load_config_first"))
                    return
                # Парсим JSON5/JSON
                try:
                    import json5
                    config_data = json5.loads(config_text)
                except ImportError:
                    # Fallback на обычный JSON если json5 недоступен
                    config_data = json.loads(config_text)
                # Сохраняем в переменную для возврата
                dialog._config_data = config_data
                dialog.accept()
            except Exception as e:
                show_info_dialog(dialog, tr("profile.edit_profile_dialog_title"), tr("profile.invalid_json") + f": {str(e)}")
                return
    
    btn_save.clicked.connect(on_save_clicked)
    btn_layout.addWidget(btn_save)
    
    dialog.content_layout.addLayout(btn_layout)
    
    result = dialog.exec_()
    if result == BaseDialog.Accepted:
        name = name_input.text().strip()
        profile_type = type_combo.currentData()
        
        if profile_type == "subscription":
            url = url_input.text().strip()
            if name and url:
                return name, url, None, "subscription", True
        else:  # config
            config = getattr(dialog, '_config_data', None)
            if not config:
                # Пробуем получить из редактора еще раз
                try:
                    config_text = get_config_content()
                    if config_text:
                        try:
                            import json5
                            config = json5.loads(config_text)
                        except ImportError:
                            # Fallback на обычный JSON если json5 недоступен
                            config = json.loads(config_text)
                except:
                    pass
            if name and config:
                return name, None, config, "config", True
    
    return None, None, None, None, False