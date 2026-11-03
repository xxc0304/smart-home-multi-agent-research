# Lab3090 GPU preflight results — 2026-11-03

Assistant self-review PASS for CUDA environment, fixed-model integrity, answer-only template, bounded technical training and adapter reload only. No scientific task accuracy or expert qualification claim.

- Environment spec06ec4d42; torch2.14.1+cu126, transformers5.22.1, peft0.21.2, accelerate1.15.0, bitsandbytes0.49.2. pip check and seeded CUDA/NF4 witness pass. Fresh agent executed documented witness/template commands with matching outputs.
- Official Qwen/Qwen3-4B revision1cfa9a7208912126459214e8b04321603b3df60c downloaded; all3 safetensors shard sizes/SHA256 and index match upstream. Model path/data2/xiaoxinchen/models/Qwen3-4B-1cfa9a7.
- All1796train+200V: exact prefix/answer-loss alignment, no truncation; max7326/5012 tokens. enable_thinking=false. No C/H bodies evaluated.
- Existing B0 nine+B1 twenty-two engineering checks pass on new environment; not real team results.
- Longest training example:1 optimizer step COMPLETE,9.00s total/5.86s training; peak allocated20450959360B(19.05GiB), finite loss/grad. CUDA allocator logged a recovered allocation OOM warning; no Python OOM exception or failed batch, but margin is narrow. Preserve this warning; do not describe as warning-free or proof of unlimited context capacity.
- Ten technical steps: COMPLETE,37.91s total/22.63s training loop,peak allocated14514756608B(13.52GiB), finite losses/gradients. Different examples make loss curve unsuitable for judging task improvement.
- Actual saved10step adapter reloaded with same4bit base: finite logits and10 generated tokens on synthetic Say OK prompt. No task accuracy measured. Technical adapters marked purpose=technical_preflight, never eligible expert candidates.

Artifacts on server: CoReTA/runs/lab3090-gpu-preflight-20261103/. Config/code/train hashes in TECHNICAL_FREEZE.json; review in EXPERIMENT_REVIEW.md. Downloads required HTTP fallback and temporary loopback SSH proxy; failed logs retained. No system driver/service modifications.

Next permitted action: review and freeze finite full-training/V generation budget and candidate schedule using these measured costs, then first formal B0 candidate; V-only selection, independent C160 after selection. Full1epoch/1796 optimizer steps at batch1 rough linear extrapolation of this short batch is68min training loop, not a runtime guarantee (length mixture/checkpoint work/thermal/load differ). Validation generation throughput not measured. No full training, V/C inference or team generation launched in this stage.
