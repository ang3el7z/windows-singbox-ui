# Архитектура проекта SingBox-UI

## Структура проекта

```
SingBox-UI/
├── .version                # Application version file (read at startup)
├── main/                   # Main application files
│   ├── main.py            # Main application file (window management and coordination)
│   ├── updater.py         # Update utility (built as updater.exe)
│   └── post_build.py      # Post-build script
├── icons/                  # Application icons
│   ├── icon.ico           # Windows icon
│   ├── icon.png           # PNG icon
│   └── icon.svg           # SVG icon (source)
├── scripts/                # Utility scripts
│   ├── build_parallel.py   # Parallel build script (builds both exe simultaneously)
│   ├── build_qrc.py        # QRC compilation script
│   ├── check_locales.py    # Locale validation script
│   ├── create_icon.py      # Icon creation script
│   └── register_protocol.py # Protocol registration script
├── config/                 # Configuration
│   ├── __init__.py
│   └── paths.py           # File paths and directories
├── managers/              # Data managers
│   ├── __init__.py
│   ├── settings.py        # Settings manager
│   ├── subscriptions.py   # Subscriptions manager
│   └── log_ui_manager.py  # Log UI manager
├── utils/                 # Utilities
│   ├── __init__.py
│   ├── i18n.py           # Localization system
│   ├── icon_manager.py   # Icon management
│   ├── logger.py         # Logging
│   ├── singbox.py        # SingBox utilities
│   └── theme_manager.py  # Theme management
├── core/                  # Core logic
│   ├── __init__.py
│   ├── deep_link_handler.py # Deep link handler
│   ├── downloader.py     # Core downloader
│   ├── protocol.py       # Protocol registration and admin rights
│   └── singbox_manager.py # SingBox process management
├── app/                   # Application initialization
│   ├── __init__.py
│   └── application.py    # QApplication creation and theme
├── workers/               # Background threads
│   ├── __init__.py
│   ├── base_worker.py    # Base worker class
│   ├── init_worker.py    # Initialization worker (load subscriptions, versions)
│   └── version_worker.py # Version check workers
├── ui/                    # User interface
│   ├── __init__.py
│   ├── pages/            # Application pages
│   │   ├── __init__.py
│   │   ├── base_page.py  # Base page class
│   │   ├── profile_page.py # Profile management page
│   │   ├── home_page.py  # Home page
│   │   └── settings_page.py # Settings page
│   ├── widgets/          # Reusable widgets
│   │   ├── __init__.py
│   │   ├── animated_button.py # Animated button widget
│   │   ├── card.py       # Card widget
│   │   ├── logs_window.py # Logs window widget
│   │   ├── nav_button.py # Navigation button
│   │   └── version_label.py # Version label
│   ├── utils/            # UI utilities
│   │   ├── animations.py # Page transition animations
│   │   ├── responsive_layout.py # Responsive layout helpers
│   │   └── responsive_scaler.py # Responsive scaling system
│   ├── styles/           # Styling system
│   │   ├── __init__.py
│   │   ├── constants.py  # Constants (colors, fonts, sizes)
│   │   ├── theme.py      # Theme management
│   │   └── stylesheet.py # Widget stylesheet generation
│   ├── dialogs/          # Dialog windows
│   │   ├── __init__.py
│   │   ├── base_dialog.py # Base dialog class
│   │   ├── confirm_dialog.py # Confirmation dialogs
│   │   ├── info_dialog.py # Info dialogs
│   │   └── language_dialog.py # Language selection dialog
│   └── tray_manager.py   # System tray manager
├── resources/            # Resources
│   ├── app.qrc          # Qt resource file
│   └── icons/           # Icon resources
│       └── app.ico      # Application icon
├── resources_rc.py       # Compiled Qt resources (generated)
├── locales/              # Исходные файлы локализации
│   ├── ru.json           # Русский язык
│   └── en.json           # Английский язык
├── changelog/            # История изменений версий
│   ├── CHANGELOG_v1.0.0.md
│   ├── CHANGELOG_v1.0.1.md
│   ├── CHANGELOG_v1.0.2.md
│   ├── CHANGELOG_v1.0.3.md
│   └── ...
├── data/                 # Данные приложения (создается автоматически)
│   ├── core/             # Ядро SingBox
│   ├── logs/             # Логи
│   ├── locales/          # Файлы локализации (копируются из locales/)
│   ├── themes/           # Файлы тем (находятся в data/themes в исходном проекте)
│   └── config.json       # Конфиг
├── SingBox-UI.spec       # Конфигурация PyInstaller для основного приложения
├── updater.spec          # Конфигурация PyInstaller для updater
├── post_build.py         # Скрипт пост-обработки сборки
└── requirements.txt      # Зависимости
```

