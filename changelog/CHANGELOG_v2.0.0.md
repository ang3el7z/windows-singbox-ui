# 🎉 SingBox-UI v2.0.0

## 🚀 Major Architecture Refactoring

### ✨ Complete Code Restructuring
- **Modular architecture**: Complete reorganization of codebase into clean, modular structure
- **Separation of concerns**: UI, core logic, managers, and utilities are now properly separated
- **Better maintainability**: Improved code organization makes the project easier to maintain and extend
- **Modern project structure**: Following best practices for Python application architecture

### 🏗️ New Project Structure

#### UI Components (`ui/`)
- **Pages**: Modular page components (`home_page.py`, `profile_page.py`, `settings_page.py`)
- **Design System**: New three-tier component architecture
  - **Base Components** (`ui/design/base/`): Base UI components used only by components (`base_card.py`, `base_dialog.py`, `base_title_bar.py`)
  - **Components** (`ui/design/component/`): Reusable UI components used throughout the project
    - Button components (`button.py`: `Button`, `NavButton`, `AnimatedStartButton`, `RoundGradientButton`)
    - Form components (`checkbox.py`, `combo_box.py`, `line_edit.py`, `list_widget.py`, `text_edit.py`)
    - Display components (`label.py`: `Label`, `VersionLabel`, `progress_bar.py`, `widget.py`: `Container`)
    - Dialog functions (`dialog.py`: `show_info_dialog`, `show_confirm_dialog`, `DownloadDialog`, etc.)
    - Window components (`window.py`: `LogsWindow`)
- **Styles**: Centralized styling system (`constants.py`, `theme.py`, `stylesheet.py`)
- **Tray Manager**: Dedicated system tray management (`tray_manager.py`)

#### Core Logic (`core/`)
- **Protocol Management**: Protocol registration and admin rights handling (`protocol.py`)
- **SingBox Manager**: Process management for SingBox (`singbox_manager.py`)
- **Deep Link Handler**: Deep link processing (`deep_link_handler.py`)
- **Downloader**: Core download functionality (`downloader.py`)
- **Restart Manager**: Application restart management (`restart_manager.py`) - new!

#### Application Layer (`app/`)
- **Application Initialization**: QApplication creation and theme application (`application.py`)

#### Managers (`managers/`)
- **Settings Manager**: Centralized settings management (`settings.py`)
- **Subscription Manager**: Subscription handling (`subscriptions.py`)
- **Log UI Manager**: UI log management (`log_ui_manager.py`)

#### Workers (`workers/`)
- **Base Worker**: Base class for background workers (`base_worker.py`)
- **Init Worker**: Initialization operations in background (`init_worker.py`)
- **Version Worker**: Version checking workers (`version_worker.py`)

#### Utilities (`utils/`)
- **Internationalization**: Localization system (`i18n.py`)
- **Logger**: Logging utilities (`logger.py`)
- **SingBox Utils**: SingBox-related utilities (`singbox.py`)
- **Theme Manager**: Theme management system (`theme_manager.py`)
- **Icon Manager**: Icon loading and management (`icon_manager.py`, `icon_helper.py`)

### 🌍 New Language Support

- **Chinese (Simplified)**: Added full localization support for Chinese language (`zh.json`)
- **Extended language system**: Enhanced language detection and management

### 🎨 Multi-Theme System

- **Multiple themes**: Added support for multiple color themes
  - **Dark theme** (default): Classic dark color scheme
  - **Light theme**: Bright light color scheme
  - **Black theme**: Pure black theme for OLED displays
  - **New Year theme**: Special festive theme
- **Dynamic theme switching**: Change themes on-the-fly without restart (requires app restart for full effect)
- **Theme management in updater**: Updater now supports theme files
- **Localized theme names**: Theme names are localized in user's language
- **Theme persistence**: Selected theme is saved and restored on application restart

### 🔧 Resource Management System

