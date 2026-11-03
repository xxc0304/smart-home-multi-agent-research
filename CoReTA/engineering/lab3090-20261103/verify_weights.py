import hashlib
import json
from pathlib import Path
from huggingface_hub import HfApi

revision = '1cfa9a7208912126459214e8b04321603b3df60c'
root = Path('/data2/xiaoxinchen/models/Qwen3-4B-1cfa9a7')
info = HfApi().model_info('Qwen/Qwen3-4B', revision=revision, files_metadata=True)
assert info.sha == revision
checks = []
for entry in info.siblings:
    if not entry.rfilename.endswith('.safetensors'):
        continue
    path = root / entry.rfilename
    assert path.stat().st_size == entry.size, entry.rfilename
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    expected = entry.lfs.sha256
    assert digest.hexdigest() == expected, entry.rfilename
    checks.append(dict(file=entry.rfilename, size=entry.size, sha256=expected))
index = json.loads((root/'model.safetensors.index.json').read_text())
assert set(index['weight_map'].values()) == {r['file'] for r in checks}
report = dict(status='MODEL_SHARDS_VERIFIED', revision=revision, files=checks)
Path('runs/lab3090-gpu-preflight-20261103/WEIGHT_CHECKS.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
