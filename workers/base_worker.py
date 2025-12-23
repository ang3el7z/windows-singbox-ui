"""Базовый класс для всех фоновых потоков"""
from typing import Optional
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import traceback


class BaseWorker(QThread):
    """
    Базовый класс для всех фоновых потоков с обработкой ошибок
    
    Предоставляет единообразный интерфейс для всех фоновых операций
    с автоматической обработкой ошибок и возможностью остановки.
    """
    
    # Сигналы для всех workers
    error = pyqtSignal(str)  # Сообщение об ошибке
    finished_signal = pyqtSignal()  # Завершение работы
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Инициализация базового worker
        
        Args:
            parent: Родительский объект Qt
        """
        super().__init__(parent)
        self._should_stop: bool = False
    
    def stop(self) -> None:
        """Остановка потока"""
        self._should_stop = True
        self.terminate()
    
    def run(self) -> None:
        """
        Основной метод выполнения (вызывается Qt)
        
        Оборачивает _run() в try/except для обработки ошибок
        """
        try:
            self._run()
            self.finished_signal.emit()
        except Exception as e:
            error_msg = f"{self.__class__.__name__} error: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)
    
    def _run(self) -> None:
        """
        Внутренний метод выполнения (переопределяется в наследниках)
        
        Raises:
            NotImplementedError: Если не переопределен в наследнике
        """
        raise NotImplementedError("Subclasses must implement _run()")
    
    def _check_stop(self) -> bool:
        """
        Проверка необходимости остановки
        
        Returns:
            True если поток должен остановиться
        """
        return self._should_stop

