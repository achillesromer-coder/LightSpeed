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
    $headerPattern = '(?m)^' + [Regex]::Escape($header) + '\s*$'
    $headerMatch = [Regex]::Match($text, $headerPattern)

    if ($headerMatch.Success) {
        $afterHeader = $headerMatch.Index + $headerMatch.Length
        $nextHeader = [Regex]::Match($text.Substring($afterHeader), '(?m)^\[')
        if ($nextHeader.Success) {
            $blockEnd = $afterHeader + $nextHeader.Index
        } else {
            $blockEnd = $text.Length
        }
        $block = $text.Substring($headerMatch.Index, $blockEnd - $headerMatch.Index)
        if ($block -match '(?m)^\s*enabled\s*=\s*(true|false)\s*$') {
            $newBlock = [Regex]::Replace(
                $block,
                '(?m)^\s*enabled\s*=\s*(true|false)\s*$',
                'enabled = true',
                1
            )
        } else {
            $newBlock = $header + $nl + 'enabled = true' + $nl + $block.Substring($headerMatch.Length).TrimStart([char]13,[char]10)
        }
        $text = $text.Substring(0, $headerMatch.Index) + $newBlock + $text.Substring($blockEnd)
    } else {
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
$MarketplaceHeader = "[marketplaces.$MarketplaceName]"
$MarketplaceRegistered = $false
if (Test-Path $UserConfig) {
    $MarketplaceRegistered = (Get-Content -LiteralPath $UserConfig -Raw).Contains($MarketplaceHeader)
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

Write-Host "Verified all nine Cognigrex selector IDs in user plugin config."
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
