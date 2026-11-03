import hashlib,json
from pathlib import Path
from b0_answers import write_json,read_jsonl
root=Path('runs/b0-first-run-20261103-v2');root.mkdir(exist_ok=False)
old=Path('runs/b0-first-run-20261103')
score=json.loads((old/'V_B_score.json').read_text());assert score['status']=='INCOMPLETE' and score['metrics'] is None
rows=read_jsonl(old/'V_B/responses.jsonl');print('OLD_FAILURE_COUNTS',{s:sum(r['status']==s for r in rows) for s in {r['status'] for r in rows}})
for source,target in [('config/b0_lab3090_attempt1_20261103.json','config/b0_lab3090_attempt1_v2_20261103.json'),('config/b0_lab3090_V_20261103.json','config/b0_lab3090_V_v2_20261103.json')]:
 c=json.loads(Path(source).read_text());c['generation']['max_new_tokens']=256;write_json(target,c)
length=json.loads((old/'V_GENERATION_LENGTHS.json').read_text());assert length['max_input_tokens']+256<=length['max_length'];length['answer_cap']=256;write_json(root/'V_GENERATION_LENGTHS.json',length)
text=(old/'EXPERIMENT_REVIEW.md').read_text()
text+='''
## v2 superseding batch — before launch
Original fullV200 produced OUTPUT_LIMIT so scored INCOMPLETE and pipeline stopped
before any formal training. Original responses/failed selection gate retained. Only
change: same B/E greedy output cap256 (previous64). No correctness-based selection,
new prompt, sample, seed, train-target or scoring change. Both groups fully evaluated
under new cap, old baseline cannot be mixed with new E. Raw entire responses scored,
no gold extraction, verbosity can still lower EM/F1. Engineering protocol revision
per existing plan allowance for systematic truncation; not a second train attempt.
Max5045+256<7326 confirmed. Prior3 real outputs replayed and full200 failures retained.
Readiness PASS for bounded v2 conditional on affected regression pass. Scientific
meaning PASS within new decoding condition only. RUN_ALLOWED V_B200 once; only if
COMPLETE launch original first formal1796/1epoch training and then V_E200, with same
3h/1h/1h budgets and stop rules. If any v2 technical incomplete, STOP this pipeline;
no further prompt/cap search in this work stage. No C/H or B1.
'''
(root/'EXPERIMENT_REVIEW.md').write_text(text)
files=['config/b0_lab3090_attempt1_v2_20261103.json','config/b0_lab3090_V_v2_20261103.json','tools/b0_training.py','tools/b0_answers.py','tools/b0_expert.py','data/expert-training-answer-only-20261031/train.messages.jsonl','data/expert-training-20261030-v1/validation.inputs.jsonl','data/expert-training-20261030-v1/validation.targets.jsonl']
write_json(root/'FORMAL_FREEZE.json',{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files})
print('V2_REVIEW_PASS',length)
