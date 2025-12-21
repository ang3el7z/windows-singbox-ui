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
    print(f"Включаем sing-box.exe в сборку: {core_exe_path}")

# Собираем все локали
locales_data = []
locales_dir = Path('locales')
if locales_dir.exists():
    for locale_file in locales_dir.glob('*.json'):
        locales_data.append((str(locale_file), 'locales'))
        print(f"Включаем локализацию: {locale_file}")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries_list,
    datas=locales_data,
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
    onefile=True,  # Все в одном файле - не будет _internal
)

