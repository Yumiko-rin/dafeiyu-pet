# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 — 大肥鱼桌宠（无AI版）。

打包命令：
    pyinstaller --noconfirm --clean 桌宠.spec
产物：dist/大肥鱼桌宠.exe
"""
from PyInstaller.utils.hooks import collect_all

datas = [('sprites', 'sprites'), ('sounds', 'sounds')]
binaries = []
hiddenimports = ['PySide6.QtMultimedia', 'psutil']

a = Analysis(
    ['桌宠.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='大肥鱼桌宠',
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
    icon=['icon.ico'],
)
