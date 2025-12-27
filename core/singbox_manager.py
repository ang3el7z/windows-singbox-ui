"""Управление процессом sing-box"""
import subprocess
import sys
from pathlib import Path
from typing import Optional
from PyQt5.QtCore import QThread, pyqtSignal
from config.paths import CORE_EXE, CONFIG_FILE, CORE_DIR


class StartSingBoxThread(QThread):
    """Поток для запуска SingBox без блокировки UI"""
    finished = pyqtSignal(object)  # subprocess.Popen
    error = pyqtSignal(str)
    
    def __init__(self, core_exe: Path, config_file: Path, core_dir: Path):
        """
        Инициализация потока запуска sing-box
        
        Args:
            core_exe: Путь к sing-box.exe
            config_file: Путь к config.json
            core_dir: Рабочая директория
        """
        super().__init__()
        self.core_exe = core_exe
        self.config_file = config_file
        self.core_dir = core_dir
    
    def run(self) -> None:
        """Запуск sing-box процесса"""
        try:
            # Скрываем окно консоли
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            proc = subprocess.Popen(
                [str(self.core_exe), "run", "-c", str(self.config_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(self.core_dir),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            
            # Небольшая задержка, чтобы процесс успел запуститься
            import time
            time.sleep(0.2)
            
            # Проверяем, что процесс все еще запущен
            if proc.poll() is None:
                # Процесс запущен успешно
                self.finished.emit(proc)
            else:
                # Процесс завершился сразу после запуска
                returncode = proc.returncode if proc.returncode is not None else -1
                self.error.emit(f"Процесс завершился сразу после запуска с кодом {returncode}")
        except Exception as e:
            self.error.emit(str(e))


def reload_singbox_config(core_exe: Path, config_file: Path, core_dir: Path) -> bool:
    """
    Перезагрузить конфигурацию sing-box без перезапуска процесса
    
    Args:
        core_exe: Путь к sing-box.exe
        config_file: Путь к config.json
        core_dir: Рабочая директория
        
    Returns:
        True если команда выполнена успешно, False в противном случае
    """
    try:
        # Скрываем окно консоли
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Выполняем команду reload
        result = subprocess.run(
            [str(core_exe), "reload", "-c", str(config_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(core_dir),
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            timeout=10,
        )
        
        return result.returncode == 0
    except Exception as e:
        # Импортируем log_to_file если доступен
        try:
            from utils.logger import log_to_file
            log_to_file(f"Ошибка при выполнении reload: {e}")
        except ImportError:
            pass
        return False


