# Lab3090 GPU environment (2026-11-03)

SSH alias: lab3090. Project: /data2/xiaoxinchen/agent-research/CoReTA.
Interpreter: /data2/xiaoxinchen/venvs/coreta/bin/python.
Spec: env-spec.json, canonical SHA256 first8=06ec4d42.

Run these commands verbatim from local PowerShell:

```powershell
ssh -o BatchMode=yes lab3090 'cd /data2/xiaoxinchen/agent-research/CoReTA && OMP_NUM_THREADS=4 HF_HOME=/data2/xiaoxinchen/cache/huggingface /data2/xiaoxinchen/venvs/coreta/bin/python engineering/lab3090-20261103/gpu_witness.py'
ssh -o BatchMode=yes lab3090 'cd /data2/xiaoxinchen/agent-research/CoReTA && OMP_NUM_THREADS=4 /data2/xiaoxinchen/venvs/coreta/bin/python engineering/lab3090-20261103/template_check.py'
```

Expected first command: GPU_WITNESS_PASS, RTX3090, CUDA12.6, bf16 true, nf4_finite true.
Expected second: train1796 max7326 and validation200 max5012; aligned loss, no truncation. It writes a pending technical config with reviewed_for_run=false. Neither command loads pretrained model weights or trains a task model. Each may overwrite its own engineering check report. No C/H bodies read.

Installed versions: torch2.14.1+cu126, transformers5.22.1, peft0.21.2, accelerate1.15.0, bitsandbytes0.49.2. pip check passed. B0 existing9 fixture checks passed.

Fixed weights: Qwen/Qwen3-4B@1cfa9a7208912126459214e8b04321603b3df60c at /data2/xiaoxinchen/models/Qwen3-4B-1cfa9a7. Download and official shard integrity complete; longest7326-token technical step,10 technical steps and actual adapter reload pass. See RESULTS.md for recovered allocation warning and measured memory. Formal task training/qualification are NOT completed. Do not launch train using this README.

No system driver/service changes. HF_HOME/PIP_CACHE_DIR/TMPDIR live under /data2. Direct Hub downloads had repeated connection resets; temporary loopback SSH proxy17898 reuses local proxy7897, has no public listener and is for downloads only.

