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
    
    Используется в трех местах:
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
    from core.protocol import is_admin
    
    app = QApplication.instance()
    if not app:
        return False
    
    try:
        # Если требуется запуск от имени администратора, проверяем, не админ ли уже
        if run_as_admin and is_admin():
            return False
        
        args = sys.argv[1:]
        
        if getattr(sys, 'frozen', False):
            # Собранное приложение
            exe_path = sys.executable
            work_dir = str(Path(exe_path).parent)
            
            if run_as_admin and sys.platform == "win32":
                params = " ".join(f'"{a}"' for a in args)
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
                    return False
            else:
                subprocess.Popen([exe_path] + args, cwd=work_dir, close_fds=True)
        else:
            # Режим разработки
            exe_path = sys.executable
            script = Path(__file__).parent.parent / "main" / "main.py"
            work_dir = str(Path(__file__).parent.parent)
            
            if run_as_admin and sys.platform == "win32":
                params = f'"{script}" ' + " ".join(f'"{a}"' for a in args)
                result = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    exe_path,
                    params,
                    work_dir,
                    1
                )
                if result <= 32:
                    return False
            else:
                subprocess.Popen([exe_path, str(script)] + args, cwd=work_dir, close_fds=True)
        
        # Даем время новому процессу запуститься перед закрытием старого
        # Это важно для корректной работы QSharedMemory и трея
        if run_as_admin:
            time.sleep(1)
            # Используем processEvents чтобы дать время новому процессу запуститься
            for _ in range(10):
                app.processEvents()
                time.sleep(0.1)
        
        # Корректно завершаем текущее приложение
        _shutdown_and_quit(main_window)
        
        return True
    except Exception:
        return False


def _shutdown_and_quit(main_window: 'MainWindow'):
    """Корректно завершает приложение перед перезапуском"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtNetwork import QLocalServer
    from main import release_global_mutex
    
    try:
        # Останавливаем sing-box, если запущен
        main_window.stop_singbox()
    except Exception:
        pass
    
    try:
        # Закрываем local_server
        if hasattr(main_window, "local_server") and main_window.local_server:
            main_window.local_server.close()
            QLocalServer.removeServer("SingBox-UI-Instance")
    except Exception:
        pass
    
    try:
        # Освобождаем mutex
        release_global_mutex()
    except Exception:
        pass
    
    # Завершаем приложение
    app = QApplication.instance()
    if app:
        app.quit()

