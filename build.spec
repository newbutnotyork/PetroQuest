# -*- mode: python ; coding: utf-8 -*-
import glob
import os

block_cipher = None

def get_resources():
    resources = [
        ('fonts/*.ttf', 'fonts'),
        ('icons/*.svg', 'icons'),
        ('icons/author.gif', 'icons'),
        ('animations/*.png', 'animations'),
        ('animations/*.jpg', 'animations'),
        ('*.ico', '.'),
        ('*.py', '.'),
        ('*.png', '.')
    ]
    
    # Проверка существования файлов
    for pattern, dest in resources:
        for file in glob.glob(pattern):
            if not os.path.exists(file):
                raise FileNotFoundError(f"Resource file missing: {file}")
    return resources

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=get_resources(),  # Используем нашу функцию
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'pygame._sdl2',
        'scipy.interpolate',
        'numpy',
        'pygame'
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
PYZ = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    PYZ,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OilQuest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True
)