## Version Management

The application version is stored in the `.version` file in the project root. During build, this file is copied to `data/.version`, from where the application reads the version at startup.

The `get_version()` function in `main/main.py`:
1. First tries to read `data/.version` (for built application)
2. Then tries to read root `.version` (for development)
3. Falls back to version "1.0.0" on error

During CI/CD build by tag, the version in `.version` should be updated automatically if the tag is greater than the current version.

## Модули

### main/
- **main.py** - Main application file
  - `get_version()` function - reads version from file
  - `MainWindow` class - main application window
  - Manages pages, subscriptions, SingBox start/stop
  
- **updater.py** - Update utility
  - GUI updater window in application style
  - Update execution thread
  - Downloads update from GitHub
  - Installs update with user data protection
  
- **post_build.py** - Post-build script
  - Organizes files after build
  - Copies locales, themes, .version file
  - Creates folder structure

### icons/
- **icon.ico** - Windows icon (used in exe and tray)
- **icon.png** - PNG version of icon (fallback)
- **icon.svg** - Source SVG icon

### scripts/
- **build_parallel.py** - Parallel build script
  - Builds both SingBox-UI.exe and updater.exe simultaneously
  - Faster than sequential build
  - Automatically runs post-build script after successful builds
  
- **build_qrc.py** - QRC compilation script
  - Compiles Qt resource files (.qrc) to Python module (resources_rc.py)
  
- **check_locales.py** - Locale validation script
  - Validates locale files for missing translations
  
- **create_icon.py** - Icon creation script
  - Creates application icons in different formats
  
- **register_protocol.py** - Protocol registration script
  - Registers `sing-box://` and `singbox-ui://` in Windows
  - Requires administrator rights

### config/
- **paths.py** - Определение всех путей к файлам и директориям
- Функция `ensure_dirs()` - создание необходимых папок

### managers/
- **settings.py** - Управление настройками приложения
  - Сохранение/загрузка настроек
  - Поддержка языка интерфейса
  
- **subscriptions.py** - Управление подписками
  - CRUD операции с подписками
  - Скачивание конфигов

- **log_ui_manager.py** - Управление логами в UI
  - Класс `LogUIManager` - централизованное управление отображением логов
  - Метод `load_logs_to_ui()` - загрузка основных логов из файла в QTextEdit
  - Метод `load_debug_logs_from_file_to_ui()` - загрузка debug логов
  - Метод `refresh_logs_from_files()` - автоматическое обновление логов каждую секунду
  - Метод `cleanup_logs_if_needed()` - очистка логов раз в сутки
  - Метод `append_log_to_ui()` - добавление новой строки лога в UI
  - Метод `_auto_scroll_if_needed()` - автоматическая прокрутка логов
  - Метод `on_scroll_value_changed()` - обработка ручной прокрутки (остановка автоскролла)
  - Метод `_resume_auto_scroll()` - возобновление автоскролла после 5 секунд бездействия
  - Метод `update_debug_logs_visibility()` - управление видимостью debug логов

### utils/
- **i18n.py** - Localization system
  - `Translator` class for working with translations
  - `tr()` function for getting translations
  - String formatting support
  - Support for custom languages via `_language_name` in locale files
  
- **icon_manager.py** - Icon management
  - Icon loading from Qt resources
  - Application and window icon management
  - Uses Qt Resource System (QRC)
  
- **logger.py** - Logging system
  - Logging to files
  - Debug logs
  - Main window integration for UI log display
  
- **singbox.py** - SingBox utilities
  - Getting SingBox version
  - Checking for SingBox and application updates
  
- **theme_manager.py** - Theme management
  - Theme loading from JSON files
  - Theme switching
  - Color management
  - Available themes listing

### core/
- **protocol.py** - Protocol registration and admin rights management
  - `register_protocols()` function - registers deep link protocols
  - `is_admin()` function - checks admin rights
  - `restart_as_admin()` function - restarts with admin rights

- **singbox_manager.py** - SingBox process management
  - `SingBoxManager` class - manages process lifecycle
  - `StartSingBoxWorker` class - thread for starting SingBox

- **deep_link_handler.py** - Deep link handler
  - `DeepLinkHandler` class - handles sing-box:// and singbox-ui:// protocols
  - URL normalization and subscription import
  - Duplicate detection

- **downloader.py** - Core downloader
  - `DownloadThread` class - downloads SingBox core from GitHub
  - Progress tracking
  - Automatic extraction and installation

