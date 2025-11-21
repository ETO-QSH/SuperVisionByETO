# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('src', 'src'),
        ('D:/Work Files/PyQt-Fluent-Widgets-exploit/.venv/Lib/site-packages/qfluentwidgets', 'qfluentwidgets'),
    ],
    hiddenimports=[
        'scipy',
        'scipy._lib.messagestream',
        'numpy',
        'numpy._distributor_init',
        'qfluentwidgets',
        'qfluentwidgets.components.widgets.acrylic_label',
        'qfluentwidgets.common.image_utils',
    ],
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
    name='SuperVisionByETO',
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
    icon=['src\\夕.ico'],
)
