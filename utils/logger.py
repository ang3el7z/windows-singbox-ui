"""Модуль для логирования (можно использовать до инициализации MainWindow)"""
import sys
from pathlib import Path
from datetime import datetime
from config.paths import DEBUG_LOG_FILE, SETTINGS_FILE

# Глобальная ссылка на MainWindow для показа логов в UI при isDebug
_main_window_instance = None


def set_main_window(main_window):
    """Устанавливает ссылку на MainWindow для показа логов в UI"""
    global _main_window_instance
    _main_window_instance = main_window


def log_to_file(msg: str, log_file: Path = None):
    """Логирование в debug файл (всегда пишет в debug.log, UI обновляется автоматически при чтении файла)"""
    # Проверяем настройку isDebug из файла напрямую
    is_debug = False
    try:
        if SETTINGS_FILE.exists():
            import json
            settings_data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            is_debug = settings_data.get("isDebug", False)
    except Exception:
        pass
    
    # Всегда записываем в debug файл
    if log_file is None:
        log_file = DEBUG_LOG_FILE
    
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        
        # Не отправляем напрямую в UI - только через файл debug.log
        # UI будет обновляться автоматически при чтении файла
        
        # Также выводим в консоль, если доступна (только в режиме разработки)
        if not getattr(sys, 'frozen', False):
            print(line)
    except Exception as e:
        # Если не удалось записать в файл, хотя бы в консоль
        error_msg = f"[LOG ERROR] Не удалось записать в лог: {e}"
        if not getattr(sys, 'frozen', False):
            print(error_msg)
            print(f"[LOG] {msg}")

