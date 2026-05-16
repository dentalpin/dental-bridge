# Builds the dental-bridge Windows binary locally.
# Mirrors what .github/workflows/release.yml does on CI.
#
# Usage (PowerShell, from repo root):
#   pwsh ./scripts/build-windows.ps1
#
# Outputs:
#   dist/dental-bridge.exe
#   release/dental-bridge-<version>-windows-x64.exe
#   release/dental-bridge-<version>-windows-x64.exe.sha256
#
# Requirements:
#   - Python 3.12 (installed by uv on first run)
#   - uv (https://github.com/astral-sh/uv)
#   - Microsoft ODBC Driver 18 for SQL Server (msodbcsql18)

$ErrorActionPreference = "Stop"

Write-Host "Checking uv..."
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is not on PATH. Install from https://github.com/astral-sh/uv and re-run."
}

Write-Host "Syncing dependencies..."
uv sync --all-extras

Write-Host "Cleaning previous build..."
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist, build\dental-bridge, release

Write-Host "Running PyInstaller..."
uv run pyinstaller --noconfirm --clean build/dental-bridge.spec

if (-not (Test-Path "dist/dental-bridge.exe")) {
    throw "Build failed: dist/dental-bridge.exe was not produced."
}

Write-Host "Smoke testing the built binary..."
& "dist/dental-bridge.exe" --version

Write-Host "Reading version from package..."
$version = (uv run python -c "import dental_bridge; print(dental_bridge.__version__)").Trim()

$artifactName = "dental-bridge-$version-windows-x64.exe"
$shaName      = "$artifactName.sha256"

New-Item -ItemType Directory -Force -Path release | Out-Null
Copy-Item "dist/dental-bridge.exe" "release/$artifactName"
$hash = (Get-FileHash "release/$artifactName" -Algorithm SHA256).Hash
"$hash *$artifactName" | Out-File -FilePath "release/$shaName" -Encoding ASCII

Write-Host ""
Write-Host "Build complete:" -ForegroundColor Green
Write-Host "  release/$artifactName"
Write-Host "  release/$shaName"
Write-Host ""
Write-Host "SHA-256: $hash"
Write-Host ""
Write-Host "This build is UNSIGNED. SmartScreen will warn on first run."
Write-Host "Publish the SHA-256 alongside the release for manual verification."
