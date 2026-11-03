$ErrorActionPreference = 'Stop'
$folder = Join-Path $PSScriptRoot '..\..\related_work\papers\acl-2026.findings-emnlp.1445'
$target = Join-Path $folder 'paper.pdf'
if (Test-Path -LiteralPath $target) { Write-Output 'EXISTS official PDF'; exit 0 }
New-Item -ItemType Directory -Path $folder -Force | Out-Null
$tmp = Join-Path $folder 'download.tmp'
try {
  Invoke-WebRequest -Uri 'https://aclanthology.org/2026.findings-emnlp.1445.pdf' -OutFile $tmp -TimeoutSec 40
  $bytes = [System.IO.File]::ReadAllBytes($tmp)
  if ($bytes.Length -lt 1024 -or [System.Text.Encoding]::ASCII.GetString($bytes,0,5) -ne '%PDF-') { throw 'Invalid PDF content' }
  Move-Item -LiteralPath $tmp -Destination $target
  $body = "# Perceive-Then-Adjudicate`n`n- Official proceedings: https://aclanthology.org/2026.findings-emnlp.1445/`n- PDF: https://aclanthology.org/2026.findings-emnlp.1445.pdf`n- Retrieved for CoReTA literature review on 2026-10-28.`n"
  [System.IO.File]::WriteAllText((Join-Path $folder 'README.md'), $body, [System.Text.Encoding]::UTF8)
  Write-Output "OK official PDF $($bytes.Length) bytes"
} catch {
  if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
  Write-Output "FAILED official PDF: $($_.Exception.Message)"
}
