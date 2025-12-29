"""
Менеджер логов для UI
Управление загрузкой, обновлением и очисткой логов в интерфейсе
"""
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from config.paths import LOG_FILE, SINGBOX_CORE_LOG_FILE
from utils.logger import log_to_file

if TYPE_CHECKING:
    from main import MainWindow
    from PyQt5.QtWidgets import QTextEdit


class LogUIManager:
    """Менеджер логов для UI"""

    # Удаляем ANSI-цвета, чтобы логи SingBox отображались без управляющих последовательностей
    _ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    
    def __init__(self, main_window: 'MainWindow'):
        """
        Инициализация менеджера логов
        
        Args:
            main_window: Ссылка на главное окно
        """
        self.main_window = main_window
    
    def load_logs(self, logs_widget: Optional['QTextEdit'] = None) -> None:
        """
        Загрузка логов приложения в виджет
        
        Args:
            logs_widget: Виджет для отображения логов (если None, используется page_settings.logs)
        """
        if logs_widget is None:
            if not hasattr(self.main_window, 'page_settings') or not hasattr(self.main_window.page_settings, 'logs'):
                return
            logs_widget = self.main_window.page_settings.logs
        
        combined = self.get_logs()
        if logs_widget:
            logs_widget.setPlainText(combined)
            cursor = logs_widget.textCursor()
            cursor.movePosition(cursor.End)
            logs_widget.setTextCursor(cursor)
    
    def load_debug_logs(self, debug_logs_widget: Optional['QTextEdit'] = None) -> None:
        """
        Загрузка логов приложения (для обратной совместимости, теперь использует тот же файл что и load_logs)
        
        Args:
            debug_logs_widget: Виджет для отображения логов (если None, используется page_settings.debug_logs)
        """
        self.load_logs(debug_logs_widget)
    
    def _load_logs_from_file(self, widget: 'QTextEdit', log_file: Path) -> None:
        """
        Загрузка логов из файла в виджет
        
        Args:
            widget: Виджет для отображения логов
            log_file: Путь к файлу логов
        """
        if not log_file.exists():
            return
        
        try:
            with log_file.open("r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split('\n')
                formatted_lines = []
                for line in lines:
                    formatted = self._format_line(line)
                    if formatted:
                        formatted_lines.append(formatted)
                formatted_content = '\n'.join(formatted_lines)
                widget.setPlainText(formatted_content)
                cursor = widget.textCursor()
                cursor.movePosition(cursor.End)
                widget.setTextCursor(cursor)
        except Exception:
            pass
    
    def _get_logs_from_file(self, log_file: Path) -> str:
        """
        Получение логов из файла в виде строки
        
        Args:
            log_file: Путь к файлу логов
            
        Returns:
            Строка с логами
        """
        if not log_file.exists():
            return ""
        
        try:
            with log_file.open("r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split('\n')
                formatted_lines = []
                for line in lines:
                    formatted = self._format_line(line)
                    if formatted:
                        formatted_lines.append(formatted)
                return '\n'.join(formatted_lines)
        except Exception:
            return ""
    
    def get_logs(self) -> str:
        """
        Получение логов приложения в виде строки
        
        Returns:
            Строка с логами из singbox-ui.log
        """
        return self._get_logs_from_file(LOG_FILE)
    
    def get_debug_logs(self) -> str:
        """
        Получение логов приложения (для обратной совместимости, теперь использует тот же файл что и get_logs)
        
        Returns:
            Строка с логами приложения
        """
        return self.get_logs()
    
    def load_singbox_logs(self, singbox_logs_widget: Optional['QTextEdit'] = None) -> None:
        """
        Загрузка логов sing-box из singbox.log в виджет
        
        Args:
            singbox_logs_widget: Виджет для отображения логов sing-box (если None, используется page_settings.singbox_logs)
        """
        if singbox_logs_widget is None:
            if not hasattr(self.main_window, 'page_settings') or not hasattr(self.main_window.page_settings, 'singbox_logs'):
                return
            singbox_logs_widget = self.main_window.page_settings.singbox_logs
        
        self._load_logs_from_file(singbox_logs_widget, SINGBOX_CORE_LOG_FILE)
    
    def get_singbox_logs(self) -> str:
        """
        Получение логов sing-box из singbox.log в виде строки
        
        Returns:
            Строка с логами sing-box
        """
        return self._get_logs_from_file(SINGBOX_CORE_LOG_FILE)
    
    def refresh_logs(self, current_page_index: int = None) -> None:
        """
        Обновление логов из файлов
        
        Этот метод не выполняет обновление виджетов, так как логи теперь в отдельном окне,
        которое само обновляет логи через свой таймер (каждые 500мс).
        
        Args:
            current_page_index: Индекс текущей страницы (не используется, оставлен для совместимости)
        """
        pass
    
    def cleanup_if_needed(self) -> None:
        """Очистка логов раз в сутки (полная очистка файла)"""
        try:
            last_cleanup = self.main_window.settings.get("last_log_cleanup", None)
            now = datetime.now()
            
            if last_cleanup:
                # Парсим дату последней очистки
                try:
                    last_date = datetime.fromisoformat(last_cleanup)
                    # Проверяем, прошло ли больше суток
                    time_diff = now - last_date
                    if time_diff.total_seconds() < 24 * 60 * 60:  # Меньше 24 часов
                        return  # Еще не прошло сутки
                except (ValueError, TypeError):
                    # Если дата некорректная, считаем что нужно очистить
                    pass
            
            # Полностью очищаем все файлы логов (singbox-ui.log и singbox.log)
            if LOG_FILE.exists():
                try:
                    # Получаем размер файла для информации
                    file_size = LOG_FILE.stat().st_size
                    # Полностью очищаем файл
                    LOG_FILE.write_text("", encoding="utf-8")
                    self.main_window._log_version_debug(f"[Log Cleanup] singbox-ui.log очищен (было {file_size} байт)")
                except Exception as e:
                    self.main_window._log_version_debug(f"[Log Cleanup] Ошибка при очистке singbox-ui.log: {e}")
            
            if SINGBOX_CORE_LOG_FILE.exists():
                try:
                    # Получаем размер файла для информации
                    file_size = SINGBOX_CORE_LOG_FILE.stat().st_size
                    # Полностью очищаем файл
                    SINGBOX_CORE_LOG_FILE.write_text("", encoding="utf-8")
                    self.main_window._log_version_debug(f"[Log Cleanup] singbox.log очищен (было {file_size} байт)")
                except Exception as e:
                    self.main_window._log_version_debug(f"[Log Cleanup] Ошибка при очистке singbox.log: {e}")
            
            # Сохраняем дату последней очистки
            self.main_window.settings.data["last_log_cleanup"] = now.isoformat()
            self.main_window.settings.save()
        except Exception as e:
            # Не критично, просто логируем
            log_to_file(f"[Log Cleanup] Ошибка: {e}")
    
    def log_to_ui(self, msg: str) -> None:
        """
        Логирование в UI панель
        
        Args:
            msg: Сообщение для логирования
        """
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        
        # Показываем в UI (это для пользователя - только важные сообщения)
        if hasattr(self.main_window, 'page_settings') and hasattr(self.main_window.page_settings, 'logs'):
            self.main_window.page_settings.logs.append(line)
            cursor = self.main_window.page_settings.logs.textCursor()
            cursor.movePosition(cursor.End)
            self.main_window.page_settings.logs.setTextCursor(cursor)

    def _format_line(self, line: str) -> str:
        """
        Приводит строку лога к компактному виду без ANSI-кодов и с временем в формате [HH:MM:SS].
        Поддерживает:
        - Формат приложения: [YYYY-MM-DD HH:MM:SS] ...
        - Формат SingBox: +0300 2025-12-28 19:31:02 ERROR ...
        - Уже нормализованный формат [HH:MM:SS] ...
        """
        if not line:
            return ""

        # Удаляем ANSI управляющие последовательности
        line = self._ANSI_RE.sub("", line)

        # Нормализация разных форматов времени к [HH:MM:SS]
        # 1) [YYYY-MM-DD HH:MM:SS] -> [HH:MM:SS]
        line = re.sub(r'\[\d{4}-\d{2}-\d{2} (\d{2}:\d{2}:\d{2})\]', r'[\1]', line)
        # 2) +0300 2025-12-28 19:31:02 ... -> [19:31:02] ...
        line = re.sub(
            r'^\+\d{4}\s+\d{4}-\d{2}-\d{2}\s+(\d{2}:\d{2}:\d{2})\s+',
            r'[\1] ',
            line
        )

        line = line.strip()
        return line

