"""Hash-only split verification; never reads H bodies, no model calls."""
import hashlib,json,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;DATA=ROOT/'data/external/musique-v1.0-20261030'
load=lambda p:json.loads(p.read_text());pack=load(ROOT/'runs/b1-grounded-revision-20261107-v1/INPUTS.json')
meta={r['id']:r for r in (json.loads(x) for x in (DATA/'corpus_index.jsonl').open())};roles={r['id']:r['role'] for r in (json.loads(x) for x in (DATA/'split_assignments.jsonl').open())}
digest=lambda t:hashlib.sha256(' '.join(unicodedata.normalize('NFKC',t).casefold().split()).encode()).hexdigest()
def keys(r,answers=True):
  z={('q',r['question_hash'])}|{('s',str(x)) for x in r['component_ids']}|{('p',x) for x in r['support_hashes']}|{('u',x) for x in r['standalone_component_question_hashes']}
  return z|({('a',x) for x in r['component_answer_hashes']}|{('a',r['final_answer_hash'])} if answers else set())
def guard(rs,answers=True):return dict(keys=set().union(*(keys(r,answers) for r in rs)),support={x for r in rs for x in r['support_hashes']},context={x for r in rs for x in r['context_hashes']})
def clear(r,g,answers=True):return not (keys(r,answers)&g['keys'] or set(r['support_hashes'])&g['context'] or set(r['context_hashes'])&g['support'])
others=guard([r for i,r in meta.items() if roles[i] in ('C_calibration','D_development','H_confirmation_candidate')]);train=[r for i,r in meta.items() if roles[i]=='T_optional_training'];tg=guard(train,False);tfull=guard(train,True)
strict=overlap=0
for e in pack['tasks']:
  r=meta[e['id']];assert digest(e['task']['question'])==r['question_hash']
  assert {digest(p['paragraph_text']) for p in e['task']['paragraphs']}==set(r['context_hashes'])
  if e['cohort']=='fresh':
    assert roles[e['id']]=='TRAIN_UNUSED_ELIGIBLE_RESERVE' and clear(r,others) and clear(r,tg,False)
    hit=clear(r,tfull);assert hit==e['strict_training_answer_isolation'];strict+=hit;overlap+=not hit
  else:assert roles[e['id']]=='D_development'
assert (strict,overlap)==(29,27)
qs=[digest(e['task']['question']) for e in pack['tasks']];assert len(set(qs))==100
out=dict(verdict='PASS_RECORDED_SPLIT_AND_CONTENT_GUARDS',fresh=56,old_coverage=36,mechanism=8,strict_T_answer=29,T_answer_only_overlap=27,fresh_groups=len({pack['groups'][e['id']] for e in pack['tasks'] if e['cohort']=='fresh'}),unique_question_texts=100,C_D_H_full_guards=True,T_question_component_support_and_gold_context_guards=True,H_bodies_read=False,new_model_calls=0,quality_scope='Metadata/content isolation only; not certification of all semantic referents or distractor ambiguity',reviewer='assistant',independence='none/provisional')
(HERE/'SELECTION_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out),flush=True)
