# 🎉 SingBox-UI v1.1.2

## 🔗 Deep Links Protocol Registration Improvements

### ✨ Enhanced Protocol Registration
- **Automatic path updates**: Protocol registration now automatically updates the executable path on every application launch, ensuring deep links always point to the current installation location
- **Multi-registry support**: Now checks both `HKEY_CURRENT_USER` and `HKEY_LOCAL_MACHINE` registry locations to detect existing protocol registrations
- **Official sing-box protection**: Smart detection prevents overwriting official sing-box protocol registration - if official sing-box is registered, it will be preserved
- **Comprehensive logging**: Added detailed logging for all protocol registration operations to help with debugging

### 🐛 Bug Fixes

- ✅ Fixed deep links not working after application update or relocation
- ✅ Fixed old executable path remaining in registry after moving application to new location
- ✅ Fixed potential conflict with official sing-box protocol registration

## 🔧 Technical Improvements

- 🛠️ **Smart protocol detection**: `register_protocols()` now intelligently checks if protocols are registered by official sing-box before updating
- 🛠️ **Registry priority handling**: Properly handles registry priority (HKCU takes precedence over HKLM)
- 🛠️ **Path validation**: Automatically updates protocol registration path on every startup to ensure accuracy
- 🛠️ **Error handling**: Improved error handling for registry operations with proper permission checks

## 📝 Protocol Behavior

- **sing-box://**: Only updated if registered by SingBox-UI, preserves official sing-box registration
- **singbox-ui://**: Always updated (unique to SingBox-UI, no conflicts possible)
- **Registration scope**: Uses `HKEY_CURRENT_USER` (no admin rights required, works per-user)

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v1.1.1...v1.1.2


