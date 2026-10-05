[CmdletBinding()]
param(
    [ValidateSet("core", "api", "data", "validation", "dev", "desktop")]
    [string]$Profile = "api",
    [string]$VenvPath = "",
    [string]$ReceiptPath = "",
    [string]$PythonCommand = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RuntimeRoot = Join-Path $RepoRoot "desktop\LightSpeed_Runtime"
$ScriptsRoot = Join-Path $RepoRoot "scripts"

if (-not (Test-Path $RuntimeRoot)) { throw "Missing LightSpeed Runtime source root." }
if (-not (Test-Path $ScriptsRoot)) { throw "Missing repository CGX scripts root." }
if (-not $VenvPath) { $VenvPath = Join-Path $RepoRoot ".venv-lightspeed" }

$Profiles = @{
    core       = "requirements-core.txt"
    api        = "requirements-api.txt"
    data       = "requirements-data.txt"
    validation = "requirements-validation.txt"
    dev        = "requirements-dev.txt"
    desktop    = "requirements-desktop.txt"
}
$Requirements = Join-Path $RuntimeRoot $Profiles[$Profile]
if (-not (Test-Path $Requirements)) { throw "Missing requirements profile: $Requirements" }

$Python = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $Python)) {
    if ($PythonCommand) {
        & $PythonCommand -m venv $VenvPath
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.11 -m venv $VenvPath
    } else {
        & python -m venv $VenvPath
    }
    if ($LASTEXITCODE -ne 0) { throw "Failed to create Python virtual environment." }
}

$PythonVersion = (& $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
if ($PythonVersion -ne "3.11") {
    throw "LightSpeed Runtime requires Python 3.11; found $PythonVersion."
}

& $Python -m pip install --disable-pip-version-check -r $Requirements
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed for profile '$Profile'." }

$SitePackages = (& $Python -c "import site; print(site.getsitepackages()[0])").Trim()
$PthPath = Join-Path $SitePackages "lightspeed_workspace.pth"
[System.IO.File]::WriteAllText($PthPath, $RuntimeRoot + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

& $Python -c "import lightspeed_runtime; from lightspeed_runtime.cgx_preflight import build_assurance_preflight; print('LIGHTSPEED_RUNTIME_IMPORT_PASS')"
if ($LASTEXITCODE -ne 0) { throw "LightSpeed Runtime import/preflight probe failed." }

if ($Profile -in @("api", "dev", "desktop")) {
    & $Python -c "import fastapi, uvicorn; print('LIGHTSPEED_API_IMPORT_PASS')"
    if ($LASTEXITCODE -ne 0) { throw "API profile import probe failed." }
}
if ($Profile -in @("data", "validation", "dev", "desktop")) {
    & $Python -c "import duckdb, pandas, openpyxl, PyPDF2; print('LIGHTSPEED_DATA_IMPORT_PASS')"
    if ($LASTEXITCODE -ne 0) { throw "Data profile import probe failed." }
}
if ($Profile -in @("validation", "dev")) {
    & $Python -c "import pandera; print('LIGHTSPEED_VALIDATION_IMPORT_PASS')"
    if ($LASTEXITCODE -ne 0) { throw "Validation profile import probe failed." }
}

if ($Profile -eq "desktop") {
    & $Python -c "import importlib; from lightspeed_runtime.startup_options import LAUNCH_CORE_MODULES; [importlib.import_module(name) for name in LAUNCH_CORE_MODULES]; from PIL import ImageTk; import tkinter; tkinter.Tcl(); print('LIGHTSPEED_DESKTOP_DEPENDENCIES_PASS')"
    if ($LASTEXITCODE -ne 0) { throw "Desktop dependency probe failed. Use Python 3.11 with Tcl/Tk support; no application was launched." }
}

if (-not $ReceiptPath) {
    $ReceiptPath = Join-Path $RepoRoot "State\Install\lightspeed-runtime-install.json"
}
$ReceiptDir = Split-Path -Parent $ReceiptPath
New-Item -ItemType Directory -Path $ReceiptDir -Force | Out-Null

$Head = (& git -C $RepoRoot rev-parse HEAD).Trim()
$Receipt = [ordered]@{
    schema = "LIGHTSPEED-RUNTIME-INSTALL/0.1"
    profile = $Profile
    repo_root = $RepoRoot
    runtime_root = $RuntimeRoot
    scripts_root = $ScriptsRoot
    source_head = $Head
    python = $Python
    python_version = $PythonVersion
    requirements = $Requirements
    workspace_pth = $PthPath
    freecad = "external-host-capability-not-pip-managed"
    authority = "digital-runtime-install-receipt-only"
    verification_scope = "dependency-imports-only; repository-linked environment, not standalone distribution or application acceptance"
}
$Receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ReceiptPath -Encoding UTF8
Write-Output ("LIGHTSPEED_RUNTIME_INSTALL_RECEIPT=" + $ReceiptPath)
