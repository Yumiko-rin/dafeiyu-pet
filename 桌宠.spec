# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 — 大肥鱼桌宠（独立程序，与系统监控台并存）。

打包命令：
    pyinstaller --noconfirm --clean 桌宠.spec
产物：dist/大肥鱼桌宠.exe
"""
from PyInstaller.utils.hooks import collect_all

datas = [('sprites', 'sprites'), ('sounds', 'sounds')]
binaries = []
hiddenimports = ['PySide6.QtMultimedia']

# requests 及其证书资源
try:
    ret = collect_all('requests')
    datas += ret[0]
    binaries += ret[1]
    hiddenimports += ret[2]
except Exception:
    pass

# certifi CA 证书（打包后 HTTPS 请求的 SSL 校验必需）
try:
    ret = collect_all('certifi')
    datas += ret[0]
    binaries += ret[1]
    hiddenimports += ret[2]
except Exception:
    pass

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
