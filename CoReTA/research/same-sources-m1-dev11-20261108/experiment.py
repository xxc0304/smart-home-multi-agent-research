"""Conditional same-source M1-only comparison; no new teammate generation."""
import argparse, importlib.util, json, os, sys, time, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
SOURCE=HERE.parent/'name-protocol-dev11-20261108'
spec=importlib.util.spec_from_file_location('source_experiment',SOURCE/'experiment.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
load,write,append,sha=e.load,e.write,e.append,e.sha
ARM='S_same_sources_m1'

def inputs():
    cfg=load(HERE/'config.json');tasks=load(SOURCE/'tasks.json')
    original=ROOT/cfg['source_run'];rows=[json.loads(s) for s in (original/'responses.jsonl').read_text().splitlines()]
    assert load(original/'STATUS.json')['status']=='COMPLETED'
    index={e.key(r):r for r in rows};assert len(index)==len(rows)==1056
    return cfg,tasks,rows,index

def context(task,index):
    n=task['id'];initial=index[(n,'M1','initial','COMMON',0)]['text']
    selected={a:e.refs(index[(n,a,'facts','FACTS_SHARED',0)]['text'],e.visible(task,a)) for a in e.ACTORS}
    assert all(r['status']=='OK' for r in selected.values())
    public=e.public_facts(task,selected,{},False)
    own=[index[(n,'M1','facts','FACTS_SHARED',0)]['text']]
    return initial,own,public

def request(task,cfg,stage,rn,initial,own,public):
    # Identical E prompt and stage seeds, removing ONLY generated teammate work.
    req=e.request(task,'M1',stage,'E_facts',cfg,initial,own,public,rn)
    req['arm']=ARM
    return req

def reusable(req,index):
    old=index[(req['task_id'],'M1',req['stage'],'E_facts',req['round'])]
    return old if all(req[k]==old[k] for k in ['payload','cap','generation_seed']) else None

def frozen():
    cfg=load(HERE/'config.json');original=ROOT/cfg['source_run']
    paths=[HERE/n for n in ['experiment.py','launch.py','config.json','EXPERIMENT_REVIEW.md']]
    paths += [SOURCE/'experiment.py',SOURCE/'tasks.json',SOURCE/'labels.json']
    paths += [original/n for n in ['responses.jsonl','scores.json','STATUS.json','manifest.json']]
    paths += [ROOT/p for p in load(original/'manifest.json')['freeze']]
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}

