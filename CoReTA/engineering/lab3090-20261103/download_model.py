import json
from pathlib import Path
from huggingface_hub import snapshot_download

revision = '1cfa9a7208912126459214e8b04321603b3df60c'
target = '/data2/xiaoxinchen/models/Qwen3-4B-1cfa9a7'
snapshot_download('Qwen/Qwen3-4B', revision=revision, local_dir=target,
    allow_patterns=['*.json', '*.safetensors', '*.jinja', 'merges.txt', 'vocab.json', 'LICENSE', 'README.md'],
    max_workers=3)
Path(target, 'DOWNLOAD_PROVENANCE.json').write_text(json.dumps(dict(
    repo='Qwen/Qwen3-4B', revision=revision, source='official huggingface_hub snapshot_download')))
print('MODEL_DOWNLOAD_COMPLETE', target, flush=True)
