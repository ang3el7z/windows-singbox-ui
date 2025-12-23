"""Поток для инициализации тяжелых операций при старте"""
from typing import Optional, Dict, Any, TYPE_CHECKING
from workers.base_worker import BaseWorker
from PyQt5.QtCore import pyqtSignal, QObject

if TYPE_CHECKING:
    from managers.subscriptions import SubscriptionManager
    from managers.settings import SettingsManager


class InitOperationsWorker(BaseWorker):
    """
    Поток для инициализации тяжелых операций при старте
    
    Выполняет загрузку подписок, проверку версий и очистку логов
    в фоновом режиме для ускорения запуска приложения.
    """
    subscriptions_loaded = pyqtSignal(list)  # список имен подписок
    version_checked = pyqtSignal(str)  # версия sing-box или None
    profile_info_loaded = pyqtSignal(dict)  # данные профиля
    cleanup_finished = pyqtSignal()
    
    def __init__(
        self,
        subs_manager: 'SubscriptionManager',
        settings_manager: 'SettingsManager',
        running_index: int,
        current_index: int,
        parent: Optional[QObject] = None
    ) -> None:
        """
        Инициализация worker
        
        Args:
            subs_manager: Менеджер подписок
            settings_manager: Менеджер настроек
            running_index: Индекс запущенного профиля
            current_index: Индекс выбранного профиля
            parent: Родительский объект Qt
        """
        super().__init__(parent)
        self.subs_manager = subs_manager
        self.settings_manager = settings_manager
        self.running_index = running_index
        self.current_index = current_index
    
    def _run(self) -> None:
        """
        Выполнение инициализации
        
        Последовательно выполняет:
        1. Загрузку списка подписок
        2. Проверку версии sing-box
        3. Загрузку информации о профилях
        4. Очистку логов (если нужно)
        """
        # Загружаем подписки
        if self._check_stop():
            return
        try:
            names = self.subs_manager.list_names()
            self.subscriptions_loaded.emit(names)
        except Exception:
            self.subscriptions_loaded.emit([])
        
        # Проверяем версию sing-box
        if self._check_stop():
            return
        try:
            from utils.singbox import get_singbox_version
            version = get_singbox_version()
            self.version_checked.emit(version if version else None)
        except Exception:
            self.version_checked.emit(None)
        
        # Загружаем информацию о профиле
        if self._check_stop():
            return
        try:
            running_sub = None
            selected_sub = None
            
            if self.running_index >= 0:
                running_sub = self.subs_manager.get(self.running_index)
            
            if self.current_index >= 0:
                selected_sub = self.subs_manager.get(self.current_index)
            
            self.profile_info_loaded.emit({
                'running_sub': running_sub,
                'selected_sub': selected_sub
            })
        except Exception:
            self.profile_info_loaded.emit({'running_sub': None, 'selected_sub': None})
        
        # Очистка логов
        if self._check_stop():
            return
        try:
            from datetime import datetime
            from config.paths import DEBUG_LOG_FILE, LOG_FILE
            last_cleanup = self.settings_manager.get("last_log_cleanup", None)
            now = datetime.now()
            
            if last_cleanup:
                try:
                    last_date = datetime.fromisoformat(last_cleanup)
                    time_diff = now - last_date
                    if time_diff.total_seconds() < 24 * 60 * 60:
                        self.cleanup_finished.emit()
                        return
                except (ValueError, TypeError):
                    pass
            
            if LOG_FILE.exists():
                try:
                    LOG_FILE.write_text("", encoding="utf-8")
                except Exception:
                    pass
            
            if DEBUG_LOG_FILE.exists():
                try:
                    DEBUG_LOG_FILE.write_text("", encoding="utf-8")
                except Exception:
                    pass
            
            self.settings_manager.data["last_log_cleanup"] = now.isoformat()
            self.settings_manager.save()
        except Exception:
            pass
        finally:
            self.cleanup_finished.emit()

