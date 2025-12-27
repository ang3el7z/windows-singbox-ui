# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import subprocess
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Automatic QRC compilation before build (if resources_rc.py is missing)
resources_rc_path = Path('scripts/resources_rc.py')
qrc_file = Path('resources/app.qrc')

if not resources_rc_path.exists() and qrc_file.exists():
    print("[spec] Compiling QRC resources...")
    commands = [
        ['py', '-m', 'PyQt5.pyrcc_main', str(qrc_file), '-o', str(resources_rc_path)],
        ['python', '-m', 'PyQt5.pyrcc_main', str(qrc_file), '-o', str(resources_rc_path)],
        ['pyrcc5', str(qrc_file), '-o', str(resources_rc_path)],
    ]
    compiled = False
    for cmd in commands:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            if resources_rc_path.exists():
                print(f"[spec] QRC compiled: {resources_rc_path}")
                compiled = True
                break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    if not compiled:
        print(f"[spec] WARNING: Failed to compile QRC. Run: py scripts/build_qrc.py")
elif not qrc_file.exists():
    print(f"[spec] WARNING: QRC file not found: {qrc_file}")

# Check for sing-box.exe in data/core to include in build
core_exe_path = Path('data/core/sing-box.exe')
binaries_list = []
if core_exe_path.exists():
    binaries_list = [(str(core_exe_path), 'data/core')]
    # print(f"Including sing-box.exe in build: {core_exe_path}")  # Removed to avoid encoding issues in CI

# Collect all locales to data/locales
locales_data = []
locales_dir = Path('locales')
if locales_dir.exists():
    for locale_file in locales_dir.glob('*.json'):
        locales_data.append((str(locale_file), 'data/locales'))
        # print(f"Including locale: {locale_file}")  # Removed to avoid encoding issues in CI

# Collect Ace Editor files
ace_data = []
ace_dir = Path('resources/web/ace')
if ace_dir.exists():
    for ace_file in ace_dir.glob('*.js'):
        ace_data.append((str(ace_file), 'resources/web/ace'))

# Combine all data files
# Note: Fonts are now embedded via Qt Resource System (QRC) - see resources/app.qrc
all_datas = locales_data + ace_data

# Icon is NO LONGER added to datas - it's embedded via Qt Resource System (QRC)
# Uses resources_rc.py, which is compiled from resources/app.qrc

a = Analysis(
    ['main/main.py'],
    pathex=[],
    binaries=binaries_list,
    datas=all_datas,  # Includes locales (fonts are in QRC)
    hiddenimports=[
        'scripts.resources_rc',  # Critical: registers Qt resources (icon and fonts)
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
        'ui.design',
        'ui.design.base',
        'ui.design.component',
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

# Create single exe file with all libraries inside (onefile mode)
# This prevents creation of _internal folder
# Check for icon and use absolute path
icon_path = None
icon_file = Path('icons/icon.ico')
if icon_file.exists():
    icon_path = str(icon_file.resolve())
    # print(f"Using icon: {icon_path}")  # Removed to avoid encoding issues in CI
else:
    # Try to find icon.png
    icon_png = Path('icons/icon.png')
    if icon_png.exists():
        # print("WARNING: icon.ico not found, but icon.png found. Use icon.ico for better compatibility.")  # Removed to avoid encoding issues in CI
        pass
    # print("WARNING: icon.ico not found! Exe will be without icon.")  # Removed to avoid encoding issues in CI

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # Include all libraries in exe
    a.zipfiles,
    a.datas,  # Include locales in exe (they will be available via sys._MEIPASS)
    # Icon and fonts are embedded via Qt Resource System (scripts/resources_rc.py), not needed in datas
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
    icon=icon_path,  # Icon for exe file
    onefile=True,  # All in one file - no _internal folder
)

