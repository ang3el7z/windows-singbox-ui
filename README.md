# SingBox-UI

Modern Windows client for working with SingBox subscriptions with a mobile design.

> ⚠️ **Disclaimer**  
> This project is intended **strictly for educational and research purposes**.  
> The author **takes no responsibility** for misuse, damage to devices, or any consequences of use.  
> You use everything at **your own risk**. Commercial or malicious use is **not encouraged**.

[Read in Russian](./README.ru.md)

## Screenshots

<p align="center">
  <img src="https://github.com/user-attachments/assets/7b10bc3c-4a28-4688-8f3e-042eb6784aa0" width="320" height="700" alt="Profile"/>
  <img src="https://github.com/user-attachments/assets/9f89cf4e-e367-4fca-bff5-81872ac73a20" width="320" height="700" alt="Home"/>
  <img src="https://github.com/user-attachments/assets/f2bd3451-5913-45a2-8e02-6ef70667ec15" width="320" height="700" alt="Settings"/>
</p>

## Features

- 🎨 Modern mobile design
- 🌍 Support for Russian, English, and Chinese languages (with custom language support)
- 📥 Automatic SingBox core download
- 🔄 Automatic configuration updates
- 📊 Built-in logs
- ⚙️ Autostart and auto-update settings
- 🔔 Update availability notifications
- 🚀 **Automatic application updates** with beautiful GUI updater
- 🛡️ **Smart update system** - preserves user data (subscriptions, settings, core, logs)

## Project Structure

For detailed architecture documentation, see [ARCHITECTURE.md](./ARCHITECTURE.md).

```
SingBox-UI/
├── .version                # Application version file
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
│   └── paths.py           # File paths
├── managers/              # Data managers
│   ├── settings.py        # Settings
│   ├── subscriptions.py   # Subscriptions
│   └── log_ui_manager.py  # Log UI manager
├── utils/                 # Utilities
│   ├── i18n.py           # Localization
│   ├── icon_manager.py   # Icon management
│   ├── icon_helper.py   # Icon helper (embedded fonts)
│   ├── logger.py         # Logging
│   ├── singbox.py        # SingBox utilities
│   └── theme_manager.py  # Theme management
├── core/                  # Core logic
│   ├── deep_link_handler.py # Deep link handler
│   ├── downloader.py     # Core downloader
│   ├── protocol.py       # Protocol registration and admin rights
│   ├── restart_manager.py # Application restart manager
│   └── singbox_manager.py # SingBox process management
├── app/                   # Application initialization
│   └── application.py    # QApplication creation and theme
├── workers/               # Background threads
│   ├── base_worker.py    # Base worker class
│   ├── init_worker.py    # Initialization worker
│   └── version_worker.py # Version check workers
├── ui/                    # User interface
│   ├── pages/            # Application pages
│   │   ├── base_page.py  # Base page class
│   │   ├── profile_page.py # Profile management page
│   │   ├── home_page.py  # Home page
│   │   └── settings_page.py # Settings page
│   ├── design/           # Design system
│   │   ├── base/         # Base UI components (used only by components)
│   │   │   ├── base_card.py # Base card component
│   │   │   ├── base_dialog.py # Base dialog component
│   │   │   └── base_title_bar.py # Base title bar component
│   │   └── component/    # UI components (used in project)
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
│   ├── widgets/          # Legacy widgets (deprecated, use design/component)
│   │   └── logs_window.py # Logs window widget (moved to design/component/window.py)
│   ├── utils/            # UI utilities
│   │   └── animations.py # Page transition animations
│   ├── styles/           # Styling system
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
│   └── resources_rc.py   # Compiled Qt resources (generated)
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
│   └── ...
└── data/                 # Data (created automatically)
    ├── core/             # SingBox core
    ├── logs/             # Logs
    ├── locales/          # Localization files (copied from locales/)
    │   ├── ru.json       # Russian
    │   ├── en.json       # English
    │   └── zh.json       # Chinese
    ├── themes/           # Theme files (copied from themes/)
    │   ├── dark.json     # Dark theme
    │   ├── light.json    # Light theme
    │   ├── black.json    # Black theme
    │   └── newyear.json  # New Year theme
    ├── updater.exe       # Update utility executable (with GUI)
    ├── .version          # Application version (copied from root)
    └── config.json       # Config
```

## Installation

### From Source

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main/main.py
   ```

### Build exe

**Recommended: Use parallel build script (builds both exe simultaneously, faster):**

```bash
# Build both SingBox-UI.exe and updater.exe in parallel
python scripts/build_parallel.py --clean-build
```

**Alternative: Manual build (sequential):**

```bash
# Build main application
py -m PyInstaller SingBox-UI.spec --clean --noconfirm

# Build updater
py -m PyInstaller updater.spec --clean --noconfirm

# Run post-build script to organize files
python main/post_build.py
```

The parallel build script automatically runs the post-build script after successful builds.

The result will be in the `dist/SingBox-UI/` folder with the following structure:
- `SingBox-UI.exe` - Main application
- `data/updater.exe` - Update utility
- `data/locales/` - Localization files
- `data/themes/` - Theme files
- `data/core/` - SingBox core (downloaded on first run)

## Usage

1. Launch the application
2. If the core is not installed - click the update icon and download it
3. Add subscriptions in the "Profile" section
4. Select a subscription and click "START" on the main page

### Updating the Application

When a new version is available:
1. The version label will show "Update available: vX.X.X" (clickable)
2. Click on the version to start the update
3. The updater window will open showing the update progress
4. The updater will automatically:
   - Download the update
   - Stop the application and SingBox
   - Install the update (preserving your data)
   - Start the updated application
5. On success, the updater closes automatically. On error, it stays open for review.

## Data Structure

On first launch, the application automatically creates:

- `data/core/sing-box.exe` - SingBox core (can be downloaded automatically)
- `data/logs/` - Application logs directory
  - `singbox.log` - SingBox logs
  - `debug.log` - Debug logs
- `data/locales/` - Localization files (copied during build)
  - `ru.json` - Russian translations
  - `en.json` - English translations
- `data/themes/` - Theme files (copied during build)
  - `dark.json` - Dark theme
  - `light.json` - Light theme
  - `black.json` - Black theme
  - `newyear.json` - New Year theme
- `data/updater.exe` - Update utility with GUI (handles entire update process)
- `data/config.json` - Configuration file (downloaded from subscription)
- `data/.subscriptions` - Subscription list (preserved during updates)
- `data/.settings` - Application settings (merged during updates - new keys added, existing preserved)

## Requirements

- Python 3.8+
- Windows 10/11
- PyQt5
- requests

## License

MIT License - see [LICENSE](./LICENSE) file for details

---

You can also create a Pull Request or Issue. And don't forget to click the star ⭐ icon to support the project.
