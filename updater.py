"""Updater для автоматического обновления SingBox-UI"""
import sys
import time
import shutil
import subprocess
from pathlib import Path

# Определяем корневую папку приложения
if getattr(sys, 'frozen', False):
    exe_path = Path(sys.executable)
    if exe_path.parent.name == '_internal':
        ROOT = exe_path.parent.parent
    else:
        ROOT = exe_path.parent
else:
    ROOT = Path(__file__).resolve().parent

def main():
    """Основная функция обновления"""
    if len(sys.argv) < 3:
        print("Usage: updater.exe <extract_dir> <app_dir>")
        time.sleep(5)
        return
    
    extract_dir = Path(sys.argv[1])
    app_dir = Path(sys.argv[2])
    
    print("SingBox-UI Updater")
    print("=" * 50)
    print(f"Извлеченные файлы: {extract_dir}")
    print(f"Папка приложения: {app_dir}")
    print()
    
    try:
        # Ждем немного, чтобы основное приложение успело закрыться
        print("Ожидание закрытия приложения...")
        time.sleep(2)
        
        # Закрываем все процессы SingBox-UI.exe
        print("Закрытие процессов SingBox-UI...")
        exe_name = "SingBox-UI.exe"
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", exe_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
        except Exception:
            pass  # Игнорируем ошибки
        
        time.sleep(1)
        
        # Находим папку SingBox-UI в распакованных файлах
        new_app_dir = None
        for item in extract_dir.iterdir():
            if item.is_dir() and item.name == "SingBox-UI":
                new_app_dir = item
                break
        
        if not new_app_dir:
            # Если папка SingBox-UI не найдена, возможно файлы в корне
            new_app_dir = extract_dir
        
        print(f"Найдена папка с обновлением: {new_app_dir}")
        print()
        
        # Копируем все файлы из новой версии
        print("Копирование файлов...")
        for item in new_app_dir.iterdir():
            # Пропускаем updater.exe в корне, так как он уже запущен и находится в data
            if item.name == "updater.exe" and item.is_file():
                continue
            
            dest = app_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest, ignore_errors=True)
                shutil.copytree(item, dest, dirs_exist_ok=True)
                print(f"  Скопирована папка: {item.name}")
            else:
                if dest.exists():
                    dest.unlink()
                shutil.copy2(item, dest)
                print(f"  Скопирован файл: {item.name}")
        
        # Копируем updater.exe из новой версии в data (если есть)
        new_updater = new_app_dir / "data" / "updater.exe"
        if new_updater.exists():
            app_data_dir = app_dir / "data"
            app_data_dir.mkdir(parents=True, exist_ok=True)
            app_updater = app_data_dir / "updater.exe"
            # Не перезаписываем себя, если мы уже запущены из этого места
            if app_updater.resolve() != Path(sys.executable).resolve():
                if app_updater.exists():
                    app_updater.unlink()
                shutil.copy2(new_updater, app_updater)
                print(f"  Скопирован updater.exe в data")
        
        # Убеждаемся что locales скопированы в data/locales
        new_locales = new_app_dir / "data" / "locales"
        if new_locales.exists():
            app_data_locales = app_dir / "data" / "locales"
            app_data_locales.mkdir(parents=True, exist_ok=True)
            if app_data_locales.exists():
                shutil.rmtree(app_data_locales, ignore_errors=True)
            shutil.copytree(new_locales, app_data_locales)
            print(f"  Скопированы локали в data/locales")
        
        print()
        print("Обновление завершено!")
        
        # Удаляем временные файлы
        print("Очистка временных файлов...")
        try:
            if extract_dir.parent.exists():
                shutil.rmtree(extract_dir.parent, ignore_errors=True)
        except Exception:
            pass
        
        print()
        print("Запуск обновленного приложения...")
        time.sleep(1)
        
        # Запускаем обновленное приложение
        new_exe = app_dir / "SingBox-UI.exe"
        if new_exe.exists():
            subprocess.Popen([str(new_exe)], cwd=str(app_dir))
            print("Приложение запущено!")
        else:
            print(f"ОШИБКА: {new_exe} не найден!")
            time.sleep(5)
        
    except Exception as e:
        print(f"ОШИБКА при обновлении: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(10)
    finally:
        # Даем время на запуск приложения перед закрытием
        time.sleep(2)

if __name__ == "__main__":
    main()

