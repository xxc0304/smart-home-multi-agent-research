# SSH lab3090 environment ledger

### env: coreta@06ec4d42
how: /data2/xiaoxinchen/venvs/coreta on lab3090 (Ubuntu24.04/Python3.12)
tier: {cpus_for_checks:4, mem_gib:62, gpus:1 RTX3090 24GB}
weights: /data2/xiaoxinchen/models/Qwen3-4B-1cfa9a7; official fixed revision,3SHA256 verified
validated: 2026-11-03 seeded CUDA/NF4 witness, documented-command fresh-agent pass,31fixture checks, longest actual step,10steps and real adapter reload
spec: engineering/lab3090-20261103/env-spec.json
lock: engineering/lab3090-20261103/INSTALLED.lock.txt
gotcha: direct Hub/Xet/pip downloads reset; successful official HTTP transfers via temporary SSH loopback proxy17898 to local7897. No public listener.
gotcha: longest7326-token step completed but allocator recovered allocation OOM warning; peak allocated19.05GiB, preserve memory-margin limitation.
readiness: technical engineering only; formal train/V/C/B1 still require their existing batch reviews and finite budgets.
