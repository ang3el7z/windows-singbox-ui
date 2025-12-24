"""
Скрипт для компиляции Qt Resource файлов (QRC) в Python модуль
Запускается перед сборкой PyInstaller для зашивания ресурсов в код
"""
import sys
import subprocess
from pathlib import Path


def compile_qrc():
    """
    Компилирует resources/app.qrc в scripts/resources_rc.py
    """
    qrc_file = Path('resources/app.qrc')
    output_file = Path('scripts/resources_rc.py')
    
    if not qrc_file.exists():
        print(f"❌ ERROR: QRC файл не найден: {qrc_file}", file=sys.stderr)
        print(f"   Создайте файл {qrc_file} с описанием ресурсов", file=sys.stderr)
        return False
    
    print(f"[build_qrc] Компиляция QRC: {qrc_file} -> {output_file}")
    
    # Пробуем разные способы вызова pyrcc5
    commands = [
        ['py', '-m', 'PyQt5.pyrcc_main', str(qrc_file), '-o', str(output_file)],
        ['python', '-m', 'PyQt5.pyrcc_main', str(qrc_file), '-o', str(output_file)],
        ['pyrcc5', str(qrc_file), '-o', str(output_file)],
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            if output_file.exists():
                print(f"[OK] QRC compiled: {output_file}")
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print(f"❌ ERROR: Не удалось скомпилировать QRC", file=sys.stderr)
    print(f"   Убедитесь, что PyQt5 установлен и pyrcc5 доступен", file=sys.stderr)
    return False


if __name__ == '__main__':
    success = compile_qrc()
    sys.exit(0 if success else 1)

