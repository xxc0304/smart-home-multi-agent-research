"""Fresh development from reserve; hash-only guards, never opens H bodies."""
import argparse,collections,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
DATA=ROOT/'data/external/musique-v1.0-20261030'
sys.path.insert(0,str(ROOT/'research/musique-data-preparation-20261030'))
from build_pack import guard,reasons,select
from audit_corpus import sanitize,keys
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[json.loads(s) for s in (DATA/'corpus_index.jsonl').open()];by={r['id']:r for r in rows}
assign=[json.loads(s) for s in (DATA/'split_assignments.jsonl').open()]
role={r['id']:r['role'] for r in assign}
protected=[r for r in rows if role[r['id']] in ('C_calibration','D_development','H_confirmation_candidate','T_optional_training')]
g=guard(protected);reserve=[r for r in rows if role[r['id']]=='TRAIN_UNUSED_ELIGIBLE_RESERVE']
tg=guard([r for r in protected if role[r['id']]=='T_optional_training']);tg['keys']={k for k in tg['keys'] if k[0]!='a'}
other=guard([r for r in protected if role[r['id']]!='T_optional_training'])
available=[r for r in reserve if not reasons(r,tg) and not reasons(r,other) and r['input_tokens']<=3800]
print(json.dumps(dict(reserve=len(reserve),after_all_role_and_length_guards=len(available),shapes=dict(collections.Counter(r['shape'] for r in available)))),flush=True)
if '--counts-only' in sys.argv:sys.exit(0)
assert len(available)>=92
candidates=select(available,min(220,len(available)),'D100_input_review_20261107')
if '--candidates' in sys.argv:
  ids={r['id'] for r in candidates};data=[]
  for line in (DATA/'musique_ans_v1.0_train.jsonl').open():
    r=json.loads(line)
    if r['id'] in ids:data.append(r)
  byraw={r['id']:r for r in data}
  out=[dict(candidate=i,id=z['id'],strict_training_answer_isolation=not reasons(z,g),input_tokens=z['input_tokens'],question=byraw[z['id']]['question'],answer=byraw[z['id']]['answer'],support_paragraphs=[p for p in byraw[z['id']]['paragraphs'] if p['is_supporting']],task=sanitize(byraw[z['id']])) for i,z in enumerate(candidates)]
  (HERE/'CANDIDATES.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(candidates=len(out))),flush=True);sys.exit(0)
review_decision=load(HERE/'QUALITY_DECISIONS.json');accepted=review_decision['accepted_candidates'];assert len(accepted)==56 and len(set(accepted))==56
chosen=[candidates[i] for i in accepted];ids={r['id'] for r in chosen}
raw={}
for line in (DATA/'musique_ans_v1.0_train.jsonl').open():
  r=json.loads(line)
  if r['id'] in ids:raw[r['id']]=r
assert set(raw)==ids
old=load(ROOT/'research/b1-independent-first-work-20261106/INPUTS.json')
oldlabels=load(ROOT/'research/b1-independent-first-work-20261106/LABELS.json')['targets']
old_indices=[0,18,23,26,34,52,77,78]
excluded={71,44,53,67,9,13,35,50,54,61,66,58,48,7,29,12,59,20,51,57,79}
old_all=load(ROOT/'runs/b1-dev80-20261106-v1/INPUTS.json')
old_pool=[i for i in range(80) if i not in excluded and i not in old_indices]
old_coverage=sorted(old_pool,key=lambda i:hashlib.sha256(f'coreta-old-coverage-20261107|{i}'.encode()).hexdigest())[:36]
entries=[];targets={};review=[]
for i,z in enumerate(chosen):
  r=raw[z['id']];entries.append(dict(index=i,id=r['id'],task=sanitize(r),coverage=True,mechanism=False,cohort='fresh',origin='FRESH_TASK_AND_SUPPORT_PURGED_RESERVE',strict_training_answer_isolation=not reasons(z,g),shape=z['shape']))
  targets[r['id']]={k:r[k] for k in ('id','answer','answer_aliases','answerable')}
  targets[r['id']]['paragraphs']=r['paragraphs']
  review.append(dict(index=i,id=r['id'],question=r['question'],support_paragraphs=[p for p in r['paragraphs'] if p['is_supporting']],answer=r['answer'],input_tokens=z['input_tokens']))
for j,oi in enumerate(old_coverage+old_indices):
  t=load(ROOT/f'runs/b1-dev80-20261106-v1/trials/{oi:03d}.json');r=by[t['task']['id']];mechanism=oi in old_indices
  entries.append(dict(index=56+j,id=r['id'],task=t['task'],coverage=not mechanism,mechanism=mechanism,cohort='mechanism' if mechanism else 'old_coverage',origin='REUSED_D80_INPUT',old_index=oi,shape=r['shape']))
  scoring={x['id']:x for x in [json.loads(s) for s in (DATA/'scoring/D_development.jsonl').open()]}
  targets[r['id']]=scoring[r['id']]
  supporting={p['idx'] for p in targets[r['id']]['paragraphs'] if p['is_supporting']}
  review.append(dict(index=56+j,id=r['id'],old_index=oi,question=t['task']['question'],support_paragraphs=[p for p in t['task']['paragraphs'] if p['idx'] in supporting],answer=targets[r['id']]['answer'],input_tokens=r['input_tokens']))
# Deterministic dependency components within this batch, conservatively including answer strings.
parent=list(range(100));seen={}
def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
for i,e in enumerate(entries):
  r=by[e['id']];ks=keys(r)|{('a',x) for x in r['component_answer_hashes']}|{('a',r['final_answer_hash'])}
  for k in ks:
    if k in seen:parent[find(i)]=find(seen[k])
    else:seen[k]=i
groups={e['id']:f'g{find(i)}' for i,e in enumerate(entries)}
sources=[DATA/'corpus_index.jsonl',DATA/'split_assignments.jsonl',ROOT/'research/b1-independent-first-work-20261106/INPUTS.json',ROOT/'research/b1-independent-first-work-20261106/LABELS.json']
sources+=[DATA/'scoring/D_development.jsonl',ROOT/'runs/b1-dev80-20261106-v1/INPUTS.json',HERE/'QUALITY_DECISIONS.json',HERE/'CANDIDATES.json']
sources+=[ROOT/f'runs/b1-dev80-20261106-v1/trials/{i:03d}.json' for i in old_coverage+old_indices]
pack=dict(version='B1_GROUNDED_REVISION_100_V1',scope='56_FRESH_TASK_SUPPORT_DISJOINT_36_OLD_COVERAGE_8_OLD_MECHANISM',tasks=entries,groups=groups,unique_questions=100,fresh_questions=56,old_coverage_questions=36,mechanism_questions=8,repeats=[0],source_sha256={str(p):sha(p) for p in sources})
for name,obj in [('INPUTS.json',pack),('LABELS.json',dict(targets=targets)),('SELECTION_REVIEW.json',dict(scope='Fresh primary56 input-screened; old36 coverage and8 purposeful separately; training answer-string overlap stratified',reserve=len(reserve),eligible=len(available),fresh=56,old=44,prior_all_answer_purged_pool_size=47,selection_revision='Poor input bridges rejected before launch; T answer-only overlaps allowed as explicit development stratum, T content overlaps still forbidden; C/D/H full guards unchanged',old_known_input_exclusions=sorted(excluded),protected_roles=['T2000 question/component/support and gold-context; answer-only overlap flagged','C160/D80/H full frozen-key guards'],H_body_read=False,source_guards='Question/component IDs/standalone questions/support and gold-context both directions; answer strings protected for C/D/H, stratified for T',selected_support_review=review))]:
  (HERE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(selected=100,fresh=56,old_coverage=36,mechanism=8,strict_T_answers=sum(e.get('strict_training_answer_isolation',False) for e in entries),groups=len(set(groups.values())))),flush=True)
