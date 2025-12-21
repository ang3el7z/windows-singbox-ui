"""Утилиты для работы с SingBox"""
import subprocess
import re
import sys
import requests
from pathlib import Path
from config.paths import CORE_EXE

# Импортируем log_to_file если доступен
try:
    from utils.logger import log_to_file
except ImportError:
    # Если модуль еще не загружен, используем простой print
    def log_to_file(msg: str, log_file=None):
        print(msg)

def _log_version_check(msg: str):
    """Логирование для проверки версий"""
    log_to_file(msg)


def get_singbox_version() -> str:
    """Получить версию singbox"""
    if not CORE_EXE.exists():
        return None
    try:
        # Скрываем окно консоли
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        result = subprocess.run(
            [str(CORE_EXE), "version"],
            capture_output=True,
            text=True,
            timeout=5,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            # Извлекаем версию из вывода (например, "sing-box version 1.11.4")
            match = re.search(r'(\d+\.\d+\.\d+)', version)
            if match:
                return match.group(1)
            return version
    except Exception:
        pass
    return None


def get_latest_version() -> str:
    """
    Получить последнюю версию SingBox с GitHub
    Returns: версия в формате "x.y.z" или None при ошибке
    """
    try:
        api_url = "https://api.github.com/repos/SagerNet/sing-box/releases/latest"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        release_data = response.json()
        tag_name = release_data.get("tag_name", "")
        
        if not tag_name:
            _log_version_check("[Version Check] Пустой tag_name в ответе API")
            return None
        
        # Убираем 'v' из начала если есть (например, "v1.11.4" -> "1.11.4")
        version = tag_name.lstrip('v')
        
        # Проверяем формат версии (может быть "1.11.4" или "1.11.4-beta.1")
        match = re.match(r'^(\d+\.\d+\.\d+)', version)
        if match:
            version = match.group(1)
            _log_version_check(f"[Version Check] Получена последняя версия: {version}")
            return version
        else:
            _log_version_check(f"[Version Check] Неверный формат версии: {tag_name} -> {version}")
            return None
    except requests.exceptions.Timeout:
        _log_version_check("[Version Check] Таймаут при запросе к GitHub API")
        return None
    except requests.exceptions.RequestException as e:
        _log_version_check(f"[Version Check] Ошибка запроса к GitHub API: {e}")
        return None
    except Exception as e:
        _log_version_check(f"[Version Check] Неожиданная ошибка при получении версии: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_versions(current: str, latest: str) -> int:
    """
    Сравнивает версии
    Returns: -1 если current < latest, 0 если равны, 1 если current > latest
    """
    if not current or not latest:
        return 0
    
    try:
        current_parts = [int(x) for x in current.split('.')]
        latest_parts = [int(x) for x in latest.split('.')]
        
        # Дополняем до одинаковой длины
        max_len = max(len(current_parts), len(latest_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        latest_parts.extend([0] * (max_len - len(latest_parts)))
        
        for c, l in zip(current_parts, latest_parts):
            if c < l:
                return -1
            elif c > l:
                return 1
        return 0
    except Exception:
        return 0

