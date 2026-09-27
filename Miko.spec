# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import copy_metadata


datas = []
datas += collect_data_files('tensorflow')
datas += collect_data_files('lightning', include_py_files=True, includes=['**/*.py'])
datas += collect_data_files('lightning-fabric', include_py_files=True, includes=['**/*.py'])
datas += collect_data_files('torch')
datas += collect_data_files('huggingface-hub')
datas += collect_data_files('pyyaml')
datas += collect_data_files('rich')
datas += collect_data_files('pytorch-lightning')
datas += collect_data_files('whisperx')
datas += collect_data_files('audiostretchy')
datas += collect_data_files('gruut')
datas += collect_data_files('transformers', include_py_files=True, includes=['**/*.py'])
datas += collect_data_files('speechbrain', include_py_files=True, includes=['**/*.py'])
datas += collect_data_files('pyannote.audio')
datas += collect_data_files('asteroid-filterbanks')
datas += copy_metadata('asteroid-filterbanks')
datas += copy_metadata('tensorflow')
datas += copy_metadata('pyannote.audio')
datas += copy_metadata('gruut')
datas += copy_metadata('audiostretchy')
datas += copy_metadata('speechbrain')
datas += copy_metadata('rich')
datas += copy_metadata('pytorch-lightning')
datas += copy_metadata('whisperx')
datas += copy_metadata('lightning')
datas += copy_metadata('torch')
datas += copy_metadata('tqdm')
datas += copy_metadata('regex')
datas += copy_metadata('sacremoses')
datas += copy_metadata('requests')
datas += copy_metadata('packaging')
datas += copy_metadata('filelock')
datas += copy_metadata('numpy')
datas += copy_metadata('tokenizers')
datas += copy_metadata('importlib_metadata')
datas += copy_metadata('huggingface-hub')
datas += copy_metadata('pyyaml')


a = Analysis(
    ['Miko.py'],
    pathex=[r'C:\Users\danu0\Downloads\OneReality\MITSUHA_COMPILE_VENV\Lib\site-packages'],
    binaries=[],
    datas=datas,
    hiddenimports=['asteroid-filterbanks', 'lightning', 'lightning-fabric', 'tensorflow', 'pytorch', 'sklearn.utils._cython_blas', 'sklearn.neighbors.typedefs', 'sklearn.neighbors.quad_tree', 'sklearn.tree', 'sklearn.tree._utils', 'huggingface-hub', 'pyyaml'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    module_collection_mode={
        'gradio': 'py',
    },
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Miko',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Miko',
)
