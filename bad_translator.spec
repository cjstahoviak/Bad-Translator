# bad_translator.spec — PyInstaller build specification
#
# Builds a single-file windowed executable of the Bad Translator GUI.
#
# Usage:
#   pip install pyinstaller
#   pyinstaller bad_translator.spec
#
# Output: dist/Bad-Translator  (or Bad-Translator.exe on Windows)

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect customtkinter assets (theme JSON files, images, etc.)
ctk_datas = collect_data_files("customtkinter")

# Collect translators data files (language lists, etc.)
ts_datas = collect_data_files("translators")

# Bundle the Examples/ directory so users have sample texts available.
examples_src = Path("Examples")
examples_datas = [
    (str(f), "Examples") for f in examples_src.glob("*.txt")
] if examples_src.exists() else []

a = Analysis(
    ["src/bad_translator/gui.py"],
    pathex=[],
    binaries=[],
    datas=ctk_datas + ts_datas + examples_datas,
    hiddenimports=[
        # translators uses dynamic imports for each provider
        *collect_submodules("translators"),
        # tkinter backend needed by customtkinter
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
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
    name="Bad-Translator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # windowed=True hides the terminal window on Windows/macOS.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Set to an .ico/.icns path to add a custom icon.
)
