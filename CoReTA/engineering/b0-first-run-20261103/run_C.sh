#!/bin/bash
set -euo pipefail
cd /data2/xiaoxinchen/agent-research/CoReTA
export OMP_NUM_THREADS=4 CUDA_VISIBLE_DEVICES=0 PYTHONPATH="$PWD/tools"
export HF_HOME=/data2/xiaoxinchen/cache/huggingface TMPDIR=/data2/xiaoxinchen/tmp
py=/data2/xiaoxinchen/venvs/coreta/bin/python
out=runs/b0-C160-20261103
adapter=runs/b0-first-run-20261103-v2/attempt1/adapter
trap 'echo "PIPELINE_EXIT=$? $(date -Iseconds)"' EXIT
"$py" -c 'import json,hashlib,pathlib;d=json.load(open("runs/b0-C160-20261103/FREEZE.json"));assert all(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==h for p,h in d.items())'
"$py" tools/b0_expert.py generate --config config/b0_C160_20261103.json --role C --condition B --output "$out/C_B"
"$py" tools/b0_expert.py score --run "$out/C_B" --output "$out/C_B_score.json"
"$py" -c 'import json;assert json.load(open("runs/b0-C160-20261103/C_B_score.json"))["status"]=="COMPLETE"'
"$py" tools/b0_expert.py generate --config config/b0_C160_20261103.json --role C --condition E --adapter "$adapter" --output "$out/C_E"
"$py" tools/b0_expert.py score --run "$out/C_E" --output "$out/C_E_score.json"
"$py" tools/b0_expert.py compare --baseline "$out/C_B_score.json" --expert "$out/C_E_score.json" --groups implement-stage/expert-answer-only-20261101/C_GROUPS.json --output "$out/C_comparison.json"
echo 'C160_PIPELINE_COMPLETE'
