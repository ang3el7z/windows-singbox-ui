# 🎉 SingBox-UI v2.1.0

## 🔄 Updater Improvements

### ✨ Updater Fixes and Enhancements

- **Fixed profile file path**: Updated updater to use `.profile` instead of deprecated `.subscribe`
  - Updater now correctly protects user profiles during updates
  - Fixed compatibility with current application structure
  - Ensures user profiles are preserved during automatic updates

- **Added Ace Editor support**: Updater now properly handles Ace Editor files
  - Added separate handling for `data/resources/web/ace/` directory
  - Ace Editor files are now updated during application updates
  - Ensures code editor functionality works correctly after updates

- **Localization updates**: Added translation strings for Ace Editor update process
  - 🇷🇺 Russian: "Обновление Ace Editor..."
  - 🇬🇧 English: "Updating Ace Editor..."
  - 🇨🇳 Chinese: "正在更新 Ace Editor..."

## 🐛 Bug Fixes

- ✅ Fixed updater not preserving user profiles (`.profile` file)
- ✅ Fixed updater not updating Ace Editor files
- ✅ Fixed updater using outdated `.subscribe` path

## 🔧 Technical Improvements

- 🛠️ **Updater refactoring**: Improved file handling logic in update process
- 🛠️ **Path management**: Updated protected paths to match current application structure
- 🛠️ **Resource handling**: Added dedicated method for Ace Editor file updates

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v2.0.6...v2.1.0

