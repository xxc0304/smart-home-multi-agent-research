import hashlib
import json
from pathlib import Path

root = Path('runs/lab3090-gpu-preflight-20261103')
assert json.loads((root/'WEIGHT_CHECKS.json').read_text())['status'] == 'MODEL_SHARDS_VERIFIED'
witness = json.loads((root/'GPU_WITNESS.json').read_text())
assert witness['status'] == 'GPU_WITNESS_PASS' and witness['nf4_finite'] and witness['bf16']
lengths = json.loads((root/'TEMPLATE_LENGTHS.json').read_text())
assert lengths['train']['n'] == 1796 and lengths['train']['max'] == 7326
assert lengths['validation']['n'] == 200
for name in ['b0-unit.log', 'b1-unit.log']:
    assert '\nOK\n' in (root/name).read_text()
config = json.loads(Path('config/b0_lab3090_technical_pending.json').read_text())
assert config['purpose'] == 'technical_preflight' and not config['fixture']
assert config['wall_seconds'] == 1800 and config['max_length'] == 7326
config['reviewed_for_run'] = True
Path('config/b0_lab3090_technical.json').write_text(json.dumps(config,indent=2))
files = ['config/b0_lab3090_technical.json','tools/b0_training.py','tools/b0_expert.py',
         'data/expert-training-answer-only-20261031/train.messages.jsonl']
freeze = {f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files}
(root/'TECHNICAL_FREEZE.json').write_text(json.dumps(freeze,indent=2))
(root/'EXPERIMENT_REVIEW.md').write_text('''# Technical preflight review 2026-11-03

Assistant self-review; not independent scientific review.
Scientific meaning PASS: check actual Qwen answer-only execution, longest training context,
finite optimizer loss, adapter save/load and throughput needed before bounded expert preparation.
Supports only engineering feasibility; no task accuracy, expert advantage or collaboration claims.
Read only frozen T1796/V200; no C/H bodies or evaluation. No outcome-based item selection;
longest training item is selected by token length solely for memory validation.
Readiness PASS: exact revision and all3 official shard SHA256 verified; CUDA/NF4 seeded
witness PASS; bf16 true; all1996 template prefix/loss checks pass without truncation;
max7326, B0 nine/B1 twenty-two existing checks PASS, pip check PASS.
Fresh agent followed the two documented witness/template commands; outputs matched.
RUN_ALLOWED only for one longest-example optimizer step, then if successful ten technical
steps on original training rows; each wall budget1800s, no automatic retry, seed20261102,
NF4/bf16/checkpointing, batch1/accum1, LoRA r8/alpha16 all attention+MLP projections.
OOM/nonfinite/budget failure stops affected batch; retain partial adapter marked NOT_CANDIDATE.
Technical outputs are not candidate experts. Actual long-context execution is the unknown tested.
Formal training, V/C qualification and B1 remain DO_NOT_RUN until subsequent review.
Configuration/code/train data hashes in TECHNICAL_FREEZE.json.
''')
print('TECHNICAL_RUN_ALLOWED', json.dumps(freeze))
