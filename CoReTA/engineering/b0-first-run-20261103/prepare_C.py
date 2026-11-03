import hashlib,json
from pathlib import Path
from b0_answers import read_jsonl,write_json
from b0_training import load_tokenizer
from expert_mechanism_protocol import task_data
from prepare_answer_only_expert import SYSTEM

root=Path('runs/b0-C160-20261103')
root.mkdir(parents=True,exist_ok=False)
previous=Path('runs/b0-first-run-20261103-v2')
for name in ['V_B_score.json','V_E1_score.json']:
    assert json.loads((previous/name).read_text())['status']=='COMPLETE'
selected=json.loads((previous/'selected.json').read_text())
adapter=Path(selected['selected_adapter'])
origin=json.loads((adapter/'b0_origin.json').read_text())
assert origin['purpose']=='expert_training' and origin['technical_steps'] is None
config=json.loads(Path('config/b0_lab3090_V_v2_20261103.json').read_text())
assert config['revision']==origin['revision'] and config['model_path']==origin['model_path']
assert config['generation']==dict(do_sample=False,max_new_tokens=256)
cpath='data/external/musique-v1.0-20261030/inputs/C_calibration.jsonl'
tasks=read_jsonl(cpath)
ids={t['id'] for t in tasks}
groupfile=Path('implement-stage/expert-answer-only-20261101/C_GROUPS.json')
groups=json.loads(groupfile.read_text())
assert len(tasks)==len(ids)==160 and ids==set(groups['expected_ids'])==set(groups['groups'])
assert groups['n_groups']==139 and groups['largest_group_n']==4
trainids={r['id'] for r in read_jsonl('data/expert-training-answer-only-20261031/train.messages.jsonl')}
vids={r['id'] for r in read_jsonl('data/expert-training-20261030-v1/validation.inputs.jsonl')}
assert ids.isdisjoint(trainids|vids)
tok=load_tokenizer(config)
lengths=[]
for task in tasks:
    messages=[dict(role='system',content=SYSTEM),dict(role='user',content='TASK_DATA\n'+
        json.dumps(task_data(task),ensure_ascii=False,indent=2)+config['evaluation_answer_suffix'])]
    lengths.append(len(tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,
        return_dict=False,**config['template_kwargs'])))
assert max(lengths)+256<=config['max_length']
write_json(root/'DATA_PREFLIGHT.json',dict(n_C=160,n_groups=139,largest_group=4,
    no_exact_T_V_overlap=True,max_input_tokens=max(lengths),answer_cap=256,
    max_length=config['max_length'],C_labels_read_for_preflight=False,
    H_bodies_read=False,grouping='existing predeclared C_GROUPS; exact-ID disjointness not proof of semantic independence'))
write_json('config/b0_C160_20261103.json',config)
write_json(root/'SELECTED_ADAPTER.json',selected)
(root/'EXPERIMENT_REVIEW.md').write_text('''# C160 independent qualification review 2026-11-03

Assistant self-review, review_independence=none, provisional.
Scientific meaning PASS: test whether V-selected sole candidate has independent task
advantage under the same frozen short-answer inference conditions as its base.
C160 original selection,139 predeclared dependency groups/max4, no re-selection,
no C-based training/prompt tuning. Exact T/V ID overlap absent; existing related-item
grouping used, not a proof of absence of pretraining contamination or all semantic overlap.
Readiness PASS: source environment warm-reuse06ec4d42 and prior actual V200 B/E both
COMPLETE; real full V responses and failure handling previously exercised. Selected
adapter is formal task-trained, not technical. Config copied exactly from V,including
suffix,greedy256,max7326,seed20261102,NF4/bf16/thinkingfalse,wall3600s each.
All160 actual C input lengths including256budget fit, labels excluded from model messages;
existing scorer receives labels only after generation, H not read. Snapshot records
source/data/config/adapter; OOM/nonfinite/budget failure retained, no automatic retries.
RUN_ALLOWED: C_B160 once then C_E160 once only if baseline technically complete;
same input/order/inference, then score and existing paired grouped-bootstrap compare.
Any missing/output-limit means INCOMPLETE and no qualification; don't count failure
as semantic wrong or drop samples. No cap expansion/retry/extra sample/second training.
Primary EM difference paired by question,10000 group bootstrap,seed20261102,95percentileCI;
item bootstrap sensitivity and F1 auxiliary. SUPPORTED_TASK_ADVANTAGE only complete
realC,EMdelta>0 and groupCI lower>0 with no grouping precision warnings.5–10pp not a
hard gate. Positive result supports advantage under this condition, not pure reasoning
ability, communication capability, general superiority or team effectiveness. B1 not launched.
Budget maximum2GPUhours soft total; prior V batches suggest minutes, not guaranteed.
''')
paths=['config/b0_C160_20261103.json','tools/b0_training.py','tools/b0_expert.py','tools/b0_answers.py',
    cpath,'data/external/musique-v1.0-20261030/scoring/C_calibration.jsonl',str(groupfile),
    str(previous/'selected.json'),str(adapter/'adapter_config.json'),str(adapter/'adapter_model.safetensors')]
write_json(root/'FREEZE.json',{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths})
print('C160_RUN_ALLOWED',max(lengths))
