"""Prespecified B/E/S development expansion, 32 source tasks by two seeds."""
import argparse, importlib.util, json, os, sys, tempfile, time, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('reference_protocol',HERE.parent/'name-protocol-dev11-20261108/experiment.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
load,write,append,sha=e.load,e.write,e.append,e.sha
ARMS=['B_ordinary','E_facts','S_same_sources_m1']

def freeze():
    paths=[HERE/n for n in ['experiment.py','inventory.py','prepare.cjs','launch.py','config.json','tasks.json','labels.json','SELECTION.json','CONTENT_REVIEW.md','EXPERIMENT_REVIEW.md','REMOTE_EXPOSURE_AUDIT.json']]
    paths.append(HERE.parent/'name-protocol-dev11-20261108/benchmark.json')
    old=ROOT/'runs/name-protocol-dev11-20261108-v1'
    paths += [old/n for n in ['responses.jsonl','manifest.json']]
    paths += [ROOT/p for p in load(old/'manifest.json')['freeze']]
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}

def req(t,cfg,actor,stage,arm,initial='',own=None,public=None,rn=0):
    r=e.request(t,actor,stage,'E_facts' if arm=='S_same_sources_m1' else arm,cfg,initial,own,public,rn)
    r.update(arm=arm,unit_seed=cfg['seed']);return r

