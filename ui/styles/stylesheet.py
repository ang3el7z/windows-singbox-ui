"""Генератор стилей для UI компонентов"""
from typing import Optional
from .theme import theme


class StyleSheet:
    """Класс для генерации стилей Qt"""
    
    @staticmethod
    def button(
        variant: str = "default",
        size: str = "medium",
        full_width: bool = False
    ) -> str:
        """
        Генерирует стиль кнопки
        
        Args:
            variant: Вариант кнопки (default, primary, secondary, danger)
            size: Размер (small, medium, large)
            full_width: Занимать всю ширину
        """
        colors = {
            'default': {
                'bg': 'transparent',
                'bg_hover': theme.get_color('accent_light'),
                'text': theme.get_color('text_secondary'),
                'border': 'none',
            },
            'primary': {
                'bg': theme.get_color('accent'),
                'bg_hover': theme.get_color('accent_hover'),
                'text': theme.get_color('background_primary'),
                'border': 'none',
            },
            'secondary': {
                'bg': theme.get_color('background_secondary'),
                'bg_hover': theme.get_color('background_tertiary'),
                'text': theme.get_color('text_primary'),
                'border': f"1px solid {theme.get_color('border')}",
            },
            'danger': {
                'bg': theme.get_color('error'),
                'bg_hover': '#ff5252',
                'text': '#ffffff',
                'border': 'none',
            },
        }
        
        sizes_config = {
            'small': {'padding': '8px 16px', 'font_size': theme.get_font('size_small')},
            'medium': {'padding': '12px 24px', 'font_size': theme.get_font('size_medium')},
            'large': {'padding': '16px 32px', 'font_size': theme.get_font('size_large')},
        }
        
        variant_style = colors.get(variant, colors['default'])
        size_style = sizes_config.get(size, sizes_config['medium'])
        
        width = 'width: 100%;' if full_width else ''
        
        return f"""
        QPushButton {{
            background-color: {variant_style['bg']};
            color: {variant_style['text']};
            border: {variant_style['border']};
            border-radius: {theme.get_size('border_radius_medium')}px;
            padding: {size_style['padding']};
            font-size: {size_style['font_size']}px;
            font-weight: {theme.get_font('weight_medium')};
            font-family: {theme.get_font('family')};
            {width}
        }}
        QPushButton:hover {{
            background-color: {variant_style['bg_hover']};
        }}
        QPushButton:pressed {{
            background-color: {variant_style['bg_hover']};
            opacity: 0.9;
        }}
        QPushButton:disabled {{
            background-color: {theme.get_color('background_secondary')};
            color: {theme.get_color('text_disabled')};
            opacity: 0.5;
        }}
        """
    
    @staticmethod
    def card(radius: Optional[int] = None) -> str:
        """Генерирует стиль карточки"""
        radius = radius or theme.get_size('border_radius_large')
        bg_color = theme.get_color('background_secondary')
        return f"""
        CardWidget {{
            background-color: {bg_color};
            border-radius: {radius}px;
            border: none;
            min-height: 1px;
        }}
        QWidget#CardWidget {{
            background-color: {bg_color};
            border-radius: {radius}px;
            border: none;
        }}
        """
    
    @staticmethod
    def label(
        variant: str = "default",
        size: str = "medium"
    ) -> str:
        """
        Генерирует стиль лейбла
        
        Args:
            variant: Вариант (default, primary, secondary, success, error, warning)
            size: Размер (small, medium, large, xlarge)
        """
        colors = {
            'default': theme.get_color('text_primary'),
            'primary': theme.get_color('accent'),
            'secondary': theme.get_color('text_secondary'),
            'success': theme.get_color('success'),
            'error': theme.get_color('error'),
            'warning': theme.get_color('warning'),
        }
        
        sizes_config = {
            'small': theme.get_font('size_small'),
            'medium': theme.get_font('size_medium'),
            'large': theme.get_font('size_large'),
            'xlarge': theme.get_font('size_xlarge'),
        }
        
        color = colors.get(variant, colors['default'])
        font_size = sizes_config.get(size, sizes_config['medium'])
        
        return f"""
        QLabel {{
            color: {color};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-size: {font_size}px;
            font-family: {theme.get_font('family')};
        }}
        """
    
    @staticmethod
    def input(
        variant: str = "default"
    ) -> str:
        """Генерирует стиль поля ввода"""
        return f"""
        QLineEdit, QSpinBox {{
            background-color: {theme.get_color('background_secondary')};
            color: {theme.get_color('text_primary')};
            border: 1px solid {theme.get_color('border')};
            border-radius: {theme.get_size('border_radius_medium')}px;
            padding: {theme.get_size('padding_medium')}px {theme.get_size('padding_large')}px;
            font-size: {theme.get_font('size_medium')}px;
            font-family: {theme.get_font('family')};
        }}
        QLineEdit:focus, QSpinBox:focus {{
            border: 1px solid {theme.get_color('border_focus')};
            background-color: {theme.get_color('background_tertiary')};
        }}
        QLineEdit:disabled, QSpinBox:disabled {{
            background-color: {theme.get_color('background_secondary')};
            color: {theme.get_color('text_disabled')};
            opacity: 0.5;
        }}
        """
    
    @staticmethod
    def list_widget() -> str:
        """Генерирует стиль списка"""
        return f"""
        QListWidget {{
            background-color: {theme.get_color('background_secondary')};
            border: 1px solid {theme.get_color('border')};
            border-radius: {theme.get_size('border_radius_medium')}px;
            padding: {theme.get_size('padding_small')}px;
            outline: none;
        }}
        QListWidget::item {{
            background-color: transparent;
            border-radius: {theme.get_size('border_radius_small')}px;
            padding: {theme.get_size('padding_medium')}px;
            margin: 2px;
        }}
        QListWidget::item:hover {{
            background-color: {theme.get_color('accent_light')};
        }}
        QListWidget::item:selected {{
            background-color: {theme.get_color('accent_light')};
            color: {theme.get_color('accent')};
        }}
        """
    
    @staticmethod
    def text_edit() -> str:
        """Генерирует стиль текстового поля"""
        return f"""
        QTextEdit {{
            background-color: {theme.get_color('background_secondary')};
            color: {theme.get_color('text_primary')};
            border: 1px solid {theme.get_color('border')};
            border-radius: {theme.get_size('border_radius_medium')}px;
            padding: {theme.get_size('padding_medium')}px;
            font-size: {theme.get_font('size_small')}px;
            font-family: 'Consolas', 'Courier New', monospace;
            outline: none;
        }}
        QTextEdit:focus {{
            border: 1px solid {theme.get_color('border_focus')};
        }}
        """
    
    @staticmethod
    def checkbox() -> str:
        """Генерирует стиль чекбокса"""
        return f"""
        QCheckBox {{
            color: {theme.get_color('text_primary')};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-size: {theme.get_font('size_medium')}px;
            font-family: {theme.get_font('family')};
            spacing: {theme.get_size('spacing_small')}px;
        }}
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {theme.get_color('border')};
            border-radius: 4px;
            background-color: {theme.get_color('background_secondary')};
        }}
        QCheckBox::indicator:hover {{
            border-color: {theme.get_color('border_hover')};
        }}
        QCheckBox::indicator:checked {{
            background-color: {theme.get_color('accent')};
            border-color: {theme.get_color('accent')};
        }}
        """
    
    @staticmethod
    def combo_box() -> str:
        """Генерирует стиль комбобокса"""
        return f"""
        QComboBox {{
            background-color: {theme.get_color('background_secondary')};
            color: {theme.get_color('text_primary')};
            border: 1px solid {theme.get_color('border')};
            border-radius: {theme.get_size('border_radius_medium')}px;
            padding: {theme.get_size('padding_medium')}px {theme.get_size('padding_large')}px;
            font-size: {theme.get_font('size_medium')}px;
            font-family: {theme.get_font('family')};
            min-width: 120px;
        }}
        QComboBox:hover {{
            border: 1px solid {theme.get_color('border_hover')};
            background-color: {theme.get_color('background_tertiary')};
        }}
        QComboBox:focus {{
            border: 1px solid {theme.get_color('border_focus')};
            background-color: {theme.get_color('background_tertiary')};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 0px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {theme.get_color('text_secondary')};
            width: 0px;
            height: 0px;
            margin-right: 8px;
        }}
        QComboBox::down-arrow:hover {{
            border-top-color: {theme.get_color('text_primary')};
        }}
        QComboBox QAbstractItemView {{
            background-color: {theme.get_color('background_secondary')};
            color: {theme.get_color('text_primary')};
            border: 1px solid {theme.get_color('border')};
            border-radius: {theme.get_size('border_radius_medium')}px;
            selection-background-color: {theme.get_color('accent_light')};
            selection-color: {theme.get_color('accent')};
            padding: 4px;
        }}
        QComboBox QAbstractItemView::item {{
            padding: {theme.get_size('padding_medium')}px;
            border-radius: {theme.get_size('border_radius_small')}px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {theme.get_color('accent_light')};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {theme.get_color('accent_light')};
            color: {theme.get_color('accent')};
        }}
        QComboBox:disabled {{
            background-color: {theme.get_color('background_secondary')};
            color: {theme.get_color('text_disabled')};
            opacity: 0.5;
        }}
        """
    
    @staticmethod
    def navigation() -> str:
        """Генерирует стиль навигации"""
        return f"""
        QWidget {{
            background-color: {theme.get_color('background_primary')};
            border: none;
        }}
        QPushButton {{
            color: {theme.get_color('text_secondary')};
            font-size: {theme.get_font('size_medium')}px;
            font-weight: {theme.get_font('weight_medium')};
            padding: 32px 8px;
            background-color: transparent;
            border: none;
            border-radius: 0px;
        }}
        QPushButton:hover {{
            background-color: {theme.get_color('accent_light')};
        }}
        QPushButton:checked {{
            color: {theme.get_color('accent')};
            font-weight: {theme.get_font('weight_semibold')};
            background-color: transparent;
        }}
        QLabel {{
            color: inherit;
            background-color: transparent;
            border: none;
        }}
        """
    
    @staticmethod
    def global_styles() -> str:
        """Генерирует глобальные стили приложения"""
        return f"""
        QWidget {{
            font-family: {theme.get_font('family')};
        }}
        QLabel {{
            background-color: transparent;
            border: none;
        }}
        QPushButton {{
            background-color: transparent;
            border: none;
        }}
        QListWidget {{
            outline: none;
        }}
        QSpinBox {{
            outline: none;
        }}
        QTextEdit {{
            outline: none;
        }}
        /* Исключаем CardWidget из глобальных стилей, чтобы его стили не перезаписывались */
        CardWidget {{
            /* Стили CardWidget устанавливаются отдельно */
        }}
        """

