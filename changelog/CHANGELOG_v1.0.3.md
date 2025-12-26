# 🎉 SingBox-UI v1.0.3

## 🌍 Improved Localization System

### ✨ Enhanced Language Support
- **Custom language names**: Language names are now read from `_language_name` field in locale files
- **User-defined languages**: Users can now add custom language files (e.g., `eng2.json`) with custom names
- **Flexible language structure**: Removed hardcoded language name dictionary - all names come from locale files
- **Better extensibility**: Easier to add new languages without code changes

### 🔧 Code Improvements
- **Removed backward compatibility**: Cleaned up old locale path compatibility code
- **Simplified update logic**: Removed unnecessary `_internal` folder checks in update process
- **Code cleanup**: Removed unused imports and simplified code structure

## 🐛 Bug Fixes

- ✅ Fixed `FileExistsError` in post_build.py when copying locales to existing directory
- ✅ Fixed CI/CD build process with improved error handling and logging
- ✅ Fixed post_build script to properly handle existing directories

## 🔧 CI/CD Improvements

- 🛠️ **Enhanced logging**: Added comprehensive logging to post_build.py for better CI debugging
- 📋 **File verification**: Added pre-build checks to verify required files exist
- ✅ **Build verification**: Added post-build checks to verify both executables were built successfully
- 📝 **Better error messages**: Improved error messages in CI workflow for easier debugging

## 🎯 Developer Experience

- 📚 **English-only comments**: Replaced all Russian comments with English in post_build.py for better CI compatibility
- 🔍 **Better diagnostics**: Enhanced logging helps identify build issues faster
- 🧹 **Code quality**: Removed legacy code and improved maintainability

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v1.0.2...v1.0.3




