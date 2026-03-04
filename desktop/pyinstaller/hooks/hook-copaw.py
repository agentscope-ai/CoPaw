# -*- coding: utf-8 -*-
"""PyInstaller hook for copaw package."""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect data files from copaw package, but exclude bundled console assets.
# Frontend assets are injected explicitly from PROJECT_ROOT/console/dist in the
# spec file to guarantee we ship the latest build output.
datas = collect_data_files(
    "copaw",
    include_py_files=False,
    excludes=["**/console/**"],
)

# Collect all submodules
hiddenimports = collect_submodules("copaw")
