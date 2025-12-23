"""
Менеджер системного трея
Управление созданием, настройкой и удалением иконки в системном трее
"""
import sys
from pathlib import Path
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication, QStyle
from PyQt5.QtGui import QIcon
from utils.i18n import tr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import MainWindow


class TrayManager:
    """Менеджер системного трея"""
    
    def __init__(self, main_window: 'MainWindow'):
        """
        Инициализация менеджера трея
        
        Args:
            main_window: Ссылка на главное окно
        """
        self.main_window = main_window
        self.tray_icon: QSystemTrayIcon = None
    
    def setup(self) -> bool:
        """
        Настройка системного трея
        
        Returns:
            True если трей успешно настроен, False иначе
        """
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return False
        
        # Создаем иконку для трея
        tray_icon = self._load_icon()
        
        self.tray_icon = QSystemTrayIcon(self.main_window)
        # Если иконка не найдена, используем системную иконку вместо пустой
        if tray_icon.isNull():
            tray_icon = QApplication.instance().style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(tray_icon)
        self.tray_icon.setToolTip(tr("app.title"))
        
        # Создаем контекстное меню для трея
        self._create_menu()
        
        # Обработка клика по иконке трея
        self.tray_icon.activated.connect(self._on_activated)
        
        # Показываем иконку в трее
        self.tray_icon.show()
        return True
    
    def _load_icon(self) -> QIcon:
        """
        Загрузка иконки для трея
        
        Returns:
            QIcon объект с иконкой
        """
        tray_icon = QIcon()
        
        if getattr(sys, 'frozen', False):
            # В frozen режиме (PyInstaller) используем sys._MEIPASS для доступа к ресурсам
            base_path = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
            
            # Пробуем загрузить иконку из временной папки PyInstaller (icons/)
            icon_path = base_path / "icons" / "icon.ico"
            if not icon_path.exists():
                icon_path = base_path / "icon.ico"
            if icon_path.exists():
                tray_icon = QIcon(str(icon_path))
            
            # Если не нашли .ico, пробуем .png
            if tray_icon.isNull():
                icon_path = base_path / "icons" / "icon.png"
                if not icon_path.exists():
                    icon_path = base_path / "icon.png"
                if icon_path.exists():
                    tray_icon = QIcon(str(icon_path))
            
            # Если не нашли в _MEIPASS, пробуем рядом с exe
            if tray_icon.isNull():
                exe_path = Path(sys.executable)
                icon_path = exe_path.parent / "icons" / "icon.ico"
                if not icon_path.exists():
                    icon_path = exe_path.parent / "icon.ico"
                if icon_path.exists():
                    tray_icon = QIcon(str(icon_path))
                else:
                    icon_path = exe_path.parent / "icons" / "icon.png"
                    if not icon_path.exists():
                        icon_path = exe_path.parent / "icon.png"
                    if icon_path.exists():
                        tray_icon = QIcon(str(icon_path))
            
            # Если не нашли, пробуем извлечь из exe
            if tray_icon.isNull():
                exe_path = Path(sys.executable)
                tray_icon = QIcon(str(exe_path))
        else:
            # В режиме разработки используем icons/icon.ico или icons/icon.png
            root = Path(__file__).parent.parent
            icon_path = root / "icons" / "icon.ico"
            if icon_path.exists():
                tray_icon = QIcon(str(icon_path))
            else:
                icon_path = root / "icons" / "icon.png"
                if icon_path.exists():
                    tray_icon = QIcon(str(icon_path))
            
            # Если не нашли в icons/, пробуем иконку окна
            if tray_icon.isNull():
                tray_icon = self.main_window.windowIcon()
            if tray_icon.isNull():
                icon_path = Path(__file__).parent.parent / "icon.ico"
                if icon_path.exists():
                    tray_icon = QIcon(str(icon_path))
                else:
                    icon_path = Path(__file__).parent.parent / "icon.png"
                    if icon_path.exists():
                        tray_icon = QIcon(str(icon_path))
        
        return tray_icon
    
    def _create_menu(self) -> None:
        """Создание контекстного меню для трея"""
        tray_menu = QMenu(self.main_window)
        
        # Действие "Открыть"
        show_action = QAction(tr("tray.show"), self.main_window)
        show_action.triggered.connect(self.main_window.show)
        show_action.triggered.connect(self.main_window.raise_)
        show_action.triggered.connect(self.main_window.activateWindow)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # Действие "Закрыть"
        quit_action = QAction(tr("tray.quit"), self.main_window)
        quit_action.triggered.connect(self.main_window.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
    
    def _on_activated(self, reason: int) -> None:
        """
        Обработка активации иконки трея
        
        Args:
            reason: Причина активации (QSystemTrayIcon.ActivationReason)
        """
        if reason == QSystemTrayIcon.DoubleClick:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
    
    def show(self) -> None:
        """Показать иконку в трее"""
        if self.tray_icon:
            self.tray_icon.show()
    
    def hide(self) -> None:
        """Скрыть иконку в трее"""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def is_visible(self) -> bool:
        """
        Проверка видимости иконки
        
        Returns:
            True если иконка видна, False иначе
        """
        return self.tray_icon.isVisible() if self.tray_icon else False
    
    def show_message(self, title: str, message: str, icon: int = QSystemTrayIcon.Information, duration: int = 2000) -> None:
        """
        Показать уведомление в трее
        
        Args:
            title: Заголовок уведомления
            message: Сообщение
            icon: Тип иконки (QSystemTrayIcon.Information, Warning, Critical)
            duration: Длительность показа в миллисекундах
        """
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, duration)
    
    def cleanup(self) -> None:
        """Очистка ресурсов трея"""
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
            self.tray_icon = None

