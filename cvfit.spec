# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import os
import sys

block_cipher = None

# Determine the platform
is_windows = sys.platform.startswith('win')
is_mac = sys.platform == 'darwin'
is_linux = sys.platform.startswith('linux')

# Get additional files we need to include
added_files = [
    ('README.md', '.'),
    ('yolov8n-pose.pt', '.'),
]

datas = []
datas.extend(collect_data_files('ultralytics'))
datas.extend(collect_data_files('matplotlib'))

a = Analysis(
    ['cvfit.py'],
    pathex=[],
    binaries=[],
    datas=datas + added_files,
    hiddenimports=[
        'scipy.spatial.transform._rotation_groups', 
        'opencv-python',
        'matplotlib',
        'numpy',
        'pandas',
        'torch',
        'PIL',
        'scipy',
        'sklearn',
        'ultralytics',
        'supervision',
        'tkinter',
        'matplotlib.backends.backend_tkagg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='CVFit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico' if os.path.exists('resources/icon.ico') else None,
)

if is_mac:
    app = BUNDLE(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='CVFit.app',
        icon='resources/icon.icns' if os.path.exists('resources/icon.icns') else None,
        bundle_identifier='com.cvfit.app',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': 'True',
            'NSCameraUsageDescription': 'CVFit requires camera access to track body movements for fitness analysis.',
        },
    )
else:
    # For Windows and Linux
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='CVFit',
    )