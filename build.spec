# build.spec  –  PyInstaller spec for CrudeAI Asphaltene Predictor
# Run with:  pyinstaller build.spec

import sys, os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# ── Hidden imports ────────────────────────────────────────────────────────────
hidden = (
    collect_submodules('uvicorn')
  + collect_submodules('fastapi')
  + collect_submodules('anyio')
  + collect_submodules('starlette')
  + collect_submodules('sklearn')
  + collect_submodules('xgboost')
  + collect_submodules('lightgbm')
  + collect_submodules('webview')
  + collect_submodules('scipy')
  + [
      'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
      'uvicorn.protocols', 'uvicorn.protocols.http',
      'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets',
      'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan',
      'uvicorn.lifespan.on',
      'engineio.async_drivers.threading',
      'jinja2', 'openpyxl', 'joblib',
      'email', 'email.mime', 'email.mime.text',
      'scipy', 'scipy.special', 'scipy.linalg',
      'sklearn.utils._chunking', 'sklearn.utils._param_validation',
  ]
)

# ── Native DLLs for XGBoost / LightGBM ───────────────────────────────────────
def _pkg_dlls(package_name):
    try:
        import importlib, pathlib
        pkg_dir = pathlib.Path(importlib.import_module(package_name).__file__).parent
        return [(str(d), package_name)
                for d in list(pkg_dir.rglob('*.dll')) + list(pkg_dir.rglob('*.pyd'))]
    except Exception:
        return []

binaries = _pkg_dlls('xgboost') + _pkg_dlls('lightgbm')
for pkg in ('xgboost', 'lightgbm'):
    try: binaries += collect_dynamic_libs(pkg)
    except Exception: pass

# ── Data files ────────────────────────────────────────────────────────────────
datas = [
    ('templates', 'templates'),
    ('data',      'data'),
    ('models',    'models'),
]
for pkg in ('xgboost', 'lightgbm', 'webview', 'sklearn'):
    try: datas += collect_data_files(pkg)
    except Exception: pass

# ── Only exclude GUI toolkits — nothing else ──────────────────────────────────
excludes = [
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
    'tkinter', 'wx',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CrudeAI_AsphaltenePredictor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['xgboost.dll', 'xgboost_cuda.dll', 'lib_lightgbm.dll',
                 'libgomp*.dll', 'msvcp*.dll', 'vcruntime*.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
