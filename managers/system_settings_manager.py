"""Менеджер системных настроек приложения

Управляет системными настройками Windows:
- Автозапуск приложения (Task Scheduler)
- Регистрация протоколов (deep links)
- Проверка и синхронизация состояния
"""
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Literal
from enum import Enum

# Импорты для работы с реестром и протоколами
try:
    import winreg
except ImportError:
    winreg = None

# Импорты для логирования
try:
    from utils.logger import log_to_file
except ImportError:
    def log_to_file(msg: str, log_file=None):
        print(msg)

# Импорты для работы с протоколами
try:
    from core.protocol import register_protocols, unregister_protocols
except ImportError:
    def register_protocols() -> bool:
        return False
    def unregister_protocols() -> bool:
        return False


class SettingsAction(Enum):
    """Действия для управления настройками"""
    CHECK = "check"  # Проверка состояния
    APPLY = "apply"  # Применение настроек
    CLEAR = "clear"  # Очистка всех настроек


class SystemSettingsManager:
    """Менеджер системных настроек приложения"""
    
    def __init__(self, settings_manager=None):
        """
        Инициализация менеджера
        
        Args:
            settings_manager: Экземпляр SettingsManager для доступа к настройкам
        """
        self.settings = settings_manager
        self.task_name = "SingBox-UI-AutoStart"
        self.app_name = "SingBox-UI"
        
        # Определяем путь к исполняемому файлу
        if getattr(sys, "frozen", False):
            self.exe_path = Path(sys.executable).resolve()
        else:
            self.exe_path = (Path(__file__).parent.parent / "main" / "run_dev.bat").resolve()
        self.task_command = f'"{self.exe_path}"'
    
    def _check_autostart_enabled(self) -> bool:
        """
        Проверяет, включен ли автозапуск в системе
        
        Returns:
            True если автозапуск включен, False иначе
        """
        if sys.platform != "win32":
            return False
        
        try:
            # Проверяем Task Scheduler
            result = subprocess.run(
                ["schtasks", "/query", "/tn", self.task_name],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _migrate_old_autostart(self) -> bool:
        """
        Миграция: удаляет старый автозапуск из реестра (Run) если он существует.
        Этот метод должен вызываться при запуске приложения для очистки старых записей.
        
        Returns:
            True если миграция выполнена (или не требовалась), False при ошибке
        """
        if sys.platform != "win32" or not winreg:
            return True
        
        try:
            run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_ALL_ACCESS) as key:
                    try:
                        # Проверяем, существует ли старая запись
                        value = winreg.QueryValueEx(key, self.app_name)
                        # Если запись существует, удаляем её
                        winreg.DeleteValue(key, self.app_name)
                        log_to_file(f"[SystemSettings] Миграция: удален старый автозапуск из реестра (Run)")
                        return True
                    except FileNotFoundError:
                        # Записи нет - это нормально, миграция не требуется
                        return True
            except OSError:
                # Ключ не существует или нет доступа - это нормально
                return True
        except Exception as e:
            log_to_file(f"[SystemSettings] Ошибка при миграции автозапуска: {e}")
            return False
    
    def _check_protocols_registered(self) -> bool:
        """
        Проверяет, зарегистрированы ли протоколы
        
        Returns:
            True если протоколы зарегистрированы, False иначе
        """
        if sys.platform != "win32" or not winreg:
            return False
        
        try:
            protocols = ["sing-box", "singbox-ui"]
            for protocol in protocols:
                key_path = f"Software\\Classes\\{protocol}\\shell\\open\\command"
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                        command = winreg.QueryValue(key, "")
                        # Проверяем, что команда указывает на наше приложение
                        if self.exe_path.name.lower() not in command.lower() and "singbox-ui" not in command.lower():
                            return False
                except FileNotFoundError:
                    return False
            return True
        except Exception:
            return False
    
    def _set_autostart(self, enabled: bool) -> bool:
        """
        Устанавливает автозапуск приложения
        
        Args:
            enabled: True для включения, False для отключения
            
        Returns:
            True если операция успешна, False иначе
        """
        if sys.platform != "win32":
            return False
        
        try:
            # Удаляем старый способ через Run (на случай старых версий)
            if winreg:
                run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_ALL_ACCESS) as key:
                        try:
                            winreg.DeleteValue(key, self.app_name)
                        except FileNotFoundError:
                            pass
                except OSError:
                    pass
            
            # Всегда удаляем существующую задачу перед пересозданием
            subprocess.run(
                ["schtasks", "/delete", "/tn", self.task_name, "/f"],
                capture_output=True,
                check=False,
                timeout=5
            )
            
            if enabled:
                # Создаем задачу в Task Scheduler
                create_cmd = [
                    "schtasks",
                    "/create",
                    "/tn", self.task_name,
                    "/tr", self.task_command,
                    "/sc", "ONLOGON",
                    "/RL", "HIGHEST",
                    "/F",
                ]
                result = subprocess.run(
                    create_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False
                )
                if result.returncode != 0:
                    error_msg = result.stderr.strip() or result.stdout.strip() or f"schtasks exit code {result.returncode}"
                    log_to_file(f"[SystemSettings] Ошибка при создании автозапуска: {error_msg}")
                    return False
            
            return True
        except Exception as e:
            log_to_file(f"[SystemSettings] Ошибка при установке автозапуска: {e}")
            return False
    
    def _set_protocols(self, enabled: bool) -> bool:
        """
        Устанавливает регистрацию протоколов
        
        Args:
            enabled: True для регистрации, False для удаления
            
        Returns:
            True если операция успешна, False иначе
        """
        if sys.platform != "win32":
            return False
        
        try:
            if enabled:
                return register_protocols()
            else:
                return unregister_protocols()
        except Exception as e:
            log_to_file(f"[SystemSettings] Ошибка при управлении протоколами: {e}")
            return False
    
    def check(self) -> Dict[str, Any]:
        """
        Проверяет состояние всех системных настроек
        
        Returns:
            Словарь с результатами проверки:
            {
                "autostart": {"expected": bool, "actual": bool, "match": bool},
                "protocols": {"expected": bool, "actual": bool, "match": bool},
                "all_match": bool
            }
        """
        if not self.settings:
            log_to_file("[SystemSettings] SettingsManager не передан, проверка невозможна")
            return {"all_match": False}
        
        # Получаем ожидаемые значения из настроек
        expected_autostart = self.settings.get("start_with_windows", False)
        
        # Проверяем фактическое состояние
        actual_autostart = self._check_autostart_enabled()
        actual_protocols = self._check_protocols_registered()
        
        # Для протоколов всегда ожидаем True (они должны быть зарегистрированы)
        expected_protocols = True
        
        result = {
            "autostart": {
                "expected": expected_autostart,
                "actual": actual_autostart,
                "match": expected_autostart == actual_autostart
            },
            "protocols": {
                "expected": expected_protocols,
                "actual": actual_protocols,
                "match": expected_protocols == actual_protocols
            }
        }
        
        result["all_match"] = result["autostart"]["match"] and result["protocols"]["match"]
        
        return result
    
    def apply(self, settings_updates: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """
        Применяет системные настройки
        
        Args:
            settings_updates: Опциональный словарь с изменениями настроек.
                            Если None, используются значения из SettingsManager.
                            Формат: {"start_with_windows": bool, ...}
        
        Returns:
            Словарь с результатами применения:
            {"autostart": bool, "protocols": bool}
        """
        if not self.settings:
            log_to_file("[SystemSettings] SettingsManager не передан, применение невозможно")
            return {"autostart": False, "protocols": False}
        
        # Определяем значения для применения
        if settings_updates is not None:
            autostart_enabled = settings_updates.get("start_with_windows", False)
        else:
            autostart_enabled = self.settings.get("start_with_windows", False)
        
        # Применяем настройки
        autostart_result = self._set_autostart(autostart_enabled)
        protocols_result = self._set_protocols(True)  # Протоколы всегда должны быть зарегистрированы
        
        if autostart_result:
            log_to_file(f"[SystemSettings] Автозапуск применен: {autostart_enabled}")
        if protocols_result:
            log_to_file("[SystemSettings] Протоколы применены")
        
        return {
            "autostart": autostart_result,
            "protocols": protocols_result
        }
    
    def clear(self) -> Dict[str, bool]:
        """
        Очищает все системные настройки (отключает все)
        
        Returns:
            Словарь с результатами очистки:
            {"autostart": bool, "protocols": bool}
        """
        log_to_file("[SystemSettings] Очистка всех системных настроек")
        
        autostart_result = self._set_autostart(False)
        protocols_result = self._set_protocols(False)
        
        if autostart_result:
            log_to_file("[SystemSettings] Автозапуск отключен")
        if protocols_result:
            log_to_file("[SystemSettings] Протоколы удалены")
        
        return {
            "autostart": autostart_result,
            "protocols": protocols_result
        }
    
    def migrate_old_settings(self) -> bool:
        """
        Выполняет миграцию старых системных настроек (удаляет старые записи из реестра).
        Должен вызываться при запуске приложения для очистки устаревших записей.
        
        Returns:
            True если миграция выполнена успешно, False иначе
        """
        return self._migrate_old_autostart()
    
    def manage(
        self,
        action: Literal["check", "apply", "clear"],
        settings_updates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Универсальный метод управления настройками
        
        Args:
            action: Действие - "check", "apply" или "clear"
            settings_updates: Опциональный словарь с изменениями настроек (для action="apply")
        
        Returns:
            Результат выполнения действия
        """
        if action == "check":
            return self.check()
        elif action == "apply":
            return self.apply(settings_updates)
        elif action == "clear":
            return self.clear()
        else:
            log_to_file(f"[SystemSettings] Неизвестное действие: {action}")
            return {"error": f"Unknown action: {action}"}

