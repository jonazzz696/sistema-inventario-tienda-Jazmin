# -*- mode: python ; coding: utf-8 -*-
# Compilar con:  python -m PyInstaller main.spec --noconfirm


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # (archivo de origen, carpeta destino dentro del ejecutable)
    datas=[
        ('database/schema.sql', 'database'),
        ('ui/styles/theme.qss', 'ui/styles'),
        ('tienda_jazmin.ico', '.'),
    ],
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
    name='TiendaJazmin',
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
    icon=['tienda_jazmin.ico'],
)
