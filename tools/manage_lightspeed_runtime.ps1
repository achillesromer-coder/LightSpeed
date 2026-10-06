[CmdletBinding()]
param(
    [ValidateSet("status", "configure", "install", "update", "rollback")]
    [string]$Action = "status",
    [string]$Slot = "default",
    [ValidateSet("core", "api", "data", "validation", "dev", "desktop")]
    [string]$Profile = "",
    [switch]$Confirm,
    [string]$ManagedRoot = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RuntimeRoot = Join-Path $RepoRoot "desktop\LightSpeed_Runtime"

if (-not (Test-Path -LiteralPath $RuntimeRoot)) {
    throw "Missing LightSpeed Runtime source root: $RuntimeRoot"
}

if ($ManagedRoot) {
    $env:LIGHTSPEED_RUNTIME_MANAGED_ROOT = $ManagedRoot
}

$PreviousPythonPath = $env:PYTHONPATH
try {
    if ($PreviousPythonPath) {
        $env:PYTHONPATH = $RuntimeRoot + [IO.Path]::PathSeparator + $PreviousPythonPath
    }
    else {
        $env:PYTHONPATH = $RuntimeRoot
    }

    $ArgsList = @(
        "-3.11",
        "-m",
        "lightspeed_runtime.runtime_productization",
        $Action,
        "--slot",
        $Slot
    )
    if ($Profile) {
        $ArgsList += @("--profile", $Profile)
    }
    if ($Confirm) {
        $ArgsList += "--confirmed"
    }

    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $PyLauncher) {
        throw "Python launcher 'py' is required for the operator wrapper."
    }

    & $PyLauncher.Source @ArgsList
    if ($LASTEXITCODE -ne 0) {
        throw "LightSpeed runtime productization action failed with exit code $LASTEXITCODE"
    }
}
finally {
    $env:PYTHONPATH = $PreviousPythonPath
}
