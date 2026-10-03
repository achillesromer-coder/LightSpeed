param(
    [string]$MarketplaceRef = "main"
)

$ErrorActionPreference = "Stop"
$MarketplaceName = "cognigrex-lightspeed"
$CodexCommand = (Get-Command codex.cmd -ErrorAction SilentlyContinue).Source
if (-not $CodexCommand) {
    $CodexCommand = (Get-Command codex -ErrorAction SilentlyContinue).Source
}
if (-not $CodexCommand) {
    throw "Codex CLI was not found on PATH."
}

$PluginIds = @(
    "achilles@$MarketplaceName",
    "neo@$MarketplaceName",
    "athene@$MarketplaceName",
    "raphael@$MarketplaceName",
    "cognigrex@$MarketplaceName",
    "romer-grex@$MarketplaceName",
    "eco-grex@$MarketplaceName",
    "emassc@$MarketplaceName",
    "lightspeed@$MarketplaceName"
)

function Set-CodexPluginEnabled {
    param(
        [Parameter(Mandatory = $true)][string]$PluginId,
        [Parameter(Mandatory = $true)][string]$ConfigPath
    )

    $nl = [Environment]::NewLine
    $text = ""
    if (Test-Path $ConfigPath) {
        $text = Get-Content -LiteralPath $ConfigPath -Raw
    }

    $header = '[plugins."' + $PluginId + '"]'
    $headerPattern = '(?m)^' + [Regex]::Escape($header) + '[ \t]*\r?$'
    $headerMatch = [Regex]::Match($text, $headerPattern)

    if ($headerMatch.Success) {
        $afterHeader = $headerMatch.Index + $headerMatch.Length
        $nextHeader = [Regex]::Match($text.Substring($afterHeader), '(?m)^\[')
        if ($nextHeader.Success) {
            $blockEnd = $afterHeader + $nextHeader.Index
        }
        else {
            $blockEnd = $text.Length
        }

        $block = $text.Substring($headerMatch.Index, $blockEnd - $headerMatch.Index)
        $enabledPattern = '(?m)^[ \t]*enabled[ \t]*=[ \t]*(true|false)[ \t]*\r?$'
        if ($block -match $enabledPattern) {
            $newBlock = [Regex]::Replace(
                $block,
                $enabledPattern,
                'enabled = true',
                1
            )
        }
        else {
            $newBlock = (
                $header + $nl +
                'enabled = true' + $nl +
                $block.Substring($headerMatch.Length).TrimStart([char]13, [char]10)
            )
        }

        $text = (
            $text.Substring(0, $headerMatch.Index) +
            $newBlock +
            $text.Substring($blockEnd)
        )
    }
    else {
        if ($text.Length -gt 0 -and -not $text.EndsWith($nl)) {
            $text += $nl
        }
        $text += $nl + $header + $nl + 'enabled = true' + $nl
    }

    $parent = Split-Path -Parent $ConfigPath
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Set-Content -LiteralPath $ConfigPath -Value $text -Encoding utf8
}

$UserConfig = Join-Path $HOME ".codex\config.toml"
$HadUserConfig = Test-Path $UserConfig
$BackupPath = $UserConfig + ".pre-cgx-bootstrap-backup"

if ($HadUserConfig) {
    Copy-Item -LiteralPath $UserConfig -Destination $BackupPath -Force
    Write-Host "Backed up existing Codex config to: $BackupPath"
}

$MarketplaceHeader = "[marketplaces.$MarketplaceName]"
$MarketplaceRegistered = $false
if (Test-Path $UserConfig) {
    $MarketplaceRegistered = (
        Get-Content -LiteralPath $UserConfig -Raw
    ).Contains($MarketplaceHeader)
}

