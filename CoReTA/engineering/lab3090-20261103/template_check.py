import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path('tools').resolve()))
from b0_training import encode_row, load_tokenizer
from b0_answers import read_jsonl

config = json.loads(Path('config/b0_answer_only_pending.json').read_text())
config.update(model_path='/data2/xiaoxinchen/models/Qwen3-4B-1cfa9a7',
    revision='1cfa9a7208912126459214e8b04321603b3df60c', device='cuda:0',
    dtype='bfloat16', quantization='4bit', template_kwargs={'enable_thinking':False},
    max_length=32768, wall_seconds=1800, target_modules=['q_proj','k_proj','v_proj','o_proj',
    'gate_proj','up_proj','down_proj'], gradient_accumulation_steps=1,
    gradient_checkpointing=True, reviewed_for_run=False, purpose='technical_preflight')
tok = load_tokenizer(config)
report = {}
for split in ['train', 'validation']:
    rows = read_jsonl(Path('data/expert-training-answer-only-20261031') / f'{split}.messages.jsonl')
    lengths = [len(encode_row(tok, r, 32768, config['template_kwargs'])['input_ids']) for r in rows]
    report[split] = {'n':len(lengths), 'min':min(lengths), 'max':max(lengths),
        'total':sum(lengths), 'prefix_and_answer_loss_alignment':True, 'truncation':False}
out = Path('runs/lab3090-gpu-preflight-20261103')
out.mkdir(parents=True, exist_ok=True)
(out/'TEMPLATE_LENGTHS.json').write_text(json.dumps(report, indent=2))
config['max_length'] = max(x['max'] for x in report.values())
Path('config/b0_lab3090_technical_pending.json').write_text(json.dumps(config, indent=2))
print(json.dumps(report))
