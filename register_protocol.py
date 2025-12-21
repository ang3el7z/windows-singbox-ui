"""Скрипт для регистрации протоколов sing-box:// и singbox-ui:// в Windows"""
import sys
import winreg
import os
import ctypes
from pathlib import Path

def register_protocol():
    """Регистрация протоколов sing-box:// и singbox-ui:// в Windows"""
    protocols = ["sing-box", "singbox-ui"]  # Регистрируем оба протокола
    
    # Получаем путь к exe файлу
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        # В режиме разработки используем python скрипт
        exe_path = sys.executable
        script_path = Path(__file__).parent / "main.py"
        exe_path = f'"{exe_path}" "{script_path}"'
    
    try:
        for protocol in protocols:
            # Регистрируем протокол в HKEY_CURRENT_USER
            key_path = f"Software\\Classes\\{protocol}"
            
            # Создаем ключ протокола
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"URL:{protocol} Protocol")
                winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            # Создаем ключ для команды по умолчанию
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\shell\\open\\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{exe_path}" "%1"')
            
            print(f"Протокол {protocol}:// успешно зарегистрирован!")
        
        print(f"\nТеперь можно использовать ссылки вида:")
        print(f"  sing-box://https://example.com/subscription")
        print(f"  singbox-ui://https://example.com/subscription")
        return True
    except Exception as e:
        print(f"Ошибка регистрации протокола: {e}")
        return False

if __name__ == "__main__":
    if sys.platform != "win32":
        print("Этот скрипт работает только в Windows")
        sys.exit(1)
    
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("Для регистрации протокола требуются права администратора")
        print("Запустите скрипт от имени администратора")
        sys.exit(1)
    
    register_protocol()

