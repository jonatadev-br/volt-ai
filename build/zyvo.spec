# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=[
        (str(BASE_DIR / 'frontend'), 'frontend'),
        (str(BASE_DIR / 'skills'), 'skills'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'litellm',
        'tiktoken',
        'keyring',
        'cryptography',
        'pydantic',
        'yaml',
        'httpx',
        'rich',
        'typer',
        'sqlite3',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Volt-AI',
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
    icon=str(BASE_DIR / 'build' / 'icon.png') if (BASE_DIR / 'build' / 'icon.png').exists() else None,
)