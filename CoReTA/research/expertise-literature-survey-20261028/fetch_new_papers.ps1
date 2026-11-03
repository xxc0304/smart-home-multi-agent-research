$ErrorActionPreference = 'Stop'
$paperRoot = Join-Path $PSScriptRoot '..\..\related_work\papers'
$papers = @(
  @{ id='2606.08457v1'; title='The Consistency Illusion: How Multi-Agent Debate Hides Reasoning Misalignment'; url='https://arxiv.org/pdf/2606.08457v1' },
  @{ id='2606.03032v1'; title='The Deliberative Illusion'; url='https://arxiv.org/pdf/2606.03032v1' },
  @{ id='2610.01244v1'; title='Right Answers, Wrong States: Hidden Information Failures in Multi-Agent Collaboration'; url='https://arxiv.org/pdf/2610.01244v1' },
  @{ id='2610.17893v1'; title='Training LLMs for Multi-Agent Collaboration with Verifiable Information Rewards'; url='https://arxiv.org/pdf/2610.17893v1' },
  @{ id='2610.01042v1'; title='Beyond Final Accuracy: Auditing Communication in LLM Multi-Agent Systems'; url='https://arxiv.org/pdf/2610.01042v1' },
  @{ id='2607.01661v1'; title='Diverse Evidence, Better Forecasts: Multi-Agent Deliberation Under Information Asymmetry'; url='https://arxiv.org/pdf/2607.01661v1' },
  @{ id='2606.00476v2'; title='Doing What They Say, Not What They Reason: Locating the Faithfulness Gap in LLM Agents'; url='https://arxiv.org/pdf/2606.00476v2' },
  @{ id='2609.35279v1'; title='Measuring Collapse and Correction in Homogeneous-Panel LLM Debate'; url='https://arxiv.org/pdf/2609.35279v1' },
  @{ id='2610.31639v1'; title='Causal Chain of Thought: Mitigating Attention Leakage via Context Isolation'; url='https://arxiv.org/pdf/2610.31639v1' },
  @{ id='2601.21742v1'; title='Epistemic Context Learning: Building Trust the Right Way in LLM-Based Multi-Agent Systems'; url='https://arxiv.org/pdf/2601.21742v1' },
  @{ id='2609.36855v1'; title='When Upstream Messages Override Correct Answers: A Controlled Study of Multi-Agent LLM Collaboration'; url='https://arxiv.org/pdf/2609.36855v1' },
  @{ id='2610.02005v1'; title='Counting Moves, Weighing Voices: Bayesian Dialectical Argumentation for Calibrated Multi-LLM Councils under Persistent Adversaries'; url='https://arxiv.org/pdf/2610.02005v1' },
  @{ id='2607.20529v1'; title='Uncertainty-Aware Trust Estimation for Multi-LLM Systems via Structured Expert Judgement'; url='https://arxiv.org/pdf/2607.20529v1' },
  @{ id='2405.14092v3'; title='Large Language Models Can Self-Correct with Key Condition Verification'; url='https://arxiv.org/pdf/2405.14092v3' },
  @{ id='2402.08115v2'; title='On the Self-Verification Limitations of Large Language Models on Reasoning and Planning Tasks'; url='https://arxiv.org/pdf/2402.08115v2' },
  @{ id='2606.02866v1'; title='When Helping Hurts and How to Fix It: Multi-Agent Debate for Data Cleaning'; url='https://arxiv.org/pdf/2606.02866v1' }
)
foreach ($paper in $papers) {
  $folder = Join-Path $paperRoot ('arxiv-' + $paper.id)
  $target = Join-Path $folder 'paper.pdf'
  if (Test-Path -LiteralPath $target) { Write-Output "EXISTS $($paper.id)"; continue }
  New-Item -ItemType Directory -Path $folder -Force | Out-Null
  $tmp = Join-Path $folder 'download.tmp'
  try {
    Invoke-WebRequest -Uri $paper.url -OutFile $tmp -TimeoutSec 40
    $bytes = [System.IO.File]::ReadAllBytes($tmp)
    if ($bytes.Length -lt 1024 -or [System.Text.Encoding]::ASCII.GetString($bytes,0,5) -ne '%PDF-') { throw 'Invalid PDF content' }
    Move-Item -LiteralPath $tmp -Destination $target
    $body = "# $($paper.title)`n`n- arXiv: https://arxiv.org/abs/$($paper.id)`n- Original PDF: $($paper.url)`n- Version: $($paper.id)`n- Retrieved for CoReTA literature review on 2026-10-28.`n"
    [System.IO.File]::WriteAllText((Join-Path $folder 'README.md'), $body, [System.Text.Encoding]::UTF8)
    Write-Output "OK $($paper.id) $($bytes.Length) bytes"
  } catch {
    if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    Write-Output "FAILED $($paper.id): $($_.Exception.Message)"
  }
}
