# One-click build: console -> conda-pack -> NSIS .exe. Run from repo root.
# Requires: conda, node/npm (for console), NSIS (makensis) on PATH.

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $RepoRoot
$PackDir = $PSScriptRoot
$Dist = if ($env:DIST) { $env:DIST } else { "dist" }
$Archive = Join-Path $Dist "copaw-env.zip"
$Unpacked = Join-Path $Dist "win-unpacked"
$NsiPath = Join-Path $PackDir "copaw_desktop.nsi"

New-Item -ItemType Directory -Force -Path $Dist | Out-Null

Write-Host "== Building console frontend =="
if (Test-Path "console\package.json") {
  Push-Location console
  npm ci
  npm run build
  Pop-Location
  if (Test-Path src\copaw\console) { Remove-Item -Recurse -Force src\copaw\console }
  New-Item -ItemType Directory -Force -Path src\copaw\console | Out-Null
  Copy-Item -Recurse -Force console\dist\* src\copaw\console\
} else {
  Write-Warning "console/ not found; packing without web console."
}

Write-Host "== Building conda-packed env =="
& python $PackDir\build_common.py --output $Archive --format zip

Write-Host "== Unpacking env =="
if (Test-Path $Unpacked) { Remove-Item -Recurse -Force $Unpacked }
Expand-Archive -Path $Archive -DestinationPath $Unpacked -Force

# Launcher .bat so that working dir is the env root
$LauncherBat = Join-Path $Unpacked "CoPaw Desktop.bat"
@"
@echo off
cd /d "%~dp0"
"%~dp0python.exe" -m copaw.cli.main desktop
pause
"@ | Set-Content -Path $LauncherBat -Encoding ASCII

Write-Host "== Building NSIS installer =="
$Version = & (Join-Path $Unpacked "python.exe") -c \
  "from importlib.metadata import version; print(version('copaw'))" 2>$null
if (-not $Version) { $Version = "0.0.0" }
$OutInstaller = Join-Path $Dist "CoPaw-Setup-$Version.exe"
& makensis /DCOPAW_VERSION=$Version "/DOUTPUT_EXE=$OutInstaller" $NsiPath
Write-Host "== Built $OutInstaller =="
