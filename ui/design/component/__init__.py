"""Вариации компонентов - используют базовые компоненты из design"""
from .dialog import (
    show_info_dialog,
    show_confirm_dialog,
    show_input_dialog,
    show_language_selection_dialog,
    show_add_subscription_dialog,
    show_add_profile_dialog,
    show_edit_profile_dialog,
    show_restart_admin_dialog,
    show_kill_all_confirm_dialog,
    show_kill_all_success_dialog,
    DownloadDialog,
    DialogType
)
from .button import (
    Button,
    NavButton,
    AnimatedStartButton,
    RoundGradientButton,
    GradientWidget
)
from .label import Label, VersionLabel
from .text_edit import TextEdit
from .progress_bar import ProgressBar
from .line_edit import LineEdit
from .checkbox import CheckBox
from .combo_box import ComboBox
from .list_widget import ListWidget
from .widget import Container
from .window import LogsWindow

__all__ = [
    # Диалоги
    'show_info_dialog',
    'show_confirm_dialog',
    'show_input_dialog',
    'show_language_selection_dialog',
    'show_add_subscription_dialog',
    'show_add_profile_dialog',
    'show_edit_profile_dialog',
    'show_restart_admin_dialog',
    'show_kill_all_confirm_dialog',
    'show_kill_all_success_dialog',
    'DownloadDialog',
    'DialogType',
    # Кнопки
    'Button',
    'NavButton',
    'AnimatedStartButton',
    'RoundGradientButton',
    'GradientWidget',
    # Лейблы
    'Label',
    'VersionLabel',
    # Поля ввода
    'TextEdit',
    'LineEdit',
    # Другие компоненты
    'ProgressBar',
    'CheckBox',
    'ComboBox',
    'ListWidget',
    'Container',
    # Окна
    'LogsWindow'
]

