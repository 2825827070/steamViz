# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

block_cipher = None

# mtp_data, mtp_bin, mtp_hidden = collect_all('matplotlib')
# pq5_data, pq5_bin, pq5_hidden = collect_all('PyQt5')

# 自动收集资源文件
added_files = [
    ('icon', 'icon'),
]

a = Analysis(
    ['main.py'],
    pathex=[os.getcwd()],
    binaries=[], # mtp_bin + pq5_bin,
    datas=added_files,
    hiddenimports=[
        'pandas._libs.tslibs.base',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'PyQt5',
        'PyQt5.sip',
    ],
    excludes=[
        'notebook', 'jupyter', 'IPython', 'tkinter',
        'torch', 'tensorflow', 'keras', 'cv2', 'PIL.ImageQt',
        'PySide2', 'PySide6', 'PyQt6', 'matplotlib.tests', 'matplotlib.testing',
        'scipy', 'sklearn', 'dask', 'distributed', 'bokeh', 'plotly',
        'selenium', 'playwright', 'astropy', 'lxml', 'sentry_sdk', 'uvicorn',
        'nltk', 'spacy', 'statsmodels', 'h5py', 'tables', 'IPython',
        'ipykernel', 'ipython_genutils', 'traitlets'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SteamViz',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # 恢复为 False，正式版不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon/icon.ico'],  # 使用刚转换的 .ico 图标
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SteamViz',
)
