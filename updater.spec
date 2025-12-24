# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Добавляем иконку в сборку
icon_data = []
icon_file = Path('icons/icon.ico')
if icon_file.exists():
    icon_data.append((str(icon_file), 'icons'))
else:
    icon_png = Path('icons/icon.png')
    if icon_png.exists():
        icon_data.append((str(icon_png), 'icons'))

# Collect qtawesome fonts and data files
# This ensures fonts are available in bundled data, not just temp directory
# Critical for app restart - prevents errors when temp _MEI directory is deleted
# The hook file (hooks/hook-qtawesome.py) handles proper collection of qtawesome files
# We still collect here as a fallback, but the hook should handle it
qtawesome_data = collect_data_files('qtawesome')

# Combine all data files
all_datas = icon_data + qtawesome_data

a = Analysis(
    ['main/updater.py'],
    pathex=[],
    binaries=[],
    datas=all_datas,  # Includes icon and qtawesome fonts/data
    hiddenimports=[
        'config',
        'config.paths',
        'requests',
        'zipfile',
        'qtawesome',
    ],
    hookspath=['hooks'],  # Use custom hooks for qtawesome
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure)

# Проверяем наличие иконки и используем абсолютный путь
icon_path = None
icon_file = Path('icons/icon.ico')
if icon_file.exists():
    icon_path = str(icon_file.resolve())
else:
    icon_png = Path('icons/icon.png')
    if icon_png.exists():
        pass

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='updater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI приложение, не показываем консоль
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
    onefile=True,
)



