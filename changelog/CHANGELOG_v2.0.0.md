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
- **Widgets**: Reusable UI widgets (`card.py`, `nav_button.py`, `version_label.py`)
- **Dialogs**: Standardized dialog components (`base_dialog.py`, `confirm_dialog.py`, `info_dialog.py`, `language_dialog.py`)
- **Styles**: Centralized styling system (`constants.py`, `theme.py`, `stylesheet.py`)
- **Tray Manager**: Dedicated system tray management (`tray_manager.py`)

#### Core Logic (`core/`)
- **Protocol Management**: Protocol registration and admin rights handling (`protocol.py`)
- **SingBox Manager**: Process management for SingBox (`singbox_manager.py`)
- **Deep Link Handler**: Deep link processing (`deep_link_handler.py`)
- **Downloader**: Core download functionality (`downloader.py`)

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

### 🎨 UI/UX Improvements

- **Modern component system**: Reusable, well-structured UI components
- **Consistent styling**: Centralized theme and style management
- **Better dialog system**: Standardized dialog components with consistent behavior
- **Improved navigation**: Enhanced navigation button component with better visual feedback

### 🔧 Technical Improvements

- **Better code organization**: Clear separation between UI, business logic, and utilities
- **Improved maintainability**: Modular structure makes it easier to add features and fix bugs
- **Enhanced type safety**: Better code structure for future type hints
- **Cleaner imports**: Organized imports with clear module boundaries

### 📦 Build System Updates

- **Updated build configuration**: Improved PyInstaller specs for better organization
- **Better resource management**: Icons and resources properly organized
- **Scripts organization**: Utility scripts moved to dedicated `scripts/` directory

### 🐛 Bug Fixes

- ✅ Improved code organization reduces potential for bugs
- ✅ Better separation of concerns prevents cross-module issues
- ✅ Cleaner architecture makes debugging easier

### 📝 Migration Notes

This is a major version release with significant architectural changes. The application functionality remains the same, but the internal structure has been completely reorganized for better maintainability and future development.

---

**Full Changelog**: https://github.com/ang3el7z/windows-singbox-ui/compare/v1.1.2...v2.0.0

