[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$TaskName = 'LightSpeed Friday Maintenance'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$python = 'C:\LightSpeed_Consolidated\venv\Scripts\python.exe'
$workingDirectory = 'C:\LightSpeed_Consolidated\LightSpeed_Runtime'
$runtimeRoot = 'C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed'
$arguments = '-m lightspeed_runtime.maintenance --root C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed'

foreach ($requiredPath in @($python, $workingDirectory, $runtimeRoot)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required LightSpeed path is missing: $requiredPath"
    }
}

$action = New-ScheduledTaskAction `
    -Execute $python `
    -Argument $arguments `
    -WorkingDirectory $workingDirectory
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At '19:00'
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -WakeToRun:$false `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

if ($PSCmdlet.ShouldProcess($TaskName, 'Register governed weekly maintenance')) {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description 'Quarantine generated LightSpeed duplicates after Friday 19:00 without waking the computer.' `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Force | Out-Null
}

$registered = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
[pscustomobject]@{
    TaskName = $TaskName
    Registered = $null -ne $registered
    Executable = $python
    Arguments = $arguments
    WorkingDirectory = $workingDirectory
    Schedule = 'Friday 19:00 Australia/Brisbane local time'
    StartWhenAvailable = $true
    WakeToRun = $false
} | ConvertTo-Json
