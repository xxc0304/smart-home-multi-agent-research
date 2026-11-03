param([Parameter(Mandatory=$true)][string]$ReportDirectory)
$ErrorActionPreference='Stop'
$result=[ordered]@{ checked_at=(Get-Date -Format o); error=$null; hypervisor_changed=$false }
try {
    $result.last_boot=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToString('o')
    $result.hardware=Get-CimInstance Win32_Processor | Select-Object VirtualizationFirmwareEnabled,SecondLevelAddressTranslationExtensions
    $result.hypervisor_present=(Get-CimInstance Win32_ComputerSystem).HypervisorPresent
    $result.platform_state=[string](Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform).State
    $bootText=(& "$env:SystemRoot/System32/bcdedit.exe" /enum '{current}' | Out-String)
    $result.boot_read_exit_code=$LASTEXITCODE
    $bootText | Set-Content -LiteralPath (Join-Path $ReportDirectory 'boot-current-before.txt') -Encoding UTF8
    $result.hypervisor_launch_type=if ($bootText -match '(?im)^hypervisorlaunchtype\s+(\S+)') { $Matches[1] } else { 'not_explicit' }
    if ($result.boot_read_exit_code -eq 0 -and $result.hypervisor_launch_type -eq 'Off') {
        & "$env:SystemRoot/System32/bcdedit.exe" /set '{current}' hypervisorlaunchtype Auto | Out-File -LiteralPath (Join-Path $ReportDirectory 'hypervisor-enable.log') -Encoding UTF8
        $result.change_exit_code=$LASTEXITCODE
        $result.hypervisor_changed=($LASTEXITCODE -eq 0)
        $result.restart_required=$result.hypervisor_changed
        & "$env:SystemRoot/System32/bcdedit.exe" /enum '{current}' | Set-Content -LiteralPath (Join-Path $ReportDirectory 'boot-current-after.txt') -Encoding UTF8
    }
} catch { $result.error=$_.Exception.Message }
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $ReportDirectory 'hypervisor-boot-check.json') -Encoding UTF8