### app/
- **application.py** - Application initialization
  - `create_application()` function - creates and configures QApplication
  - `apply_dark_theme()` function - applies dark theme (deprecated, now uses theme system)

### workers/
- **base_worker.py** - Base class for background threads
  - `BaseWorker` class - wrapper over QThread with finished/error signals

- **init_worker.py** - Initialization worker
  - `InitOperationsWorker` class - loads subscriptions, checks versions, cleans logs

- **version_worker.py** - Version check workers
  - `CheckVersionWorker` class - checks SingBox version
  - `CheckAppVersionWorker` class - checks application version

### ui/pages/
- **base_page.py** - Base class for all pages
  - `BasePage` class - provides common layout and `add_card()` method

- **profile_page.py** - Profile management page
  - Subscription list
  - Management buttons (add, delete, rename, test)

- **home_page.py** - Home page
  - SingBox version display
  - Profile information
  - Admin status
  - Large Start/Stop button

- **settings_page.py** - Settings page
  - Application settings (autostart, update interval, language)
  - Logs (regular and debug)
  - Debug section (hidden by default)

### ui/widgets/
- **animated_button.py** - Animated button widget with loading indicator
- **card.py** - Card widget with background and rounded corners
- **logs_window.py** - Logs window widget for displaying application logs
- **nav_button.py** - Navigation button with icon and text
- **version_label.py** - Version label for displaying version information

### ui/utils/
- **animations.py** - Page transition animations
  - Slide animations for page transitions

- **responsive_layout.py** - Responsive layout helpers
  - `ResponsiveLayoutHelper` class - helpers for creating responsive layouts
  - Widget and button size calculations based on window size

- **responsive_scaler.py** - Responsive scaling system
  - `ResponsiveScaler` class - scales all UI elements proportionally to window size
  - Font size, minimum and maximum size scaling
  - Automatic scaling on window resize

### ui/styles/
- **constants.py** - UI constants (colors, fonts, sizes, transitions)
- **theme.py** - Application theme management
  - `Theme` class - centralized theme management
  - Global `theme` instance
  - Integrates with `utils.theme_manager`
  
- **stylesheet.py** - Widget stylesheet generation
  - `StyleSheet` class - static methods for generating CSS styles

### ui/dialogs/
- **base_dialog.py** - Base dialog class
  - `create_dialog()` function - universal dialog factory
  - `DialogType` enum - dialog types (INFO, CONFIRM, WARNING, SUCCESS)

- **confirm_dialog.py** - Confirmation dialogs
  - `show_confirm_dialog()` function - universal confirmation dialog
  - `show_restart_admin_dialog()` function - admin restart dialog
  - `show_kill_all_confirm_dialog()` function - process termination confirmation dialog

- **info_dialog.py** - Info dialogs
  - `show_info_dialog()` function - universal info dialog
  - `show_kill_all_success_dialog()` function - process termination success dialog

- **language_dialog.py** - Language selection dialog
  - `show_language_selection_dialog()` function - language selection dialog on first run

### ui/
- **tray_manager.py** - System tray manager
  - `TrayManager` class - manages creation, configuration and removal of tray icon
  - `setup()` method - initializes tray icon with context menu
  - `_get_tray_icon()` method - loads icon from various sources (exe, ico, png)
  - `_show_main_window()` method - shows and activates main window
  - `_tray_icon_activated()` method - handles icon activation (double click)
  - `_quit_application()` method - properly terminates application
  - `show_message()` method - shows notifications via system tray
  - `cleanup()` method - cleans up resources on application close

### main/updater.py
- **UpdaterWindow** - GUI updater window in application style
- **UpdateThread** - Thread for update execution
  - Downloads update from GitHub
  - Stops application processes
  - Installs update with user data protection
  - Starts updated application

### locales/
- **ru.json** - Russian translations
- **en.json** - English translations

## Localization Usage

```python
from utils.i18n import tr, set_language

# Получить перевод
text = tr("home.version")  # "Версия SingBox"

# С параметрами
text = tr("home.installed", version="1.8.0")  # "Установлено: версия 1.8.0"

# Изменить язык
set_language("en")  # Переключить на английский
```

## Добавление нового языка

1. Создайте файл `data/locales/xx.json` (где xx - код языка, например `eng2.json`)
2. Скопируйте структуру из `ru.json` или `en.json`
3. Добавьте поле `"_language_name"` в корень JSON с названием языка (например, `"_language_name": "English (Custom)"`)
4. Переведите все строки
5. Язык будет доступен автоматически в настройках

## Преимущества архитектуры

