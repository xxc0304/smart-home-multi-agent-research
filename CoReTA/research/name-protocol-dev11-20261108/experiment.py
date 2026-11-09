"""One fixed dev11 review, exact technical protocol and verified immutable reuse."""
import argparse, collections, importlib.util, json, os, sys, time, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BASE=HERE.parent/'name-interface-tech-20261108-v2/experiment.py'
spec=importlib.util.spec_from_file_location('verified_name_protocol',BASE)
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
load,write,append,sha=base.load,base.write,base.append,base.sha
ACTORS,ARMS=base.ACTORS,base.ARMS
IDS=[1,4,7,8,9,11,23,30,33,34,50]
visible,answer,answer_mode,refs=base.visible,base.answer,base.answer_mode,base.refs
packet,public_facts,order,expected_vote=base.packet,base.public_facts,base.order,base.expected_vote
normalize_name,answer_fields,backend_module,re=base.normalize_name,base.answer_fields,base.backend_module,base.re

def budget(cfg,tasks):return 96*len(tasks)

def prepare():
    source={r['id']:r for r in load(HERE/'benchmark.json')};tasks=[];labels={}
    for number in IDS:
        r=source[number];options={s:s for s in r['possible_answers']}
        assert len(options)==len(r['possible_answers']) and r['correct_answer'] in options
        t={'id':number,'name':r['name'],'description':r['description'],
           'shared':{f'S{i:02d}':s for i,s in enumerate(r['shared_information'],1)},
           'hidden':{f'H{i:02d}':s for i,s in enumerate(r['hidden_information'],1)},'options':options}
        tasks.append(t);labels[str(number)]={'correct':r['correct_answer'],'official_text':r['correct_answer']}
    write(HERE/'tasks.json',tasks);write(HERE/'labels.json',labels)
    write(HERE/'SELECTION.json',{'ids':IDS,'source_sha256':sha(HERE/'benchmark.json'),
          'rule':'Original fixed eleven previously used development tasks, no selection from new outcomes.',
          'not_unseen_or_holdout':True,'historical_split_manifest_unavailable':True,
          'predeclared_clearer_subset':[9,33,34],'technical_complete_task_reuse':[11,33],
          'technical_initial_only_reuse':[7,8,23,34],'n_distinct_source_ids':11,'independence_not_established':True})

def key(r):return (r['task_id'],r['actor'],r['stage'],r['arm'],r['round'])

def request(task,actor,stage,arm,cfg,initial='',own=None,public=None,round_no=0):
    stage_code={'initial':0,'exchange':100,'facts':200,'work':1000,'final':9000}[stage]
    seed=(cfg['seed']+task['id']*100000+stage_code+round_no*10+ACTORS.index(actor))%(2**32)
    cap=cfg['initial_tokens'] if stage=='initial' else cfg['final_tokens'] if stage=='final' else cfg['work_tokens']
    return {'task_id':task['id'],'actor':actor,'stage':stage,'arm':arm,'round':round_no,
            'generation_seed':seed,'cap':cap,'payload':packet(task,actor,stage,arm,initial,own,public)}

def cache_index(cfg):
    if not cfg.get('initial_cache'):return {}
    p=ROOT/cfg['initial_cache'];assert sha(p)==cfg['initial_cache_sha256']
    rows=[json.loads(s) for s in p.read_text().splitlines()];mapping={key(r):r for r in rows}
    assert len(mapping)==len(rows) and all(r['status']=='OK' for r in rows)
    return mapping

def check_cached(req,old):
    for k,v in req.items():assert old[k]==v,('reuse_request_diff',key(old),k)

def replay_task(task,cfg,cache):
    """Reconstruct every downstream request of a completed technical task without generation."""
    consumed=[]
    def get(actor,stage,arm,initial='',own=None,public=None,round_no=0):
        req=request(task,actor,stage,arm,cfg,initial,own,public,round_no)
        old=cache[key(req)];check_cached(req,old);consumed.append(key(req));return old
    first,orders=order(task,cfg);initial={a:get(a,'initial','COMMON') for a in first}
    texts={a:initial[a]['text'] for a in ACTORS};prep={};selected={}
    for arm in ['A_private','B_ordinary','FACTS_SHARED']:
        prep[arm]={}
        for a in first:
            row=get(a,'facts' if arm=='FACTS_SHARED' else 'exchange',arm,texts[a]);prep[arm][a]=row
            if arm=='FACTS_SHARED':
                selected[a]=refs(row['text'],visible(task,a));assert selected[a]['status']=='OK'
    for arm in ARMS:
        parent='FACTS_SHARED' if arm.startswith(('E_','F_')) else arm
        own={a:[prep[parent][a]['text']] for a in ACTORS}
        public=[] if arm=='A_private' else [(a,prep[arm][a]['text']) for a in first] if arm=='B_ordinary' else public_facts(task,selected,texts,arm=='F_facts_opinions')
        for round_no,actors in enumerate(orders,1):
            for a in actors:
                row=get(a,'work',arm,texts[a],own[a],public,round_no);own[a].append(row['text'])
                if arm!='A_private':public.append((a,row['text']))
        for a in ACTORS:get(a,'final',arm,texts[a],own[a],public)
    assert len(consumed)==96 and len(set(consumed))==96
    return consumed

