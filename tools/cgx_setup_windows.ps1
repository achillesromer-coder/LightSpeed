[CmdletBinding()]
param(
    [ValidateSet('first-run', 'resume', 'repair', 'upgrade')]
    [string]$Mode = 'resume',
    [string]$Repo = '',
    [string]$CanonicalRoot = 'D:\LightSpeed',
    [string]$HostRoot = 'C:\Cognigrex',
    [string]$LoadSourceRegistry = '',
    [switch]$Offline,
    [switch]$PrepareMintReview,
    [switch]$BootExistingStack,
    [switch]$ApproveNativeStackRestart
)

# Existing LightSpeed/CGX Windows setup wizard.
# Never installs another runtime, mints IDs, grants leases, changes execution
# policy, imports source bodies, or promotes a DBR.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $Repo) { $Repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }
$Python = Join-Path $CanonicalRoot 'Environment\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    $systemPython = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $systemPython) {
        throw 'No Python available for diagnostics. Managed LightSpeed Python is not installed.'
    }
    $Python = $systemPython.Source
}
$Probe = Join-Path $Repo 'cgx\bootstrap\cgxWindowsBootEvidence.py'
$Planner = Join-Path $Repo 'cgx\bootstrap\cgxSetupCli.mjs'
$Launcher = Join-Path $Repo 'tools\launch_lightspeed.ps1'
if (-not (Test-Path -LiteralPath $Probe)) { throw 'Existing CGX Windows evidence source missing.' }
if (-not (Test-Path -LiteralPath $Planner)) { throw 'Existing CGX unified bootstrap planner missing.' }
if (-not (Test-Path -LiteralPath $Launcher)) { throw 'Existing native LightSpeed launcher missing.' }

if ($LoadSourceRegistry -and -not (Test-Path -LiteralPath $LoadSourceRegistry)) {
    throw 'Alexandria projection is not a local file. No provider retrieval attempted.'
}
$ReceiptRoot = Join-Path $HOME 'Downloads'
if (-not (Test-Path -LiteralPath $ReceiptRoot)) { $ReceiptRoot = $env:TEMP }
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$Receipt = Join-Path $ReceiptRoot ("CGX_WINDOWS_SETUP_" + $Stamp + ".json")

$Arguments = @('-I', '-B', $Probe,
    '--repo', $Repo, '--canonical-root', $CanonicalRoot,
    '--host-root', $HostRoot, '--output', $Receipt)
if ($Offline) { $Arguments += '--offline' }
if ($LoadSourceRegistry) { $Arguments += @('--load-source-registry', $LoadSourceRegistry) }

# Python writes a receipt with exclusive-create semantics outside canonical DB.
$null = & $Python @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "CGX read-only setup evidence returned nonzero status: $LASTEXITCODE"
}
if (-not (Test-Path -LiteralPath $Receipt)) {
    throw 'No CGX setup evidence receipt was produced.'
}
$Evidence = Get-Content -LiteralPath $Receipt -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Evidence.schema -ne 'CGX-WINDOWS-SETUP-AND-BOOT-EVIDENCE/0.1' -or
    $Evidence.mint.native_mint_authorised -ne $false -or
    $Evidence.mint.canonical_db_writes -ne 0) {
    throw 'CGX evidence contract violated; refusing subsequent actions.'
}

# Invoke the existing source planner: CLI arguments never grant native proof.
$Node = Get-Command node.exe -ErrorAction SilentlyContinue
$PlannerState = 'NODE_NOT_INSTALLED'
if ($Node) {
    $PlannerOutput = & $Node.Source $Planner --family Cognigrex.cgx --mode $Mode --device desktop --profile core --offline=true --ls-go=false
    if ($LASTEXITCODE -ne 0) { throw 'Existing CGX bootstrap planner rejected source.' }
    $Planned = ($PlannerOutput -join [Environment]::NewLine) | ConvertFrom-Json
    if ($Planned.setup.canonical_accepted -ne $false -or
        $Planned.setup.runtime_installed -ne $false) {
        throw 'Untrusted setup plan claimed native authority.'
    }
    $PlannerState = 'SOURCE_REVIEW_ONLY'
}

Write-Output ('CGX SETUP EVIDENCE: ' + $Receipt)
Write-Output ('Native parent carrier: ' + $Evidence.s92_carrier.binding_match)
Write-Output ('Operational parent state: ' + $Evidence.operational.parent_instance_state)
Write-Output ('LOAD source-only references: ' + $Evidence.load_alexandria.source_refs)
Write-Output ('Existing stack boot preflight: ' + $Evidence.boot.existing_stack_prerequisites_ready)
Write-Output ('Integrated CGX/UniSpace readiness: ' + $Evidence.boot.complete_integrated_cgx_ready)
Write-Output ('Existing setup planner: ' + $PlannerState)
Write-Output ('Native mint authorised: ' + $Evidence.mint.native_mint_authorised)

