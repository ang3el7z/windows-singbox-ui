"""Post-build скрипт для настройки структуры проекта"""
import shutil
from pathlib import Path

def post_build():
    """Настраивает структуру папки проекта после сборки"""
    dist_dir = Path('dist')
    standalone_exe = dist_dir / 'SingBox-UI.exe'
    
    if not standalone_exe.exists():
        # print("Exe file not found!")  # Removed to avoid encoding issues in CI
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
    if source_locales.exists():
        data_dir = project_dir / 'data'
        locales_dest = data_dir / 'locales'
        # Удаляем существующую папку если есть
        if locales_dest.exists():
            shutil.rmtree(locales_dest)
        locales_dest.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_locales, locales_dest)
        # print(f"Locales copied to: {locales_dest}")  # Removed to avoid encoding issues in CI
    
    # Копируем updater.exe из dist в data в папке проекта
    dist_updater = dist_dir / 'updater.exe'
    if dist_updater.exists():
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
            # print(f"updater.exe copied to: {updater_dest}")  # Removed to avoid encoding issues in CI
        except Exception as e:
            # print(f"Error copying updater.exe: {e}")  # Removed to avoid encoding issues in CI
            pass
    
    # Копируем sing-box.exe из исходников в data/core в папке проекта
    source_core_exe = Path('data/core/sing-box.exe')
    if source_core_exe.exists():
        data_dir = project_dir / 'data'
        core_dir = data_dir / 'core'
        core_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_core_exe, core_dir / 'sing-box.exe')
        # print(f"sing-box.exe copied to: {core_dir / 'sing-box.exe'}")  # Removed to avoid encoding issues in CI
    else:
        # Создаем структуру папок даже если sing-box.exe нет
        data_dir = project_dir / 'data'
        core_dir = data_dir / 'core'
        core_dir.mkdir(parents=True, exist_ok=True)
        # print(f"Created directory structure: {core_dir} (sing-box.exe will be downloaded on first run)")  # Removed to avoid encoding issues in CI
    
    # print(f"\nProject structure created:")  # Removed to avoid encoding issues in CI
    # print(f"  {project_dir}/")  # Removed to avoid encoding issues in CI
    # print(f"    - SingBox-UI.exe")  # Removed to avoid encoding issues in CI
    # print(f"    - locales/")  # Removed to avoid encoding issues in CI
    # print(f"    - data/core/")  # Removed to avoid encoding issues in CI

if __name__ == '__main__':
    post_build()

