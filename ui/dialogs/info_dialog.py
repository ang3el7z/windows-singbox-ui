"""Информационные диалоги"""
from typing import Optional
from PyQt5.QtWidgets import QWidget
from .base_dialog import create_dialog, DialogType
from utils.i18n import tr


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
    dialog = create_dialog(parent, title, message, dialog_type, ok_text=ok_text or tr("messages.ok"))
    return dialog.exec_() == dialog.Accepted


def show_kill_all_success_dialog(parent: QWidget, title: str, message: str) -> bool:
    """Диалог для уведомления об успешной остановке процессов"""
    return show_info_dialog(parent, title, message, success=True)

