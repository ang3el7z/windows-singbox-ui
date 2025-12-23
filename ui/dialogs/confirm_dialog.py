"""Диалоги подтверждения"""
from typing import Optional
from PyQt5.QtWidgets import QWidget
from .base_dialog import create_dialog, DialogType


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
    dialog = create_dialog(parent, title, message, dialog_type, yes_text=yes_text, no_text=no_text)
    return dialog.exec_() == dialog.Accepted


def show_restart_admin_dialog(parent: QWidget, title: str, message: str) -> bool:
    """Диалог для перезапуска от имени администратора"""
    from utils.i18n import tr
    return show_confirm_dialog(
        parent, title, message,
        yes_text=tr("messages.restart_yes"),
        no_text=tr("download.cancel")
    )


def show_kill_all_confirm_dialog(parent: QWidget, title: str, message: str) -> bool:
    """Диалог для подтверждения остановки всех процессов"""
    from utils.i18n import tr
    return show_confirm_dialog(
        parent, title, message,
        yes_text=tr("messages.kill_all_yes"),
        no_text=tr("download.cancel"),
        warning=True
    )

