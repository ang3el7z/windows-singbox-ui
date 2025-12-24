# -*- coding: utf-8 -*-
"""
PyInstaller hook for qtawesome
This hook ensures that all qtawesome font files are included in the bundle
with the correct directory structure.
"""

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all data files from qtawesome, including fonts
# collect_data_files automatically includes subdirectories and preserves structure
datas = collect_data_files('qtawesome')

# Additionally, explicitly collect font files to ensure they're included
# This is a safety measure to catch any fonts that might be missed
try:
    import qtawesome
    qtawesome_path = Path(qtawesome.__file__).parent
    fonts_path = qtawesome_path / 'fonts'
    
    if fonts_path.exists():
        # Explicitly add all font files with proper directory structure
        for font_file in fonts_path.rglob('*'):
            if font_file.is_file() and font_file.suffix in ['.ttf', '.otf', '.woff', '.woff2', '.json']:
                # Get relative path from qtawesome package root
                rel_path = font_file.relative_to(qtawesome_path.parent)
                # Add to datas if not already included
                font_tuple = (str(font_file), str(rel_path.parent))
                if font_tuple not in datas:
                    datas.append(font_tuple)
except Exception:
    # If we can't find qtawesome, rely on collect_data_files
    pass

# Collect all submodules
hiddenimports = collect_submodules('qtawesome')

