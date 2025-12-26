"""
Менеджер системного трея
Управление созданием, настройкой и удалением иконки в системном трее
"""
import sys
from pathlib import Path
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication, QStyle
from typing import Union
from PyQt5.QtGui import QIcon
from utils.i18n import tr
from utils.icon_manager import get_icon
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
        
        Использует централизованный IconManager для получения той же иконки,
        что используется в приложении и окне.
        
        Returns:
            QIcon объект с иконкой
        """
        # Используем централизованный менеджер иконок
        tray_icon = get_icon()
        
        # Если иконка не загружена, используем системную иконку как fallback
        if tray_icon.isNull():
            tray_icon = QApplication.instance().style().standardIcon(QStyle.SP_ComputerIcon)
        
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
    
    def show_message(self, title: str, message: str, icon: Union[int, QSystemTrayIcon.MessageIcon] = QSystemTrayIcon.Information, duration: int = 2000) -> None:
        """
        Показать уведомление в трее
        
        Args:
            title: Заголовок уведомления
            message: Сообщение
            icon: Тип иконки (QSystemTrayIcon.Information, Warning, Critical)
            duration: Длительность показа в миллисекундах
        """
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, timeout=duration)  # type: ignore
    
    def update_menu(self) -> None:
        """Обновление меню трея (например, при смене языка)"""
        if not self.tray_icon:
            return
        
        # Обновляем tooltip
        self.tray_icon.setToolTip(tr("app.title"))
        
        # Пересоздаем меню с новыми переводами
        self._create_menu()
    
    def cleanup(self) -> None:
        """Очистка ресурсов трея"""
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
            self.tray_icon = None

