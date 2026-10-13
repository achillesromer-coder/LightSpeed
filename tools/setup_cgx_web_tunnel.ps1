# CGX / LightSpeed single-host, web-only MCP tunnel onboarding.
# This script does not clone repositories, modify live runtime, install services,
# write secrets to disk, or start a Smith worker. Default mode is diagnostics.
[CmdletBinding()]
param(
    [string]$TunnelId,
    [string]$ApprovedHeadSha,
    [string]$Profile = "cgx-web-readonly",
    [string]$TunnelClientPath = "tunnel-client",
    [switch]$Configure,
    [switch]$Start
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-Exit([string]$Action) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Action exited with code $LASTEXITCODE; stopping without starting a tunnel."
    }
}

function Find-Program([string]$Name) {
    $candidate = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $candidate) { throw "$Name is not installed or is not on PATH." }
    return $candidate.Source
}

function Invoke-NoSecrets([string]$Executable, [string[]]$Arguments, [string]$Label) {
    & $Executable @Arguments
    Assert-Exit $Label
}

if ($Profile -notmatch '^[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}$') {
    throw "Profile must contain only ASCII letters, digits, - and _, max 48 characters."
}
if ($Configure -and $TunnelId -notmatch '^tunnel_[A-Za-z0-9]+$') {
    throw "Use your real tunnel_* ID from OpenAI Platform; no placeholder or guessed ID."
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$wrapper = Join-Path $repoRoot "tools\run_cgx_web_readonly_mcp.mjs"
$mcpDirectory = Join-Path $repoRoot "desktop\LightSpeed_Runtime\mcp\cgx_tools"
$server = Join-Path $mcpDirectory "server.mjs"
$testFile = Join-Path $mcpDirectory "test_web_tunnel.mjs"

foreach ($required in @($wrapper, $server, $testFile, (Join-Path $mcpDirectory "package-lock.json"))) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required reviewed LightSpeed file missing: $required"
    }
}
$node = Find-Program "node"
$git = Find-Program "git"
$npm = Find-Program "npm.cmd"
$actualHead = ((& $git -C $repoRoot rev-parse HEAD) | Out-String).Trim()
Assert-Exit "Read Git HEAD"
$origin = ((& $git -C $repoRoot remote get-url origin) | Out-String).Trim()
Assert-Exit "Read Git origin"
if ($origin -notmatch '(?:github\.com[:/])achillesromer-coder/LightSpeed(?:\.git)?$') {
    throw "Unexpected Git origin. This package must run in the canonical LightSpeed checkout."
}
$branch = ((& $git -C $repoRoot branch --show-current) | Out-String).Trim()
Assert-Exit "Read Git branch"
if (-not $branch) { throw "Detached HEAD checkout; review and bind a dedicated owner worktree first." }

Write-Host "CGX web-only onboarding: verified repository layout."
Write-Host "Repository: $repoRoot"
Write-Host "Branch: $branch"
Write-Host "Commit: $actualHead"
Write-Host "Executable wrapper: $wrapper"
Write-Host "Default web profile: ONE cgx_web_handshake tool; NO shell, git commit, or local work tools."

if (-not ($Configure -or $Start)) {
    Write-Host "Diagnostic only: no tunnel configured, no dependencies installed, no processes started."
    Write-Host "Use -Configure -TunnelId tunnel_<actual> -ApprovedHeadSha <reviewed SHA> for setup."
    Write-Host "Then use -Start -ApprovedHeadSha <same SHA> to run the existing profile."
    exit 0
}

if ($ApprovedHeadSha -notmatch '^[a-fA-F0-9]{40}$' -or
    $actualHead -ne $ApprovedHeadSha.ToLowerInvariant()) {
    throw "Reviewed exact Git commit mismatch; inspect current PR HEAD before configuration."
}

$dirty = @(& $git -C $repoRoot status --porcelain --untracked-files=no)
Assert-Exit "Read Git worktree status"
if ($dirty.Count -gt 0 -and ($dirty | Where-Object { $_ -ne "" }).Count -gt 0) {
    throw "Tracked worktree is modified; use a clean reviewed worktree. No files changed."
}

$tunnel = Find-Program $TunnelClientPath
$envPrompted = $false
try {
    # Credentials exist only in the process and inherited child environment.
    if ([string]::IsNullOrWhiteSpace($env:CONTROL_PLANE_API_KEY)) {
        $secureKey = Read-Host "Paste the OpenAI Platform tunnel runtime API key (input hidden)" -AsSecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
        try {
            $env:CONTROL_PLANE_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
        } finally {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
            $secureKey.Dispose()
        }
        $envPrompted = $true
    }
    if ([string]::IsNullOrWhiteSpace($env:CONTROL_PLANE_API_KEY)) {
        throw "Missing CONTROL_PLANE_API_KEY; no tunnel operation attempted."
    }

    # Install only the exact checked-in package lock; suppress npm lifecycle scripts.
    Push-Location $mcpDirectory
    try {
        Invoke-NoSecrets $npm @("ci", "--ignore-scripts", "--no-audit", "--no-fund") "Pinned npm ci"
        Invoke-NoSecrets $npm @("run", "test:web") "CGX web-only negative privilege test"
    } finally {
        Pop-Location
    }

    if ($Configure) {
        # The wrapper sets CGX_MCP_EXPOSURE itself: never target server.mjs directly.
        $stdioCommand = '"' + $node + '" "' + $wrapper + '"'
        Invoke-NoSecrets $tunnel @(
            "init", "--sample", "sample_mcp_stdio_local",
            "--profile", $Profile, "--tunnel-id", $TunnelId,
            "--mcp-command", $stdioCommand
        ) "Configure approved stdio tunnel"
    }

    Invoke-NoSecrets $tunnel @("doctor", "--profile", $Profile, "--explain") "Tunnel diagnostic"
    if ($Start) {
        Write-Host "Starting outbound-only CGX web tunnel. Press Ctrl+C to stop."
        Write-Host "Next: ChatGPT web > Plugins > Add custom MCP server > Tunnel."
        Invoke-NoSecrets $tunnel @("run", "--profile", $Profile) "Run CGX tunnel"
    } else {
        Write-Host "Configuration and diagnostics complete. Not running a long-lived process."
        Write-Host "To connect, rerun with -Start -ApprovedHeadSha $actualHead"
    }
} finally {
    if ($envPrompted) {
        Remove-Item Env:\CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue
    }
}
