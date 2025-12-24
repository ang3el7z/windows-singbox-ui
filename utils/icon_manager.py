"""
Централизованный менеджер иконок (PyQt5 >= 5.15)
Иконка полностью зашита через Qt Resource System
"""

import ctypes
from PyQt5.QtGui import QIcon
from typing import Optional

# ОБЯЗАТЕЛЬНО: регистрирует ресурсы Qt
try:
    import scripts.resources_rc  # noqa: F401
except ImportError:
    # В режиме разработки, если resources_rc.py еще не создан
    pass

try:
    from utils.logger import log_to_file
except ImportError:
    def log_to_file(msg: str):
        pass


class IconManager:
    """
    Менеджер иконок приложения
    Использует Qt Resource System для зашивания иконки в код
    """
    
    _instance: Optional["IconManager"] = None
    _icon: Optional[QIcon] = None
    _initialized: bool = False

    APP_ICON_PATH = ":/icons/app.ico"
    APP_USER_MODEL_ID = "com.singbox.ui.app"

    def __new__(cls):
        """Singleton паттерн"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Инициализация менеджера иконок"""
        if self._initialized:
            return

        self._set_app_user_model_id()
        self._icon = self._load_icon()

        self._initialized = True

    def _set_app_user_model_id(self):
        """
        Критично для корректной иконки в таскбаре Windows
        Устанавливает AppUserModelID для правильного отображения иконки
        """
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                self.APP_USER_MODEL_ID
            )
            log_to_file("[IconManager] ✓ AppUserModelID установлен")
        except Exception as e:
            log_to_file(f"[IconManager] ⚠ Не удалось установить AppUserModelID: {e}")

    def _load_icon(self) -> QIcon:
        """
        Загружает иконку из Qt Resource System
        
        Returns:
            QIcon объект с иконкой приложения
            
        Raises:
            RuntimeError: если иконка не загружена из QRC
        """
        icon = QIcon(self.APP_ICON_PATH)
        if icon.isNull():
            error_msg = "❌ Не удалось загрузить иконку из Qt Resource"
            log_to_file(f"[IconManager] {error_msg}")
            raise RuntimeError(error_msg)
        
        log_to_file(f"[IconManager] ✓ Иконка успешно загружена из QRC: {self.APP_ICON_PATH}")
        return icon

    def get_icon(self) -> QIcon:
        """
        Получить иконку приложения
        
        Returns:
            QIcon объект с иконкой
        """
        if self._icon is None:
            self._icon = self._load_icon()
        return self._icon

    def set_application_icon(self, app) -> bool:
        """
        Устанавливает иконку для QApplication
        
        Args:
            app: Экземпляр QApplication
            
        Returns:
            True если иконка успешно установлена, False иначе
        """
        icon = self.get_icon()
        if not icon.isNull():
            app.setWindowIcon(icon)
            log_to_file("[IconManager] ✓ Иконка установлена для QApplication")
            return True
        else:
            log_to_file("[IconManager] ✗ Не удалось установить иконку для QApplication (иконка пустая)")
            return False

    def set_window_icon(self, window) -> bool:
        """
        Устанавливает иконку для окна
        
        Args:
            window: Экземпляр QMainWindow или QWidget
            
        Returns:
            True если иконка успешно установлена, False иначе
        """
        icon = self.get_icon()
        if not icon.isNull():
            window.setWindowIcon(icon)
            log_to_file("[IconManager] ✓ Иконка установлена для окна")
            return True
        else:
            log_to_file("[IconManager] ✗ Не удалось установить иконку для окна (иконка пустая)")
            return False

    # Алиасы для обратной совместимости
    def icon(self) -> QIcon:
        """Алиас для get_icon()"""
        return self.get_icon()

    def apply_to_app(self, app) -> None:
        """Алиас для set_application_icon()"""
        self.set_application_icon(app)

    def apply_to_window(self, window) -> None:
        """Алиас для set_window_icon()"""
        self.set_window_icon(window)


def get_icon() -> QIcon:
    """
    Получить иконку приложения (удобная функция)
    
    Returns:
        QIcon объект с иконкой
    """
    return IconManager().get_icon()


def set_application_icon(app) -> bool:
    """
    Установить иконку для QApplication (удобная функция)
    
    Args:
        app: Экземпляр QApplication
        
    Returns:
        True если иконка успешно установлена, False иначе
    """
    return IconManager().set_application_icon(app)


def set_window_icon(window) -> bool:
    """
    Установить иконку для окна (удобная функция)
    
    Args:
        window: Экземпляр QMainWindow или QWidget
        
    Returns:
        True если иконка успешно установлена, False иначе
    """
    return IconManager().set_window_icon(window)
