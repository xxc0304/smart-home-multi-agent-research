param([Parameter(Mandatory=$true)][string]$ReportDirectory)
$ErrorActionPreference='Stop'
$result=[ordered]@{ started_at=(Get-Date -Format o); feature=$null; restart_required=$false; error=$null }
try {
    $feature=Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All -NoRestart
    $result.feature='VirtualMachinePlatform'
    $result.restart_required=[bool]$feature.RestartNeeded
    $result.state=[string](Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform).State
} catch { $result.error=$_.Exception.Message }
$result.finished_at=Get-Date -Format o
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $ReportDirectory 'platform-enable-result.json') -Encoding UTF8
