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

# Собираем все локали в data/locales
locales_data = []
locales_dir = Path('locales')
if locales_dir.exists():
    for locale_file in locales_dir.glob('*.json'):
        locales_data.append((str(locale_file), 'data/locales'))
        # print(f"Including locale: {locale_file}")  # Removed to avoid encoding issues in CI

# Добавляем иконку в сборку для использования в трее
icon_data = []
icon_file = Path('icons/icon.ico')
if icon_file.exists():
    icon_data.append((str(icon_file), 'icons'))
else:
    icon_png = Path('icons/icon.png')
    if icon_png.exists():
        icon_data.append((str(icon_png), 'icons'))

a = Analysis(
    ['main/main.py'],
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
        'managers.log_ui_manager',
        'utils',
        'utils.i18n',
        'utils.logger',
        'utils.singbox',
        'core',
        'core.downloader',
        'core.protocol',
        'core.singbox_manager',
        'core.deep_link_handler',
        'workers',
        'workers.base_worker',
        'workers.init_worker',
        'workers.version_worker',
        'app',
        'app.application',
        'ui',
        'ui.tray_manager',
        'ui.pages',
        'ui.pages.base_page',
        'ui.pages.profile_page',
        'ui.pages.home_page',
        'ui.pages.settings_page',
        'ui.widgets',
        'ui.widgets.card',
        'ui.widgets.nav_button',
        'ui.widgets.version_label',
        'ui.dialogs',
        'ui.dialogs.base_dialog',
        'ui.dialogs.confirm_dialog',
        'ui.dialogs.info_dialog',
        'ui.dialogs.language_dialog',
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
icon_file = Path('icons/icon.ico')
if icon_file.exists():
    icon_path = str(icon_file.resolve())
    # print(f"Using icon: {icon_path}")  # Removed to avoid encoding issues in CI
else:
    # Пробуем найти icon.png
    icon_png = Path('icons/icon.png')
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

