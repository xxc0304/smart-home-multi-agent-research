$ErrorActionPreference = 'Stop'
$folder = Join-Path $PSScriptRoot '..\..\related_work\papers\arxiv-2606.08457v1'
$target = Join-Path $folder 'paper-acl-2026.pdf'
if (Test-Path -LiteralPath $target) { Write-Output 'EXISTS formal GDP'; exit 0 }
$tmp = Join-Path $folder 'acl-download.tmp'
try {
  Invoke-WebRequest -Uri 'https://aclanthology.org/2026.emnlp-main.1780.pdf' -OutFile $tmp -TimeoutSec 40
  $bytes = [System.IO.File]::ReadAllBytes($tmp)
  if ($bytes.Length -lt 1024 -or [System.Text.Encoding]::ASCII.GetString($bytes,0,5) -ne '%PDF-') { throw 'Invalid PDF content' }
  Move-Item -LiteralPath $tmp -Destination $target
  Write-Output "OK formal GDP $($bytes.Length) bytes"
} catch {
  if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
  Write-Output "FAILED formal GDP: $($_.Exception.Message)"
}
