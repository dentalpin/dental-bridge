# PyInstaller spec for dental-bridge.
#
# Invoked by scripts/build-windows.ps1 and by the GitHub Actions release
# workflow. Mac developers can use the same spec for a smoke build with
# `uv run pyinstaller build/dental-bridge.spec`.
#
# Notes:
# - typer + click resolve adapter entry-points lazily via importlib.metadata.
#   PyInstaller does not see those imports statically, so we list them
#   explicitly under ``hiddenimports``.
# - pyodbc is a compiled extension; PyInstaller picks it up automatically.
#   On Windows the user must still have ODBC Driver 18 for SQL Server
#   installed — we detect this at startup, see adapters/gesden/connection.py.

# pylint: disable=undefined-variable

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

block_cipher = None


hiddenimports: list[str] = []
hiddenimports += collect_submodules("dental_bridge")
hiddenimports += [
    "pyodbc",
    "zstandard",
    "cryptography",
    "cryptography.hazmat.primitives.ciphers.aead",
    "cryptography.hazmat.primitives.kdf.scrypt",
    "yaml",
    "jinja2",
    "structlog",
    "rich",
    "typer",
]


a = Analysis(
    ["../src/dental_bridge/__main__.py"],
    pathex=["../src"],
    binaries=[],
    datas=copy_metadata("dental-bridge"),
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # PyInstaller pulls these in by default; we never need them and
        # they add ~30 MB to the bundle on Windows.
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "IPython",
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="dental-bridge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Manifest opt-in for long Windows paths (>260 chars in clinic image folders).
    manifest=None,
    icon=None,
)
