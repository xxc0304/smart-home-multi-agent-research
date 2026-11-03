import hashlib
import importlib.metadata
import json
from pathlib import Path
import torch
import transformers, peft, accelerate, bitsandbytes

torch.manual_seed(20261103)
assert torch.cuda.is_available()
x = torch.randn(64, 64)
reference = x @ x.T
actual = (x.cuda() @ x.cuda().T).cpu()
torch.testing.assert_close(actual, reference, rtol=1e-4, atol=1e-4)
layer = bitsandbytes.nn.Linear4bit(64, 32, quant_type='nf4',
    compute_dtype=torch.bfloat16).to('cuda')
y = layer(torch.randn(2, 64, device='cuda', dtype=torch.bfloat16))
assert torch.isfinite(y).all()
spec = json.loads(Path('engineering/lab3090-20261103/env-spec.json').read_text(encoding='utf-8-sig'))
report = dict(status='GPU_WITNESS_PASS', gpu=torch.cuda.get_device_name(),
    torch_cuda=torch.version.cuda, bf16=torch.cuda.is_bf16_supported(),
    compute_capability=torch.cuda.get_device_capability(),
    matmul_max_error=(actual-reference).abs().max().item(),
    nf4_finite=True, versions={n:importlib.metadata.version(n) for n in
    ['torch','transformers','peft','accelerate','bitsandbytes']},
    spec_hash=hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:8])
out = Path('runs/lab3090-gpu-preflight-20261103/GPU_WITNESS.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2))
print(json.dumps(report))
