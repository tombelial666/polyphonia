# -*- mode: python ; coding: utf-8 -*-

# PyInstaller spec for the Polyphonia desktop build (PETS repository).
# Build: pyinstaller polyphonia.spec  →  dist/polyphonia.exe

a = Analysis(
    ['phrygian_app.py'],
    pathex=[],
    binaries=[],
    datas=[('index.html', '.'), ('assets', 'assets')],
    hiddenimports=[],
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
    name='polyphonia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
