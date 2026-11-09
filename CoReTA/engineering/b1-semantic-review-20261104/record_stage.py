from pathlib import Path
import hashlib
import json
root = Path(__file__).resolve().parents[2]
folder = Path(__file__).resolve().parent
hashes = json.loads((folder / 'SOURCE_HASHES.json').read_text(encoding='utf-8'))
for name, expected in hashes.items():
    source = root / name
    if not source.exists() and name.startswith('engineering/b1-audit-20261104/'):
        # Laptop copied manifest/trials into its audit folder; server retains
        # those immutable files in the original run directory.
        source = root / 'runs/b1-dev32-final-20261104-v2' / name.removeprefix('engineering/b1-audit-20261104/')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected, str(source)
rows = json.loads((folder / 'CASE_LEDGER.json').read_text(encoding='utf-8'))
assert len(rows) == len({(r['task_id'], r['arm']) for r in rows}) == 48
rules_hash = hashlib.sha256((folder / 'SEMANTIC_RULES.md').read_bytes()).hexdigest()
assert all(r['source']['rules_sha256'] == rules_hash for r in rows)
entry = Path(__file__).with_name('STAGE_ENTRY.md').read_text(encoding='utf-8')
for name in ('handoff.md', 'CURRENT_STATE.md', 'brainstorm.md',
             'refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md',
             'refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
    p = root / name
    old = p.read_text(encoding='utf-8')
    if entry.splitlines()[0] not in old:
        p.write_text(entry + old, encoding='utf-8')
print(f'T1_STAGE_RECORDED; {len(rows)} paths; {len(hashes)} original hashes matched; NO_MODEL_RUNS')
