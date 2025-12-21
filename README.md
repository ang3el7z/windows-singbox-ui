# SingBox-UI

Modern Windows client for working with SingBox subscriptions with a mobile design.

> ⚠️ **Disclaimer**  
> This project is intended **strictly for educational and research purposes**.  
> The author **takes no responsibility** for misuse, damage to devices, or any consequences of use.  
> You use everything at **your own risk**. Commercial or malicious use is **not encouraged**.

[Read in Russian](./README.ru.md)

## Screenshots

<p align="center">
  <img src="https://github.com/user-attachments/assets/7b10bc3c-4a28-4688-8f3e-042eb6784aa0" width="320" alt="Profile"/>
  <img src="https://github.com/user-attachments/assets/9f89cf4e-e367-4fca-bff5-81872ac73a20" width="320" alt="Home"/>
  <img src="https://github.com/user-attachments/assets/f2bd3451-5913-45a2-8e02-6ef70667ec15" width="320" alt="Settings"/>
</p>

## Features

- 🎨 Modern mobile design
- 🌍 Support for Russian and English languages (with custom language support)
- 📥 Automatic SingBox core download
- 🔄 Automatic configuration updates
- 📊 Built-in logs
- ⚙️ Autostart and auto-update settings
- 🔔 Update availability notifications
- 🚀 **Automatic application updates** with beautiful GUI updater
- 🛡️ **Smart update system** - preserves user data (subscriptions, settings, core, logs)

## Project Structure

```
SingBox-UI/
├── main.py                 # Main application file
├── updater.py              # Update utility (built as updater.exe)
├── config/                 # Configuration
│   └── paths.py           # File paths
├── managers/              # Data managers
│   ├── settings.py        # Settings
│   └── subscriptions.py   # Subscriptions
├── utils/                 # Utilities
│   ├── i18n.py           # Localization
│   ├── logger.py         # Logging
│   └── singbox.py        # SingBox utilities
├── core/                  # Core logic
│   └── downloader.py     # Core download
├── locales/              # Localization source files
│   ├── ru.json           # Russian
│   └── en.json           # English
├── changelog/            # Version changelogs
│   ├── CHANGELOG_v1.0.0.md
│   ├── CHANGELOG_v1.0.1.md
│   ├── CHANGELOG_v1.0.2.md
│   ├── CHANGELOG_v1.0.3.md
│   └── ...
└── data/                 # Data (created automatically)
    ├── core/             # SingBox core
    ├── logs/             # Logs
    ├── locales/          # Localization files (copied from locales/)
    │   ├── ru.json       # Russian
    │   └── en.json       # English
    ├── updater.exe       # Update utility executable (with GUI)
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
   python main.py
   ```

### Build exe

```bash
# Build main application
py -m PyInstaller SingBox-UI.spec --clean --noconfirm

# Build updater
py -m PyInstaller updater.spec --clean --noconfirm

# Run post-build script to organize files
py post_build.py
```

The result will be in the `dist/SingBox-UI/` folder with the following structure:
- `SingBox-UI.exe` - Main application
- `data/updater.exe` - Update utility
- `data/locales/` - Localization files
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
- `data/updater.exe` - Update utility with GUI (handles entire update process)
- `data/config.json` - Configuration file (downloaded from subscription)
- `data/.subscriptions` - Subscription list (preserved during updates)
- `data/.settings` - Application settings (merged during updates - new keys added, existing preserved)

## Requirements

- Python 3.8+
- Windows 10/11
- PyQt5
- qtawesome
- requests

## License

MIT License - see [LICENSE](./LICENSE) file for details

---

You can also create a Pull Request or Issue. And don't forget to click the star ⭐ icon to support the project.
