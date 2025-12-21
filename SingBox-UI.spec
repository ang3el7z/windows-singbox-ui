# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# Проверяем наличие sing-box.exe в data/core для включения в сборку
core_exe_path = Path('data/core/sing-box.exe')
binaries_list = []
if core_exe_path.exists():
    binaries_list = [(str(core_exe_path), 'data/core')]
    # print(f"Including sing-box.exe in build: {core_exe_path}")  # Removed to avoid encoding issues in CI

# Собираем все локали
locales_data = []
locales_dir = Path('locales')
if locales_dir.exists():
    for locale_file in locales_dir.glob('*.json'):
        locales_data.append((str(locale_file), 'locales'))
        # print(f"Including locale: {locale_file}")  # Removed to avoid encoding issues in CI

# Добавляем иконку в сборку для использования в трее
icon_data = []
icon_file = Path('icon.ico')
if icon_file.exists():
    icon_data.append((str(icon_file), '.'))
    # print(f"Including icon in build: {icon_file}")  # Removed to avoid encoding issues in CI
else:
    icon_png = Path('icon.png')
    if icon_png.exists():
        icon_data.append((str(icon_png), '.'))
        # print(f"Including PNG icon in build: {icon_png}")  # Removed to avoid encoding issues in CI

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries_list,
    datas=locales_data + icon_data,
    hiddenimports=[
        'qtawesome',
        'requests',
        'winreg',
        'config',
        'config.paths',
        'managers',
        'managers.settings',
        'managers.subscriptions',
        'utils',
        'utils.i18n',
        'utils.singbox',
        'core',
        'core.downloader',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure)

# Создаем один exe файл со всеми библиотеками внутри (onefile режим)
# Это позволит не создавать папку _internal
# Проверяем наличие иконки и используем абсолютный путь
icon_path = None
icon_file = Path('icon.ico')
if icon_file.exists():
    icon_path = str(icon_file.resolve())
    # print(f"Using icon: {icon_path}")  # Removed to avoid encoding issues in CI
else:
    # Пробуем найти icon.png и конвертировать
    icon_png = Path('icon.png')
    if icon_png.exists():
        # print("WARNING: icon.ico not found, but icon.png found. Use icon.ico for better compatibility.")  # Removed to avoid encoding issues in CI
        pass
    # print("WARNING: icon.ico not found! Exe will be without icon.")  # Removed to avoid encoding issues in CI

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # Включаем все библиотеки в exe
    a.zipfiles,
    a.datas,  # Включаем локали и sing-box.exe в exe (они будут доступны через sys._MEIPASS)
    [],
    name='SingBox-UI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,  # Иконка для exe
    onefile=True,  # Все в одном файле - не будет _internal
)

