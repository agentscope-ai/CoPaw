# -*- coding: utf-8 -*-
"""PyInstaller hook for playwright package."""
from PyInstaller.utils.hooks import collect_data_files

# Collect playwright driver and related files
datas = collect_data_files("playwright", include_py_files=False)

# Ensure all playwright modules are included
hiddenimports = [
    "playwright",
    "playwright.async_api",
    "playwright.sync_api",
    "playwright._impl",
    "playwright._impl._api_structures",
    "playwright._impl._api_types",
    "playwright._impl._browser",
    "playwright._impl._browser_context",
    "playwright._impl._browser_type",
    "playwright._impl._page",
    "playwright._impl._playwright",
    "playwright._impl._connection",
]