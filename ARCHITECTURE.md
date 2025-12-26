# SingBox-UI Project Architecture

## Project Structure

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
│   ├── icon_helper.py   # Icon helper (embedded fonts)
│   ├── logger.py         # Logging
│   ├── singbox.py        # SingBox utilities
│   └── theme_manager.py  # Theme management
├── core/                  # Core logic
│   ├── __init__.py
│   ├── deep_link_handler.py # Deep link handler
│   ├── downloader.py     # Core downloader
│   ├── protocol.py       # Protocol registration and admin rights
│   ├── restart_manager.py # Application restart manager
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
│   ├── design/           # Design system
│   │   ├── __init__.py
│   │   ├── base/         # Base UI components (used only by components)
│   │   │   ├── __init__.py
│   │   │   ├── base_card.py # Base card component
│   │   │   ├── base_dialog.py # Base dialog component
│   │   │   └── base_title_bar.py # Base title bar component
│   │   └── component/    # UI components (used in project)
│   │       ├── __init__.py
│   │       ├── button.py # Button components (Button, NavButton, etc.)
│   │       ├── checkbox.py # CheckBox component
│   │       ├── combo_box.py # ComboBox component
│   │       ├── dialog.py # Dialog functions and DownloadDialog
│   │       ├── label.py # Label components (Label, VersionLabel)
│   │       ├── line_edit.py # LineEdit component
│   │       ├── list_widget.py # ListWidget component
│   │       ├── progress_bar.py # ProgressBar component
│   │       ├── text_edit.py # TextEdit component
│   │       ├── widget.py # Container component
│   │       └── window.py # LogsWindow component
│   ├── utils/            # UI utilities
│   │   └── animations.py # Page transition animations
│   ├── styles/           # Styling system
│   │   ├── __init__.py
│   │   ├── constants.py  # Constants (colors, fonts, sizes)
│   │   ├── theme.py      # Theme management
│   │   └── stylesheet.py # Widget stylesheet generation
│   └── tray_manager.py   # System tray manager
├── resources/            # Resources
│   ├── app.qrc          # Qt resource file
│   ├── icons/           # Icon resources
│   │   └── app.ico      # Application icon
│   └── fonts/           # Font resources
│       └── materialdesignicons5-webfont-5.9.55.ttf  # Material Design Icons font
├── scripts/
│   └── resources_rc.py  # Compiled Qt resources (generated)
├── locales/              # Localization source files
│   ├── ru.json           # Russian
│   ├── en.json           # English
│   └── zh.json           # Chinese
├── themes/               # Theme source files
│   ├── dark.json         # Dark theme
│   ├── light.json        # Light theme
│   ├── black.json        # Black theme
│   └── newyear.json      # New Year theme
├── changelog/            # Version changelogs
│   ├── CHANGELOG_v1.0.0.md
│   ├── CHANGELOG_v1.0.1.md
│   ├── CHANGELOG_v1.0.2.md
│   ├── CHANGELOG_v1.0.3.md
│   └── ...
├── data/                 # Application data (created automatically)
│   ├── core/             # SingBox core
│   ├── logs/             # Logs
│   ├── locales/          # Localization files (copied from locales/)
│   ├── themes/           # Theme files (copied from themes/)
│   ├── .version          # Application version (copied from root during build)
│   └── config.json       # Config
├── SingBox-UI.spec       # PyInstaller configuration for main application
├── updater.spec          # PyInstaller configuration for updater
├── post_build.py         # Post-build script
└── requirements.txt      # Dependencies
```

## Version Management

The application version is stored in the `.version` file in the project root. During build, this file is copied to `data/.version`, from where the application reads the version at startup.

The `get_version()` function in `main/main.py`:
1. First tries to read `data/.version` (for built application)
2. Then tries to read root `.version` (for development)
3. Falls back to version "1.0.0" on error

During CI/CD build by tag, the version in `.version` should be updated automatically if the tag is greater than the current version.

## Modules

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
  - Compiles Qt resource files (.qrc) to Python module (scripts/resources_rc.py)
  
- **check_locales.py** - Locale validation script
  - Validates locale files for missing translations
  
- **create_icon.py** - Icon creation script
  - Creates application icons in different formats
  
- **register_protocol.py** - Protocol registration script
  - Registers `sing-box://` and `singbox-ui://` in Windows
  - Requires administrator rights

### config/
- **paths.py** - Definition of all file and directory paths
- `ensure_dirs()` function - creates necessary directories

### managers/
- **settings.py** - Application settings management
  - Save/load settings
  - Interface language support
  
- **subscriptions.py** - Subscription management
  - CRUD operations with subscriptions
  - Config downloading

