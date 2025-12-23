# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

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

a = Analysis(
    ['main/updater.py'],
    pathex=[],
    binaries=[],
    datas=icon_data,
    hiddenimports=[
        'config',
        'config.paths',
        'requests',
        'zipfile',
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



