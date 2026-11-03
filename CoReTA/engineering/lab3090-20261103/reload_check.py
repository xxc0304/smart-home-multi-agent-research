import json
import sys
from pathlib import Path
import torch
from peft import PeftModel
from transformers import GenerationConfig
sys.path.insert(0, str(Path('tools').resolve()))
from b0_training import load_base, load_tokenizer

config = json.loads(Path('config/b0_lab3090_technical.json').read_text())
adapter = Path('runs/lab3090-gpu-preflight-20261103/ten_steps/adapter')
origin = json.loads((adapter/'b0_origin.json').read_text())
assert origin['technical_steps'] == 10 and origin['purpose'] == 'technical_preflight'
model = PeftModel.from_pretrained(load_base(config), adapter, is_trainable=False).eval()
tok = load_tokenizer(config)
inputs = tok.apply_chat_template([{'role':'user','content':'Say OK.'}],
    enable_thinking=False, add_generation_prompt=True, return_dict=True, return_tensors='pt').to('cuda')
with torch.inference_mode():
    logits = model(**inputs).logits
    assert torch.isfinite(logits).all()
    generated = model.generate(**inputs, generation_config=GenerationConfig(
        do_sample=False, max_new_tokens=16, eos_token_id=tok.eos_token_id,
        pad_token_id=tok.pad_token_id))
report = dict(status='REAL_ADAPTER_RELOAD_PASS', synthetic_prompt=True,
    task_accuracy_measured=False, adapter_is_candidate=False,
    generated_tokens=generated.shape[-1]-inputs['input_ids'].shape[-1],
    finite_logits=True, peak_allocated_bytes=torch.cuda.max_memory_allocated())
Path('runs/lab3090-gpu-preflight-20261103/RELOAD_CHECK.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
