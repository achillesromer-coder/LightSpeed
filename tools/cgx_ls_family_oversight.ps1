[CmdletBinding()]
param(
    [string]$Repo = 'C:\LightSpeed_Consolidated\_analysis_remote\LightSpeed_Canonical',
    [string]$CanonicalRoot = 'D:\LightSpeed',
    [string]$LoadSourceRegistry = '',
    [switch]$BindCurrentProcess,
    [string]$ReceiptPath = ''
)

# Additive read-only oversight facet for the EXISTING LightSpeed stack.
# Does not start/stop services, migrate DB, install a second store,
# mint CGX IDs, run providers, or request owner credentials.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$identity = Join-Path $Repo 'cgx\domain_templates\domain_child_identity_registry.json'
$runtime = Join-Path $Repo 'desktop\LightSpeed_Runtime'
$db = Join-Path $CanonicalRoot 'Data\db\lightspeed_unified.db'
$rootRegistry = 'C:\Cognigrex\cognigrex.root.json'
$carrier = 'C:\Cognigrex\Cognigrex.cgx'
$python = Join-Path $CanonicalRoot 'Environment\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    throw 'Existing managed LightSpeed Python is unavailable; do not create a replacement environment.'
}
foreach ($required in @($identity, $runtime, $db)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Existing source or native DB unavailable: $required"
    }
}
if ($LoadSourceRegistry -and -not (Test-Path -LiteralPath $LoadSourceRegistry)) {
    throw 'The LOAD projection must be supplied from the existing Alexandria review source.'
}
if ((Test-Path $rootRegistry) -xor (Test-Path $carrier)) {
    throw 'S92 host root/carrier incomplete; no partial binding will be used.'
}

$arguments = @(
    '-I', '-B', (Join-Path $runtime 'lightspeed_runtime\cgx_family_ingestion.py'),
    '--family-registry', $identity,
    '--database', $db
)
if ($LoadSourceRegistry) {
    $arguments += @('--load-registry', $LoadSourceRegistry)
}
if ((Test-Path $rootRegistry) -and (Test-Path $carrier)) {
    $arguments += @('--root-registry', $rootRegistry, '--carrier', $carrier)
}

# Python's isolated mode is deliberate: script imports only standard library.
$lines = & $python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Read-only family ingestion failed (exit $LASTEXITCODE)."
}
$payload = ($lines -join [Environment]::NewLine) | ConvertFrom-Json
if ($payload.schema -ne 'CGX-LS-FAMILY-OVERSIGHT/0.1' -or
    $payload.effects.canonical_db_writes -ne 0 -or
    $payload.effects.object_ids_minted -ne 0) {
    throw 'Family oversight output failed its non-mutation contract.'
}

if ($BindCurrentProcess) {
    # Process-only environment. The already-running bridge does not inherit it.
    $env:CGX_FAMILY_IDENTITY_REGISTRY = $identity
    if ($LoadSourceRegistry) { $env:CGX_LOAD_SOURCE_REGISTRY = $LoadSourceRegistry }
    else { Remove-Item Env:CGX_LOAD_SOURCE_REGISTRY -ErrorAction SilentlyContinue }
    $env:LIGHTSPEED_CANONICAL_DB = $db
    if ((Test-Path $rootRegistry) -and (Test-Path $carrier)) {
        $env:CGX_ROOT_REGISTRY = $rootRegistry
        $env:CGX_ROOT_CARRIER = $carrier
    } else {
        Remove-Item Env:CGX_ROOT_REGISTRY -ErrorAction SilentlyContinue
        Remove-Item Env:CGX_ROOT_CARRIER -ErrorAction SilentlyContinue
    }
}

if ($ReceiptPath) {
    $target = [IO.Path]::GetFullPath($ReceiptPath)
    if (Test-Path -LiteralPath $target) {
        throw 'Existing receipt cannot be overwritten.'
    }
    $json = $payload | ConvertTo-Json -Depth 20
    [IO.File]::WriteAllText($target, $json, [Text.UTF8Encoding]::new($false))
}

# No private locators or source bytes are present in the projection.
$payload | ConvertTo-Json -Depth 20
