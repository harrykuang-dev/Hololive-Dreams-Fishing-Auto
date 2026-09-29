$ErrorActionPreference = 'Stop'

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name 'Hololive-Fishing-Auto-0.1.1' `
    --version-file '.\version_info.txt' `
    '.\gui.py'

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host "Built: $((Resolve-Path '.\dist\Hololive-Fishing-Auto-0.1.1.exe').Path)"
