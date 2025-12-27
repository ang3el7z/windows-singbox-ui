# 🎉 SingBox-UI v2.1.1

## 🔧 Code Simplification & Architecture Improvements

### ✨ Administrator Rights Simplification

- **Always run as administrator**: Application now always requires administrator rights via manifest
  - Removed `run_as_admin` setting from settings page
  - Removed administrator status indicator from home page
  - Simplified autostart logic (removed Task Scheduler, using registry only)
  - Application manifest now requires administrator rights at build time

- **Code cleanup**: Removed all administrator-related UI and logic
  - Removed administrator status label and click handler
  - Removed admin check dialogs and restart prompts
  - Removed unused admin-related translations
  - Simplified `restart_application()` function

- **Build improvements**: Manifest handling simplified
  - Removed `app.manifest` file (using PyInstaller's `uac_admin=True` instead)
  - Manifest is now automatically generated during build process

## 🐛 Bug Fixes

- ✅ Fixed autostart complexity (simplified to registry-only approach)
- ✅ Removed unnecessary administrator permission checks

## 🔧 Technical Improvements

- 🛠️ **Settings cleanup**: Removed `run_as_admin` from SettingsManager
- 🛠️ **UI simplification**: Removed administrator status UI elements
- 🛠️ **Autostart refactoring**: Removed Task Scheduler logic, using simple registry approach
- 🛠️ **Code reduction**: Removed ~200 lines of unnecessary administrator-related code
- 🛠️ **Localization cleanup**: Removed unused admin-related translation strings

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v2.1.0...v2.1.1

