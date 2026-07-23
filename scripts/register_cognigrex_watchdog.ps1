[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$TaskName = 'LightSpeed Cognigrex Local Guard',
    [string]$CanonicalRoot = 'D:\LightSpeed'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = [System.IO.Path]::GetFullPath($CanonicalRoot)
$python = Join-Path $root 'Environment\Scripts\python.exe'
$script = Join-Path $root 'Automation\ensure_cognigrex_local_stack.py'

foreach ($requiredPath in @($python, $script, $root)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required LightSpeed path is missing: $requiredPath"
    }
}

$action = New-ScheduledTaskAction `
    -Execute $python `
    -Argument ('"{0}" --canonical-root "{1}"' -f $script, $root) `
    -WorkingDirectory $root
$repeating = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$atLogon = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -WakeToRun:$false `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 4)
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

if ($PSCmdlet.ShouldProcess($TaskName, 'Register canonical Cognigrex local guard')) {
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Description 'Keep the local Merovingian and LS GO bridge live; repair only missing bounded services.' `
            -Action $action `
            -Trigger @($atLogon, $repeating) `
            -Settings $settings `
            -Principal $principal `
            -Force `
            -ErrorAction Stop | Out-Null
    }
    catch [Microsoft.Management.Infrastructure.CimException] {
        $taskCommand = ('"{0}" "{1}" --canonical-root "{2}"' -f $python, $script, $root)
        & schtasks.exe /Create /TN $TaskName /TR $taskCommand /SC MINUTE /MO 5 /F /RL LIMITED | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw
        }
    }
}

$registered = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
[pscustomobject]@{
    TaskName = $TaskName
    Registered = $null -ne $registered
    Executable = $python
    Script = $script
    WorkingDirectory = $root
    IntervalMinutes = 5
    AtLogon = $true
    WakeToRun = $false
} | ConvertTo-Json