if ($PrepareMintReview) {
    $MintReceipt = Join-Path $ReceiptRoot ("CGX_MINT_REVIEW_" + $Stamp + ".json")
    $Proposal = [ordered]@{
        schema = 'CGX-NATIVE-MINT-REVIEW-PROPOSAL/0.1'
        state = 'OWNER_REVIEW_REQUIRED_NOT_EXECUTED'
        parent_instance_object_id = $Evidence.mint.root_instance_for_review
        semantic_parent_object_id = 'cgx:root:cognigrex'
        source_git_head = $Evidence.source.git_head
        existing_parent_state = $Evidence.operational.parent_instance_state
        source_reference_candidates = $Evidence.mint.source_reference_candidates
        source_bodies_copied = 0
        object_ids_created = 0
        authenticated_owner_approval = $false
        signed_lease_issuer_and_revocation_verified = $false
        native_dbr_and_independent_receiver_verified = $false
        canonical_db_committed = $false
        github_review_merged = $false
        public_release = $false
        input_setup_receipt_name = [IO.Path]::GetFileName($Receipt)
    }
    $bytes = [Text.Encoding]::UTF8.GetBytes(($Proposal | ConvertTo-Json -Depth 8) + [Environment]::NewLine)
    $stream = [IO.File]::Open($MintReceipt, [IO.FileMode]::CreateNew,
        [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
    Write-Output ('Mint and commit OWNER-REVIEW proposal: ' + $MintReceipt)
    Write-Output 'No native mint or source promotion was executed.'
}

if ($BootExistingStack) {
    if (-not $ApproveNativeStackRestart) {
        throw 'Explicit -ApproveNativeStackRestart required: launcher may restart Ollama.'
    }
    if ($Evidence.boot.existing_stack_prerequisites_ready -ne $true) {
        throw 'Existing stack preflight failed; no service start attempted.'
    }
    # Process/child-only host configuration, not a persistent Windows setting.
    $env:CGX_FAMILY_IDENTITY_REGISTRY = Join-Path $Repo 'cgx\domain_templates\domain_child_identity_registry.json'
    $env:LIGHTSPEED_CANONICAL_DB = Join-Path $CanonicalRoot 'Data\db\lightspeed_unified.db'
    $env:CGX_ROOT_REGISTRY = Join-Path $HostRoot 'cognigrex.root.json'
    $env:CGX_ROOT_CARRIER = Join-Path $HostRoot 'Cognigrex.cgx'
    if ($LoadSourceRegistry) { $env:CGX_LOAD_SOURCE_REGISTRY = $LoadSourceRegistry }
    Write-Output 'Starting only existing LightSpeed stack; no mint, owner decision or DBR mutation.'
    # Inherit PowerShell host signing policy. Never request a policy bypass.
    & $Launcher -NoBrowser
    $PostBoot = Join-Path $ReceiptRoot ("CGX_WINDOWS_POSTBOOT_" + $Stamp + ".json")
    $ReadbackArguments = @('-I', '-B', $Probe,
      '--repo', $Repo, '--canonical-root', $CanonicalRoot,
      '--host-root', $HostRoot, '--output', $PostBoot)
    if ($LoadSourceRegistry) {
        $ReadbackArguments += @('--load-source-registry', $LoadSourceRegistry)
    }
    $null = & $Python @ReadbackArguments
    if ($LASTEXITCODE -ne 0) { throw 'Post-boot host readback failed.' }
    $After = Get-Content -LiteralPath $PostBoot -Raw -Encoding UTF8 | ConvertFrom-Json
    Write-Output ('Post-boot readback: ' + $PostBoot)
    Write-Output ('Bridge service: ' + $After.services.bridge)
    Write-Output ('UniSpace/LS GO service: ' + $After.services.go)
    if ($After.services.bridge -ne 'LS_GO_IDENTITY_SEEN' -or
        $After.services.go -ne 'HTTP_200') {
        Write-Warning 'Native stack boot not verified by both services; hold release.'
    }
    if ($After.boot.complete_integrated_cgx_ready -ne $true) {
        Write-Warning 'Full CGX/UniSpace setup still held pending PR #214 and native acceptance.'
    }
}
