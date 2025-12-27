# 🎉 SingBox-UI v2.0.6

## 🎨 UI Improvements

### ✨ Logs Window Enhancements

- **Fixed log tabs visibility**: All three log tabs are now always visible
  - "Info" tab (application logs) - always visible
  - "Singbox" tab (sing-box process logs) - always visible
  - "Debug" tab (debug logs) - visible only when debug mode is enabled

- **Visual active tab indicator**: Active tab button now has distinct visual styling
  - Active tab uses accent color background with bold text
  - Inactive tabs use secondary styling
  - Clear visual feedback for current log view

- **Debug logs styling**: Debug logs button now uses danger (red) color variant
  - Matches the styling of debug settings in settings page
  - Consistent visual language for debug-related UI elements

### 📝 Logs Improvements

- **Sing-box logs format**: Sing-box logs are now saved as-is without timestamp formatting
  - Logs are written exactly as received from the process
  - No additional timestamp processing for sing-box logs
  - Cleaner log output matching original sing-box format

### 🌐 Localization Updates

- **Logs window labels**: Updated log tab names for better clarity
  - 🇷🇺 Russian: "Info", "Singbox", "Отладочные"
  - 🇬🇧 English: "Info", "Singbox", "Debug"
  - 🇨🇳 Chinese: "信息", "Singbox", "调试"

- **Settings button**: Simplified log button label in settings
  - Changed from "Логи приложения" to "Логи" in Russian
  - Changed from "Application Logs" to "Logs" in English
  - Changed from "应用程序日志" to "日志" in Chinese

## 🐛 Bug Fixes

- ✅ Fixed logs window not showing all three tabs correctly
- ✅ Fixed active tab not being visually distinct
- ✅ Fixed sing-box logs formatting issues
- ✅ Fixed debug logs button styling inconsistency

## 🔧 Technical Improvements

- 🛠️ **Logs window refactoring**: Improved tab switching logic and state management
- 🛠️ **Button styling**: Added support for danger variant in checked state
- 🛠️ **Localization keys**: Added separate keys for logs window tabs vs settings button

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v2.0.5...v2.0.6

