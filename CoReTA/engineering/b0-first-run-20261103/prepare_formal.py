import hashlib,json
from pathlib import Path
from b0_answers import read_jsonl,score_run,write_json
from b0_training import load_tokenizer
from expert_mechanism_protocol import task_data
from prepare_answer_only_expert import SYSTEM

root=Path('runs/b0-first-run-20261103')
records=read_jsonl(root/'V_prefix_v2/responses.jsonl')
assert len(records)==3 and all(r['status']=='OK' for r in records)
targets={r['id']:r for r in read_jsonl('data/expert-training-20261030-v1/validation.targets.jsonl')}
replay=score_run(root/'V_prefix_v2',targets)
assert replay['status']=='COMPLETE' and not replay['primary_enabled']
write_json(root/'V_PREFIX_REPLAY.json',replay)
failed=score_run(root/'V_prefix',targets)
assert failed['status']=='INCOMPLETE' and failed['metrics'] is None
write_json(root/'V_PREFIX_FAILURE_REPLAY.json',failed)
c=json.loads(Path('config/b0_v_prefix_v2_20261103.json').read_text())
tok=load_tokenizer(c)
tasks=read_jsonl('data/expert-training-20261030-v1/validation.inputs.jsonl')
lengths=[]
for task in tasks:
    messages=[dict(role='system',content=SYSTEM),dict(role='user',content='TASK_DATA\n'+
        json.dumps(task_data(task),ensure_ascii=False,indent=2)+c['evaluation_answer_suffix'])]
    lengths.append(len(tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,
        return_dict=False,**c['template_kwargs'])))
assert max(lengths)+64<=c['max_length']
write_json(root/'V_GENERATION_LENGTHS.json',dict(n=len(lengths),max_input_tokens=max(lengths),
    answer_cap=64,max_length=c['max_length'],truncation=False))
c.update(purpose='expert_training',wall_seconds=10800,reviewed_for_run=True)
write_json('config/b0_lab3090_attempt1_20261103.json',c)
evaluation=dict(c,wall_seconds=3600)
write_json('config/b0_lab3090_V_20261103.json',evaluation)
(root/'EXPERIMENT_REVIEW.md').write_text('''# Formal B0 attempt1 + V review 2026-11-03

Assistant self-review, review_independence=none, acceptance_status=provisional.
Scientific meaning PASS: construct one task adapter, compare against same base on fixed V200.
This is bounded expert preparation, not expert qualification or team mechanism evidence.
T1796/V200 fixed, no re-split/no C/H. Original prefix3 used only for EOS/interface;
v1 all3 OUTPUT_LIMIT retained, v2 same3 normal EOS. No correctness-based prompt search.
Evaluation suffix strengthened existing short-answer requirement, applied identically B/E;
training examples unchanged. Scores apply to this evaluation condition only, future B1
needs matching standalone controls. No gold injected into model prompts or extracted answers.

Readiness PASS: official3-shard integrity, environment06ec4d42, CUDA/NF4/bf16,
allT/V template masks/lengths, longest7326-token actual step,10step save/reload passed.
Actual prefix outputs replay through original scorer; incomplete original cannot gain metrics,
technical v2 cannot enable primary scoring. All200 actual generation prompts fit cap7326
including64new tokens. Affected10unit checks pass; final source frozen below.

RUN_ALLOWED: V_B200 once (wall3600s); only if technically COMPLETE, train attempt1
original1796 rows,1epoch/batch1/accum1/r8/alpha16/LR2e-5/seed20261102/NF4bf16,
checkpointing, wall10800s. FullV_E200 same inference and wall3600s after COMPLETE
training and saved adapter origin expert_training. Select sole candidate by V EM/F1;
selection does not establish independent task advantage. No auto second attempt/C/B1.
Known longest allocator recovery warning retained; record reserved/retry/OOM stats.
OOM/nonfinite/timeout stops affected batch and dependent actions; no automatic retries.
No candidate from partial or technical adapters. Raw baseline/adapter outputs and null
failures remain. Prefix repeated only as clearly separate engineering/official evaluations.
Maximum active budget5h (3h train +1h eachV), no paidAPI. Previous short training
suggests ~68min loop but not guarantee; prefixV latency is small/nonrepresentative.
''')
files=['config/b0_lab3090_attempt1_20261103.json','config/b0_lab3090_V_20261103.json',
    'tools/b0_training.py','tools/b0_answers.py','tools/b0_expert.py',
    'data/expert-training-answer-only-20261031/train.messages.jsonl',
    'data/expert-training-20261030-v1/validation.inputs.jsonl',
    'data/expert-training-20261030-v1/validation.targets.jsonl']
write_json(root/'FORMAL_FREEZE.json',{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files})
print('FORMAL_RUN_ALLOWED',max(lengths))
