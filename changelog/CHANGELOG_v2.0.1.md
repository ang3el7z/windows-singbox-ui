# 🎉 SingBox-UI v2.0.1

## 🔄 Updater Improvements

### ✨ Enhanced Update Mechanism
- **Self-update capability**: Updater can now update itself even when running by using file renaming strategy
- **Old file cleanup**: Automatic cleanup of old updater files (`.old` files) on startup
- **Better file handling**: Improved updater.exe replacement logic that handles locked files gracefully
- **Optimized progress logging**: Download progress now logs every 10 MB instead of continuously, reducing log spam

### 🔧 Version Check Updates
- **GitHub API integration**: Version checking now uses GitHub Releases API (`releases/latest`) instead of reading `.version` file
- **Better version parsing**: Improved version tag parsing that handles both `v1.2.0` and `1.2.0` formats
- **Repository name update**: Updated repository references from `SingBox-UI` to `windows-singbox-ui` throughout the codebase

## 🐛 Bug Fixes

- ✅ Fixed updater unable to update itself when running (now uses rename strategy)
- ✅ Fixed old updater files accumulating in data directory (automatic cleanup on startup)
- ✅ Fixed version checking using outdated method (now uses GitHub Releases API)
- ✅ Fixed repository name inconsistencies across codebase

## 🔧 Technical Improvements

- 🛠️ **Improved type hints**: Added `Optional[str]` return types for version checking functions
- 🛠️ **Better error handling**: Enhanced error handling for file operations during updater self-update
- 🛠️ **Optimized logging**: Reduced log verbosity during download by implementing interval-based logging
- 🛠️ **File locking workaround**: Implemented rename-based file replacement for locked executable files

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v2.0.0...v2.0.1

