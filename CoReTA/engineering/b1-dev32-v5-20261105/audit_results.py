"""Read-only post-run recomputation; writes only separate audit artifacts."""
import hashlib,json,os,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import load_json,development_data,trial_parameters
from b1_controls import replay,summarize
HERE=Path(__file__).resolve().parent
OUT=ROOT/'runs/b1-dev32-20261105-v5'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze=load_json(OUT/'FREEZE.json')
assert all(sha(p)==h for p,h in freeze['files'].items())
assert load_json(OUT/'APPROVAL.json')['freeze_sha256']==sha(OUT/'FREEZE.json')
tasks,groups,targets=development_data(32,targets=True)
original={str(p):sha(p) for p in OUT.rglob('*') if p.is_file()}
checks={};all_rows=[]
for n,prior in ((2,0),(8,2),(32,8)):
    d=OUT/f'stage{n}';m=load_json(d/'manifest.json');score=load_json(d/'scores.json')
    traces=[load_json(p) for p in sorted((d/'trials').glob('*.json'))]
    assert m['expected_ids']==[t['id'] for t in tasks[:n]]
    assert m['groups']=={t['id']:groups[t['id']] for t in tasks[:n]}
    for i,t in enumerate(traces):
        assert t['task']==tasks[i] and t['config']==trial_parameters(m['config'],i)
        assert replay(t).export()==t and t['complete'] and len(t['records'])==52
        if i<prior:assert (d/f'trials/{i:03d}.json').read_bytes()==(OUT/f'stage{prior}/trials/{i:03d}.json').read_bytes()
    recomputed=summarize(traces,targets,m['expected_ids'],m['groups'])
    assert recomputed==score,'scores_changed_on_recompute'
    rows=[json.loads(s) for s in (d/'responses.jsonl').read_text().splitlines()]
    assert len(rows)==52*n
    for i,t in enumerate(traces):
        journal=[{k:v for k,v in r.items() if k not in ('item_index','inherited')} for r in rows if r['item_index']==i]
        assert journal==t['records']
    new=[r for r in rows if not r.get('inherited',False)]
    assert len(new)==52*(n-prior)==load_json(d/'execution.json')['new_backend_requests']
    all_rows+=new
    checks[n]=dict(trace_count=len(traces),score_exact_match=True,prefix_byte_match=True,new_calls=len(new))
assert len(all_rows)==1664 and len({r['request_id'] for r in all_rows})==1664
assert all(r['status']=='OK' and r['usage']['finish_reason']=='EOS' for r in all_rows)
assert all(r['usage']['adapter_enabled']==(r['actor']=='M1') for r in all_rows)
assert all(r['source_kind']=='ACTUAL_LOCAL_MODEL_RESPONSE' and not r['fixture'] for r in all_rows)
s=load_json(OUT/'stage32/scores.json');traces=[load_json(p) for p in sorted((OUT/'stage32/trials').glob('*.json'))]
warnings=[dict(item=r['item_index'],actor=r['actor'],stage=r['stage'],arm=r['arm'],reason=r['usage']['format_warning'],raw=r['raw_output']) for r in all_rows if r['usage'].get('format_warning')]
by_phase={p:dict(n=sum(r['stage']==p for r in all_rows),input_tokens=sum(r['usage']['input_tokens'] for r in all_rows if r['stage']==p),output_tokens=sum(r['usage']['output_tokens'] for r in all_rows if r['stage']==p),generation_seconds=sum(r['usage']['elapsed_seconds'] for r in all_rows if r['stage']==p)) for p in ('initial','work','final')}
homogeneity={}
for label,get_answers in [('initial',lambda t:t['initials'])]+[(a,lambda t,a=a:t['finals'][a]) for a in 'ABCD']:
    answers=[get_answers(t) for t in traces]
    homogeneity[label]=dict(raw_identical_ordinary=sum(len({x[a] for a in ('M2','M3','M4')})==1 for x in answers),ordinary_all_unknown=sum(all(x[a].strip().lower()=='unknown' for a in ('M2','M3','M4')) for x in answers))
events=[]
for i,(t,r) in enumerate(zip(traces,s['reports'])):
    for a,v in r['arms'].items():
        if v['expert_harm'] or v['expert_correction'] or v['expert_correct_but_not_selected_actual']:
            events.append(dict(index=i,id=r['id'],arm=a,question=t['task']['question'],expert_initial=r['initial']['members']['M1'],expert_final=v['members']['M1'],harm_EM=v['expert_harm'],correction_EM=v['expert_correction'],readout_loss_actual=v['expert_correct_but_not_selected_actual'],team_expected_em=v['expected_em'],vote=v['vote'],all_finals=t['finals'][a],expert_work=[w['text'] for w in t['work'][a] if w['sender']=='M1']))
assert all(sha(p)==h for p,h in original.items()),'original_run_mutated'
audit=dict(verdict='PASS',reviewer='assistant',independence='none/provisional',scope='DEVELOPMENT_NOT_INDEPENDENT_CONFIRMATION',stage_checks=checks,freeze_hashes_all_match=True,approval_bound=True,all_original_run_files_unchanged=True,unique_actual_calls=len(all_rows),eos_calls=1664,adapter_route_flags_match=True,by_phase=by_phase,format_warnings=warnings,unknown_by_phase=dict(Counter(r['stage'] for r in all_rows if r['raw_output'].strip().lower()=='unknown')),homogeneity=homogeneity,initial_member_em={a:sum(r['initial']['members'][a]['em'] for r in s['reports']) for a in ('M1','M2','M3','M4')},summary={k:v for k,v in s.items() if k!='reports'})
(HERE/'POST_RUN_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
(HERE/'EVENT_LEDGER.json').write_text(json.dumps(events,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(verdict='PASS',calls=1664,format_warnings=len(warnings),unknown=audit['unknown_by_phase'],homogeneity=homogeneity,events=len(events),initial_member_em=audit['initial_member_em'],by_phase=by_phase),ensure_ascii=False))
print(json.dumps([dict(index=e['index'],arm=e['arm'],harm=e['harm_EM'],correction=e['correction_EM'],before=e['expert_initial']['answer'],after=e['expert_final']['answer']) for e in events if e['harm_EM'] or e['correction_EM']],ensure_ascii=False))