- **log_ui_manager.py** - Log management in UI
  - `LogUIManager` class - centralized log display management
  - `load_logs_to_ui()` method - loads main logs from file to QTextEdit
  - `load_debug_logs_from_file_to_ui()` method - loads debug logs
  - `refresh_logs_from_files()` method - automatically refreshes logs every second
  - `cleanup_logs_if_needed()` method - cleans logs once per day
  - `append_log_to_ui()` method - adds new log line to UI
  - `_auto_scroll_if_needed()` method - automatic log scrolling
  - `on_scroll_value_changed()` method - handles manual scrolling (stops auto-scroll)
  - `_resume_auto_scroll()` method - resumes auto-scroll after 5 seconds of inactivity
  - `update_debug_logs_visibility()` method - manages debug log visibility

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
  
- **icon_helper.py** - Icon helper for embedded fonts
  - Replaces qtawesome dependency
  - Loads Material Design Icons font from QRC
  - Provides `icon()` function for creating QIcon and QPixmap from font characters
  - Uses embedded font via Qt Resource System
  
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

- **restart_manager.py** - Application restart manager
  - `restart_application()` function - restarts application (optionally as admin)
  - Used for theme changes, admin mode activation, and settings updates
  - Properly shuts down SingBox and releases resources before restart

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
  - `apply_theme()` function - applies theme to QApplication
  - `apply_dark_theme()` function - deprecated wrapper for `apply_theme()` (kept for compatibility)

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

