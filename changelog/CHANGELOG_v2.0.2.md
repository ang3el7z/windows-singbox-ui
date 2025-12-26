# 🎉 SingBox-UI v2.0.2

## 🌍 Localization Fixes

### ✨ Translation Improvements
- **Logs button translation**: Fixed "Logs" button not updating when language is changed
- **Allow multiple processes translation**: Fixed checkbox text not updating on language change
- **Debug mode dialogs**: All debug mode dialogs now properly translate when language is changed
- **Chinese localization**: Added missing `debug_logs` translation for Chinese language
- **Logs window translation**: Logs window buttons and title now update correctly on language change

### 🔧 Code Improvements
- **Dynamic UI updates**: Enhanced `refresh_ui_texts()` method to update all UI elements including logs button and debug settings
- **LogsWindow refresh**: Added `refresh_texts()` method to LogsWindow for proper translation updates
- **Complete localization**: All debug mode messages now use translation system instead of hardcoded strings

## 🐛 Bug Fixes

- ✅ Fixed "Logs" button not translating when language is changed in settings
- ✅ Fixed "Allow multiple processes" checkbox not translating on language change
- ✅ Fixed debug mode dialogs showing hardcoded text instead of translated messages
- ✅ Fixed missing `debug_logs` translation in Chinese language file
- ✅ Fixed LogsWindow not updating button texts when language is changed

## 🎨 UI/UX Improvements

- 🔄 **Better language switching**: All UI elements now properly update when language is changed, including previously missed components
- 🌐 **Complete localization**: Debug mode messages are now fully localized in all supported languages (English, Russian, Chinese)

## 🔧 Technical Improvements

- 🛠️ **Enhanced refresh_ui_texts()**: Added missing UI element updates for logs button and allow multiple processes checkbox
- 🛠️ **LogsWindow improvements**: Added refresh_texts() method for proper translation updates
- 🛠️ **Workflow naming**: Improved GitHub Actions workflow run names to show "SingBox-UI v{version}" format

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v2.0.1...v2.0.2

