# 🎉 SingBox-UI v1.0.2

## 🔄 Improved Auto-Update System

### ✨ New Update Mechanism
- **Separate updater executable**: Created dedicated `updater.exe` for reliable update process
- **Manual update trigger**: Update dialog no longer shows automatically - user clicks version to update when ready
- **Better update flow**: Updater properly closes application, updates files, and restarts automatically
- **Improved reliability**: Replaced batch script with native Python updater for better cross-platform compatibility

### 📁 Better File Organization
- **Locales moved to data**: All localization files now stored in `data/locales` for better organization
- **Consistent structure**: All application data (logs, configs, locales) now in `data/` directory

## 🐛 Bug Fixes

- ✅ Fixed issue where application would close after update download but not restart
- ✅ Fixed update process hanging after download completion
- ✅ Improved update script reliability by replacing batch file with dedicated updater
- ✅ Fixed locales not being copied correctly during update process

## 🔧 Technical Improvements

- 🛠️ **New updater module**: Created `updater.py` as separate executable for update operations
- 📦 **Build system updates**: Added `updater.spec` for building updater executable
- 🔄 **Post-build script**: Updated to copy locales to `data/locales` and include updater.exe
- 📝 **Code cleanup**: Removed batch script generation, replaced with cleaner updater.exe approach
- 🚀 **CI/CD improvements**: Updated GitHub Actions workflow to build both main app and updater.exe
- 📚 **Documentation updates**: Updated README files to reflect new project structure with updater.exe and data/locales

## 🎯 User Experience

- 👆 **User control**: Users now have full control over when to update (no automatic popups)
- 🔔 **Visual indicator**: Version label shows update availability and is clickable to start update
- ⚡ **Smoother updates**: Update process is more reliable and handles edge cases better
- 🎨 **Better organization**: Cleaner file structure makes maintenance easier

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v1.0.1...v1.0.2

