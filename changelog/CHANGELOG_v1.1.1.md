# 🎉 SingBox-UI v1.1.1

## 🐛 Bug Fixes

- ✅ Fixed navigation buttons not updating language immediately when language is changed
- ✅ Fixed "Change" button not appearing when one profile is running and another is selected
- ✅ Fixed "Test" button not providing clear feedback to users
- ✅ Fixed updater.exe remaining in dist/ folder after build (now properly moved)

## 🎨 UI/UX Improvements

- 🟠 **Orange "Change" button**: When a different profile is selected while one is running, the button now shows in orange color (#ffa500) for better visual distinction
- 📐 **Profile info indentation**: Added consistent indentation (4px) for profile information display, matching the "update available" message style
- 🔄 **Smart profile switching**: "Change" button now properly stops current profile and starts the selected one with smooth transition
- 💬 **Enhanced test feedback**: Test button now shows informative dialog boxes with success/error messages and subscription names

## 🔧 Technical Improvements

- 🛠️ Improved `_update_nav_button()` method to correctly find and update nested navigation button elements
- 🛠️ Enhanced `on_big_button()` logic to handle profile switching with proper timing
- 🛠️ Updated `on_test_sub()` with better error handling and user feedback
- 🛠️ Fixed `post_build.py` to move updater.exe instead of copying it

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v1.1.0...v1.1.1

