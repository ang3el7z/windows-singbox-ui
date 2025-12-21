"""Post-build script for project structure setup"""
import shutil
import sys
from pathlib import Path

def log(msg: str):
    """Логирование для CI"""
    print(msg, file=sys.stderr)
    sys.stderr.flush()

def post_build():
    """Настраивает структуру папки проекта после сборки"""
    dist_dir = Path('dist')
    standalone_exe = dist_dir / 'SingBox-UI.exe'
    
    log(f"[post_build] Starting post-build script")
    log(f"[post_build] Checking for SingBox-UI.exe: {standalone_exe}")
    
    if not standalone_exe.exists():
        log(f"[post_build] ERROR: SingBox-UI.exe not found at {standalone_exe}")
        return
    
    # Создаем папку проекта
    project_dir = dist_dir / 'SingBox-UI'
    if project_dir.exists():
        try:
            shutil.rmtree(project_dir)
        except PermissionError:
            # print(f"Warning: Could not delete {project_dir}, files may be in use.")  # Removed to avoid encoding issues in CI
            # print("Attempting to continue without deletion...")  # Removed to avoid encoding issues in CI
            pass
    project_dir.mkdir(parents=True, exist_ok=True)
    # print(f"Project directory: {project_dir}")  # Removed to avoid encoding issues in CI
    
    # Перемещаем exe в папку проекта
    exe_dest = project_dir / 'SingBox-UI.exe'
    # Удаляем старый exe файл, если он существует
    if exe_dest.exists():
        try:
            # Пробуем переименовать старый файл, затем удалить
            old_exe = project_dir / 'SingBox-UI.exe.old'
            if old_exe.exists():
                old_exe.unlink()
            exe_dest.rename(old_exe)
            old_exe.unlink()
        except (PermissionError, OSError) as e:
            # print(f"Warning: Could not delete {exe_dest}, file may be in use.")  # Removed to avoid encoding issues in CI
            # print(f"Error: {e}")  # Removed to avoid encoding issues in CI
            # print("Skipping exe update. New file is in dist\\SingBox-UI.exe")  # Removed to avoid encoding issues in CI
            pass
            # Продолжаем с остальными файлами
    else:
        # Если файла нет, просто перемещаем
        try:
            shutil.move(str(standalone_exe), str(exe_dest))
            # print(f"Exe moved to project directory: {exe_dest}")  # Removed to avoid encoding issues in CI
        except Exception as e:
            # print(f"Error moving exe: {e}")  # Removed to avoid encoding issues in CI
            # print("Skipping exe update.")  # Removed to avoid encoding issues in CI
            pass
    
    # Копируем локали из исходников в data/locales в папке проекта
    source_locales = Path('locales')
    log(f"[post_build] Checking for locales: {source_locales}")
    if source_locales.exists():
        data_dir = project_dir / 'data'
        locales_dest = data_dir / 'locales'
        # Удаляем существующую папку если есть
        if locales_dest.exists():
            shutil.rmtree(locales_dest)
        locales_dest.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copytree(source_locales, locales_dest)
            log(f"[post_build] Locales copied to: {locales_dest}")
        except Exception as e:
            log(f"[post_build] ERROR copying locales: {e}")
    else:
        log(f"[post_build] WARNING: locales directory not found at {source_locales}")
    
    # Копируем updater.exe из dist в data в папке проекта
    dist_updater = dist_dir / 'updater.exe'
    log(f"[post_build] Checking for updater.exe: {dist_updater}")
    if dist_updater.exists():
        log(f"[post_build] Found updater.exe, copying to data/")
        data_dir = project_dir / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        updater_dest = data_dir / 'updater.exe'
        if updater_dest.exists():
            try:
                updater_dest.unlink()
            except PermissionError:
                pass
        try:
            shutil.copy2(dist_updater, updater_dest)
            log(f"[post_build] updater.exe copied to: {updater_dest}")
        except Exception as e:
            log(f"[post_build] ERROR copying updater.exe: {e}")
    else:
        log(f"[post_build] WARNING: updater.exe not found at {dist_updater}")
    
    # Копируем sing-box.exe из исходников в data/core в папке проекта
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
        # Создаем структуру папок даже если sing-box.exe нет
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

