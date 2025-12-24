"""Управление регистрацией протоколов"""
import sys
import ctypes
from typing import Optional
from pathlib import Path


def register_protocols() -> bool:
    """
    Регистрация протоколов sing-box:// и singbox-ui:// в Windows (без прав админа)
    Проверяет оба места в реестре (HKEY_CURRENT_USER и HKEY_LOCAL_MACHINE)
    и не перезаписывает регистрацию официального sing-box
    
    Returns:
        True если регистрация успешна
    """
    if sys.platform != "win32":
        return False
    
    try:
        import winreg
        protocols = ["sing-box", "singbox-ui"]
        
        # Получаем путь к exe файлу
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = sys.executable
            script_path = Path(__file__).parent.parent / "main" / "main.py"
            exe_path = f'"{exe_path}" "{script_path}"'
        
        # Формируем команду запуска
        command = f'"{exe_path}" "%1"'
        
        def check_protocol_registration(protocol: str, hive: int) -> Optional[str]:
            """Проверяет регистрацию протокола в указанном месте реестра"""
            key_path = f"Software\\Classes\\{protocol}"
            command_path = f"{key_path}\\shell\\open\\command"
            
            try:
                with winreg.OpenKey(hive, command_path) as cmd_key:
                    current_command = winreg.QueryValue(cmd_key, "")
                    return current_command
            except FileNotFoundError:
                return None
        
        for protocol in protocols:
            key_path = f"Software\\Classes\\{protocol}"
            command_path = f"{key_path}\\shell\\open\\command"
            
            # Проверяем оба места в реестре
            hkcu_command = check_protocol_registration(protocol, winreg.HKEY_CURRENT_USER)
            hklm_command = None
            try:
                hklm_command = check_protocol_registration(protocol, winreg.HKEY_LOCAL_MACHINE)
            except PermissionError:
                # Нет прав на чтение HKEY_LOCAL_MACHINE - это нормально
                pass
            
            # Определяем, какая регистрация активна (HKCU имеет приоритет)
            active_command = hkcu_command or hklm_command
            
            # Для протокола sing-box:// проверяем, не зарегистрирован ли он официальным sing-box
            if protocol == "sing-box":
                if active_command:
                    # Проверяем, не указывает ли команда на официальный sing-box.exe
                    if "sing-box.exe" in active_command.lower() and "singbox-ui.exe" not in active_command.lower():
                        continue
                    # Если это наша старая регистрация - обновим
                    if hkcu_command and hkcu_command != command:
                        pass  # Обновим без логов
                    elif not hkcu_command and hklm_command:
                        pass  # Создадим без логов
            
            # Для singbox-ui:// всегда обновляем (это наш уникальный протокол)
            else:  # singbox-ui
                if hkcu_command == command:
                    continue  # Уже зарегистрирован правильно
                elif hkcu_command:
                    pass  # Обновим без логов
                else:
                    pass  # Создадим без логов
            
            # Создаем/обновляем ключ протокола в HKEY_CURRENT_USER (имеет приоритет)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"URL:{protocol} Protocol")
                winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            # Создаем/обновляем ключ для команды по умолчанию
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, command)
        
        return True
    except Exception:
        return False


def is_admin() -> bool:
    """
    Проверяет, запущено ли приложение от имени администратора
    
    Returns:
        True если приложение запущено от имени администратора
    """
    if sys.platform != "win32":
        return False
    
    try:
        # Проверяем, является ли текущий процесс администратором
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def restart_as_admin() -> bool:
    """
    Перезапускает приложение от имени администратора
    
    Returns:
        True если перезапуск успешно инициирован
    """
    if sys.platform != "win32":
        return False
    
    if is_admin():
        return False
    
    try:
        # Получаем путь к исполняемому файлу
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            base_params = [arg for arg in sys.argv[1:] if arg != "--ignore-single-instance"]
            base_params.append("--ignore-single-instance")
            params = " ".join(f'"{arg}"' for arg in base_params)
            work_dir = str(Path(exe_path).parent)
        else:
            # В режиме разработки запускаем main/main.py через Python
            exe_path = sys.executable
            script_path = Path(__file__).parent.parent / "main" / "main.py"
            base_params = [arg for arg in sys.argv[1:] if arg != "--ignore-single-instance"]
            base_params.append("--ignore-single-instance")
            params = f'"{script_path}" ' + " ".join(f'"{arg}"' for arg in base_params)
            work_dir = str(Path(__file__).parent.parent)
        
        # Перезапускаем с правами администратора
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
        
        # Даем время новому процессу запуститься перед закрытием старого
        # Это важно для корректной работы QSharedMemory и трея
        import time
        time.sleep(1)  # Ждем 1 секунду, чтобы новый процесс начал запускаться
        
        # Закрываем старое приложение
        try:
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                # Используем processEvents чтобы дать время новому процессу запуститься
                for _ in range(10):
                    app.processEvents()
                    time.sleep(0.1)
                # Закрываем приложение
                app.quit()
        except ImportError:
            # Если PyQt5 не доступен, просто возвращаем True
            pass
        
        return True
    except Exception:
        return False

