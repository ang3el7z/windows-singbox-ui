"""Post-build скрипт для настройки структуры проекта"""
import shutil
from pathlib import Path

def post_build():
    """Настраивает структуру папки проекта после сборки"""
    dist_dir = Path('dist')
    standalone_exe = dist_dir / 'SingBox-UI.exe'
    
    if not standalone_exe.exists():
        print("Exe файл не найден!")
        return
    
    # Создаем папку проекта
    project_dir = dist_dir / 'SingBox-UI'
    if project_dir.exists():
        try:
            shutil.rmtree(project_dir)
        except PermissionError:
            print(f"Предупреждение: Не удалось удалить {project_dir}, возможно файлы используются.")
            print("Попытка продолжить без удаления...")
    project_dir.mkdir(parents=True, exist_ok=True)
    print(f"Папка проекта: {project_dir}")
    
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
            print(f"Предупреждение: Не удалось удалить {exe_dest}, возможно файл используется.")
            print(f"Ошибка: {e}")
            print("Пропускаем обновление exe файла. Новый файл находится в dist\\SingBox-UI.exe")
            # Продолжаем с остальными файлами
    else:
        # Если файла нет, просто перемещаем
        try:
            shutil.move(str(standalone_exe), str(exe_dest))
            print(f"Exe перемещен в папку проекта: {exe_dest}")
        except Exception as e:
            print(f"Ошибка при перемещении exe: {e}")
            print("Пропускаем обновление exe файла.")
    
    # Копируем локали из исходников в папку проекта
    source_locales = Path('locales')
    if source_locales.exists():
        locales_dest = project_dir / 'locales'
        # Удаляем существующую папку если есть
        if locales_dest.exists():
            shutil.rmtree(locales_dest)
        shutil.copytree(source_locales, locales_dest)
        print(f"Локали скопированы в: {locales_dest}")
    
    # Копируем sing-box.exe из исходников в data/core в папке проекта
    source_core_exe = Path('data/core/sing-box.exe')
    if source_core_exe.exists():
        data_dir = project_dir / 'data'
        core_dir = data_dir / 'core'
        core_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_core_exe, core_dir / 'sing-box.exe')
        print(f"sing-box.exe скопирован в: {core_dir / 'sing-box.exe'}")
    else:
        # Создаем структуру папок даже если sing-box.exe нет
        data_dir = project_dir / 'data'
        core_dir = data_dir / 'core'
        core_dir.mkdir(parents=True, exist_ok=True)
        print(f"Создана структура папок: {core_dir} (sing-box.exe будет скачан при первом запуске)")
    
    # Копируем иконку рядом с exe файлом для использования в трее
    source_icon_ico = Path('icon.ico')
    if source_icon_ico.exists():
        icon_dest = project_dir / 'icon.ico'
        shutil.copy2(source_icon_ico, icon_dest)
        print(f"icon.ico скопирован в: {icon_dest}")
    else:
        # Пробуем скопировать icon.png если есть
        source_icon_png = Path('icon.png')
        if source_icon_png.exists():
            icon_dest = project_dir / 'icon.png'
            shutil.copy2(source_icon_png, icon_dest)
            print(f"icon.png скопирован в: {icon_dest}")
    
    print(f"\nСтруктура проекта создана:")
    print(f"  {project_dir}/")
    print(f"    - SingBox-UI.exe")
    print(f"    - icon.ico (или icon.png)")
    print(f"    - locales/")
    print(f"    - data/core/")

if __name__ == '__main__':
    post_build()

