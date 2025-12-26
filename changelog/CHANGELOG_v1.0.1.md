# 🎉 SingBox-UI v1.0.1

## ✨ New Features

### 🌍 Language Selection
- **First launch dialog**: Choose your preferred interface language on first startup
- **Settings integration**: Change language anytime from settings with instant UI updates
- **Dynamic language detection**: Automatically detects all available languages from `locales` folder
- **Default language**: English is used as default until language is selected

### 🔄 Automatic Application Updates
- **Update check on startup**: Automatically checks for new versions when application starts
- **Progress dialog**: Beautiful progress bar during update download and installation
- **One-click update**: Download, extract, and install updates automatically
- **Auto-restart**: Application automatically restarts after successful update

## 🐛 Bug Fixes

- ✅ Fixed crash when selecting profile from empty list
- ✅ Fixed `get_app_latest_version is not defined` error
- ✅ Improved profile selection validation and error handling
- ✅ Fixed profile click handling when no profile is selected

## 🎨 UI Improvements

- 🇷🇺 **Localized button text**: Main buttons now show "ЗАПУСК"/"ОСТАНОВИТЬ" (START/STOP) in Russian
- 🔄 **Change button**: Added "СМЕНИТЬ" (CHANGE) button when a different profile is selected while SingBox is running
- 🧹 **Cleanup**: Removed redundant "Остановлено"/"Запущено" status text below main button
- ⚡ **Dynamic updates**: All UI text updates instantly when language is changed (no restart required)
- 📱 **Better profile display**: Improved current/selected profile information display

## 🔧 CI/CD Improvements

- 🛠️ Fixed GitHub Actions workflow for proper tag and version extraction
- 📦 Improved artifact upload to releases
- 📝 Fixed release description handling (no longer overwrites existing descriptions)

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v1.0.0...v1.0.1






