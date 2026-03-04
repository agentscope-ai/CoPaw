# -*- coding: utf-8 -*-
"""PyInstaller hook for agentscope package."""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all data files
datas = collect_data_files("agentscope", include_py_files=False)
datas.extend(collect_data_files("agentscope_runtime", include_py_files=False))

# Collect all submodules
hiddenimports = collect_submodules("agentscope")
hiddenimports.extend(collect_submodules("agentscope_runtime"))