"""
Обработчик deep links
Обработка протоколов sing-box:// и singbox-ui:// для импорта подписок
"""
import sys
from urllib.parse import urlparse, unquote
from typing import TYPE_CHECKING
from utils.i18n import tr
from ui.design.component import show_info_dialog

if TYPE_CHECKING:
    from main import MainWindow


class DeepLinkHandler:
    """Обработчик deep links"""
    
    def __init__(self, main_window: 'MainWindow'):
        """
        Инициализация обработчика
        
        Args:
            main_window: Ссылка на главное окно
        """
        self.main_window = main_window
    
    def handle(self) -> None:
        """Обработка deep link для импорта подписки (поддержка sing-box:// и singbox-ui://)"""
        # Проверяем аргументы командной строки
        args = sys.argv[1:] if len(sys.argv) > 1 else []
        
        if not args:
            return
        
        for arg in args:
            # Убираем кавычки если есть (Windows может передавать аргументы в кавычках)
            arg = arg.strip('"\'')
            
            # Проверяем, является ли аргумент URL
            if arg.startswith('http://') or arg.startswith('https://') or arg.startswith('sing-box://') or arg.startswith('singbox-ui://'):
                url = self._normalize_url(arg)
                if url:
                    self._import_subscription(url)
                    break  # Обрабатываем только первый URL
    
    def _normalize_url(self, arg: str) -> str:
        """
        Нормализация URL из deep link
        
        Args:
            arg: Исходный аргумент (может содержать протокол sing-box:// или singbox-ui://)
        
        Returns:
            Нормализованный URL или пустая строка если невалидный
        """
        url = arg
        
        if url.startswith('sing-box://'):
            # Убираем протокол sing-box://
            url = url.replace('sing-box://', '', 1)
            # Декодируем URL (sing-box передает URL в encoded виде)
            url = unquote(url)
            # Если после протокола нет http:// или https://, добавляем https://
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
        elif url.startswith('singbox-ui://'):
            # Убираем протокол singbox-ui://
            url = url.replace('singbox-ui://', '', 1)
            # Декодируем URL (может быть в encoded виде)
            url = unquote(url)
            # Если после протокола нет http:// или https://, добавляем https://
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
        
        # Убираем лишние пробелы и нормализуем URL
        url = url.strip()
        return url
    
    def _import_subscription(self, url: str) -> None:
        """
        Импорт подписки из URL
        
        Args:
            url: URL подписки
        """
        # Извлекаем имя из URL (можно использовать часть URL или параметры)
        parsed = urlparse(url)
        
        # Пытаемся извлечь имя из фрагмента или параметров
        name = None
        if parsed.fragment:
            # Пытаемся извлечь имя из фрагмента (например, [tg_5818132224]_ang3el_(cdn_1))
            fragment = parsed.fragment
            # Убираем квадратные скобки и другие символы
            if '_' in fragment:
                parts = fragment.split('_')
                if len(parts) > 1:
                    name = '_'.join(parts[1:])  # Берем все после первого подчеркивания
                    # Убираем скобки и другие символы
                    name = name.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
        
        # Если имя не найдено, используем домен или путь
        if not name or len(name) < 3:
            if parsed.netloc:
                name = parsed.netloc.split('.')[0] if '.' in parsed.netloc else parsed.netloc
            elif parsed.path:
                name = parsed.path.split('/')[-1] if '/' in parsed.path else parsed.path
            else:
                name = "Imported Subscription"
        
        # Ограничиваем длину имени
        if len(name) > 50:
            name = name[:50]
        
        # Проверяем, нет ли уже такой подписки (сравниваем нормализованные URL)
        existing_urls = [s.get("url", "").strip() for s in self.main_window.subs.data.get("subscriptions", [])]
        if url in existing_urls:
            self.main_window.log(tr("messages.subscription_already_exists"))
            show_info_dialog(
                self.main_window,
                tr("messages.subscription_exists_title"),
                tr("messages.subscription_exists_text")
            )
            return
        
        # Добавляем подписку
        try:
            self.main_window.subs.add(name, url)
            self.main_window.refresh_subscriptions_ui()
            self.main_window.log(tr("profile.added", name=name))
            
            # Показываем уведомление
            show_info_dialog(
                self.main_window,
                tr("messages.subscription_imported_title"),
                tr("messages.subscription_imported_text", name=name),
                success=True
            )
            
            # Переключаемся на страницу профилей
            self.main_window.switch_page(0)
        except Exception as e:
            from utils.logger import log_to_file
            log_to_file(f"[Deep Link] Error importing subscription: {e}")
            self.main_window.log(tr("messages.subscription_import_error", error=str(e)))
            show_info_dialog(
                self.main_window,
                tr("messages.subscription_import_error_title"),
                tr("messages.subscription_import_error_text", error=str(e))
            )