def execute(cfg,tasks,labels,backend,out):
    out.mkdir(parents=True,exist_ok=False)
    write(out/'manifest.json',{'config':cfg,'freeze':freeze(),'task_ids':[t['id'] for t in tasks],
          'max_logical_calls':len(tasks)*len(cfg['seeds'])*57,'max_output_tokens':len(tasks)*len(cfg['seeds'])*27776,
          'purpose':'NEW_TO_AVAILABLE_LOCAL_QWEN_LOGS_DEVELOPMENT_EXPANSION_NOT_SECRET_HOLDOUT'})
    for n in ['attempts.jsonl','responses.jsonl']:(out/n).touch()
    write(out/'PID.json',{'pid':os.getpid()});started=time.monotonic();count=0;reused=0;scores=[];fatal=None;cache={}
    def status(state,**extra):
        write(out/'STATUS.json',{'status':state,'calls':count,'new_generation_calls':count-reused,'shared_exact_calls':reused,
            'max_logical_calls':len(tasks)*len(cfg['seeds'])*57,'complete_arms':sum(s['complete'] for s in scores),
            'processed_units':len({(s['task_id'],s['unit_seed']) for s in scores}),
            'elapsed_seconds':time.monotonic()-started,**extra})
    status('STARTING')
    def call(t,uc,a,stage,arm,initial='',own=None,public=None,rn=0):
        nonlocal count,reused
        r=req(t,uc,a,stage,arm,initial,own,public,rn)
        old=cache.get((stage,rn)) if arm=='S_same_sources_m1' else None
        if old and not all(r[k]==old[k] for k in ['payload','generation_seed','cap']):old=None
        attempt=dict(r,call=count,shared_within_run=old is not None);append(out/'attempts.jsonl',attempt)
        if old:
            row=dict(old,**attempt,source_call=old['call']);reused+=1
        else:row=dict(backend.respond(r['payload'],r['cap'],r['generation_seed']),**attempt)
        row['answer']=None if stage=='facts' else e.answer(row['text'],t)
        if stage=='facts':row['references']=e.refs(row['text'],e.visible(t,a))
        append(out/'responses.jsonl',row);count+=1
        if arm=='E_facts' and a=='M1':cache[(stage,rn)]=row
        status('RUNNING',task_id=t['id'],unit_seed=uc['seed'],arm=arm,stage=stage,round=rn)
        if row['status']!='OK' or not row['text'].strip():raise Dependency('incomplete_generation')
        return row
    try:
        for t in tasks:
            for seed in cfg['seeds']:
                uc=dict(cfg,seed=seed);cache={};first,orders=e.order(t,uc);initial={};prep={};selected={};pre_failed={}
                try:
                    for a in first:initial[a]=call(t,uc,a,'initial','COMMON')
                except Dependency as exc:
                    scores.extend({'task_id':t['id'],'unit_seed':seed,'arm':arm,'complete':False,'reason':'COMMON_INITIAL_'+str(exc)} for arm in ARMS)
                    write(out/'scores.json',scores);continue
                texts={a:initial[a]['text'] for a in e.ACTORS}
                for parent in ['B_ordinary','FACTS_SHARED']:
                    prep[parent]={}
                    try:
                        for a in first:
                            row=call(t,uc,a,'facts' if parent=='FACTS_SHARED' else 'exchange',parent,texts[a]);prep[parent][a]=row
                            if parent=='FACTS_SHARED':
                                if row['references']['status']!='OK':raise Dependency('invalid_source_selection')
                                selected[a]=row['references']
                    except Dependency as exc:pre_failed[parent]=str(exc)
                for arm in ARMS:
                    parent='B_ordinary' if arm=='B_ordinary' else 'FACTS_SHARED'
                    try:
                        if parent in pre_failed:raise Dependency(pre_failed[parent])
                        actors=['M1'] if arm=='S_same_sources_m1' else e.ACTORS
                        own={a:[prep[parent][a]['text']] for a in actors}
                        public=[(a,prep[parent][a]['text']) for a in first] if arm=='B_ordinary' else e.public_facts(t,selected,{},False)
                        for rn,turns in enumerate(orders,1):
                            for a in (['M1'] if arm=='S_same_sources_m1' else turns):
                                row=call(t,uc,a,'work',arm,texts[a],own[a],public,rn)
                                own[a].append(row['text']);public.append((a,row['text']))
                        finals=[call(t,uc,a,'final',arm,texts[a],own[a],public) for a in actors]
                        gold=labels[str(t['id'])]['correct'];ans=[r['answer'] for r in finals]
                        value=(None if ans[0] is None else float(ans[0]==gold)) if len(actors)==1 else (e.expected_vote(ans,gold) or {}).get('expected_accuracy')
                        s={'task_id':t['id'],'unit_seed':seed,'arm':arm,'complete':True,'final_answers':dict(zip(actors,ans)),
                             'initial_answers':{a:initial[a]['answer'] for a in e.ACTORS},'score':value,
                             'M1_correct':None if ans[0] is None else ans[0]==gold}
                        if arm!='B_ordinary':s['selected_hidden_ids']=sorted({k for r in selected.values() for k in r['selected'] if k.startswith('H')})
                    except Dependency as exc:s={'task_id':t['id'],'unit_seed':seed,'arm':arm,'complete':False,'reason':str(exc)}
                    scores.append(s);write(out/'scores.json',scores)
                write(out/f'task-{t["id"]}-seed-{seed}.json',[s for s in scores if s['task_id']==t['id'] and s['unit_seed']==seed])
    except BaseException as exc:fatal={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    status('FAILED' if fatal else 'COMPLETED',failure=fatal,freeze_unchanged=freeze()==load(HERE/'FREEZE.json'))
    return load(out/'STATUS.json')

class Dependency(Exception):pass

def preflight():
    cfg=load(HERE/'config.json');tasks=load(HERE/'tasks.json');labels=load(HERE/'labels.json')
    sel=load(HERE/'SELECTION.json');audit=load(HERE/'REMOTE_EXPOSURE_AUDIT.json')
    assert len(tasks)==32 and len(cfg['seeds'])==2 and len(set(cfg['seeds']))==2
    assert [t['id'] for t in tasks]==sel['selected_ids']
    assert not set(sel['selected_ids'])&set(audit['matched_ids'])
    assert not set(sel['selected_ids'])&set(sel['prior_content_exposure_ids'])
    old_cfg=load(HERE.parent/'name-protocol-dev11-20261108/config.json')
    for k in ['model_path','revision','dtype','quantization','max_length','template_kwargs','generation','initial_tokens','work_tokens','final_tokens','adapter']:assert cfg[k]==old_cfg[k]
    old_run=ROOT/'runs/name-protocol-dev11-20261108-v1';old_rows=[json.loads(s) for s in (old_run/'responses.jsonl').read_text().splitlines()]
    idx={e.key(r):r for r in old_rows};used=[]
    for t in load(HERE.parent/'name-protocol-dev11-20261108/tasks.json'):used+=e.replay_task(t,old_cfg,idx)
    assert len(used)==len(set(used))==1056
    for p,d in load(old_run/'manifest.json')['freeze'].items():assert sha(ROOT/p)==d
    sys.path.insert(0,str(ROOT/'tools'));from b0_training import load_tokenizer
    tok=load_tokenizer(cfg);longest=sorted([r for r in old_rows if r['stage']=='work'],key=lambda r:r['output_tokens'],reverse=True)[:16];maximum=0
    for t in tasks:
        assert set(t)=={'id','name','description','shared','hidden','options'}
        assert len(t['hidden']) in [3,4] and labels[str(t['id'])]['correct'] in t['options']
        selected={a:e.refs(','.join(e.visible(t,a)),e.visible(t,a)) for a in e.ACTORS}
        facts=e.public_facts(t,selected,{},False)
        for seed in cfg['seeds']:
            uc=dict(cfg,seed=seed);first,orders=e.order(t,uc)
            for arm in ARMS:
                actors=['M1'] if arm=='S_same_sources_m1' else e.ACTORS
                for a in actors:
                    public=(facts+[(e.ACTORS[i%4],r['text']) for i,r in enumerate(longest)]) if arm!='S_same_sources_m1' else facts+[('M1',r['text']) for r in longest[:4]]
                    own=[','.join(e.visible(t,a))]+[r['text'] for r in longest[:4]]
                    for stage,rn in [('work',4),('final',0)]:
                        r=req(t,uc,a,stage,arm,old_rows[0]['text'],own,public,rn)
                        ids=tok.apply_chat_template([{'role':k,'content':r['payload'][k]} for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
                        e.backend_module.check_length(len(ids),r['cap'],cfg['max_length']);maximum=max(maximum,len(ids)+r['cap'])
                    if arm=='S_same_sources_m1':assert all(a=='M1' for a,s in public[4:])
            # Fixed near-cap history stress, not arbitrary-token upper-bound guarantee.
            public=facts+[(e.ACTORS[i%4],' word'*cfg['work_tokens']) for i in range(16)]
            r=req(t,uc,'M1','work','E_facts','INITIAL_MARKER',[' word'*512]*4,public,4)
            ids=tok.apply_chat_template([{'role':k,'content':r['payload'][k]} for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
            e.backend_module.check_length(len(ids),r['cap'],cfg['max_length']);maximum=max(maximum,len(ids)+r['cap'])
    reuse_task=next(t for t in tasks[1:] if any(e.order(t,dict(cfg,seed=s))[1][0][0]=='M1' for s in cfg['seeds']))
    tests=[];test_tasks=[tasks[0],reuse_task];test_cfg=dict(cfg,fixture=True)
    class Fake:
        def __init__(self,mode):self.mode=mode;self.once=False
        def respond(self,p,cap,seed):
            if self.mode=='system':raise RuntimeError('fixture_system_failure')
            t=next(t for t in test_tasks if t['description'] in p['user'])
            if 'Before discussion, select' in p['user']:text=','.join(e.re.findall(r'\[([SH]\d{2})\]',p['user']));stage='facts'
            else:text='ANSWER: '+next(iter(t['options']));stage='initial' if 'Answer independently before' in p['user'] else 'exchange' if 'Prepare your first message' in p['user'] else 'final' if 'Output ONLY one exact full choice' in p['user'] else 'work'
            status='OK'
            if self.mode=='unknown':text='unreadable'
            if self.mode=='badfacts' and stage=='facts':text='H99'
            if self.mode=='initial_limit' and stage=='initial':status='OUTPUT_LIMIT'
            if self.mode=='empty_initial' and stage=='initial':text=''
            if self.mode=='branch_limit' and stage=='work' and not self.once:status='OUTPUT_LIMIT';self.once=True
            if self.mode=='E_limit' and stage=='work' and 'Selected original statements:' in p['user'] and not self.once:status='OUTPUT_LIMIT';self.once=True
            return {'text':text,'status':status,'output_ids':[],'output_tokens':1,'input_tokens':1,'elapsed_seconds':0,'adapter_enabled':False,'ended_with_eos':status=='OK'}
    for mode in ['valid','unknown','badfacts','initial_limit','empty_initial','branch_limit','E_limit','system']:
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'fixture';state=execute(test_cfg,test_tasks,labels,Fake(mode),out)
            scores=load(out/'scores.json') if (out/'scores.json').exists() else []
            if mode=='system':assert state['status']=='FAILED' and state['calls']==0
            else:
                assert state['status']=='COMPLETED' and len(scores)==12
                if mode=='valid':assert all(s['complete'] for s in scores) and state['calls']==228 and state['shared_exact_calls']>0
                if mode in ['initial_limit','empty_initial']:assert all(not s['complete'] for s in scores) and state['calls']==4
                if mode in ['badfacts','unknown']:assert all(not s['complete'] for s in scores if s['arm']!='B_ordinary')
                if mode=='unknown':assert all(s.get('score') is None for s in scores)
                if mode in ['branch_limit','E_limit']:assert sum(s['complete'] for s in scores)==11
            tests.append({'mode':mode,'result':'PASS'})
    pfx={'options':{'Mr. X':'Mr. X',"Mr. X's son":"Mr. X's son"}}
    assert e.answer("ANSWER: Mr. X's son",pfx)=="Mr. X's son"
    assert e.answer('ANSWER: Mr. X\nANSWER: nonsense',pfx) is None
    assert e.expected_vote(['a','a','b','b'],'a')['expected_accuracy']==.5
    assert e.expected_vote(['a','a','a',None],'a') is None
    try:e.backend_module.check_length(16384,1,16384)
    except ValueError:pass
    else:raise AssertionError('length_guard')
    result={'result':'PASS','task_ids':sel['selected_ids'],'n_tasks':32,'n_seeds':2,'n_task_seed_units':64,
        'source_1056_requests_reconstructed':True,'new_task_matches_in_available_logs':0,'historical_split_unknown':True,
        'max_real_history_and_stress_plus_cap':maximum,'runner_fault_tests':tests,'max_logical_calls':3648,
        'max_output_tokens':1777664,'scope':'assistant provisional; newly allocated development, not secret heldout or historical exposure guarantee'}
    write(HERE/'PREFLIGHT.json',dict(result,freeze=freeze()));print(json.dumps(result))

def audit_run():
    cfg=load(HERE/'config.json');tasks={t['id']:t for t in load(HERE/'tasks.json')};labels=load(HERE/'labels.json');out=ROOT/cfg['run_dir']
    assert load(out/'manifest.json')['freeze']==freeze()==load(HERE/'FREEZE.json')
    snapshot=load(out/'STATUS.json')
    def read(p):
        text=p.read_text();return [json.loads(s) for s in text[:text.rfind('\n')+1].splitlines() if s]
    rows=read(out/'responses.jsonl');attempts=read(out/'attempts.jsonl');hist={};initial={};prep={};selected={};maximum=0
    sys.path.insert(0,str(ROOT/'tools'));from b0_training import load_tokenizer
    tok=load_tokenizer(cfg)
    for i,r in enumerate(rows):
        assert r['call']==i and all(r[k]==v for k,v in attempts[i].items())
        t=tasks[r['task_id']];u=(r['task_id'],r['unit_seed']);a=r['actor'];stage=r['stage'];arm=r['arm'];uc=dict(cfg,seed=r['unit_seed'])
        it=initial.get(u,{});own=[];public=[];prior=hist.get((*u,arm),[]);first,orders=e.order(t,uc)
        if stage in ['work','final']:
            parent='B_ordinary' if arm=='B_ordinary' else 'FACTS_SHARED'
            own=[prep[(*u,parent)][a]['text']]+[p['text'] for p in prior if p['actor']==a and p['stage']=='work']
            public=[(k,prep[(*u,parent)][k]['text']) for k in first] if arm=='B_ordinary' else e.public_facts(t,selected[u],{},False)
            public += [(p['actor'],p['text']) for p in prior if p['stage']=='work']
            if stage=='work':
                n=sum(p['stage']=='work' for p in prior)
                assert (r['round'],a)==((n+1,'M1') if arm=='S_same_sources_m1' else (n//4+1,orders[n//4][n%4]))
        expected=e.packet(t,a,stage,'E_facts' if arm=='S_same_sources_m1' else arm,'' if stage=='initial' else it[a]['text'],own,public)
        assert expected==r['payload']
        stage_code={'initial':0,'exchange':100,'facts':200,'work':1000,'final':9000}[stage]
        assert r['generation_seed']==(r['unit_seed']+t['id']*100000+stage_code+r['round']*10+e.ACTORS.index(a))%(2**32)
        assert r['cap']==(cfg['initial_tokens'] if stage=='initial' else cfg['final_tokens'] if stage=='final' else cfg['work_tokens'])
        ids=tok.apply_chat_template([{'role':k,'content':expected[k]} for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
        assert len(ids)==r['input_tokens'];e.backend_module.check_length(len(ids),r['cap'],cfg['max_length']);maximum=max(maximum,len(ids)+r['cap'])
        assert len(r['output_ids'])==r['output_tokens']<=r['cap'] and tok.decode(r['output_ids'],skip_special_tokens=True)==r['text'] and r['adapter_enabled'] is False
        if r['shared_within_run']:
            old=rows[r['source_call']];assert old['call']<i and old['arm']=='E_facts' and old['actor']=='M1'
            assert all(r[k]==old[k] for k in ['task_id','unit_seed','payload','generation_seed','cap','text','output_ids','input_tokens','output_tokens','status'])
        if stage=='facts':assert r['references']==e.refs(r['text'],e.visible(t,a))
        else:assert r['answer']==e.answer(r['text'],t)
        if stage=='initial':initial.setdefault(u,{})[a]=r
        elif stage in ['exchange','facts']:
            prep.setdefault((*u,arm),{})[a]=r
            if stage=='facts':selected.setdefault(u,{})[a]=r['references']
        else:hist.setdefault((*u,arm),[]).append(r)
    scores=load(out/'scores.json') if (out/'scores.json').exists() else [];checked=0
    for s in scores:
        if not s['complete']:continue
        finals=[r for r in hist.get((s['task_id'],s['unit_seed'],s['arm']),[]) if r['stage']=='final']
        assert len(finals)==(1 if s['arm']=='S_same_sources_m1' else 4)
        ans=[r['answer'] for r in finals];gold=labels[str(s['task_id'])]['correct']
        value=(None if ans[0] is None else float(ans[0]==gold)) if len(ans)==1 else (e.expected_vote(ans,gold) or {}).get('expected_accuracy')
        assert s['score']==value and s['final_answers']=={r['actor']:r['answer'] for r in finals};checked+=1
    if snapshot['status']=='COMPLETED':assert len(scores)==192 and len(rows)==len(attempts)==snapshot['calls']
    result={'result':'PASS','status':snapshot['status'],'responses_checked':len(rows),'attempts_snapshot':len(attempts),
         'complete_scores_checked':checked,'max_input_plus_cap':maximum,'non_eos':sum(r['status']!='OK' for r in rows),
         'unknown_finals':sum(r['answer'] is None for r in rows if r['stage']=='final'),'shared_exact_calls':sum(r['shared_within_run'] for r in rows),
         'freeze_unchanged':True,'all_requests_histories_seeds_tokens_reconstructed':True}
    write(HERE/('COMPLETION_AUDIT.json' if snapshot['status'] in ['COMPLETED','FAILED'] else 'START_VERIFICATION.json'),result);print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','preflight','run','audit']);a=p.parse_args()
    if a.mode=='freeze':write(HERE/'FREEZE.json',freeze())
    elif a.mode=='preflight':preflight()
    elif a.mode=='audit':audit_run()
    else:
        import fcntl
        assert freeze()==load(HERE/'FREEZE.json')==load(HERE/'PREFLIGHT.json')['freeze']
        assert load(HERE/'PREFLIGHT.json')['result']=='PASS' and 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
        lock=(HERE/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        cfg=load(HERE/'config.json');out=ROOT/cfg['run_dir'];assert not out.exists()
        try:backend=e.backend_module.Backend(cfg)
        except BaseException as exc:write(HERE/'STARTUP_FAILURE.json',{'type':type(exc).__name__,'message':str(exc)});raise
        result=execute(cfg,load(HERE/'tasks.json'),load(HERE/'labels.json'),backend,out);print(json.dumps(result))
        if result['status']=='FAILED':raise SystemExit(1)
