# 🎉 SingBox-UI v1.1.0

## 🚀 Major Updater Improvements

### ✨ Enhanced Update Experience
- **Smart file handling**: Fixed file duplication issue - updater now correctly identifies and uses the correct application directory
- **Better download logging**: Improved download progress logging - shows progress every 5 MB instead of every chunk
- **User-friendly completion**: Added "Done" and "Cancel" buttons with 5-second auto-close timer on successful update
- **Error handling**: Window stays open on errors for user to review logs, no auto-close on failures
- **Temporary file management**: All temporary files are now stored in system temp directory, not in application folder

### 🐛 Bug Fixes

- ✅ Fixed updater downloading files into its own directory causing duplication
- ✅ Fixed excessive logging during download (was logging every 8KB chunk)
- ✅ Fixed missing imports (QHBoxLayout, QPushButton) causing crashes
- ✅ Improved timeout handling for slow connections (increased to 60 seconds)
- ✅ Better error messages and exception handling during update process

## 🎨 UI/UX Enhancements

- 🖥️ **Completion buttons**: Added "Done" and "Cancel" buttons appear after successful update
- ⏱️ **Auto-close timer**: 5-second countdown timer with visual feedback before auto-closing
- 📊 **Progress display**: Cleaner progress logging with meaningful intervals
- 💬 **Status messages**: Clear status indicators for success/error states

## 🔧 Technical Improvements

- 🛠️ **Directory detection**: Smart detection of application directory to avoid file duplication
- 📦 **Temp file cleanup**: Proper cleanup of temporary files from system temp directory
- 🔄 **Process management**: Improved process termination and restart logic
- 📝 **Code quality**: Better error handling and logging throughout update process

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v1.0.5...v1.1.0








