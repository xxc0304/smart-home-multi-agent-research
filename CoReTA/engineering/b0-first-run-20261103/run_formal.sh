#!/bin/bash
set -euo pipefail
cd /data2/xiaoxinchen/agent-research/CoReTA
export OMP_NUM_THREADS=4 CUDA_VISIBLE_DEVICES=0
export HF_HOME=/data2/xiaoxinchen/cache/huggingface TMPDIR=/data2/xiaoxinchen/tmp
export PYTHONPATH="$PWD/tools"
py=/data2/xiaoxinchen/venvs/coreta/bin/python
out=runs/b0-first-run-20261103
trap 'echo "PIPELINE_EXIT=$? $(date -Iseconds)"' EXIT
"$py" -c 'import json,hashlib,pathlib; d=json.load(open("runs/b0-first-run-20261103/FORMAL_FREEZE.json")); assert all(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==h for p,h in d.items())'
"$py" tools/b0_expert.py generate --config config/b0_lab3090_V_20261103.json --role V --condition B --output "$out/V_B"
"$py" tools/b0_expert.py score --run "$out/V_B" --output "$out/V_B_score.json"
"$py" -c 'import json; assert json.load(open("runs/b0-first-run-20261103/V_B_score.json"))["status"]=="COMPLETE"'
"$py" tools/b0_expert.py train --config config/b0_lab3090_attempt1_20261103.json --output "$out/attempt1"
"$py" -c 'import json; assert json.load(open("runs/b0-first-run-20261103/attempt1/training_status.json"))["status"]=="COMPLETE"'
"$py" tools/b0_expert.py generate --config config/b0_lab3090_V_20261103.json --role V --condition E --adapter "$out/attempt1/adapter" --output "$out/V_E1"
"$py" tools/b0_expert.py score --run "$out/V_E1" --output "$out/V_E1_score.json"
"$py" tools/b0_expert.py select --reports "$out/V_E1_score.json" --output "$out/selected.json"
echo 'B0_ATTEMPT1_V_PIPELINE_COMPLETE'
