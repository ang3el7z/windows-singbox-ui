"""Менеджер перезапуска приложения"""
import sys
import subprocess
import ctypes
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import MainWindow




def restart_application(main_window: 'MainWindow', run_as_admin: bool = False) -> bool:
    """
    Перезапускает приложение (опционально от имени администратора).
    
    Универсальная функция перезапуска для всех случаев:
    1. После смены темы (run_as_admin=False)
    2. На главной странице при клике на статус администратора (run_as_admin=True)
    3. В настройках при включении галочки "Запускать от имени администратора" (run_as_admin=True)
    
    Args:
        main_window: Экземпляр MainWindow для доступа к методам остановки
        run_as_admin: Если True, перезапускает от имени администратора
        
    Returns:
        True если перезапуск успешно инициирован
    """
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    from core.protocol import is_admin
    
    app = QApplication.instance()
    if not app:
        return False
    
    try:
        # Если требуется запуск от имени администратора, проверяем, не админ ли уже
        if run_as_admin and is_admin():
            return False
        
        # Останавливаем sing-box перед перезапуском
        try:
            if hasattr(main_window, 'stop_singbox'):
                main_window.stop_singbox()
        except Exception:
            pass
        
        args = sys.argv[1:]
        # Добавляем специальный флаг для перезапуска
        restart_args = args + ["--restart"]
        
        if getattr(sys, 'frozen', False):
            # Собранное приложение
            exe_path = sys.executable
            work_dir = str(Path(exe_path).parent)
            
            if run_as_admin and sys.platform == "win32":
                params = " ".join(f'"{a}"' for a in restart_args) if restart_args else ""
                result = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",  # Запуск от имени администратора
                    exe_path,
                    params,
                    work_dir,
                    1  # SW_SHOWNORMAL
                )
                # ShellExecuteW возвращает значение > 32 при успехе
                if result <= 32:
                    # Пользователь отменил UAC или произошла ошибка
                    return False
                # Для UAC нужно больше времени
                wait_time = 4.0
            else:
                subprocess.Popen([exe_path] + restart_args, cwd=work_dir, close_fds=False)
                wait_time = 2.0
        else:
            # Режим разработки
            exe_path = sys.executable
            script = Path(__file__).parent.parent / "main" / "main.py"
            work_dir = str(Path(__file__).parent.parent)
            
            if run_as_admin and sys.platform == "win32":
                params = f'"{script}" ' + " ".join(f'"{a}"' for a in restart_args) if restart_args else f'"{script}"'
                result = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    exe_path,
                    params,
                    work_dir,
                    1
                )
                if result <= 32:
                    # Пользователь отменил UAC или произошла ошибка
                    return False
                wait_time = 4.0
            else:
                subprocess.Popen([exe_path, str(script)] + restart_args, cwd=work_dir, close_fds=False)
                wait_time = 2.0
        
        # Даем время новому процессу запуститься
        # Новый процесс с флагом --restart должен закрыть старый процесс
        elapsed = 0
        step = 0.1
        
        while elapsed < wait_time:
            app.processEvents()
            time.sleep(step)
            elapsed += step
        
        # Закрываем текущее приложение
        # Если новый процесс не запустился, это закроет приложение
        # Если запустился - он уже взял управление
        _shutdown_and_quit(main_window)
        
        return True
    except Exception as e:
        import traceback
        from utils.logger import log_to_file
        log_to_file(f"[Restart Error] Ошибка перезапуска: {e}\n{traceback.format_exc()}")
        return False


def _shutdown_and_quit(main_window: 'MainWindow'):
    """Корректно завершает приложение перед перезапуском"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    
    # Шрифты теперь вшиты в QRC, сброс не требуется
    
    # Закрываем окно, но НЕ закрываем local_server и mutex здесь
    # Они будут автоматически закрыты при выходе из процесса
    # Это важно, чтобы новый процесс мог их перехватить
    
    # Завершаем приложение
    app = QApplication.instance()
    if app:
        # Используем singleShot для асинхронного закрытия
        QTimer.singleShot(50, app.quit)

