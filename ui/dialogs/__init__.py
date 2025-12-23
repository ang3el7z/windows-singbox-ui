"""Диалоги приложения"""
from .base_dialog import create_dialog, DialogType
from .confirm_dialog import show_confirm_dialog
from .info_dialog import show_info_dialog
from .language_dialog import show_language_selection_dialog

__all__ = [
    'create_dialog', 'DialogType',
    'show_confirm_dialog', 'show_info_dialog',
    'show_language_selection_dialog'
]

