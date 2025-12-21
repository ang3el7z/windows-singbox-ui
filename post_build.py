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
    
    log(f"[post_build] Starting post-build script")
    log(f"[post_build] Checking for SingBox-UI.exe: {standalone_exe}")
    
    if not standalone_exe.exists():
        log(f"[post_build] ERROR: SingBox-UI.exe not found at {standalone_exe}")
        return
    
    # Create project directory
    project_dir = dist_dir / 'SingBox-UI'
    if project_dir.exists():
        try:
            shutil.rmtree(project_dir)
        except PermissionError:
            pass
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Move exe to project directory
    exe_dest = project_dir / 'SingBox-UI.exe'
    # Remove old exe file if it exists
    if exe_dest.exists():
        try:
            # Try to rename old file, then delete
            old_exe = project_dir / 'SingBox-UI.exe.old'
            if old_exe.exists():
                old_exe.unlink()
            exe_dest.rename(old_exe)
            old_exe.unlink()
        except (PermissionError, OSError) as e:
            pass
    else:
        # If file doesn't exist, just move
        try:
            shutil.move(str(standalone_exe), str(exe_dest))
        except Exception as e:
            pass
    
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
    
    log(f"[post_build] Post-build script completed")
    log(f"[post_build] Project structure:")
    log(f"[post_build]   {project_dir}/")
    log(f"[post_build]     - SingBox-UI.exe")
    log(f"[post_build]     - data/locales/")
    log(f"[post_build]     - data/core/")
    log(f"[post_build]     - data/updater.exe")

if __name__ == '__main__':
    post_build()