def check_reuse():
    cfg=load(HERE/'config.json');tasks=load(HERE/'tasks.json');old_here=HERE.parent/'name-interface-tech-20261108-v2'
    old_cfg=load(old_here/'config.json');ignored={'run_dir','purpose','flow_task_ids','initial_cache','initial_cache_sha256'}
    assert {k:v for k,v in cfg.items() if k not in ignored}=={k:v for k,v in old_cfg.items() if k not in ignored}
    old_tasks={t['id']:t for t in load(old_here/'tasks.json')};now={t['id']:t for t in tasks}
    assert all(now[n]==t for n,t in old_tasks.items())
    cache=cache_index(cfg);assert len(cache)==208
    used=[]
    for n in [11,33]:used+=replay_task(now[n],cfg,cache)
    for n in [7,8,23,34]:
        for a in ACTORS:
            req=request(now[n],a,'initial','COMMON',cfg);check_cached(req,cache[key(req)]);used.append(key(req))
    assert set(used)==set(cache)
    old_run=ROOT/old_cfg['run_dir'];assert load(old_run/'STATUS.json')['status']=='COMPLETED'
    for rel,digest in load(old_run/'manifest.json')['freeze'].items():assert sha(ROOT/rel)==digest
    result={'result':'PASS','all_208_requests_exactly_reconstructed':True,'complete_reused_task_ids':[11,33],
            'initial_only_reused_ids':[7,8,23,34],'inherited_records':208,'maximum_new_calls':848,
            'scientific_config_and_shared_tasks_identical':True,'old_freeze_unchanged':True,
            'development_data_not_new_independent_evidence':True}
    write(HERE/'REUSE_CHECK.json',result);print(json.dumps(result));return result

def freeze():
    paths=[HERE/n for n in ['experiment.py','config.json','tasks.json','labels.json','SELECTION.json','EXPERIMENT_REVIEW.md']]
    paths+=[BASE,HERE.parent/'psych-sbp-pilot-20261108/pilot.py']
    paths += [ROOT/'tools'/n for n in ['b0_training.py','b0_answers.py','prepare_answer_only_expert.py']]
    cfg=load(HERE/'config.json')
    if cfg.get('initial_cache'):paths.append(ROOT/cfg['initial_cache'])
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}