def execute(cfg,tasks,index,backend,out):
    out.mkdir(parents=True,exist_ok=False)
    write(out/'manifest.json',{'config':cfg,'freeze':frozen(),'task_ids':[t['id'] for t in tasks],
          'maximum_new_calls':55,'maximum_new_output_tokens':23936,
          'interpretation':'Conditional M1-only reasoning given unchanged four-member fact-selection artifacts; not autonomous one-agent source selection or equal-total-compute comparison.'})
    for name in ['attempts.jsonl','responses.jsonl']:(out/name).touch()
    write(out/'PID.json',{'pid':os.getpid()})
    started=time.monotonic();count=0;reused=0;scores=[];consecutive=0;fatal=None
    def status(state,**extra):
        write(out/'STATUS.json',{'status':state,'logical_calls':count,'new_generation_calls':count-reused,
             'reused_exact_E_calls':reused,'maximum_new_calls':55,'complete_tasks':sum(s['complete'] for s in scores),
             'elapsed_seconds':time.monotonic()-started,**extra})
    status('STARTING')
    try:
        for task in tasks:
            initial,own,public=context(task,index);failed=False
            for stage,rn in [('work',r) for r in range(1,5)]+[('final',0)]:
                req=request(task,cfg,stage,rn,initial,own,public)
                old=reusable(req,index)
                attempt=dict(req,call=count,inherited=old is not None)
                append(out/'attempts.jsonl',attempt)
                if old is not None:
                    row=dict(old,**attempt,source_call=old['call']);reused+=1
                else:row=dict(backend.respond(req['payload'],req['cap'],req['generation_seed']),**attempt)
                row['answer']=e.answer(row['text'],task);row['answer_mode']=e.answer_mode(row['text'],task)
                append(out/'responses.jsonl',row);count+=1
                status('RUNNING',task_id=task['id'],stage=stage,round=rn)
                if row['status']!='OK' or not row['text'].strip():
                    failed=True;break
                if stage=='work':
                    own.append(row['text']);public.append(('M1',row['text']))
            if failed:
                scores.append({'task_id':task['id'],'complete':False,'reason':'INCOMPLETE_DEPENDENCY','answer':None,'correct':None})
            else:
                gold=load(SOURCE/'labels.json')[str(task['id'])]['correct']
                scores.append({'task_id':task['id'],'complete':True,'answer':row['answer'],
                     'correct':None if row['answer'] is None else row['answer']==gold})
            write(out/'scores.json',scores);write(out/f'task-{task["id"]}.json',scores[-1])
            consecutive=consecutive+1 if failed else 0
            if consecutive>=2:raise RuntimeError('two_consecutive_dependency_failures')
    except BaseException as exc:fatal={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    status('FAILED' if fatal else 'COMPLETED',failure=fatal,freeze_unchanged=frozen()==load(HERE/'FREEZE.json'))
    return load(out/'STATUS.json')

def preflight():
    import tempfile
    cfg,tasks,rows,index=inputs();original=ROOT/cfg['source_run']
    old_cfg=load(SOURCE/'config.json')
    for k in ['model_path','revision','dtype','quantization','device','max_length','template_kwargs','generation','seed','initial_tokens','work_tokens','final_tokens','adapter']:
        assert cfg[k]==old_cfg[k],k
    for rel,digest in load(original/'manifest.json')['freeze'].items():assert sha(ROOT/rel)==digest
    # All 1056 actual source requests reconstructed, not a source subset chosen by score.
    consumed=[]
    for t in tasks:consumed+=e.replay_task(t,old_cfg,index)
    assert len(consumed)==len(set(consumed))==1056
    sys.path.insert(0,str(ROOT/'tools'));from b0_training import load_tokenizer
    tok=load_tokenizer(cfg);maximum=0;exact=0
    for t in tasks:
        initial,own,public=context(t,index)
        rendered={k for a in public for k in e.re.findall(r'\[([SH]\d{2})\]',a[1])}
        selected={k for a in e.ACTORS for k in e.refs(index[(t['id'],a,'facts','FACTS_SHARED',0)]['text'],e.visible(t,a))['selected']}
        assert rendered==selected and set(t['hidden']).issubset(rendered)
        for stage,rn in [('work',r) for r in range(1,5)]+[('final',0)]:
            req=request(t,cfg,stage,rn,initial,own,public)
            assert req['payload']['system']==e.base.SYSTEM
            assert all(a=='M1' for a,s in public[4:])
            encoded=tok.apply_chat_template([{'role':k,'content':req['payload'][k]} for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
            e.backend_module.check_length(len(encoded),req['cap'],cfg['max_length']);maximum=max(maximum,len(encoded)+req['cap'])
            exact+=reusable(req,index) is not None
            old=index[(t['id'],'M1',stage,'E_facts',rn)]
            assert tok.decode(old['output_ids'],skip_special_tokens=True)==old['text']
            if stage=='work':own.append(old['text']);public.append(('M1',old['text']))
        # Cap-sized text stress is coverage, not arbitrary tokenizer worst-case proof.
        stress=[' word'*cfg['work_tokens']]*4
        req=request(t,cfg,'final',0,initial,[own[0]]+stress,public[:4]+[('M1',s) for s in stress])
        ids=tok.apply_chat_template([{'role':k,'content':req['payload'][k]} for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
        e.backend_module.check_length(len(ids),req['cap'],cfg['max_length']);maximum=max(maximum,len(ids)+req['cap'])
    t=tasks[0]
    assert e.answer('ANSWER: '+next(iter(t['options'])),t) is not None
    for bad in ['', 'null','ANSWER: nonexistent','ANSWER: X\nANSWER: Y']:
        assert e.answer(bad,t) is None
    try:e.backend_module.check_length(16384,1,16384)
    except ValueError:pass
    else:raise AssertionError('length_guard')
    tests=[]
    class Replay:
        def __init__(self,mode):self.mode=mode
        def respond(self,p,cap,seed):
            if self.mode=='system':raise RuntimeError('fixture_system')
            text=next(iter(t['options'])) if self.mode=='valid' else 'unknown'
            return {'text':text,'status':'OUTPUT_LIMIT' if self.mode=='limit' else 'OK','output_ids':[],
                    'input_tokens':1,'output_tokens':1,'elapsed_seconds':0,'ended_with_eos':self.mode!='limit','adapter_enabled':False}
    # Disable exact reuse only within synthetic-failure test via deliberately distinct seed.
    test_cfg=dict(cfg,seed=cfg['seed']+17)
    for mode in ['valid','unknown','limit','system']:
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'run';s=execute(test_cfg,tasks[:2],index,Replay(mode),out)
            if mode in ['valid','unknown']:
                assert s['status']=='COMPLETED' and s['logical_calls']==10
                if mode=='unknown':assert all(x['correct'] is None for x in load(out/'scores.json'))
            elif mode=='limit':assert s['status']=='FAILED' and s['logical_calls']==2
            else:assert s['status']=='FAILED' and s['logical_calls']==0
            tests.append({'test':mode,'result':'PASS'})
    with tempfile.TemporaryDirectory() as tmp:
        out=Path(tmp)/'reuse';s=execute(cfg,tasks,index,Replay('valid'),out)
        assert s['status']=='COMPLETED' and s['logical_calls']==55 and s['reused_exact_E_calls']>0
        saved=[json.loads(line) for line in (out/'responses.jsonl').read_text().splitlines()]
        for r in saved:
            if r['inherited']:
                old=index[(r['task_id'],'M1',r['stage'],'E_facts',r['round'])]
                assert all(r[k]==old[k] for k in ['text','output_ids','payload','cap','generation_seed'])
        tests.append({'test':'exact_request_reuse_execution','result':'PASS','reused_calls':s['reused_exact_E_calls']})
    result={'result':'PASS','source_requests_exactly_reconstructed':1056,'same_config':True,
            'source_freeze_unchanged':True,'historical_M1_trajectories_replayed':55,'max_replay_and_stress_plus_cap':maximum,
            'fault_tests':tests,'same_source_ids_all_tasks':True,'generated_teammate_messages_absent':True,
            'max_new_calls':55,'max_new_output_tokens':23936,'exact_source_prompt_matches_in_replayed_histories':exact,
            'limitations':'11 old development tasks, one seed, fact selection supplied by four-member source run; no equal-total-compute or autonomous solo claim'}
    write(HERE/'PREFLIGHT.json',dict(result,freeze=frozen()));print(json.dumps(result))

def audit():
    cfg,tasks,source,index=inputs();out=ROOT/cfg['run_dir']
    manifest=load(out/'manifest.json');assert manifest['freeze']==frozen()==load(HERE/'FREEZE.json')
    status=load(out/'STATUS.json')
    def lines(p):
        text=p.read_text();return [json.loads(s) for s in text[:text.rfind('\n')+1].splitlines() if s]
    rows=lines(out/'responses.jsonl');attempts=lines(out/'attempts.jsonl')
    sys.path.insert(0,str(ROOT/'tools'));from b0_training import load_tokenizer
    tok=load_tokenizer(cfg);largest=0;history={};reused=0
    for i,r in enumerate(rows):
        assert all(r[k]==v for k,v in attempts[i].items()) and r['call']==i
        t=next(t for t in tasks if t['id']==r['task_id'])
        initial,own,public=context(t,index)
        prior=history.get(t['id'],[])
        assert len(prior)<5
        assert (r['stage'],r['round'])==([('work',n) for n in range(1,5)]+[('final',0)])[len(prior)]
        for prev in prior:own.append(prev['text']);public.append(('M1',prev['text']))
        req=request(t,cfg,r['stage'],r['round'],initial,own,public)
        assert all(r[k]==v for k,v in req.items())
        if r['inherited']:
            old=reusable(req,index);assert old is not None and r['source_call']==old['call']
            assert all(r[k]==old[k] for k in ['text','output_ids','input_tokens','output_tokens','status','elapsed_seconds']);reused+=1
        ids=tok.apply_chat_template([{'role':k,'content':req['payload'][k]} for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
        assert len(ids)==r['input_tokens'];e.backend_module.check_length(len(ids),r['cap'],cfg['max_length'])
        largest=max(largest,len(ids)+r['cap'])
        assert tok.decode(r['output_ids'],skip_special_tokens=True)==r['text']
        assert len(r['output_ids'])==r['output_tokens']<=r['cap'] and r['adapter_enabled'] is False
        assert r['answer']==e.answer(r['text'],t)
        if r['status']=='OK':history.setdefault(t['id'],[]).append(r)
    scores=load(out/'scores.json') if (out/'scores.json').exists() else []
    for s in scores:
        if s['complete']:
            final=history[s['task_id']][-1];assert final['stage']=='final' and s['answer']==final['answer']
            gold=load(SOURCE/'labels.json')[str(s['task_id'])]['correct']
            assert s['correct']==(None if final['answer'] is None else final['answer']==gold)
    if status['status']=='COMPLETED':assert len(rows)==len(attempts)==status['logical_calls'] and len(scores)==11
    report={'result':'PASS','status':status['status'],'responses_checked':len(rows),'attempts_snapshot':len(attempts),
        'scores_checked':len(scores),'max_input_plus_cap':largest,'reused_exact_calls_verified':reused,
        'new_responses_checked':len(rows)-reused,'non_eos':sum(r['status']!='OK' for r in rows),
        'unknown_finals':sum(r['answer'] is None for r in rows if r['stage']=='final'),
        'freeze_unchanged':True,'all_payloads_seeds_histories_tokens_reconstructed':True}
    write(HERE/('COMPLETION_AUDIT.json' if status['status'] in ['COMPLETED','FAILED'] else 'START_VERIFICATION.json'),report)
    print(json.dumps(report))

def summarize():
    cfg,tasks,rows,index=inputs();out=ROOT/cfg['run_dir'];scores=load(out/'scores.json')
    old=load(ROOT/cfg['source_run']/'scores.json');comparison=[]
    for s in scores:
        n=s['task_id'];arms={r['arm']:r for r in old if r['task_id']==n}
        comparison.append({'task_id':n,'S_complete':s['complete'],'S_correct':s['correct'],'S_answer':s['answer'],
             'A_M1':arms['A_private']['expert_final_correct'],
             'B_team':arms['B_ordinary']['final_vote']['expected_accuracy'],
             'E_team':arms['E_facts']['final_vote']['expected_accuracy'],
             'E_M1':arms['E_facts']['expert_final_correct'],'F_team':arms['F_facts_opinions']['final_vote']['expected_accuracy']})
    valid=[s for s in comparison if s['S_complete'] and s['S_correct'] is not None]
    result={'status':load(out/'STATUS.json'),'n_planned':11,'n_comparable':len(valid),'per_task':comparison,
            'mean_on_same_readable_tasks':{k:sum(s[k] for s in valid)/len(valid) if valid else None for k in ['S_correct','A_M1','B_team','E_team','E_M1','F_team']},
            'E_team_minus_S_gains':[s['task_id'] for s in valid if s['E_team']>s['S_correct']],
            'E_team_minus_S_losses':[s['task_id'] for s in valid if s['E_team']<s['S_correct']],
            'limitations':'Conditional old dev single seed; no equivalence, mechanism identification, unseen generalization or efficiency claim.'}
    write(HERE/'SUMMARY.json',result);print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','preflight','run','audit','summarize']);a=p.parse_args()
    if a.mode=='freeze':write(HERE/'FREEZE.json',frozen())
    elif a.mode=='preflight':preflight()
    elif a.mode=='run':
        import fcntl
        cfg,tasks,rows,index=inputs();assert load(HERE/'FREEZE.json')==frozen()==load(HERE/'PREFLIGHT.json')['freeze']
        assert load(HERE/'PREFLIGHT.json')['result']=='PASS' and 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
        lock=(HERE/'launch.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        out=ROOT/cfg['run_dir'];assert not out.exists()
        # Persist startup failure; actual generation logs written response by response.
        try:backend=e.backend_module.Backend(cfg)
        except BaseException as exc:
            write(HERE/'STARTUP_FAILURE.json',{'type':type(exc).__name__,'message':str(exc)});raise
        print(json.dumps(execute(cfg,tasks,index,backend,out)))
    elif a.mode=='audit':audit()
    else:summarize()
