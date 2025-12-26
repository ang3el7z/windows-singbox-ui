# 🎉 SingBox-UI v2.0.2

## 🌍 Localization Fixes

### ✨ Translation Improvements
- **Logs button translation**: Fixed "Logs" button not updating when language is changed
- **Allow multiple processes translation**: Fixed checkbox text not updating on language change
- **Debug mode dialogs**: All debug mode dialogs now properly translate when language is changed
- **Chinese localization**: Added missing `debug_logs` translation for Chinese language
- **Logs window translation**: Logs window buttons and title now update correctly on language change
- **Version title translation**: Fixed "SingBox Version" title not updating on home page when language is changed
- **Core not installed translation**: Fixed "not installed" message not translating when language is changed
- **JSON syntax fix**: Fixed JSON parsing error in Chinese localization file (`zh.json`)

### 🔧 Code Improvements
- **Dynamic UI updates**: Enhanced `refresh_ui_texts()` method to update all UI elements including logs button, debug settings, and version titles
- **LogsWindow refresh**: Added `refresh_texts()` method to LogsWindow for proper translation updates
- **Complete localization**: All debug mode messages now use translation system instead of hardcoded strings
- **Version info updates**: Added proper translation updates for core version display when language changes

## 🎨 UI/UX Improvements

### ✨ Update Mechanism Enhancements
- **Download arrows**: Added download arrow icons next to both application and SingBox core versions
- **Separate update dialogs**: 
  - Application version: Clicking version label activates debug mode (6 clicks), clicking arrow opens update dialog
  - Core version: Clicking arrow opens core update/installation dialog with appropriate messages
- **Improved update messages**: 
  - Application updates: Shows "A new version is available" with Cancel/Download buttons
  - Core updates: Shows "A new version of the core is available: X. Current version: Y" with Cancel/Download buttons
  - Core not installed: Shows "To use the application, you need to install the SingBox core" with Cancel/Download buttons
- **Visual improvements**: 
  - Removed "Update available" text, replaced with download arrow icons
  - Download arrows use warning color for better visibility
  - Hover effects on download arrows with warning_light color

### 🔄 Better Language Switching
- All UI elements now properly update when language is changed, including previously missed components
- Version titles and status messages update correctly on language change
- Complete localization: All messages are now fully localized in all supported languages (English, Russian, Chinese)

## 🐛 Bug Fixes

- ✅ Fixed "Logs" button not translating when language is changed in settings
- ✅ Fixed "Allow multiple processes" checkbox not translating on language change
- ✅ Fixed debug mode dialogs showing hardcoded text instead of translated messages
- ✅ Fixed missing `debug_logs` translation in Chinese language file
- ✅ Fixed LogsWindow not updating button texts when language is changed
- ✅ Fixed "SingBox Version" title not updating on home page when language is changed
- ✅ Fixed "not installed" message not translating when core is not installed
- ✅ Fixed debug mode activation triggering on core version click (now only works on application version)
- ✅ Fixed JSON syntax error in Chinese localization file preventing it from loading

## 🔧 Technical Improvements

- 🛠️ **Enhanced refresh_ui_texts()**: Added missing UI element updates for logs button, allow multiple processes checkbox, and version titles
- 🛠️ **LogsWindow improvements**: Added refresh_texts() method for proper translation updates
- 🛠️ **Update dialog refactoring**: Separated application and core update dialogs with distinct messages and button actions
- 🛠️ **Debug mode logic**: Separated debug mode activation to be exclusive to application version label
- 🛠️ **Version display logic**: Improved version info display with proper handling of update availability and core installation status
- 🛠️ **Workflow naming**: Improved GitHub Actions workflow run names to show "SingBox-UI v{version}" format

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v2.0.1...v2.0.2

