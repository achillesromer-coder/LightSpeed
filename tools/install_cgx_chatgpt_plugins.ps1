param(
    [string]$MarketplaceRef = "main"
)

$ErrorActionPreference = "Stop"
$MarketplaceName = "cognigrex-lightspeed"
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

Write-Host "Registering Cognigrex / LightSpeed plugin marketplace..."
& codex plugin marketplace add achillesromer-coder/LightSpeed --ref $MarketplaceRef
if ($LASTEXITCODE -ne 0) {
    throw "codex plugin marketplace add failed with exit code $LASTEXITCODE"
}

Write-Host "Refreshing plugin marketplaces..."
& codex plugin marketplace upgrade
if ($LASTEXITCODE -ne 0) {
    throw "codex plugin marketplace upgrade failed with exit code $LASTEXITCODE"
}

$UserConfig = Join-Path $HOME ".codex\config.toml"
Write-Host "Enabling nine Cognigrex selectors in user plugin config..."
foreach ($PluginId in $PluginIds) {
    Set-CodexPluginEnabled -PluginId $PluginId -ConfigPath $UserConfig
}

Write-Host "Resolved marketplaces:"
& codex plugin marketplace list
if ($LASTEXITCODE -ne 0) {
    throw "codex plugin marketplace list failed with exit code $LASTEXITCODE"
}

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
