"""Управление процессом sing-box"""
import subprocess
import sys
import io
from pathlib import Path
from typing import Optional
from PyQt5.QtCore import QThread, pyqtSignal
from config.paths import CORE_EXE, CONFIG_FILE, CORE_DIR, SINGBOX_CORE_LOG_FILE


class SingBoxLogReaderThread(QThread):
    """Поток для чтения логов из stdout/stderr процесса sing-box"""
    
    def __init__(self, process: subprocess.Popen, log_file: Path):
        """
        Инициализация потока чтения логов
        
        Args:
            process: Процесс sing-box
            log_file: Путь к файлу для сохранения логов
        """
        super().__init__()
        self.process = process
        self.log_file = log_file
        self.running = True
        
        # Убеждаемся что папка существует
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Очищаем файл при старте
        try:
            log_file.write_text("", encoding="utf-8")
        except Exception:
            pass
    
    def run(self) -> None:
        """Чтение логов из процесса"""
        try:
            if not self.process.stdout:
                return
            
            # Читаем логи построчно
            while self.running and self.process.poll() is None:
                try:
                    # Читаем байты
                    line_bytes = self.process.stdout.readline()
                    if not line_bytes:
                        # Если строка пустая, процесс может завершиться или нет данных
                        self.msleep(100)
                        continue
                    
                    # Декодируем в строку
                    try:
                        line = line_bytes.decode('utf-8', errors='replace').rstrip()
                    except Exception:
                        # Если не удалось декодировать, пробуем другие кодировки
                        try:
                            line = line_bytes.decode('cp1251', errors='replace').rstrip()
                        except Exception:
                            line = line_bytes.decode('latin1', errors='replace').rstrip()
                    
                    if line:
                        self._write_log_line(line)
                    
                    # Небольшая задержка, чтобы не нагружать CPU слишком сильно
                    self.msleep(10)
                
                except Exception as e:
                    # Если произошла ошибка чтения, проверяем, не завершился ли процесс
                    if self.process.poll() is not None:
                        break
                    # Небольшая задержка перед повторной попыткой
                    self.msleep(100)
        
        except Exception as e:
            # Импортируем log_to_file если доступен
            try:
                from utils.logger import log_to_file
                log_to_file(f"Ошибка при чтении логов sing-box: {e}")
            except ImportError:
                pass
    
    def _write_log_line(self, line: str):
        """Записать строку лога в файл"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_line = f"[{timestamp}] {line}"
        
        # Записываем в файл
        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(formatted_line + "\n")
        except Exception:
            pass
    
    def stop(self):
        """Остановка чтения логов"""
        self.running = False


class StartSingBoxThread(QThread):
    """Поток для запуска SingBox без блокировки UI"""
    finished = pyqtSignal(object, object)  # (subprocess.Popen, SingBoxLogReaderThread)
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
            
            # Перенаправляем stdout и stderr в pipe для чтения логов
            proc = subprocess.Popen(
                [str(self.core_exe), "run", "-c", str(self.config_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Объединяем stderr с stdout
                cwd=str(self.core_dir),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                bufsize=0,  # Небуферизованный режим для немедленного чтения
            )
            
            # Создаем поток для чтения логов
            log_reader = SingBoxLogReaderThread(proc, SINGBOX_CORE_LOG_FILE)
            log_reader.start()
            
            # Небольшая задержка, чтобы процесс успел запуститься
            import time
            time.sleep(0.2)
            
            # Проверяем, что процесс все еще запущен
            if proc.poll() is None:
                # Процесс запущен успешно
                self.finished.emit(proc, log_reader)
            else:
                # Процесс завершился сразу после запуска
                log_reader.stop()
                log_reader.wait(1000)  # Ждем остановки потока чтения логов
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


