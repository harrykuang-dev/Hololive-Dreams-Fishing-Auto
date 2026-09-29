$ErrorActionPreference = 'Stop'

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name 'Hololive-Fishing-Auto' `
    --version-file '.\version_info.txt' `
    '.\gui.py'

Write-Host "Built: $((Resolve-Path '.\dist\Hololive-Fishing-Auto.exe').Path)"
