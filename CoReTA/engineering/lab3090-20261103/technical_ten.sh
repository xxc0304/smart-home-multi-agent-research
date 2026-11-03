#!/bin/bash
set -euo pipefail
cd /data2/xiaoxinchen/agent-research/CoReTA
export OMP_NUM_THREADS=4 CUDA_VISIBLE_DEVICES=0
export HF_HOME=/data2/xiaoxinchen/cache/huggingface
export TMPDIR=/data2/xiaoxinchen/tmp
out=runs/lab3090-gpu-preflight-20261103
/data2/xiaoxinchen/venvs/coreta/bin/python tools/b0_expert.py train \
  --config config/b0_lab3090_technical.json --technical-steps 10 \
  --output "$out/ten_steps" 2>&1 | tee "$out/ten-steps.log"