### ui/design/
- **base/** - Base UI components (used only by components, not directly in project)
  - **base_card.py** - Base card component (BaseCard)
  - **base_dialog.py** - Base dialog component (BaseDialog)
  - **base_title_bar.py** - Base title bar component (BaseTitleBar)

- **component/** - UI components (used throughout the project)
  - **button.py** - Button components
    - `Button` - Universal button with variants (default, primary, secondary, danger)
    - `NavButton` - Navigation button with icon and text
    - `AnimatedStartButton` - Animated start/stop button
    - `RoundGradientButton` - Round button with gradient
    - `GradientWidget` - Gradient widget for button effects
  - **checkbox.py** - CheckBox component (`CheckBox`)
  - **combo_box.py** - ComboBox component (`ComboBox`)
  - **dialog.py** - Dialog functions and classes
    - `show_info_dialog()` - Info dialog
    - `show_confirm_dialog()` - Confirmation dialog
    - `show_input_dialog()` - Input dialog
    - `show_language_selection_dialog()` - Language selection dialog
    - `show_add_subscription_dialog()` - Add subscription dialog
    - `DownloadDialog` - Download dialog with progress bar
    - Dialog helper functions for admin restart, kill all, etc.
  - **label.py** - Label components
    - `Label` - Universal label with variants and sizes
    - `VersionLabel` - Version label with states
  - **line_edit.py** - LineEdit component (`LineEdit`)
  - **list_widget.py** - ListWidget component (`ListWidget`)
  - **progress_bar.py** - ProgressBar component (`ProgressBar`)
  - **text_edit.py** - TextEdit component (`TextEdit`)
  - **widget.py** - Container component (`Container`)
  - **window.py** - Window components
    - `LogsWindow` - Logs display window

### ui/utils/
- **animations.py** - Page transition animations
  - `PageTransitionAnimation` class - slide animations for page transitions
  - `FadeAnimation` class - fade in/out animations

### ui/styles/
- **constants.py** - UI constants (colors, fonts, sizes, transitions)
- **theme.py** - Application theme management
  - `Theme` class - centralized theme management
  - Global `theme` instance
  - Integrates with `utils.theme_manager`
  
- **stylesheet.py** - Widget stylesheet generation
  - `StyleSheet` class - static methods for generating CSS styles

### UI Component Architecture

The project follows a strict component hierarchy:

1. **Base UI** (`ui/design/base/`) - Base components that provide core functionality
   - Used ONLY by components, never directly in the project
   - Examples: `BaseCard`, `BaseDialog`, `BaseTitleBar`

2. **Components** (`ui/design/component/`) - Reusable UI components
   - Use base UI internally
   - Used throughout the project (main.py, updater.py, pages, etc.)
   - Examples: `Button`, `Label`, `CheckBox`, `Dialog` functions

3. **Usage Rules**:
   - ✅ Use components from `ui/design/component/` in main.py, updater.py, and pages
   - ❌ Never use base UI directly (only through components)
   - ❌ Never create PyQt5 widgets directly (QPushButton, QLabel, etc.) - use components instead

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
- **zh.json** - Chinese translations

## Localization Usage

```python
from utils.i18n import tr, set_language

# Get translation
text = tr("home.version")  # "SingBox Version"

# With parameters
text = tr("home.installed", version="1.8.0")  # "Installed: version 1.8.0"

# Change language
set_language("en")  # Switch to English
```

## Adding a New Language

1. Create file `data/locales/xx.json` (where xx is language code, e.g., `eng2.json`)
2. Copy structure from `ru.json` or `en.json`
3. Add `"_language_name"` field to JSON root with language name (e.g., `"_language_name": "English (Custom)"`)
4. Translate all strings
5. Language will be automatically available in settings

## Architecture Benefits

1. **Modularity** - code is divided into logical modules
2. **Separation of concerns** - each module is responsible for its area
3. **Reusability** - common components are extracted into separate modules
4. **Style centralization** - unified styling system via `ui/styles/`
5. **Localization** - easy to add new languages
6. **Extensibility** - easy to add new features
7. **Maintainability** - easier to find and fix bugs
8. **Testability** - modules can be tested separately
9. **Responsiveness** - heavy operations are moved to background threads

## Project Build

### Requirements
- Python 3.8+
- PyInstaller 6.0+

### Build Command
```bash
# Build main application
py -m PyInstaller SingBox-UI.spec --clean --noconfirm

# Build updater
py -m PyInstaller updater.spec --clean --noconfirm

# Post-processing
py main/post_build.py
```

### Build Result
After build, the `dist/SingBox-UI/` folder will contain:
- `SingBox-UI.exe` - main executable file
- `data/locales/` - localization files
- `data/themes/` - theme files
- `data/core/` - SingBox core (if included)
- `data/updater.exe` - update utility

## Development

### Running in Development Mode
```bash
python main/main.py
```

### Data Structure
All application data is stored in the `data/` folder:
- `data/core/sing-box.exe` - SingBox core (not updated automatically)
- `data/logs/` - application logs
  - `singbox.log` - SingBox logs
  - `debug.log` - debug logs
- `data/locales/` - localization files (updated, custom ones preserved)
- `data/themes/` - theme files (copied during build)
- `data/config.json` - SingBox configuration (downloaded from subscription)
- `data/.subscriptions` - subscription list (JSON, preserved during updates)
- `data/.settings` - application settings (JSON, merged during updates)
- `data/updater.exe` - update utility (updated during updates)

### Update System
- Updater (`main/updater.py`) - separate GUI application
- Performs entire update process: download, installation, restart
- Protects user data: subscriptions, settings, core, logs
- Merges settings: new keys added, existing ones preserved

## Architectural Decisions

### UI Page Separation
All UI pages are separated into individual classes in `ui/pages/`:
- Each page inherits from `BasePage`
- Pages are managed via `QStackedWidget` in `MainWindow`
- Access to page elements via `self.page_profile`, `self.page_home`, `self.page_settings`

### Functionality Separation into Managers
To reduce `main/main.py` size and improve architecture, functionality has been extracted into separate managers:
- **TrayManager** (`ui/tray_manager.py`) - system tray management
- **LogUIManager** (`managers/log_ui_manager.py`) - log display management in UI
- **DeepLinkHandler** (`core/deep_link_handler.py`) - deep link handling and subscription import
- **RestartManager** (`core/restart_manager.py`) - application restart management

### Centralized Styling System
All styles are centralized in `ui/styles/`:
- Constants (colors, fonts, sizes) in `constants.py`
- Theme management via `Theme` in `theme.py`
- Stylesheet generation via `StyleSheet` in `stylesheet.py`

### Background Threads
Heavy operations are moved to background threads via worker system:
- `BaseWorker` - base class for all workers
- `InitOperationsWorker` - initialization on startup
- `CheckVersionWorker` / `CheckAppVersionWorker` - version checking

### UI Component System
The project uses a three-tier component architecture:

1. **Base UI** (`ui/design/base/`) - base components:
   - `BaseCard` - base card component
   - `BaseDialog` - base dialog component
   - `BaseTitleBar` - base title bar component

2. **Components** (`ui/design/component/`) - components for use:
   - `Button`, `NavButton` - buttons
   - `Label`, `VersionLabel` - labels
   - `CheckBox`, `ComboBox`, `ListWidget` - form elements
   - `TextEdit`, `LineEdit`, `ProgressBar` - input fields and progress
   - `Container` - container
   - Dialog functions (`show_info_dialog`, `show_confirm_dialog`, etc.)
   - `LogsWindow` - logs window

3. **Usage Rules**:
   - In main.py, updater.py and pages, use ONLY components from `ui/design/component/`
   - Base UI is used only inside components, never directly
   - Direct creation of PyQt5 widgets is prohibited - use components instead

### Reducing main.py Size
To improve maintainability and code readability, the following were extracted from `main/main.py`:
- **Tray Management** → `ui/tray_manager.py` (`TrayManager` class)
  - Methods `setup_tray()`, `tray_icon_activated()`, `quit_application()` and related logic
- **Log UI Management** → `managers/log_ui_manager.py` (`LogUIManager` class)
  - Methods `load_logs()`, `refresh_logs_from_files()`, `cleanup_logs_if_needed()`, `log()` and related logic
- **Deep Link Handling** → `core/deep_link_handler.py` (`DeepLinkHandler` class)
  - Method `handle_deep_link()` and all URL parsing and subscription import logic

Current size of `main/main.py`: ~2295 lines (was significantly larger before refactoring)