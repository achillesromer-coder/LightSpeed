param(
    [string]$McpName = "lightspeed-cgx"
)

$ErrorActionPreference = "Stop"
$CodexCommand = (Get-Command codex.cmd -ErrorAction SilentlyContinue).Source
if (-not $CodexCommand) {
    $CodexCommand = (Get-Command codex -ErrorAction SilentlyContinue).Source
}
if (-not $CodexCommand) {
    throw "Codex CLI was not found on PATH."
}

$NodeCommand = (Get-Command node.exe -ErrorAction SilentlyContinue).Source
if (-not $NodeCommand) {
    $NodeCommand = (Get-Command node -ErrorAction SilentlyContinue).Source
}
if (-not $NodeCommand) {
    throw "Node.js was not found on PATH."
}

$PythonCommand = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $PythonCommand) {
    $PythonCommand = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $PythonCommand) {
    throw "Python was not found on PATH."
}
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$McpRoot = Join-Path $RepoRoot "desktop\LightSpeed_Runtime\mcp\cgx_tools"
$ServerPath = Join-Path $McpRoot "server.mjs"
$SelfTestPath = Join-Path $McpRoot "test_client.mjs"
if (-not (Test-Path -LiteralPath $ServerPath)) {
    throw "CGX MCP server missing: $ServerPath"
}
if (-not (Test-Path -LiteralPath $SelfTestPath)) {
    throw "CGX MCP self-test missing: $SelfTestPath"
}

$UserConfig = Join-Path $HOME ".codex\config.toml"
$BackupPath = $UserConfig + ".pre-cgx-mcp-bootstrap-backup"
$Existing = (& $CodexCommand mcp get $McpName 2>&1 | Out-String)
$Exists = ($LASTEXITCODE -eq 0)
$Current = (
    $Exists -and
    $Existing.Contains($ServerPath) -and
    $Existing.Contains($NodeCommand)
)

if ($Current) {
    Write-Host "Shared CGX MCP server already registered and current."
}
else {
    if (Test-Path -LiteralPath $UserConfig) {
        Copy-Item -LiteralPath $UserConfig -Destination $BackupPath -Force
        Write-Host "Backed up Codex config to: $BackupPath"
    }
    try {
        if ($Exists) {
            & $CodexCommand mcp remove $McpName
            if ($LASTEXITCODE -ne 0) {
                throw "codex mcp remove failed with exit code $LASTEXITCODE"
            }
        }

        & $CodexCommand mcp add $McpName --env "CGX_PYTHON=$PythonCommand" --env "LIGHTSPEED_CORE_ROOT=D:\LightSpeed\Core" --env "LIGHTSPEED_SHELL_ROOT=D:\LightSpeed\App\Z Axis\Z+2_Neo\data\temp_shells" --env "LIGHTSPEED_WAKEUP_CONTRACT=D:\LightSpeed\Core\exports\agent_home\local_agent_wakeup_contract.json" -- $NodeCommand $ServerPath
        if ($LASTEXITCODE -ne 0) {
            throw "codex mcp add failed with exit code $LASTEXITCODE"
        }
    }
    catch {
        if (Test-Path -LiteralPath $BackupPath) {
            Copy-Item -LiteralPath $BackupPath -Destination $UserConfig -Force
            Write-Warning "Restored Codex config after CGX MCP registration failure."
        }
        throw
    }
}

$Verified = (& $CodexCommand mcp get $McpName 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0 -or -not $Verified.Contains($ServerPath)) {
    throw "CGX MCP registration verification failed."
}
& $CodexCommand plugin --help *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Codex rejected the config after CGX MCP registration."
}

& $PythonCommand -c "import tomllib,pathlib; tomllib.loads(pathlib.Path(r'$UserConfig').read_text(encoding='utf-8-sig'))"
if ($LASTEXITCODE -ne 0) {
    throw "Python TOML validation failed after CGX MCP registration."
}

Push-Location $McpRoot
try {
    & $NodeCommand $SelfTestPath *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "CGX MCP self-test failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

Write-Host "Shared CGX MCP server verified: $McpName"
Write-Host "Transport: stdio"
Write-Host "Server: $ServerPath"
Write-Host "Heavy execution remains disabled; local execution requires confirmed=true."
