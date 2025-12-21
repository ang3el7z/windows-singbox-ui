"""Конфигурация путей приложения"""
import sys
from pathlib import Path

# Импортируем log_to_file если доступен (может быть недоступен при первом запуске)
try:
    from utils.logger import log_to_file
except ImportError:
    # Если модуль еще не загружен, используем простой print
    def log_to_file(msg: str, log_file=None):
        print(msg)

# Определяем корневую папку: для exe - папка с exe, для .py - папка с .py
if getattr(sys, 'frozen', False):
    # Запущено как exe - папка где находится exe файл
    # Если exe в _internal, берем родительскую папку
    exe_path = Path(sys.executable)
    if exe_path.parent.name == '_internal':
        ROOT = exe_path.parent.parent
    else:
        ROOT = exe_path.parent
else:
    # Запущено как скрипт
    ROOT = Path(__file__).resolve().parent.parent

# Основные директории
DATA_DIR = ROOT / "data"
CORE_DIR = DATA_DIR / "core"
LOG_DIR = DATA_DIR / "logs"
LOCALES_DIR = ROOT / "locales"

# Файлы
SUB_FILE = DATA_DIR / ".subscriptions"
SETTINGS_FILE = DATA_DIR / ".settings"
CORE_EXE = CORE_DIR / "sing-box.exe"
CONFIG_FILE = DATA_DIR / "config.json"
LOG_FILE = LOG_DIR / "singbox.log"
DEBUG_LOG_FILE = LOG_DIR / "debug.log"


def ensure_dirs():
    """Создает все необходимые папки и проверяет их создание"""
    dirs_to_create = [DATA_DIR, CORE_DIR, LOG_DIR, LOCALES_DIR]
    for p in dirs_to_create:
        try:
            p.mkdir(parents=True, exist_ok=True)
            # Проверяем что папка действительно создана
            if not p.exists():
                raise Exception(f"Не удалось создать папку: {p}")
        except Exception as e:
            log_to_file(f"ОШИБКА создания папки {p}: {e}")
            raise
    log_to_file(f"Папки созданы/проверены:")
    log_to_file(f"  ROOT: {ROOT}")
    log_to_file(f"  DATA_DIR: {DATA_DIR}")
    log_to_file(f"  CORE_DIR: {CORE_DIR}")
    log_to_file(f"  LOG_DIR: {LOG_DIR}")
    log_to_file(f"  LOCALES_DIR: {LOCALES_DIR}")

