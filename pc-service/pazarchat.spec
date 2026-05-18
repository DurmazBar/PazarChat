# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — PazarChat PC Service Windows build.

Kullanım (Windows'ta):
    pyinstaller --clean pazarchat.spec

Çıktı:
    dist/PazarChat/              # klasör (onedir mode)
    dist/PazarChat/PazarChat.exe # ana yürütülebilir

Why onedir (not onefile): EasyOCR ve PyTorch DLL'leri --onefile ile sıkıştırılınca
ilk başlatma 20-30sn'ye çıkıyor (her açılışta TEMP'e açıyor). Onedir ile 2-3sn.
Kullanıcı klasörü zip olarak alır, istediği yere açar.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None


# customtkinter'ın asset dosyalarını (theme JSON'ları, fontlar) bundle'a dahil et
_ctk_datas = collect_data_files('customtkinter')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # .env.example template'i kullanıcıya örnek olarak gitsin
        ('.env.example', '.'),
        # customtkinter theme/asset dosyaları
        *_ctk_datas,
    ],
    hiddenimports=[
        # PyInstaller'ın otomatik tespit edemediği import'lar
        # easyocr lazy import yapıyor → tüm submodule'ları açıkça ekle
        'easyocr',
        'easyocr.recognition',
        'easyocr.detection',
        'easyocr.craft',
        'easyocr.craft_utils',
        # PyTorch backend
        'torch',
        'torchvision',
        # Windows-specific (pywin32 + keyboard)
        'win32gui',
        'win32con',
        'win32api',
        'win32clipboard',
        'pythoncom',
        'pywintypes',
        'keyboard',
        # Pillow modülleri
        'PIL._tkinter_finder',
        # mss screenshot
        'mss',
        'mss.windows',
        # pystray + tray icon
        'pystray._win32',
        'pystray._base',
        # First-run setup GUI (Tkinter + customtkinter)
        'tkinter',
        'tkinter.messagebox',
        'tkinter.ttk',
        'customtkinter',
        # supabase/postgrest/httpx
        'supabase',
        'supabase._sync',
        'postgrest',
        'gotrue',
        'httpx',
        'h2',
        'hpack',
        'hyperframe',
        # pkg_resources fallback
        'pkg_resources.py2_warn',
        'pkg_resources.markers',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Tkinter (pystray tray için gerek yok)
        # 'tkinter',  # not — Pillow'un bazı kısımlarında lazım olabilir, ekleme
        # IPython, jupyter — gerek yok ama büyütüyor
        'IPython',
        'jupyter',
        'notebook',
        'pandas',
        'matplotlib',
        'scipy.weave',
    ],
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
    name='PazarChat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,             # UPX compression — bazı antivirüs false-positive verir, kapalı
    console=True,          # Console aç — log'lar görünür (beta için gerekli)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,             # TODO: assets/icon.ico ekle (yarın)
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PazarChat',      # dist/PazarChat/ klasörü
)
