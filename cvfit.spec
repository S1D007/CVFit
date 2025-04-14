# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os
import sys

block_cipher = None


is_windows = sys.platform.startswith('win')
is_mac = sys.platform == 'darwin'
is_linux = sys.platform.startswith('linux')

added_files = [
    ('yolov8n-pose.pt', '.'),
]

critical_files = [
    ('yolov8n-pose.pt', '.')
]

datas = []
ultralytics_datas = [(x[0], x[1]) for x in collect_data_files('ultralytics')
                    if 'assets' not in x[0] and 'example' not in x[0]]
datas.extend(ultralytics_datas)

matplotlib_datas = [(x[0], x[1]) for x in collect_data_files('matplotlib')
                   if any(required in x[0] for required in ['mpl-data/fonts', 'mpl-data/stylelib'])]
datas.extend(matplotlib_datas)

a = Analysis(
    ['cvfit.py'],
    pathex=[],
    binaries=[],
    datas=datas + added_files + critical_files,
    hiddenimports=[
        'scipy.spatial.transform._rotation_groups',
        'opencv-python',
        'matplotlib.backends.backend_tkagg',
        'ultralytics.nn.modules',
        'ultralytics.nn.tasks',
        'ultralytics.yolo.cfg',
        'ultralytics.yolo.data',
        'ultralytics.yolo.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib.tests', 'matplotlib.testing',
        'notebook', 'jupyter', 'ipython',
        'IPython', 'jedi', 'testpath', 'packaging',
        'PIL.ImageDraw', 'PIL.ImageFont', 'docutils',
        'pytz', 'tornado', 'zmq', 'pytest'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.binaries = [x for x in a.binaries if not x[0].startswith('scipy/tests/')]
a.binaries = [x for x in a.binaries if not x[0].startswith('torch/test/')]
a.binaries = [x for x in a.binaries if not x[0].endswith('.pdb')]
a.binaries = [x for x in a.binaries if not x[0].endswith('.a')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CVFit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
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

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=True,
        upx=True,
        upx_exclude=[],
        name='CVFit',
    )
