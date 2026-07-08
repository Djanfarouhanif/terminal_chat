# ============================================================================
#  build.ps1 — reconstruit relay.exe ET l'installeur Windows en une commande.
#
#  Usage (depuis un PowerShell) :
#     cd client
#     .\build.ps1
#
#  Produit :
#     client\dist\relay.exe
#     client\installer\Output\Relay-Setup.exe
#
#  À relancer à chaque fois que tu modifies le CLIENT (nouvelle commande /xxx,
#  affichage, etc.). Les changements BACKEND ne nécessitent PAS de rebuild.
# ============================================================================
param(
    [switch]$ExeOnly  # ne construire que relay.exe (sauter l'installeur)
)

# On NE met PAS $ErrorActionPreference = "Stop" : les outils natifs (PyInstaller,
# ISCC) écrivent sur stderr des messages non-fatals que PowerShell 5.1 traiterait
# à tort comme des erreurs. On vérifie plutôt les codes de sortie ($LASTEXITCODE).
Set-Location $PSScriptRoot

function Assert-Ok($what) {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ECHEC : $what (code $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
}

Write-Host "==> Dossier : $PSScriptRoot" -ForegroundColor Cyan

# --- 1. Environnement Python -------------------------------------------------
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "==> Création de l'environnement virtuel (.venv)..." -ForegroundColor Cyan
    py -m venv .venv;                      Assert-Ok "création du venv"
    & $py -m pip install --upgrade pip --quiet
    & $py -m pip install -r requirements.txt --quiet; Assert-Ok "installation des dépendances"
}

& $py -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "==> Installation de PyInstaller..." -ForegroundColor Cyan
    & $py -m pip install pyinstaller --quiet; Assert-Ok "installation de PyInstaller"
}

# --- 2. Construire relay.exe -------------------------------------------------
Write-Host "==> Construction de relay.exe (PyInstaller)..." -ForegroundColor Cyan
& $py -m PyInstaller `
    --onefile --name relay --noconfirm --clean --log-level WARN `
    --icon "$PSScriptRoot\installer\relay.ico" `
    --exclude-module PIL --exclude-module numpy `
    --collect-all textual `
    --collect-submodules relay_cli `
    --paths . `
    --distpath dist --workpath build\pyi --specpath build `
    build_entry.py
Assert-Ok "build PyInstaller"

$exe = Join-Path $PSScriptRoot "dist\relay.exe"
if (-not (Test-Path $exe)) { Write-Host "ECHEC : relay.exe introuvable après build." -ForegroundColor Red; exit 1 }
Write-Host ("==> OK : {0} ({1:N1} Mo)" -f $exe, ((Get-Item $exe).Length / 1MB)) -ForegroundColor Green

if ($ExeOnly) {
    Write-Host "==> Terminé (exe uniquement)." -ForegroundColor Green
    exit 0
}

# --- 3. Construire l'installeur (Inno Setup) --------------------------------
$isccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    Write-Host "==> Inno Setup introuvable, installation via winget..." -ForegroundColor Yellow
    winget install --id JRSoftware.InnoSetup -e --silent `
        --accept-package-agreements --accept-source-agreements
    $iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $iscc) {
    Write-Host "ECHEC : Inno Setup (ISCC.exe) introuvable. Installez-le : winget install JRSoftware.InnoSetup" -ForegroundColor Red
    exit 1
}

Write-Host "==> Construction de l'installeur (Inno Setup)..." -ForegroundColor Cyan
& $iscc "installer\relay.iss"
Assert-Ok "compilation de l'installeur"

$setup = Join-Path $PSScriptRoot "installer\Output\Relay-Setup.exe"
Write-Host ("==> OK : {0} ({1:N1} Mo)" -f $setup, ((Get-Item $setup).Length / 1MB)) -ForegroundColor Green

# --- 4. Zipper l'installeur (distribution : réduit l'alerte SmartScreen) -----
$zip = Join-Path $PSScriptRoot "installer\Output\Relay-Setup.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $setup -DestinationPath $zip -CompressionLevel Optimal
Write-Host ("==> OK : {0} ({1:N1} Mo)" -f $zip, ((Get-Item $zip).Length / 1MB)) -ForegroundColor Green

Write-Host ""
Write-Host "TERMINE. A distribuer : $zip" -ForegroundColor Green
