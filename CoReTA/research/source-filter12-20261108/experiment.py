"""Matched post-exchange source filtering; NOT a faithful IMP reproduction."""
import argparse, importlib.util, json, os, re, sys, tempfile, time, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('reference32',HERE.parent/'sources-expansion32-20261108/experiment.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
e=b.e;load,write,append,sha=b.load,b.write,b.append,b.sha
OLD=ROOT/'runs/sources-expansion32-20261108-v1'
ARM='R_post_exchange_source_filter'

def freeze():
    files=[HERE/n for n in ['experiment.py','launch.py','config.json','tasks.json','SELECTION.json','DESIGN.md','EXPERIMENT_REVIEW.md']]
    files += [OLD/n for n in ['responses.jsonl','scores.json','manifest.json']]
    files += [ROOT/p for p in load(OLD/'manifest.json')['freeze']]
    return {str(p.relative_to(ROOT)):sha(p) for p in files}

def source_rows():
    rows=[json.loads(s) for s in (OLD/'responses.jsonl').read_text().splitlines()]
    return {(r['task_id'],r['unit_seed'],r['actor'],r['stage'],r['arm'],r['round']):r for r in rows}

def exact(r,old):
    assert all(r[k]==old[k] for k in ['payload','generation_seed','cap']),('request_mismatch',r['task_id'],r['actor'],r['stage'],r['round'])
    assert old['status']=='OK' and old['text'].strip()

def make_request(t,uc,a,stage,initial,own,public,rn):
    r=b.req(t,uc,a,stage,'E_facts',initial,own,public,rn)
    r['arm']=ARM;return r

def inbox(t,a,cumulative):
    # Fixed ORIGINAL holdings, never augmented by received statements.
    ids=sorted(set().union(*(v for k,v in cumulative.items() if k!=a))-set(e.visible(t,a)))
    cat={**t['shared'],**t['hidden']}
    assert set(ids)<=set(cat)
    return ids,([] if not ids else [('ROUTER','Selected original statements:\n'+'\n'.join('['+k+'] '+cat[k] for k in ids))])

class Dependency(Exception):pass

def execute(cfg,tasks,backend,out,index=None):
    index=source_rows() if index is None else index
    out.mkdir(parents=True,exist_ok=False)
    write(out/'manifest.json',{'config':cfg,'freeze':freeze(),'purpose':'PURPOSEFULLY_SELECTED_DEVELOPMENT_DIAGNOSTIC','maximum_new_calls':len(tasks)*len(cfg['seeds'])*15})
    for n in ['attempts.jsonl','responses.jsonl']:(out/n).touch()
    write(out/'PID.json',{'pid':os.getpid()});start=time.monotonic();count=0;new=0;scores=[];fatal=None
    labels=load(HERE.parent/'sources-expansion32-20261108/labels.json')
    def state(status,**kw):
        write(out/'STATUS.json',dict(status=status,calls=count,new_generation_calls=new,reused_m1_calls=count-new,complete_units=sum(s['complete'] for s in scores),expected_units=len(tasks)*len(cfg['seeds']),elapsed_seconds=time.monotonic()-start,**kw))
    state('STARTING')
    try:
        for t in tasks:
            for seed in cfg['seeds']:
                uc=dict(cfg,seed=seed)
                def old(a,stage,arm,rn=0):return index[(t['id'],seed,a,stage,arm,rn)]
                first,orders=e.order(t,uc)
                initial={a:old(a,'initial','COMMON')['text'] for a in e.ACTORS}
                prep={a:old(a,'facts','FACTS_SHARED') for a in e.ACTORS}
                selected={a:e.refs(prep[a]['text'],e.visible(t,a)) for a in e.ACTORS}
                assert all(x['status']=='OK' for x in selected.values())
                public0=e.public_facts(t,selected,{},False)
                own={a:[prep[a]['text']] for a in e.ACTORS};history={a:[] for a in e.ACTORS}
                cumulative={a:set(selected[a]['selected']) for a in e.ACTORS}
                def call(a,stage,rn=0):
                    nonlocal count,new
                    ids,routed=inbox(t,a,cumulative)
                    public=public0+[(a,text) for text in history[a]]+routed
                    r=make_request(t,uc,a,stage,initial[a],own[a],public,rn)
                    cached=old(a,stage,'S_same_sources_m1',rn) if a=='M1' else None
                    if cached:exact(r,cached)
                    attempt=dict(r,call=count,reused=cached is not None,source_call=cached['call'] if cached else None,routed_ids=ids)
                    append(out/'attempts.jsonl',attempt)
                    result=cached if cached else backend.respond(r['payload'],r['cap'],r['generation_seed'])
                    row=dict(result,**attempt);row['answer']=e.answer(row['text'],t)
                    append(out/'responses.jsonl',row);count+=1;new+=int(cached is None)
                    state('RUNNING',task_id=t['id'],unit_seed=seed,actor=a,stage=stage,round=rn)
                    if row['status']!='OK' or not row['text'].strip():raise Dependency('INCOMPLETE_GENERATION')
                    return row
                try:
                    for rn,turns in enumerate(orders,1):
                        round_rows=[]
                        for a in turns:
                            row=call(a,'work',rn);own[a].append(row['text']);history[a].append(row['text']);round_rows.append(row)
                        # Synchronous cumulative reference update, preserving matched turn order.
                        for row in round_rows:
                            a=row['actor'];cumulative[a].update(set(re.findall(r'\b[SH]\d{2}\b',row['text']))&set(e.visible(t,a)))
                    finals=[call(a,'final') for a in e.ACTORS]
                    ans=[r['answer'] for r in finals];gold=labels[str(t['id'])]['correct']
                    s=dict(task_id=t['id'],unit_seed=seed,arm=ARM,complete=True,final_answers=dict(zip(e.ACTORS,ans)),score=(e.expected_vote(ans,gold) or {}).get('expected_accuracy'),M1_correct=None if ans[0] is None else ans[0]==gold)
                except Dependency as exc:s=dict(task_id=t['id'],unit_seed=seed,arm=ARM,complete=False,reason=str(exc))
                scores.append(s);write(out/'scores.json',scores)
    except BaseException as exc:fatal=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    state('FAILED' if fatal else 'COMPLETED',failure=fatal,freeze_unchanged=freeze()==load(HERE/'FREEZE.json'))
    return load(out/'STATUS.json')

def preflight():
    cfg=load(HERE/'config.json');tasks=load(HERE/'tasks.json');idx=source_rows()
    assert [t['id'] for t in tasks]==load(HERE/'SELECTION.json')['ids']
    assert len(tasks)==12 and len(cfg['seeds'])==2
    old_cfg=load(HERE.parent/'sources-expansion32-20261108/config.json')
    for k in ['seeds','model_path','revision','dtype','quantization','device','max_length','template_kwargs','generation','initial_tokens','work_tokens','final_tokens','adapter']:assert cfg[k]==old_cfg[k]
    for p,h in load(OLD/'manifest.json')['freeze'].items():assert sha(ROOT/p)==h
    sys.path.insert(0,str(ROOT/'tools'));from b0_training import load_tokenizer
    tok=load_tokenizer(cfg);maximum=0;prefix=0;stress=0
    for t in tasks:
        for seed in cfg['seeds']:
            uc=dict(cfg,seed=seed)
            for a in e.ACTORS:
                initial=idx[(t['id'],seed,a,'initial','COMMON',0)]
                exact(b.req(t,uc,a,'initial','COMMON'),initial);prefix+=1
                prep=idx[(t['id'],seed,a,'facts','FACTS_SHARED',0)]
                exact(b.req(t,uc,a,'facts','FACTS_SHARED',initial['text']),prep);prefix+=1
                assert e.refs(prep['text'],e.visible(t,a))==prep['references']
                selected={k:e.refs(idx[(t['id'],seed,k,'facts','FACTS_SHARED',0)]['text'],e.visible(t,k)) for k in e.ACTORS}
                fake_history=[' word'*cfg['work_tokens']]*4
                c={k:set(e.visible(t,k)) for k in e.ACTORS}
                public=e.public_facts(t,selected,{},False)+[(a,text) for text in fake_history]+inbox(t,a,c)[1]
                r=make_request(t,uc,a,'final',initial['text'],[prep['text']]+fake_history,public,0)
                ids=tok.apply_chat_template([{'role':k,'content':r['payload'][k]} for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
                e.backend_module.check_length(len(ids),r['cap'],cfg['max_length']);stress=max(stress,len(ids)+r['cap'])
    class Replay:
        def __init__(self,mode='real'):self.mode=mode;self.n=0
        def respond(self,p,cap,seed):
            self.n+=1
            if self.mode=='system':raise RuntimeError('fixture_system_failure')
            # Full REAL historical work/finals, used as substitute outputs for routing replay.
            t=next(t for t in tasks if t['description'] in p['user'])
            candidates=[r for r in idx.values() if r['task_id']==t['id'] and r['generation_seed']==seed and r['cap']==cap and r['arm']=='E_facts']
            assert len(candidates)==1
            r=dict(candidates[0])
            if self.mode=='unknown':r['text']='UNREADABLE'
            if self.mode=='limit' and self.n==1:r['status']='OUTPUT_LIMIT'
            if self.mode=='empty' and self.n==1:r['text']=''
            return r
    tests=[]
    for mode in ['real','unknown','limit','empty','system']:
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'replay';st=execute(cfg,tasks if mode=='real' else tasks[:1],Replay(mode),out)
            rows=[json.loads(s) for s in (out/'responses.jsonl').read_text().splitlines()]
            if mode=='real':
                assert st['status']=='COMPLETED' and st['calls']==480 and st['reused_m1_calls']==120 and st['new_generation_calls']==360
                for r in rows:
                    ids=tok.apply_chat_template([{'role':k,'content':r['payload'][k]} for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
                    e.backend_module.check_length(len(ids),r['cap'],cfg['max_length']);maximum=max(maximum,len(ids)+r['cap'])
                    assert not(set(r['routed_ids'])&set(e.visible(next(t for t in tasks if t['id']==r['task_id']),r['actor'])))
            elif mode=='system':assert st['status']=='FAILED'
            else:
                ss=load(out/'scores.json');assert st['status']=='COMPLETED' and len(ss)==2
                if mode=='unknown':assert all(s['complete'] and s['score'] is None for s in ss)
                else:assert [s['complete'] for s in ss]==[False,True]
            tests.append(dict(mode=mode,result='PASS'))
    # Explicit legal routing checks: duplicate tags dedup; original F fixed; illegal IDs never routed.
    t=tasks[0];c={a:set(e.visible(t,a)) for a in e.ACTORS}
    assert inbox(t,'M1',c)==([],[])
    x=inbox(t,'M2',c)[0];assert len(x)==len(set(x)) and x
    assert inbox(t,'M2',c)[0]==x # not removed merely because received last round
    bad=dict(idx);key=next(k for k in bad if k[0]==tasks[0]['id'] and k[4]=='S_same_sources_m1')
    bad[key]=dict(bad[key],cap=bad[key]['cap']+1)
    with tempfile.TemporaryDirectory() as tmp:
        st=execute(cfg,tasks[:1],Replay(),Path(tmp)/'mismatch',bad);assert st['status']=='FAILED' and 'request_mismatch' in st['failure']['message']
    tests.append(dict(mode='cache_mismatch',result='PASS'))
    result=dict(result='PASS',full_real_response_replay_slots=480,shared_prefix_requests_reconstructed=prefix,exact_m1_reuse_requests=120,maximum_new_calls=360,max_replay_input_plus_cap=maximum,max_synthetic_near_cap_history_plus_cap=stress,tests=tests,freeze=freeze())
    write(HERE/'PREFLIGHT.json',result);print(json.dumps({k:v for k,v in result.items() if k!='freeze'}))

def audit():
    cfg=load(HERE/'config.json');out=ROOT/cfg['run_dir'];idx=source_rows();rows=[json.loads(s) for s in (out/'responses.jsonl').read_text().splitlines() if s]
    assert freeze()==load(HERE/'FREEZE.json')==load(out/'manifest.json')['freeze']
    cursor=0
    class Recorded:
        def respond(self,p,cap,seed):
            nonlocal cursor
            while cursor<len(rows) and rows[cursor]['reused']:cursor+=1
            if cursor==len(rows):raise EOFError('AUDIT_PREFIX_END')
            row=rows[cursor];assert (p,cap,seed)==(row['payload'],row['cap'],row['generation_seed']);cursor+=1;return row
    with tempfile.TemporaryDirectory() as tmp:
        dest=Path(tmp)/'replay';replay_state=execute(cfg,load(HERE/'tasks.json'),Recorded(),dest)
        replay=[json.loads(s) for s in (dest/'responses.jsonl').read_text().splitlines()]
        for a,r in zip(rows,replay):
            for k in ['payload','cap','generation_seed','text','answer','routed_ids','actor','stage','round','task_id','unit_seed','reused']:assert a[k]==r[k],(a['call'],k)
        assert len(replay)>=len(rows)
        if load(out/'STATUS.json')['status']=='COMPLETED':
            assert replay_state['status']=='COMPLETED'
            assert len(rows)==len(replay)
            assert load(out/'scores.json')==load(dest/'scores.json')
    sys.path.insert(0,str(ROOT/'tools'));from b0_training import load_tokenizer
    tok=load_tokenizer(cfg);maximum=0
    attempts=[json.loads(s) for s in (out/'attempts.jsonl').read_text().splitlines()]
    for i,r in enumerate(rows):
        assert r['call']==i and all(r[k]==v for k,v in attempts[i].items())
        ids=tok.apply_chat_template([{'role':k,'content':r['payload'][k]} for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
        assert len(ids)==r['input_tokens'];e.backend_module.check_length(len(ids),r['cap'],cfg['max_length']);maximum=max(maximum,len(ids)+r['cap'])
        assert len(r['output_ids'])==r['output_tokens']<=r['cap'] and tok.decode(r['output_ids'],skip_special_tokens=True)==r['text']
    result=dict(result='PASS',responses_checked=len(rows),scores_replayed=True,full_payloads_histories_seeds_caps_reconstructed=True,max_input_plus_cap=maximum,unknown_finals=sum(r['stage']=='final' and r['answer'] is None for r in rows),non_eos=sum(r['status']!='OK' for r in rows),freeze_unchanged=True)
    write(HERE/'RUN_AUDIT.json',result);print(json.dumps(result))

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='freeze':write(HERE/'FREEZE.json',freeze())
    elif mode=='preflight':preflight()
    elif mode=='audit':audit()
    elif mode=='run':
        import fcntl
        assert freeze()==load(HERE/'FREEZE.json')==load(HERE/'PREFLIGHT.json')['freeze']
        assert load(HERE/'PREFLIGHT.json')['result']=='PASS' and 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
        lock=(HERE/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        cfg=load(HERE/'config.json');assert not (ROOT/cfg['run_dir']).exists()
        try:backend=e.backend_module.Backend(cfg)
        except BaseException as exc:
            write(HERE/'STARTUP_FAILURE.json',dict(type=type(exc).__name__,message=str(exc)));raise
        result=execute(cfg,load(HERE/'tasks.json'),backend,ROOT/cfg['run_dir']);print(json.dumps(result))
        if result['status']=='FAILED':raise SystemExit(1)
