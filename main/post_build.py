"""Post-build script for project structure setup"""
import shutil
import sys
from pathlib import Path

def log(msg: str):
    """Logging for CI"""
    print(msg, file=sys.stderr)
    sys.stderr.flush()

def post_build():
    """Sets up project structure after build"""
    dist_dir = Path('dist')
    standalone_exe = dist_dir / 'SingBox-UI.exe'
    project_exe = dist_dir / 'SingBox-UI' / 'SingBox-UI.exe'
    
    log(f"[post_build] Starting post-build script")
    
    # Check if exe is already in project directory or standalone
    if project_exe.exists():
        log(f"[post_build] SingBox-UI.exe already in project directory: {project_exe}")
        project_dir = dist_dir / 'SingBox-UI'
    elif standalone_exe.exists():
        log(f"[post_build] Checking for SingBox-UI.exe: {standalone_exe}")
        project_dir = dist_dir / 'SingBox-UI'
        project_dir.mkdir(parents=True, exist_ok=True)
        exe_dest = project_dir / 'SingBox-UI.exe'
        try:
            shutil.move(str(standalone_exe), str(exe_dest))
            log(f"[post_build] Moved SingBox-UI.exe to project directory")
        except Exception as e:
            log(f"[post_build] ERROR moving exe: {e}")
            return
    else:
        log(f"[post_build] ERROR: SingBox-UI.exe not found")
        return
    
    
    # Copy locales from source to data/locales in project directory
    source_locales = Path('locales')
    log(f"[post_build] Checking for locales: {source_locales}")
    if source_locales.exists():
        data_dir = project_dir / 'data'
        locales_dest = data_dir / 'locales'
        # Remove existing directory if exists
        if locales_dest.exists():
            try:
                shutil.rmtree(locales_dest)
                log(f"[post_build] Removed existing locales directory")
            except Exception as e:
                log(f"[post_build] WARNING: Could not remove existing locales directory: {e}")
        try:
            # Use dirs_exist_ok=True for Python 3.8+ to handle existing directories
            shutil.copytree(source_locales, locales_dest, dirs_exist_ok=True)
            log(f"[post_build] Locales copied to: {locales_dest}")
        except Exception as e:
            log(f"[post_build] ERROR copying locales: {e}")
    else:
        log(f"[post_build] WARNING: locales directory not found at {source_locales}")
    
    # Copy themes from source to themes in project directory
    source_themes = Path('themes')
    log(f"[post_build] Checking for themes: {source_themes}")
    if source_themes.exists():
        themes_dest = project_dir / 'themes'
        # Remove existing directory if exists
        if themes_dest.exists():
            try:
                shutil.rmtree(themes_dest)
                log(f"[post_build] Removed existing themes directory")
            except Exception as e:
                log(f"[post_build] WARNING: Could not remove existing themes directory: {e}")
        try:
            # Use dirs_exist_ok=True for Python 3.8+ to handle existing directories
            shutil.copytree(source_themes, themes_dest, dirs_exist_ok=True)
            log(f"[post_build] Themes copied to: {themes_dest}")
        except Exception as e:
            log(f"[post_build] ERROR copying themes: {e}")
    else:
        log(f"[post_build] WARNING: themes directory not found at {source_themes}")
    
    # Move updater.exe from dist to data in project directory
    dist_updater = dist_dir / 'updater.exe'
    log(f"[post_build] Checking for updater.exe: {dist_updater}")
    if dist_updater.exists():
        log(f"[post_build] Found updater.exe, moving to data/")
        data_dir = project_dir / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        updater_dest = data_dir / 'updater.exe'
        if updater_dest.exists():
            try:
                updater_dest.unlink()
            except PermissionError:
                pass
        try:
            shutil.move(str(dist_updater), str(updater_dest))
            log(f"[post_build] updater.exe moved to: {updater_dest}")
        except Exception as e:
            log(f"[post_build] ERROR moving updater.exe: {e}")
    else:
        log(f"[post_build] WARNING: updater.exe not found at {dist_updater}")
    
    # Copy sing-box.exe from source to data/core in project directory
    source_core_exe = Path('data/core/sing-box.exe')
    log(f"[post_build] Checking for sing-box.exe: {source_core_exe}")
    if source_core_exe.exists():
        log(f"[post_build] Found sing-box.exe, copying to data/core/")
        data_dir = project_dir / 'data'
        core_dir = data_dir / 'core'
        core_dir.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(source_core_exe, core_dir / 'sing-box.exe')
            log(f"[post_build] sing-box.exe copied to: {core_dir / 'sing-box.exe'}")
        except Exception as e:
            log(f"[post_build] ERROR copying sing-box.exe: {e}")
    else:
        log(f"[post_build] WARNING: sing-box.exe not found at {source_core_exe}")
        # Create directory structure even if sing-box.exe is missing
        data_dir = project_dir / 'data'
        core_dir = data_dir / 'core'
        core_dir.mkdir(parents=True, exist_ok=True)
        log(f"[post_build] Created directory structure: {core_dir} (sing-box.exe will be downloaded on first run)")
    
    # Copy .version file to data/.version
    source_version = Path('.version')
    log(f"[post_build] Checking for .version: {source_version}")
    if source_version.exists():
        log(f"[post_build] Found .version, copying to data/")
        data_dir = project_dir / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        version_dest = data_dir / '.version'
        try:
            shutil.copy2(source_version, version_dest)
            log(f"[post_build] .version copied to: {version_dest}")
        except Exception as e:
            log(f"[post_build] ERROR copying .version: {e}")
    else:
        log(f"[post_build] WARNING: .version not found at {source_version}")
    
    log(f"[post_build] Post-build script completed")
    log(f"[post_build] Project structure:")
    log(f"[post_build]   {project_dir}/")
    log(f"[post_build]     - SingBox-UI.exe")
    log(f"[post_build]     - data/locales/")
    log(f"[post_build]     - data/core/")
    log(f"[post_build]     - data/updater.exe")

if __name__ == '__main__':
    post_build()

