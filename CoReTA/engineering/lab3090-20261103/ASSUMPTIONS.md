# 2026-11-03 GPU preflight choices

Scope: establish CUDA execution and Qwen3-4B compatibility for the existing expert-utilization study, not a new method or capability result.

- Model: Qwen/Qwen3-4B at 1cfa9a7208912126459214e8b04321603b3df60c, matching prior tokenizer provenance. First candidate chosen for 24GB card, no outcome-based model selection.
- CUDA stack: torch2.14.1 cu126; HF/PEFT/Accelerate use prior CPU-tested versions; bitsandbytes0.49.2 is a compatibility candidate, must pass real NF4 witness. No global system packages/driver changes.
- Technical template: enable_thinking=false, matching short-answer-only supervision and 64-token answer budget; identical for eventual B/E, not a claim of pure ability change.
- Before load: exact prefix/assistant loss alignment and no truncation for all1796 train+200V. Max training length derived only from these lengths, not C/H.
- Technical training only: proposed10 optimizer steps, batch1/accumulation1, all linear attention+MLP LoRA r8/alpha16, NF4+bf16, gradient checkpointing, finite1800s wall budget. Not an eligible expert adapter. Start only after GPU witness/template/unit checks and saved batch review. Full training remains unlaunched.
- Downloads: official Hub revision, HTTP fallback after Xet repeated connections; preserve failed logs. All caches on /data2.
- Environment spec was recorded during phase1 installation rather than before; this ordering deviation is logged. Fresh agent must follow documented check verbatim before environment readiness is declared.
