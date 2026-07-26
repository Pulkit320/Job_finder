# ==============================================================================
# Job Finder Bot - Windows Task Scheduler Automation (Runs every 2 days)
# ==============================================================================
# To register this script in Windows Task Scheduler via PowerShell (Administrator):
# $Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\path\to\job_finder\automation\windows_task.ps1"
# $Trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM -DaysInterval 2
# Register-ScheduledTask -TaskName "JobFinderBotSchedule" -Action $Action -Trigger $Trigger

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectDir = Resolve-Path "$ScriptDir\.."

Set-Location $ProjectDir

Write-Output "Starting Scheduled Job Finder Run: $(Get-Date)"

if (Test-Path "$ProjectDir\venv\Scripts\Activate.ps1") {
    & "$ProjectDir\venv\Scripts\Activate.ps1"
}

python main.py search

Write-Output "Scheduled Run Completed: $(Get-Date)"