if (-not $MarketplaceRegistered) {
    Write-Host "Registering Cognigrex / LightSpeed plugin marketplace..."
    & $CodexCommand plugin marketplace add achillesromer-coder/LightSpeed --ref $MarketplaceRef
    if ($LASTEXITCODE -ne 0) {
        throw "codex plugin marketplace add failed with exit code $LASTEXITCODE"
    }
}
else {
    Write-Host "Cognigrex / LightSpeed marketplace already registered."
}

Write-Host "Refreshing Cognigrex / LightSpeed marketplace..."
& $CodexCommand plugin marketplace upgrade $MarketplaceName
if ($LASTEXITCODE -ne 0) {
    throw "codex plugin marketplace upgrade failed with exit code $LASTEXITCODE"
}

try {
    Write-Host "Enabling nine Cognigrex selectors in user plugin config..."
    foreach ($PluginId in $PluginIds) {
        Set-CodexPluginEnabled -PluginId $PluginId -ConfigPath $UserConfig
    }

    $ConfigText = Get-Content -LiteralPath $UserConfig -Raw

    $MissingPluginIds = @(
        $PluginIds | Where-Object {
            -not $ConfigText.Contains('[plugins."' + $_ + '"]')
        }
    )
    if ($MissingPluginIds.Count -gt 0) {
        throw "Plugin enablement verification failed for: $($MissingPluginIds -join ', ')"
    }

    $MalformedJoins = [Regex]::Matches(
        $ConfigText,
        '(?m)enabled[ \t]*=[ \t]*true[ \t]*\[plugins\.'
    )
    if ($MalformedJoins.Count -gt 0) {
        throw "Plugin enablement produced $($MalformedJoins.Count) malformed TOML table join(s)."
    }

    $InvalidPluginBlocks = @(
        $PluginIds | Where-Object {
            $escaped = [Regex]::Escape($_)
            $pattern = (
                '(?m)^\[plugins\."' + $escaped +
                '"\][ \t]*\r?\n[ \t]*enabled[ \t]*=[ \t]*true[ \t]*\r?$'
            )
            -not [Regex]::IsMatch($ConfigText, $pattern)
        }
    )
    if ($InvalidPluginBlocks.Count -gt 0) {
        throw "Plugin block validation failed for: $($InvalidPluginBlocks -join ', ')"
    }

    & $CodexCommand plugin --help *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Codex rejected the resulting config (exit code $LASTEXITCODE)."
    }

    Write-Host "Verified all nine Cognigrex selector IDs and TOML parse state."
}
catch {
    if ($HadUserConfig -and (Test-Path $BackupPath)) {
        Copy-Item -LiteralPath $BackupPath -Destination $UserConfig -Force
        Write-Warning "Restored Codex config from backup after bootstrap validation failure."
    }
    elseif (-not $HadUserConfig -and (Test-Path $UserConfig)) {
        Remove-Item -LiteralPath $UserConfig -Force
        Write-Warning "Removed newly created Codex config after bootstrap validation failure."
    }
    throw
}

$SharedMcpInstaller = Join-Path $PSScriptRoot "install_cgx_shared_mcp.ps1"
if (-not (Test-Path -LiteralPath $SharedMcpInstaller)) {
    throw "Shared CGX MCP installer missing: $SharedMcpInstaller"
}
Write-Host "Verifying shared Cognigrex / LightSpeed MCP tool plane..."
& $SharedMcpInstaller

Write-Host ""
Write-Host "Cognigrex chat plugin provisioning complete."
Write-Host "User config: $UserConfig"
Write-Host ""
Write-Host "After restarting ChatGPT Desktop, these @ mentions should be available in new chats:"
Write-Host "  @Achilles  @Neo  @Athene  @Raphael  @Cognigrex"
Write-Host "  @Römer-Grex  @Eco-Grex  @EMASSC  @LightSpeed"
Write-Host ""
Write-Host "If a selector does not appear, open Plugins > Personal > Cognigrex / LightSpeed"
Write-Host "and confirm it is installed/enabled. Local desktop plugins are not made available"
Write-Host "to web/mobile merely by saving them to the account."
