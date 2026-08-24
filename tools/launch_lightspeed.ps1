[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$AllowDeSporteLaunch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root 'venv\Scripts\python.exe'
$ollama = 'C:\Users\acc\AppData\Local\Programs\Ollama\ollama.exe'
$tabby = Join-Path $root 'Desktop_Hooks\LightSpeed\Z Axis\archive\vendor\Tabby\tabby.exe'
$goDist = Join-Path $root 'Apps\lightspeed-go\dist'
$stackRunner = Join-Path $root 'scripts\run_cognigrex_local_stack.py'
$receipt = 'D:\LightSpeed\App\Z Axis\Z-4_Merovingian\data\runtime_exports\cognigrex_local_stack_receipt.json'

$env:LIGHTSPEED_RUNTIME_ROOT = Join-Path $root 'LightSpeed_Runtime'
$env:LIGHTSPEED_SHELL_ROOT = Join-Path $root 'Desktop_Hooks\LightSpeed'
$env:LIGHTSPEED_PROJECT_ROOTS = Join-Path $root 'Projects'
$env:LIGHTSPEED_PYTHON = $python
$env:OLLAMA_MODELS = 'C:\LightSpeed_Consolidated\.dependencies\ollama\models'
$env:TABBY_ROOT = Join-Path $root '.tabby'

$stackArguments = @($stackRunner, '--skip-desporte-population', '--json-output', $receipt)
if ($AllowDeSporteLaunch) {
    $env:DESPORTE_ROOT = 'D:\De Sporte'
    $env:DESPORTE_EXECUTABLE = 'C:\Cognigrex\DeSporte_Isolated\application\DeSporte-20260616\DeSporte.exe'
    $env:DESPORTE_LAUNCH_ARGS = '--data-root "C:\Cognigrex\DeSporte_Isolated\application\DeSporte-20260616\Data" --play --window-type onscreen'
    $stackArguments += '--allow-desporte-launch'
}

foreach ($required in @($python, $ollama, $tabby, $goDist, $stackRunner)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Required LightSpeed launch surface is missing: $required"
    }
}

function Test-LocalPort([int]$Port) {
    try {
        $client = [Net.Sockets.TcpClient]::new()
        $wait = $client.ConnectAsync('127.0.0.1', $Port)
        if (-not $wait.Wait(750)) { return $false }
        $client.Dispose()
        return $true
    } catch {
        return $false
    }
}

if (-not (Test-LocalPort 11434)) {
    Start-Process -FilePath $ollama -ArgumentList 'serve' -WindowStyle Hidden
}
if (-not (Test-LocalPort 8080)) {
    Start-Process -FilePath $tabby -ArgumentList @('serve', '--host', '127.0.0.1', '--port', '8080') -WorkingDirectory (Split-Path $tabby -Parent) -WindowStyle Hidden
}
if (-not (Test-LocalPort 4173)) {
    Start-Process -FilePath $python -ArgumentList @('-m', 'http.server', '4173', '--bind', '127.0.0.1', '--directory', $goDist) -WorkingDirectory $goDist -WindowStyle Hidden
}

& $python @stackArguments
if ($LASTEXITCODE -ne 0) {
    throw "LightSpeed local stack did not pass startup checks. Review $receipt"
}

if (-not $NoBrowser) {
    Start-Process 'http://127.0.0.1:4173/'
}
