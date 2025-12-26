"""Дизайн-система - базовые компоненты"""
from .base.base_dialog import BaseDialog
from .base.base_title_bar import BaseTitleBar
from .base.base_card import BaseCard

# Алиасы для совместимости
TitleBar = BaseTitleBar
CardWidget = BaseCard

__all__ = ['BaseDialog', 'BaseTitleBar', 'BaseCard', 'TitleBar', 'CardWidget']

