# One-click build: console -> conda-pack -> NSIS .exe. Run from repo root.
# Requires: conda, node/npm (for console), NSIS (makensis) on PATH.

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $RepoRoot
Write-Host "[build_win] REPO_ROOT=$RepoRoot"
$PackDir = $PSScriptRoot
$Dist = if ($env:DIST) { $env:DIST } else { "dist" }
$Archive = Join-Path $Dist "copaw-env.zip"
$Unpacked = Join-Path $Dist "win-unpacked"
$NsiPath = Join-Path $PackDir "copaw_desktop.nsi"

New-Item -ItemType Directory -Force -Path $Dist | Out-Null

Write-Host "== Building wheel (includes console frontend) =="
# Skip wheel_build if dist already has a wheel for current version
$VersionFile = Join-Path $RepoRoot "src\copaw\__version__.py"
$CurrentVersion = ""
if (Test-Path $VersionFile) {
  $m = (Get-Content $VersionFile -Raw) -match '__version__\s*=\s*"([^"]+)"'
  if ($m) { $CurrentVersion = $Matches[1] }
}
$RunWheelBuild = $true
if ($CurrentVersion) {
  $wheelGlob = Join-Path $Dist "copaw-$CurrentVersion-*.whl"
  if ((Get-ChildItem -Path $wheelGlob -ErrorAction SilentlyContinue).Count -gt 0) {
    Write-Host "dist/ already has wheel for version $CurrentVersion, skipping."
    $RunWheelBuild = $false
  }
}
if ($RunWheelBuild) {
  $WheelBuildScript = Join-Path $RepoRoot "scripts\wheel_build.ps1"
  if (-not (Test-Path $WheelBuildScript)) {
    throw "wheel_build.ps1 not found: $WheelBuildScript"
  }
  & $WheelBuildScript
  if ($LASTEXITCODE -ne 0) { throw "wheel_build.ps1 failed with exit code $LASTEXITCODE" }
}

Write-Host "== Building conda-packed env =="
& python $PackDir\build_common.py --output $Archive --format zip
if ($LASTEXITCODE -ne 0) {
  throw "build_common.py failed with exit code $LASTEXITCODE"
}
if (-not (Test-Path $Archive)) {
  throw "Archive not created: $Archive"
}

Write-Host "== Unpacking env =="
if (Test-Path $Unpacked) { Remove-Item -Recurse -Force $Unpacked }
Expand-Archive -Path $Archive -DestinationPath $Unpacked -Force
$unpackedRoot = Get-ChildItem -Path $Unpacked -ErrorAction SilentlyContinue | Measure-Object
Write-Host "[build_win] Unpacked entries in $Unpacked : $($unpackedRoot.Count)"

# Resolve env root: conda-pack usually puts python.exe at archive root; allow one nested dir.
$EnvRoot = $Unpacked
if (-not (Test-Path (Join-Path $EnvRoot "python.exe"))) {
  $found = Get-ChildItem -Path $Unpacked -Directory -ErrorAction SilentlyContinue |
    Where-Object { Test-Path (Join-Path $_.FullName "python.exe") } |
    Select-Object -First 1
  if ($found) { $EnvRoot = $found.FullName; Write-Host "[build_win] Env root: $EnvRoot" }
}
if (-not (Test-Path (Join-Path $EnvRoot "python.exe"))) {
  throw "python.exe not found in unpacked env (checked $Unpacked and one level down)."
}
if (-not [System.IO.Path]::IsPathRooted($EnvRoot)) {
  $EnvRoot = Join-Path $RepoRoot $EnvRoot
}
Write-Host "[build_win] python.exe found at env root: $EnvRoot"

# Rewrite prefix in packed env so paths point to current location (required after move).
$CondaUnpack = Join-Path $EnvRoot "Scripts\conda-unpack.exe"
if (Test-Path $CondaUnpack) {
  Write-Host "[build_win] Running conda-unpack..."
  & $CondaUnpack
  if ($LASTEXITCODE -ne 0) { throw "conda-unpack failed with exit code $LASTEXITCODE" }
} else {
  Write-Host "[build_win] WARN: conda-unpack.exe not found at $CondaUnpack, skipping."
}

# Launcher .bat so that working dir is the env root. No pause for release.
$LauncherBat = Join-Path $EnvRoot "CoPaw Desktop.bat"
@"
@echo off
cd /d "%~dp0"
if not exist "%USERPROFILE%\.copaw\config.json" (
  "%~dp0python.exe" -m copaw init --defaults --accept-security
)
"%~dp0python.exe" -m copaw desktop
"@ | Set-Content -Path $LauncherBat -Encoding ASCII

Write-Host "== Building NSIS installer =="

# Debug: Print EnvRoot directory contents
Write-Host "=== EnvRoot=$EnvRoot ==="
Write-Host "=== EnvRoot top files ==="
Get-ChildItem -LiteralPath $EnvRoot -Force | Select-Object -First 50 | ForEach-Object { Write-Host $_.FullName }

$VersionFromEnv = $null
try {
  $VersionFromEnv = (& (Join-Path $EnvRoot "python.exe") -c "from importlib.metadata import version; print(version('copaw'))" 2>&1) -replace '\s+$', ''
} catch { Write-Host "[build_win] version from packed env failed: $_" }
$Version = $VersionFromEnv
if (-not $Version) { $Version = $CurrentVersion; Write-Host "[build_win] Using version from __version__.py: $Version" }
if (-not $Version) { $Version = "0.0.0"; Write-Host "[build_win] WARN: Using fallback version 0.0.0" }
Write-Host "[build_win] COPAW_VERSION=$Version OUTPUT_EXE will be under $Dist"
$OutInstaller = Join-Path (Join-Path $RepoRoot $Dist) "CoPaw-Setup-$Version.exe"
# Pass absolute paths to NSIS (keep backslashes).
$UnpackedFull = (Resolve-Path $EnvRoot).Path
$OutputExeNsi = [System.IO.Path]::GetFullPath($OutInstaller)
$nsiArgs = @(
  "/DCOPAW_VERSION=$Version",
  "/DOUTPUT_EXE=$OutputExeNsi",
  "/DUNPACKED=$UnpackedFull",
  $NsiPath
)

# Debug: Check if makensis is available
Write-Host "=== Checking makensis availability ==="
try {
  $makensisPath = (Get-Command makensis -ErrorAction Stop).Source
  Write-Host "[build_win] makensis found at: $makensisPath"
} catch {
  throw "makensis not found in PATH. Please install NSIS and ensure makensis.exe is in PATH."
}

Write-Host "[build_win] Running: makensis $($nsiArgs -join ' ')"
& makensis @nsiArgs
$makensisExit = $LASTEXITCODE
Write-Host "[build_win] makensis exit code: $makensisExit"
if ($makensisExit -ne 0) {
  throw "makensis failed with exit code $makensisExit. Check output above for NSIS error."
}
if (-not (Test-Path $OutInstaller)) {
  throw "NSIS did not create installer: $OutInstaller"
}
Write-Host "== Built $OutInstaller =="
