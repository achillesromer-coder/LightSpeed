[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$AllowDeSporteLaunch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$canonicalRoot = if ($env:LIGHTSPEED_CANONICAL_ROOT) { $env:LIGHTSPEED_CANONICAL_ROOT } else { 'D:\LightSpeed' }
$python = Join-Path $canonicalRoot 'Environment\Scripts\python.exe'
$ollama = 'C:\Users\acc\AppData\Local\Programs\Ollama\ollama.exe'
$goDist = Join-Path $canonicalRoot 'Apps\lightspeed-go\dist'
$stackRunner = Join-Path $canonicalRoot 'Automation\run_cognigrex_local_stack.py'
$receipt = Join-Path $canonicalRoot 'App\Z Axis\Z-4_Merovingian\data\runtime_exports\cognigrex_local_stack_receipt.json'

$env:LIGHTSPEED_CANONICAL_ROOT = $canonicalRoot
$env:LIGHTSPEED_RUNTIME_ROOT = Join-Path $canonicalRoot 'Core'
$env:LIGHTSPEED_SHELL_ROOT = Join-Path $canonicalRoot 'App'
$env:LIGHTSPEED_CANONICAL_DB = Join-Path $canonicalRoot 'Data\db\lightspeed_unified.db'
$env:LIGHTSPEED_PROJECT_ROOTS = Join-Path $canonicalRoot 'Projects'
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

foreach ($required in @($python, $ollama, $goDist, $stackRunner)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Required LightSpeed launch surface is missing: $required"
    }
}

function Test-LocalHttp([string]$Uri) {
    try {
        $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -eq 200
    } catch {
        return $false
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
if (-not (Test-LocalHttp 'http://127.0.0.1:4173/')) {
    Start-Process -FilePath $python -ArgumentList @('-m', 'http.server', '4173', '--bind', '127.0.0.1', '--directory', $goDist) -WorkingDirectory $goDist -WindowStyle Hidden
}

& $python @stackArguments
if ($LASTEXITCODE -ne 0) {
    throw "LightSpeed local stack did not pass startup checks. Review $receipt"
}
if (-not (Test-LocalHttp 'http://127.0.0.1:4173/')) {
    throw 'LightSpeed Go did not return HTTP 200 on http://127.0.0.1:4173/'
}

if (-not $NoBrowser) {
    Start-Process 'http://127.0.0.1:4173/'
}
