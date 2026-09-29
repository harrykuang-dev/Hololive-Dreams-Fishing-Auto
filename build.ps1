$ErrorActionPreference = 'Stop'

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name 'Hololive-Fishing-Auto-v0.2.2' `
    --version-file '.\version_info.txt' `
    '.\gui.py'

if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }
Write-Host "Built: $((Resolve-Path '.\dist\Hololive-Fishing-Auto-v0.2.2.exe').Path)"
