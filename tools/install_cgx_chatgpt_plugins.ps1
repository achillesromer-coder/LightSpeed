param(
    [string]$MarketplaceRef = "main"
)

$ErrorActionPreference = "Stop"

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

Write-Host "Resolved marketplaces:"
& codex plugin marketplace list
if ($LASTEXITCODE -ne 0) {
    throw "codex plugin marketplace list failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Marketplace registration complete."
Write-Host "Restart the ChatGPT desktop app, open Plugins, select 'Cognigrex / LightSpeed',"
Write-Host "and verify the nine selectors are installed/enabled. Start a new chat before first use."