1. **Модульность** - код разделен на логические модули
2. **Разделение ответственности** - каждый модуль отвечает за свою область
3. **Переиспользуемость** - общие компоненты вынесены в отдельные модули
4. **Централизация стилей** - единая система стилей через `ui/styles/`
5. **Локализация** - легко добавлять новые языки
6. **Расширяемость** - легко добавлять новые функции
7. **Поддерживаемость** - проще находить и исправлять ошибки
8. **Тестируемость** - модули можно тестировать отдельно
9. **Отзывчивость** - тяжелые операции вынесены в фоновые потоки

## Сборка проекта

### Требования
- Python 3.8+
- PyInstaller 6.0+

### Команда сборки
```bash
# Сборка основного приложения
py -m PyInstaller SingBox-UI.spec --clean --noconfirm

# Сборка updater
py -m PyInstaller updater.spec --clean --noconfirm

# Пост-обработка
py main/post_build.py
```

### Результат сборки
После сборки в папке `dist/SingBox-UI/` будет:
- `SingBox-UI.exe` - главный исполняемый файл
- `data/locales/` - файлы локализации
- `data/themes/` - файлы тем
- `data/core/` - ядро SingBox (если было включено)
- `data/updater.exe` - утилита обновления

## Разработка

### Запуск в режиме разработки
```bash
python main.py
```

### Структура данных
Все данные приложения хранятся в папке `data/`:
- `data/core/sing-box.exe` - ядро SingBox (не обновляется автоматически)
- `data/logs/` - логи приложения
  - `singbox.log` - логи SingBox
  - `debug.log` - отладочные логи
- `data/locales/` - файлы локализации (обновляются, пользовательские сохраняются)
- `data/themes/` - файлы тем (копируются при сборке)
- `data/config.json` - конфигурация SingBox (скачивается из подписки)
- `data/.subscriptions` - список подписок (JSON, сохраняется при обновлениях)
- `data/.settings` - настройки приложения (JSON, объединяются при обновлениях)
- `data/updater.exe` - утилита обновления (обновляется при обновлениях)

### Система обновлений
- Updater (`updater.py`) - отдельное приложение с GUI
- Выполняет весь процесс обновления: скачивание, установка, перезапуск
- Защищает пользовательские данные: подписки, настройки, ядро, логи
- Объединяет настройки: новые ключи добавляются, существующие сохраняются

## Архитектурные решения

### Разделение UI на страницы
Все UI страницы вынесены в отдельные классы в `ui/pages/`:
- Каждая страница наследуется от `BasePage`
- Страницы управляются через `QStackedWidget` в `MainWindow`
- Доступ к элементам страниц через `self.page_profile`, `self.page_home`, `self.page_settings`

### Разделение функциональности на менеджеры
Для уменьшения размера `main.py` и улучшения архитектуры, функциональность вынесена в отдельные менеджеры:
- **TrayManager** (`ui/tray_manager.py`) - управление системным треем
- **LogUIManager** (`managers/log_ui_manager.py`) - управление отображением логов в UI
- **DeepLinkHandler** (`core/deep_link_handler.py`) - обработка deep links и импорт подписок

### Централизованная система стилей
Все стили централизованы в `ui/styles/`:
- Константы (цвета, шрифты, размеры) в `constants.py`
- Управление темой через `Theme` в `theme.py`
- Генерация стилей через `StyleSheet` в `stylesheet.py`

### Фоновые потоки
Тяжелые операции вынесены в фоновые потоки через систему воркеров:
- `BaseWorker` - базовый класс для всех воркеров
- `InitOperationsWorker` - инициализация при старте
- `CheckVersionWorker` / `CheckAppVersionWorker` - проверка версий

### Переиспользуемые компоненты
Общие UI компоненты вынесены в `ui/widgets/`:
- `CardWidget` - карточка с фоном
- `NavButton` - кнопка навигации
- `VersionLabel` - лейбл версии

### Уменьшение размера main.py
Для улучшения поддерживаемости и читаемости кода, из `main.py` были вынесены:
- **Управление треем** → `ui/tray_manager.py` (класс `TrayManager`)
  - Методы `setup_tray()`, `tray_icon_activated()`, `quit_application()` и связанная логика
- **Управление логами в UI** → `managers/log_ui_manager.py` (класс `LogUIManager`)
  - Методы `load_logs()`, `refresh_logs_from_files()`, `cleanup_logs_if_needed()`, `log()` и связанная логика
- **Обработка deep links** → `core/deep_link_handler.py` (класс `DeepLinkHandler`)
  - Метод `handle_deep_link()` и вся логика парсинга URL и импорта подписок

Текущий размер `main.py`: ~2069 строк (было значительно больше до рефакторинга)
