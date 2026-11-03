import hashlib,json
from pathlib import Path
root=Path('runs/b0-first-run-20261103')
root.mkdir(parents=True,exist_ok=False)
c=json.loads(Path('config/b0_lab3090_technical.json').read_text())
c.update(wall_seconds=600, reviewed_for_run=True)
Path('config/b0_v_prefix_20261103.json').write_text(json.dumps(c,indent=2))
(root/'PREFIX_REVIEW.md').write_text('''# V prefix technical review
Scientific meaning PASS: verify real V generation TASK_DATA/64token/EOS and timing.
Readiness PASS: fixed original first3V, no scoring-guided selection, actual base and
unchanged environment06ec4d42 previously GPU/template/longest/reload validated;
10 affected regression checks pass. No C/H bodies. New technical manifest explicitly
disables primary scoring, full V and candidate selection remain separate.
RUN_ALLOWED: baselineV first3 only,600s wall,greedy64,original seed/model/template.
Stop dependent stages on missing/output-limit/OOM; no implicit retry. Raw outputs retained.
Assistant self-review, not independent research review.
''')
paths=['tools/b0_training.py','tools/b0_expert.py','tools/b0_answers.py',
    'config/b0_v_prefix_20261103.json','data/expert-training-20261030-v1/validation.inputs.jsonl']
(root/'PREFIX_FREEZE.json').write_text(json.dumps({p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths},indent=2))
