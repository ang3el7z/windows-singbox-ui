# 🎉 SingBox-UI v3.0.1

## 🐛 Bug Fixes

- ✅ **Fixed old autostart migration**: Added automatic cleanup of old registry-based autostart entries
  - Old autostart entries from Windows Registry (`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`) are now automatically removed on every application startup
  - Ensures clean migration from registry-based autostart to Task Scheduler approach
  - Prevents duplicate autostart entries when upgrading from older versions
  - Migration runs before settings synchronization to ensure clean state

## 🔧 Technical Improvements

- 🛠️ **SystemSettingsManager enhancement**: Added `migrate_old_settings()` method
  - New `_migrate_old_autostart()` private method for removing old registry entries
  - Public `migrate_old_settings()` method called during application startup
  - Improved startup sequence: migration → check → apply

- 🛠️ **Startup sequence improvement**: Enhanced `apply_settings_flags_on_launch()` method
  - Now performs old settings migration before checking current settings
  - Ensures old registry entries are cleaned up regardless of current autostart state
  - Better logging for migration process

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v3.0.0...v3.0.1

