param([Parameter(Mandatory=$true)][string]$ReportDirectory)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path $ReportDirectory -Force | Out-Null
$result = [ordered]@{ started_at=(Get-Date -Format o); admin=$false; wsl_exit_code=$null; features=@(); restart_required=$false; error=$null }
try {
    $result.admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $result.admin) { throw 'WSL installation requires an administrator token.' }
    & "$env:SystemRoot/System32/wsl.exe" --install --no-distribution --web-download *> (Join-Path $ReportDirectory 'wsl-install.log')
    $result.wsl_exit_code = $LASTEXITCODE
    foreach ($featureName in @('VirtualMachinePlatform','Microsoft-Windows-Subsystem-Linux')) {
        $feature = Get-WindowsOptionalFeature -Online -FeatureName $featureName
        $result.features += @{ name=$featureName; state=[string]$feature.State }
        if ([string]$feature.State -match 'Pending') { $result.restart_required=$true }
    }
    if ($result.wsl_exit_code -eq 3010) { $result.restart_required=$true }
} catch { $result.error=$_.Exception.Message }
$result.finished_at=Get-Date -Format o
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $ReportDirectory 'wsl-install-result.json') -Encoding UTF8
