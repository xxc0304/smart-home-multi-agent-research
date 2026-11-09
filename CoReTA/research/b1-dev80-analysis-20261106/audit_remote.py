"""Offline audit of completed D80; no model initialization or generation."""
import hashlib, importlib.util, json, sys
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('dev80',ROOT/'engineering/b1-dev80-20261106/experiment.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=m.OUT
m.verify_freeze()
tasks,groups,targets=m.data(80,labels=True)
traces=[load(OUT/f'trials/{i:03d}.json') for i in range(80)]
for i,t in enumerate(traces):
    assert t['task']==tasks[i] and t['config']==m.trial_parameters(load(OUT/'config.json'),i)
    assert m.replay(t).export()==t
for i in range(8):assert traces[i]==load(m.PRIOR/f'batch2/trials/{i:03d}.json')
score=m.summarize(traces,targets,[t['id'] for t in tasks],groups)
score.update(primary_enabled=False,scope='D80_SEQUENTIAL_DEVELOPMENT_NOT_CONFIRMATORY')
assert score==load(OUT/'checkpoints/080/scores.json')
journal=[];attempts=[]
for start in range(8,80,4):
    cell=OUT/f'cells/{start:03d}'
    rows=m.lines(cell/'responses.jsonl');journal.extend(rows)
    ats=m.lines(cell/'ATTEMPTS.jsonl');attempts.extend(x for a in ats for x in a['requests'])
    for i in range(start,start+4):assert [r['record'] for r in rows if r['item_index']==i]==traces[i]['records']
assert len(attempts)==len({r[1] for r in attempts})==len(journal)==3655
assert {(i,rid) for i,rid in attempts}=={(r['item_index'],r['record']['request_id']) for r in journal}
assert all(r['generated'] for r in journal)
visibility=Counter();routes=Counter();terminations=Counter();tokens=Counter()
for t in traces:
    for q in t['records']:
        u=q['usage'];tokens[q['stage']]+=u.get('output_tokens',0)
        routes[str(u.get('adapter_enabled'))]+=1
        terminations[str(u.get('finish_reason',u.get('termination')) )]+=1
        assert q['source_kind']=='ACTUAL_LOCAL_MODEL_RESPONSE' and not q['fixture']
        raw=q['payload']['user'][len('TASK_DATA\n'):]
        suffix=t['config'].get('answer_suffix','')
        if suffix and raw.endswith(suffix):raw=raw[:-len(suffix)]
        d=json.loads(raw)
        assert d['paragraphs']==t['task']['paragraphs'] and d['question']==t['task']['question']
        assert 'answer' not in d and 'answer_aliases' not in d
        if q['stage']=='initial':
            assert 'history' not in d and 'team_information' not in d
            visibility['initial']+=1
        else:
            private=q['arm'] in ('A','C')
            assert d['work_visibility']==('private_work' if private else 'team_message')
            if private:assert all(x['sender']==q['actor'] for x in d['history'])
            assert bool(d.get('team_information'))==(q['arm'] in ('C','D'))
            visibility['private' if private else 'public']+=1
        assert q['max_new_tokens']==(1024 if q['stage']=='work' else 256)
        if q['status']=='OUTPUT_LIMIT':assert u['output_tokens']==q['max_new_tokens']

def subset(name,indices):
    chosen=[traces[i] for i in indices];ids=[t['task']['id'] for t in chosen]
    s=m.summarize(chosen,targets,ids,{k:groups[k] for k in ids})
    (HERE/f'{name}_SCORES.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
    return {k:v for k,v in s.items() if k!='reports'}
subsets={name:subset(name,ids) for name,ids in [('FIRST32',range(32)),('TAIL48',range(32,80)),('NEW72',range(8,80))]}
result=dict(verdict='PASS_RECORDS_REPLAY_SCORING_AND_VISIBILITY_NOT_COMPLETE_80',reviewer='assistant',independence='none/provisional',new_model_calls=0,freeze_verified=True,inherited_8_exact=True,all_80_replayed=True,official_final_scores_exact=True,attempts_and_returns=len(journal),all_records=sum(len(t['records']) for t in traces),status_counts=dict(Counter(q['status'] for t in traces for q in t['records'])),visibility=dict(visibility),output_tokens=dict(tokens),route_field_counts=dict(routes),termination_field_counts=dict(terminations),subsets=subsets)
(HERE/'POST_RUN_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='subsets'},ensure_ascii=False))
