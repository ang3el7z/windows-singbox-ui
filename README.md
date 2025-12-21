# SingBox-UI

Modern Windows client for working with SingBox subscriptions with a mobile design.

> ⚠️ **Disclaimer**  
> This project is intended **strictly for educational and research purposes**.  
> The author **takes no responsibility** for misuse, damage to devices, or any consequences of use.  
> You use everything at **your own risk**. Commercial or malicious use is **not encouraged**.

[Read in Russian](./README.ru.md)

## Features

- 🎨 Modern mobile design
- 🌍 Support for Russian and English languages
- 📥 Automatic SingBox core download
- 🔄 Automatic configuration updates
- 📊 Built-in logs
- ⚙️ Autostart and auto-update settings
- 🔔 Update availability notifications

## Project Structure

```
SingBox-UI/
├── main.py                 # Main application file
├── config/                 # Configuration
│   └── paths.py           # File paths
├── managers/              # Data managers
│   ├── settings.py        # Settings
│   └── subscriptions.py   # Subscriptions
├── utils/                 # Utilities
│   ├── i18n.py           # Localization
│   └── singbox.py        # SingBox utilities
├── core/                  # Core logic
│   └── downloader.py     # Core download
├── locales/              # Localization
│   ├── ru.json           # Russian
│   └── en.json           # English
└── data/                 # Data (created automatically)
    ├── core/             # SingBox core
    ├── logs/             # Logs
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
py -m PyInstaller SingBox-UI.spec --clean --noconfirm
py post_build.py
```

The result will be in the `dist/SingBox-UI/` folder

## Usage

1. Launch the application
2. If the core is not installed - click the update icon and download it
3. Add subscriptions in the "Profile" section
4. Select a subscription and click "START" on the main page

## Data Structure

On first launch, the application automatically creates:

- `data/core/sing-box.exe` - SingBox core (can be downloaded automatically)
- `data/logs/singbox.log` - Application logs
- `data/config.json` - Configuration file (downloaded from subscription)
- `data/.subscriptions` - Subscription list
- `data/.settings` - Application settings

## Requirements

- Python 3.8+
- Windows 10/11
- PyQt5
- qtawesome
- requests

## License

Non-Commercial Source Available License - see [LICENSE](./LICENSE) file for details

**Summary:**
- ✅ Personal, educational, and research use allowed
- ✅ Modifications allowed (via contributions to original repository)
- ❌ Commercial use prohibited
- ❌ Forking or creating separate projects prohibited

---

You can also create a Pull Request or Issue. And don't forget to click the star ⭐ icon to support the project.
