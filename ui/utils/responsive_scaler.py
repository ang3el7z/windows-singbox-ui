"""Система адаптивного масштабирования для всех элементов UI"""
from typing import Dict, Optional
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QObject, QEvent, pyqtSignal
from PyQt5.QtGui import QFont


class ResponsiveScaler(QObject):
    """Класс для масштабирования всех элементов UI пропорционально размеру окна"""
    
    # Базовые размеры (для разрешения 420x780 - минимальный размер окна)
    BASE_WIDTH = 420
    BASE_HEIGHT = 780
    
    # Сигнал для уведомления об изменении масштаба
    scale_changed = pyqtSignal(float)
    
    def __init__(self, base_window: QWidget):
        """
        Инициализация масштабатора
        
        Args:
            base_window: Главное окно приложения
        """
        super().__init__()
        self.base_window = base_window
        self.current_scale = 1.0
        self._tracked_widgets: Dict[QWidget, Dict] = {}
        
        # Устанавливаем фильтр событий для отслеживания изменения размера
        base_window.installEventFilter(self)
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Фильтр событий для отслеживания изменения размера окна"""
        if obj == self.base_window and event.type() == QEvent.Resize:
            self._update_scale()
        return super().eventFilter(obj, event)
    
    def _update_scale(self):
        """Обновляет масштаб на основе текущего размера окна"""
        size = self.base_window.size()
        
        # Вычисляем масштаб на основе минимальной стороны
        width_scale = size.width() / self.BASE_WIDTH
        height_scale = size.height() / self.BASE_HEIGHT
        
        # Используем минимальный масштаб для сохранения пропорций
        new_scale = min(width_scale, height_scale)
        
        # Ограничиваем масштаб (от 0.8 до 1.5)
        new_scale = max(0.8, min(1.5, new_scale))
        
        if abs(new_scale - self.current_scale) > 0.01:  # Обновляем только при значительном изменении
            self.current_scale = new_scale
            self._apply_scale_to_widgets()
            self.scale_changed.emit(new_scale)
    
    def _apply_scale_to_widgets(self):
        """Применяет масштаб ко всем отслеживаемым виджетам"""
        for widget, config in self._tracked_widgets.items():
            if not widget or not widget.isVisible():
                continue
            
            # Масштабируем шрифт
            if 'base_font_size' in config:
                scaled_size = int(config['base_font_size'] * self.current_scale)
                font = widget.font()
                font.setPointSize(scaled_size)
                widget.setFont(font)
            
            # Масштабируем минимальные размеры
            if 'base_min_size' in config:
                base_size = config['base_min_size']
                scaled_width = int(base_size[0] * self.current_scale)
                scaled_height = int(base_size[1] * self.current_scale)
                widget.setMinimumSize(scaled_width, scaled_height)
            
            # Масштабируем максимальные размеры
            if 'base_max_size' in config:
                base_size = config['base_max_size']
                scaled_width = int(base_size[0] * self.current_scale)
                scaled_height = int(base_size[1] * self.current_scale)
                widget.setMaximumSize(scaled_width, scaled_height)
    
    def register_widget(self, widget: QWidget, base_font_size: Optional[int] = None,
                       base_min_size: Optional[tuple] = None, base_max_size: Optional[tuple] = None):
        """
        Регистрирует виджет для адаптивного масштабирования
        
        Args:
            widget: Виджет для масштабирования
            base_font_size: Базовый размер шрифта (для базового окна 420x780)
            base_min_size: Базовый минимальный размер (width, height)
            base_max_size: Базовый максимальный размер (width, height)
        """
        config = {}
        if base_font_size:
            config['base_font_size'] = base_font_size
        if base_min_size:
            config['base_min_size'] = base_min_size
        if base_max_size:
            config['base_max_size'] = base_max_size
        
        if config:
            self._tracked_widgets[widget] = config
            # Применяем текущий масштаб сразу
            self._apply_scale_to_widget(widget, config)
    
    def _apply_scale_to_widget(self, widget: QWidget, config: Dict):
        """Применяет масштаб к одному виджету"""
        if not widget or not widget.isVisible():
            return
        
        # Масштабируем шрифт
        if 'base_font_size' in config:
            scaled_size = int(config['base_font_size'] * self.current_scale)
            font = widget.font()
            font.setPointSize(scaled_size)
            widget.setFont(font)
        
        # Масштабируем минимальные размеры
        if 'base_min_size' in config:
            base_size = config['base_min_size']
            scaled_width = int(base_size[0] * self.current_scale)
            scaled_height = int(base_size[1] * self.current_scale)
            widget.setMinimumSize(scaled_width, scaled_height)
        
        # Масштабируем максимальные размеры
        if 'base_max_size' in config:
            base_size = config['base_max_size']
            scaled_width = int(base_size[0] * self.current_scale)
            scaled_height = int(base_size[1] * self.current_scale)
            widget.setMaximumSize(scaled_width, scaled_height)
    
    def get_scaled_value(self, base_value: int) -> int:
        """
        Возвращает масштабированное значение
        
        Args:
            base_value: Базовое значение для окна 420x780
            
        Returns:
            Масштабированное значение
        """
        return int(base_value * self.current_scale)
    
    def get_scale(self) -> float:
        """Возвращает текущий масштаб"""
        return self.current_scale


# Глобальный экземпляр масштабатора
_scaler: Optional[ResponsiveScaler] = None


def init_scaler(main_window: QWidget) -> ResponsiveScaler:
    """Инициализирует глобальный масштабатор"""
    global _scaler
    _scaler = ResponsiveScaler(main_window)
    return _scaler


def get_scaler() -> Optional[ResponsiveScaler]:
    """Возвращает глобальный масштабатор"""
    return _scaler


def get_scaled_value(base_value: int) -> int:
    """Возвращает масштабированное значение"""
    if _scaler:
        return _scaler.get_scaled_value(base_value)
    return base_value