- **Qt Resource System (QRC)**: Migrated from external dependencies to embedded Qt Resource System
- **Embedded fonts**: Material Design Icons font now embedded via QRC (replaced qtawesome dependency)
- **Embedded icons**: Application icons embedded via QRC for better portability
- **Resource compilation**: Automatic QRC compilation during build process
- **Better resource access**: Resources accessible via Qt resource paths (e.g., `:/icons/app.ico`)

### 🎨 UI/UX Improvements

- **Unified dialog system**: Standardized dialog components replacing QMessageBox with consistent styling
- **Loading indicators**: Added loading indicators for language and theme combo boxes
- **Improved button styling**: Enhanced button components with better visual feedback
- **Better card rendering**: Fixed card backgrounds on all pages with proper theme application
- **Enhanced combo box styling**: Improved dropdown appearance with better borders and subcontrol properties
- **Profile label interactivity**: Updated cursor styles for different profile states
- **Restart confirmation**: Improved restart functionality with better user feedback
- **Admin status display**: Enhanced admin status label styling and font sizing

### 🔄 Restart Management

- **Dedicated restart manager**: New `restart_manager.py` module for handling application restarts
- **Universal restart function**: Unified restart logic for theme changes, admin mode switching, and other scenarios
- **Proper process management**: Improved mutex handling during restarts
- **Restart flag system**: Prevents multiple simultaneous restarts
- **Better error handling**: Enhanced error handling during restart process

### 🔒 Single Instance & Mutex Improvements

- **Global mutex**: Implemented global mutex (`Global\\SingBox-UI-Instance`) that works across admin and non-admin sessions
- **Cross-session support**: Single instance enforcement works between different user sessions
- **Improved mutex handling**: Better mutex capture and release logic during restarts
- **Retry mechanism**: Added retry logic for mutex acquisition during process transitions
- **Better cleanup**: Improved cleanup of mutex and local server resources

### 🛠️ Build System Updates

- **QRC integration**: Build system now compiles and includes QRC resources automatically
- **Updated PyInstaller specs**: Enhanced build configuration for QRC resource handling
- **Font embedding**: Fonts properly embedded via QRC system instead of external files
- **Resource scripts**: Added utility scripts for QRC compilation (`build_qrc.py`)
- **Better resource organization**: Icons and fonts properly organized in resources directory

### 🐛 Bug Fixes

- ✅ Fixed card backgrounds not rendering properly on all pages
- ✅ Fixed theme application requiring full UI refresh (now uses quick restart)
- ✅ Fixed admin restart by properly releasing mutex/server before exit
- ✅ Fixed single instance handling across admin/non-admin modes
- ✅ Fixed resource cleanup delays to prevent PyInstaller warnings
- ✅ Fixed duplicate QMessageBox calls replaced with unified dialog system
- ✅ Fixed button sizing and font size calculations for better UI consistency
- ✅ Fixed profile label cursor styles for better user feedback
- ✅ Improved crash handling with global exception handler for PyQt5 crashes
- ✅ Fixed icon loading logic for better extraction from executable

### 📝 Migration Notes

This is a major version release with significant architectural changes and new features:

1. **Qt Resource System**: Resources (icons, fonts) are now embedded via QRC. If you're using custom resources, they should be added to `resources/app.qrc`.

2. **Theme System**: Multiple themes are now supported. Users can switch themes from settings, and the theme will be applied after application restart.

3. **Language Support**: Chinese language has been added. The language selection dialog now supports all three languages (English, Russian, Chinese).

4. **Resource Access**: Code accessing resources should use Qt resource paths (e.g., `:/icons/app.ico`) instead of file paths.

5. **Restart Manager**: Application restarts are now handled through the dedicated `restart_manager.py` module. This improves reliability and prevents multiple simultaneous restarts.

6. **Component Architecture**: UI components have been reorganized into a three-tier design system:
   - Use components from `ui/design/component/` in your code
   - Base components in `ui/design/base/` are used only internally by components
   - Direct creation of PyQt5 widgets is discouraged - use components instead

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v1.1.2...v2.0.0