def run(backend_factory=None):
    import fcntl
    cfg=load(HERE/'config.json');tasks=load(HERE/'tasks.json');labels=load(HERE/'labels.json')
    assert freeze()==load(HERE/'FREEZE.json') and load(HERE/'PREFLIGHT.json')['result']=='PASS'
    assert 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
    if backend_factory and not cfg.get('fixture'):raise ValueError('fake_backend_requires_fixture')
    cache=cache_index(cfg);out=ROOT/cfg['run_dir'];out.mkdir(parents=True,exist_ok=False)
    lock=(out/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    write(out/'manifest.json',{'config':cfg,'freeze':freeze(),'task_ids':[t['id'] for t in tasks],
          'maximum_calls':budget(cfg,tasks),'maximum_new_generation_calls':budget(cfg,tasks)-len(cache),
          'maximum_inherited_records':len(cache),'purpose':'FIXED_DEV11_ORGANIZATION_REVIEW_NOT_CONFIRMATORY'})
    write(out/'PID.json',{'pid':os.getpid()});started=time.monotonic();calls=0;inherited=0;scores=[];fatal=None;cache_used=set()
    for name in ['attempts.jsonl','responses.jsonl']:(out/name).touch()
    write(out/'STATUS.json',{'status':'STARTING','calls':0,'maximum_calls':budget(cfg,tasks),'new_generation_calls':0,'inherited_records':0})
    try:backend=(backend_factory or backend_module.Backend)(cfg)
    except BaseException as exc:
        write(out/'STATUS.json',{'status':'FAILED','calls':0,'failure':str(exc)});raise
    def call(task,actor,stage,arm,initial='',own=None,public=None,round_no=0):
        nonlocal calls,inherited
        req=request(task,actor,stage,arm,cfg,initial,own,public,round_no);k=key(req)
        old=cache.get(k);is_reused=old is not None
        if is_reused:check_cached(req,old)
        attempt=dict(req,call=calls,inherited=is_reused);append(out/'attempts.jsonl',attempt)
        if is_reused:
            row=dict(old,**attempt,source_cache=cfg['initial_cache'],source_cache_call=old['call'])
            inherited+=1;cache_used.add(k)
        else:row=dict(backend.respond(req['payload'],req['cap'],req['generation_seed']),**attempt)
        row['answer']=answer(row['text'],task) if stage!='facts' else None
        if stage=='facts':row['references']=refs(row['text'],visible(task,actor))
        else:row['answer_mode']=answer_mode(row['text'],task)
        calls+=1;append(out/'responses.jsonl',row)
        write(out/'STATUS.json',{'status':'RUNNING','calls':calls,'maximum_calls':budget(cfg,tasks),
              'task_id':task['id'],'arm':arm,'stage':stage,'elapsed_seconds':time.monotonic()-started,
              'new_generation_calls':calls-inherited,'inherited_records':inherited,'complete_arms':sum(s['complete'] for s in scores)})
        if row['status']!='OK' or not row['text'].strip():raise ValueError('INCOMPLETE_DEPENDENCY')
        return row
    consecutive=0
    try:
        for task in tasks:
            first,orders=order(task,cfg);initial={};prep={};selected={};pre_failed={}
            try:
                for a in first:initial[a]=call(task,a,'initial','COMMON')
            except ValueError as exc:
                if str(exc)!='INCOMPLETE_DEPENDENCY':raise
                scores.extend({'task_id':task['id'],'arm':a,'complete':False,'reason':'COMMON_INITIAL_INCOMPLETE'} for a in ARMS)
                write(out/'scores.json',scores);write(out/f'task-{task["id"]}.json',[s for s in scores if s['task_id']==task['id']])
                consecutive+=1
                if consecutive>=2:raise RuntimeError('SYSTEMIC_FAILURE_STOP_BATCH')
                continue
            texts={a:initial[a]['text'] for a in ACTORS}
            for arm in ['A_private','B_ordinary','FACTS_SHARED']:
                prep[arm]={}
                try:
                    for a in first:
                        r=call(task,a,'facts' if arm=='FACTS_SHARED' else 'exchange',arm,texts[a]);prep[arm][a]=r
                        if arm=='FACTS_SHARED':
                            if r['references']['status']!='OK':raise ValueError('INVALID_FACT_SELECTION')
                            selected[a]=r['references']
                except ValueError as exc:
                    if str(exc) not in ['INCOMPLETE_DEPENDENCY','INVALID_FACT_SELECTION']:raise
                    pre_failed[arm]=str(exc)
            failed=[]
            for arm in ARMS:
                try:
                    parent='FACTS_SHARED' if arm.startswith(('E_','F_')) else arm
                    if parent in pre_failed:raise ValueError(pre_failed[parent])
                    own={a:[prep[parent][a]['text']] for a in ACTORS}
                    public=[] if arm=='A_private' else [(a,prep[arm][a]['text']) for a in first] if arm=='B_ordinary' else public_facts(task,selected,texts,arm=='F_facts_opinions')
                    for rn,actors in enumerate(orders,1):
                        for a in actors:
                            r=call(task,a,'work',arm,texts[a],own[a],public,rn);own[a].append(r['text'])
                            if arm!='A_private':public.append((a,r['text']))
                    finals=[call(task,a,'final',arm,texts[a],own[a],public) for a in ACTORS];gold=labels[str(task['id'])]['correct']
                    s={'task_id':task['id'],'arm':arm,'complete':True,'gold':gold,
                       'initial_answers':{a:initial[a]['answer'] for a in ACTORS},'final_answers':{a:r['answer'] for a,r in zip(ACTORS,finals)},
                       'initial_vote':expected_vote([initial[a]['answer'] for a in ACTORS],gold),'final_vote':expected_vote([r['answer'] for r in finals],gold),
                       'expert_initial_correct':None if initial['M1']['answer'] is None else initial['M1']['answer']==gold,
                       'expert_final_correct':None if finals[0]['answer'] is None else finals[0]['answer']==gold}
                    if arm.startswith(('E_','F_')):s.update(selected_hidden_ids=sorted({k for r in selected.values() for k in r['selected'] if k.startswith('H')}),all_hidden_ids=sorted(task['hidden']))
                    scores.append(s)
                except ValueError as exc:
                    if str(exc) not in ['INCOMPLETE_DEPENDENCY','INVALID_FACT_SELECTION']:raise
                    failed.append(arm);scores.append({'task_id':task['id'],'arm':arm,'complete':False,'reason':str(exc)})
                write(out/'scores.json',scores)
            families={'FACTS_SHARED' if a.startswith(('E_','F_')) else a for a in failed}
            consecutive=consecutive+1 if families else 0
            write(out/f'task-{task["id"]}.json',[s for s in scores if s['task_id']==task['id']])
            if len(families)>=2 or consecutive>=2:raise RuntimeError('SYSTEMIC_FAILURE_STOP_BATCH')
    except BaseException as exc:fatal={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    write(out/'STATUS.json',{'status':'FAILED' if fatal else 'COMPLETED','calls':calls,'maximum_calls':budget(cfg,tasks),
          'new_generation_calls':calls-inherited,'inherited_records':inherited,'unused_cache_records':len(cache)-len(cache_used),
          'elapsed_seconds':time.monotonic()-started,'failure':fatal,'complete_arms':sum(s['complete'] for s in scores),
          'freeze_unchanged':freeze()==load(HERE/'FREEZE.json')})
    print(json.dumps(load(out/'STATUS.json')))
    if fatal:raise SystemExit(1)

def preflight():
    prepare();cfg=load(HERE/'config.json');tasks=load(HERE/'tasks.json');reuse=check_reuse()
    tests=load(HERE/'RUNNER_TESTS.json');assert all(x['pass'] for x in tests)
    prefix={'options':{'Mr. X':'Mr. X',"Mr. X's son":"Mr. X's son",'Mrs. Y':'Mrs. Y'}}
    assert answer("Other options: option_1 option_2\nANSWER: Mr. X's son",prefix)=="Mr. X's son"
    assert answer("Reason\nMr. X's son",prefix)=="Mr. X's son"
    assert answer("ANSWER: Mr. X\nANSWER: Mr. X's son",prefix) is None
    assert answer("ANSWER: Unknown\nMr. X",prefix) is None
    assert answer("Mr. X or Mr. X's son",prefix) is None
    assert expected_vote(['a','b','a','b'],'a')['expected_accuracy']==.5
    assert expected_vote(['a',None,'a','a'],'a') is None
    sys.path.insert(0,str(ROOT/'tools'));from b0_training import load_tokenizer
    tok=load_tokenizer(cfg);cache=cache_index(cfg);longest=sorted(cache.values(),key=lambda r:r['output_tokens'],reverse=True)[:16];maximum=0
    for t in tasks:
        assert set(t).isdisjoint({'correct_answer','rationale'})
        refs_all={a:refs(','.join(visible(t,a)),visible(t,a)) for a in ACTORS};initial={a:'INITIAL_MARKER '+a for a in ACTORS}
        ef=public_facts(t,refs_all,initial,False);ff=public_facts(t,refs_all,initial,True)
        assert [s for _,s in ef]==[s.split('\n\nInitial individual opinion:')[0] for _,s in ff]
        assert 'INITIAL_MARKER' not in str(ef)
        for a in ACTORS:
            assert len(set(visible(t,a))&set(t['hidden']))==(len(t['hidden']) if a=='M1' else 1)
            p=packet(t,a,'final','B_ordinary',longest[0]['text'],[r['text'] for r in longest[:5]],[(ACTORS[i%4],r['text']) for i,r in enumerate(longest)])
            ids=tok.apply_chat_template([{'role':k,'content':p[k]} for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
            backend_module.check_length(len(ids),cfg['final_tokens'],cfg['max_length']);maximum=max(maximum,len(ids)+cfg['final_tokens'])
    backend_module.check_length(16000,384,16384)
    try:backend_module.check_length(16001,384,16384)
    except ValueError:pass
    else:raise AssertionError('missing_length_guard')
    hashes=freeze();write(HERE/'FREEZE.json',hashes)
    write(HERE/'PREFLIGHT.json',{'result':'PASS','freeze':hashes,'task_ids':IDS,'reuse':reuse,'fault_tests':tests,
          'actual_208_response_reconstruction':True,'max_replayed_history_plus_cap':maximum,
          'name_field_terminal_name_prefix_and_missing_regression':'PASS',
          'maximum_logical_calls':1056,'maximum_new_generation_calls':848,'maximum_inherited_records':208,
          'maximum_total_output_tokens':495616,'maximum_new_output_tokens':389120,
          'scope':'single fixed development review, not held-out method confirmation'})
    print(json.dumps(load(HERE/'PREFLIGHT.json')))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','reuse','preflight','run']);a=p.parse_args()
    {'prepare':prepare,'reuse':check_reuse,'preflight':preflight,'run':run}[a.mode]()
