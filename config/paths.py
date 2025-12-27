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
    exe_path = Path(sys.executable)
    exe_dir = exe_path.parent
    
    # Если exe в _internal, берем родительскую папку
    if exe_dir.name == '_internal':
        ROOT = exe_dir.parent
    # Если exe в папке data (например updater.exe), берем родительскую папку
    # чтобы ROOT указывал на корень приложения, а не на data
    elif exe_dir.name == 'data':
        ROOT = exe_dir.parent
    else:
        ROOT = exe_dir
else:
    # Запущено как скрипт
    ROOT = Path(__file__).resolve().parent.parent

# Основные директории
DATA_DIR = ROOT / "data"
CORE_DIR = DATA_DIR / "core"
LOG_DIR = DATA_DIR / "logs"
LOCALES_DIR = DATA_DIR / "locales"
THEMES_DIR = DATA_DIR / "themes"

# Ресурсы (для разработки - исходники)
SOURCE_RESOURCES_DIR = ROOT / "resources"
# Ресурсы в data (для собранного приложения)
RESOURCES_DIR = DATA_DIR / "resources"
ACE_EDITOR_DIR = RESOURCES_DIR / "web" / "ace"

# Файлы
PROFILE_FILE = DATA_DIR / ".profile"
SETTINGS_FILE = DATA_DIR / ".settings"
CORE_EXE = CORE_DIR / "sing-box.exe"
CONFIG_FILE = DATA_DIR / "config.json"
LOG_FILE = LOG_DIR / "singbox.log"
DEBUG_LOG_FILE = LOG_DIR / "debug.log"
SINGBOX_CORE_LOG_FILE = LOG_DIR / "singbox-core.log"


def ensure_dirs():
    """Создает все необходимые папки и проверяет их создание"""
    dirs_to_create = [DATA_DIR, CORE_DIR, LOG_DIR, LOCALES_DIR, THEMES_DIR, ACE_EDITOR_DIR]
    for p in dirs_to_create:
        try:
            p.mkdir(parents=True, exist_ok=True)
            # Проверяем что папка действительно создана
            if not p.exists():
                raise Exception(f"Не удалось создать папку: {p}")
        except Exception as e:
            log_to_file(f"ОШИБКА создания папки {p}: {e}")
            raise

