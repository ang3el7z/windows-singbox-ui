# 🎉 SingBox-UI v1.0.4

## 🔄 Complete Updater Redesign

### ✨ New Updater System
- **Full-featured updater**: Updater now handles entire update process - download, installation, and restart
- **Beautiful GUI**: Updater has its own window with logs in application style
- **Automatic process management**: Updater automatically stops SingBox-UI and sing-box processes before update
- **Smart file protection**: User data (subscriptions, core, logs) is preserved during updates
- **Settings merge**: `.settings` file is merged intelligently - new keys are added, existing ones are preserved

### 🎯 User Experience Improvements
- **Clear status messages**: Updater shows clear status - "OK" closes in 2 seconds, "ERROR" stays open
- **Real-time progress**: Live progress updates and detailed logs during update process
- **One-click update**: Simply click version to update - updater handles everything automatically
- **Error handling**: If update fails, window stays open for user to review errors

## 🐛 Bug Fixes

- ✅ Fixed update process - now handled entirely by dedicated updater executable
- ✅ Fixed settings preservation - user settings are now properly merged during updates
- ✅ Improved process termination - updater properly stops all related processes

## 🔧 Technical Improvements

- 🛠️ **Simplified main app**: Removed AppUpdateThread from main application - updater handles everything
- 📦 **Better file handling**: Smart merge logic for settings and protected user data
- 🔄 **Process management**: Proper termination of SingBox-UI.exe and sing-box.exe before update
- 📝 **Code cleanup**: Removed redundant update code from main application

## 🎨 UI/UX Enhancements

- 🖥️ **Updater GUI**: Beautiful update window matching application design
- 📊 **Progress tracking**: Real-time progress bar and detailed logs
- 💬 **Status messages**: Clear status indicators for success/error states
- ⏱️ **Auto-close**: Window automatically closes on success, stays open on error

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v1.0.3...v1.0.4

