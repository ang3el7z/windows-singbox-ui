# 🎉 SingBox-UI v3.0.0

## 🚀 Major Release

### ✨ New Features

- **SystemSettingsManager**: New system settings manager for centralized management
  - Autostart management via Task Scheduler (instead of registry)
  - Protocol registration management (sing-box:// and singbox-ui://)
  - System settings state checking and synchronization
  - `check()`, `apply()`, and `clear()` methods for full control
  - Automatic system settings cleanup before application updates

- **Enhanced protocol cleanup function**: Added `unregister_protocols()` function in `core/protocol.py`
  - Complete removal of protocol registration from Windows registry
  - Safe deletion of all related registry keys
  - Used during system settings cleanup and updates

- **Profile selection validation**: Added `ensure_valid_profile_selection()` function
  - Automatic validation of selected profile index correctness
  - Prevents errors when working with deleted or unavailable profiles
  - Synchronizes selection with UI components

### 🔄 Improvements

- **Logging system simplification**: Consolidated all logs into a single file
  - Removed separate `debug.log` file - all logs now in `singbox-ui.log`
  - Simplified log structure - one file for all application messages
  - SingBox logs remain in separate `singbox.log` file (formerly `singbox-core.log`)
  - Improved log reading and display performance

- **Logs window improvements**: Optimization of updates and display
  - Optimized log updates (appending only new lines instead of full rewrite)
  - Removed "Debug Logs" tab - all application logs are now unified
  - Improved autoscroll and scroll position preservation
  - ANSI color removal from SingBox logs for correct display

- **Autostart improvements**: Migration to Task Scheduler
  - Autostart now uses Task Scheduler instead of Windows registry
  - More reliable autostart management
  - Automatic cleanup of old registry entries during migration

- **Update process improvements**: Automatic system settings cleanup
  - Automatic cleanup of autostart and protocols before updates
  - Prevents conflicts during application updates
  - Preserves user settings during updates

- **Ace Editor in Qt resources**: Ace Editor files are now embedded in QRC
  - Ace Editor files are no longer copied separately during updates
  - Simplified application update process
  - Reduced update size

### 🐛 Bug Fixes

- ✅ Fixed incorrect profile selection after subscription deletion/modification
- ✅ Fixed log display issues when switching between tabs
- ✅ Improved error handling when working with system settings
- ✅ Fixed log cleanup issue - now only `singbox-ui.log` is cleared
- ✅ Improved profile index validation during various operations

### 🔧 Technical Improvements

- 🛠️ **Debug mode removal**: Completely removed debug mode and related functions
  - Removed `on_version_clicked()` and `on_app_version_clicked()` methods
  - Removed `isDebug` setting and all related checks
  - Removed `allow_multiple_processes` setting from UI
  - Removed `_update_debug_logs_visibility()` and `update_debug_logs_visibility()` methods
  - Simplified settings structure

- 🛠️ **LogUIManager refactoring**: Simplified log handling logic
  - Merged `load_logs()` and `load_debug_logs()` methods - now use single file
  - Improved log line formatting handling
  - Added `_format_line()` function for uniform formatting
  - Removed references to `DEBUG_LOG_FILE`

- 🛠️ **main.py improvements**: Code simplification and optimization
  - Added `apply_settings_flags_on_launch()` method for applying settings on startup
  - Improved application launch logic considering all settings
  - Removed obsolete methods and event handlers
  - Improved integration with SystemSettingsManager

- 🛠️ **updater.py improvements**: Update process optimization
  - Added `_clear_system_settings()` function for settings cleanup
  - Removed `_copy_ace()` function - files are now in QRC
  - Improved update operation sequence

- 🛠️ **config/paths.py changes**: Updated log file paths
  - `LOG_FILE` now points to `singbox-ui.log` (formerly `singbox.log`)
  - `SINGBOX_CORE_LOG_FILE` now points to `singbox.log` (formerly `singbox-core.log`)
  - `DEBUG_LOG_FILE` marked as deprecated
  - Removed `ACE_EDITOR_DIR` from list of created directories

- 🛠️ **workers/init_worker.py improvements**: Simplified log cleanup
  - Removed `DEBUG_LOG_FILE` cleanup during initialization
  - Simplified log cleanup logic

- 🛠️ **utils/logger.py improvements**: Simplified logging
  - All logs now written to `LOG_FILE` (singbox-ui.log)
  - Removed `isDebug` setting checks
  - Simplified log writing logic

### 🎨 UI/UX Enhancements

- 🖥️ **Logs window simplification**: Removed "Debug Logs" tab
  - Logs window now contains only two tabs: "Application Logs" and "SingBox Logs"
  - Improved log readability and navigation
  - Optimized log content updates

- 🖥️ **Settings improvements**: Removed debug elements
  - Removed "Allow multiple processes" checkbox from settings
  - Simplified settings page interface
  - Improved settings readability

- 📊 **Log display improvements**: Performance optimization
  - Logs update incrementally (only new lines are added)
  - Improved autoscroll functionality
  - Improved handling of large log volumes

### 🌍 Localization Updates

- Updated localization files (`en.json`, `ru.json`, `zh.json`)
  - Removed strings related to debug mode
  - Added strings for new system settings features
  - Simplified log window tab names

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v2.1.1...v3.0.0
