"""One longest-training-example step; technical adapter is never an expert candidate."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path('tools').resolve()))
from b0_answers import read_jsonl
from b0_training import encode_row, load_tokenizer, train

config = json.loads(Path('config/b0_lab3090_technical.json').read_text())
assert config['purpose'] == 'technical_preflight'
assert config['wall_seconds'] == 1800
tokenizer = load_tokenizer(config)
rows = read_jsonl(Path('data/expert-training-answer-only-20261031/train.messages.jsonl'))
longest = max(rows, key=lambda r: len(encode_row(tokenizer, r, config['max_length'], config['template_kwargs'])['input_ids']))
train(config, [longest], Path('runs/lab3090-gpu-preflight-20261103/longest_step'), max_steps=1)
