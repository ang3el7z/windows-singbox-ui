"""Потоки для проверки версий"""
from typing import Optional
from workers.base_worker import BaseWorker
from PyQt5.QtCore import pyqtSignal, QObject


class CheckVersionWorker(BaseWorker):
    """
    Поток для проверки версии sing-box и обновлений
    
    Выполняет проверку текущей и последней версии sing-box
    в фоновом режиме без блокировки UI.
    """
    version_info_ready = pyqtSignal(str, str)  # текущая версия, последняя версия
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Инициализация worker
        
        Args:
            parent: Родительский объект Qt
        """
        super().__init__(parent)
    
    def _run(self) -> None:
        """
        Проверка версии sing-box
        
        Получает текущую установленную версию и последнюю доступную версию
        из GitHub и отправляет их через сигнал version_info_ready.
        """
        try:
            from utils.singbox import get_singbox_version, get_latest_version
            current_version = get_singbox_version()
            latest_version = get_latest_version()
            self.version_info_ready.emit(current_version or "", latest_version or "")
        except Exception:
            self.version_info_ready.emit("", "")


class CheckAppVersionWorker(BaseWorker):
    """
    Поток для проверки версии приложения
    
    Выполняет проверку последней версии приложения
    в фоновом режиме без блокировки UI.
    """
    app_version_ready = pyqtSignal(str)  # последняя версия приложения
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Инициализация worker
        
        Args:
            parent: Родительский объект Qt
        """
        super().__init__(parent)
    
    def _run(self) -> None:
        """
        Проверка версии приложения
        
        Получает последнюю доступную версию приложения из GitHub
        и отправляет её через сигнал app_version_ready.
        """
        try:
            from utils.singbox import get_app_latest_version
            app_latest = get_app_latest_version()
            self.app_version_ready.emit(app_latest or "")
        except Exception:
            self.app_version_ready.emit("")

