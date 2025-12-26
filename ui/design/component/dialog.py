"""Все вариации диалогов - используют BaseDialog из design"""
from enum import Enum
from typing import Optional, Tuple, Callable
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QProgressBar
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.styles import StyleSheet, theme
from ui.design.base.base_dialog import BaseDialog
from ui.design.component.button import Button
from ui.design.component.label import Label
from ui.design.component.line_edit import LineEdit
from ui.design.component.progress_bar import ProgressBar
from utils.i18n import tr, get_available_languages, get_language_name


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


def show_add_subscription_dialog(parent: QWidget) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Показывает диалог добавления подписки с двумя полями ввода
    
    Args:
        parent: Родительский виджет
    
    Returns:
        Кортеж (name, url, был ли нажат OK)
    """
    # Заголовок в TitleBar должен описывать действие, а не объект
    dialog = BaseDialog(parent, tr("profile.add_subscription_dialog_title"))
    dialog.setMinimumWidth(420)
    
    dialog.setStyleSheet(dialog.styleSheet() + StyleSheet.input())
    
    # Убираем дублирование заголовка - он уже в TitleBar
    name_label = Label(tr("profile.name"), variant="default", size="medium")
    name_label.setStyleSheet(name_label.styleSheet() + "margin-top: 8px;")
    dialog.content_layout.addWidget(name_label)
    
    name_input = LineEdit()
    name_input.setPlaceholderText(tr("profile.name"))
    dialog.content_layout.addWidget(name_input)
    
    url_label = Label(tr("profile.url"), variant="default", size="medium")
    url_label.setStyleSheet(url_label.styleSheet() + "margin-top: 8px;")
    dialog.content_layout.addWidget(url_label)
    
    url_input = LineEdit()
    url_input.setPlaceholderText("https://...")
    dialog.content_layout.addWidget(url_input)
    
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
        url = url_input.text().strip()
        if name and url:
            dialog.accept()
        else:
            show_info_dialog(dialog, tr("profile.add_subscription"), tr("profile.fill_all_fields"))
    
    btn_add.clicked.connect(on_add_clicked)
    btn_layout.addWidget(btn_add)
    
    dialog.content_layout.addLayout(btn_layout)
    
    name_input.setFocus()
    
    def on_enter():
        if name_input.text().strip() and url_input.text().strip():
            on_add_clicked()
    
    name_input.returnPressed.connect(lambda: url_input.setFocus())
    url_input.returnPressed.connect(on_enter)
    
    result = dialog.exec_()
    if result == BaseDialog.Accepted:
        name = name_input.text().strip()
        url = url_input.text().strip()
        if name and url:
            return name, url, True
    return None, None, False


class DownloadDialog(BaseDialog):
    """Диалог загрузки SingBox с прогресс-баром"""
    
    def __init__(self, parent: QWidget, on_download_callback: Callable[['DownloadDialog'], None]):
        """
        Инициализация диалога загрузки
        
        Args:
            parent: Родительский виджет
            on_download_callback: Функция-коллбэк для запуска загрузки (принимает dialog)
        """
        super().__init__(parent, tr("download.title"))
        self.on_download_callback = on_download_callback
        self.download_thread = None
        
        self.setMinimumWidth(400)
        self.setStyleSheet(self.styleSheet() + StyleSheet.progress_bar())
        self.content_layout.setSpacing(16)
        
        # Убираем дублирование заголовка - он уже в TitleBar
        info = Label(tr("download.description"), variant="secondary", size="medium")
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


def show_restart_admin_dialog(parent: QWidget, title: str, message: str) -> bool:
    """Диалог для перезапуска от имени администратора"""
    return show_confirm_dialog(
        parent, title, message,
        yes_text=tr("messages.restart_yes"),
        no_text=tr("download.cancel")
    )


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

