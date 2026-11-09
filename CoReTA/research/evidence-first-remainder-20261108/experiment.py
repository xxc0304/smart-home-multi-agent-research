"""Fixed development comparison: model-selected original facts, early opinions ablation."""
import argparse, collections, copy, hashlib, importlib.util, json, os, random, re, sys, time, traceback
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('sbp_backend',HERE.parent/'psych-sbp-pilot-20261108/pilot.py')
backend_module=importlib.util.module_from_spec(spec); spec.loader.exec_module(backend_module)
load,write,append,sha=backend_module.load,backend_module.write,backend_module.append,backend_module.sha
ACTORS=['M1','M2','M3','M4']; ARMS=['A_private','B_ordinary','E_facts','F_facts_opinions']
IDS=[8,9,11,23,30,33,34,50]
SYSTEM='Solve the supplied fictional decision task using the supplied facts. Do not invent evidence. Source IDs identify original task statements; the same source ID is one statement even if forwarded by several members. Other members\' opinions are not independent observations.'

def prepare():
    source=load(HERE/'benchmark.json'); selected={r['id']:r for r in source if r['id'] in IDS}
    assert set(selected)==set(IDS)
    tasks=[]; labels={}
    for number in IDS:
        r=selected[number]; choices=r['possible_answers'].copy()
        assert len(choices)==len(set(choices)) and r['correct_answer'] in choices
        random.Random(f'evidence-first-options-v1-{number}').shuffle(choices)
        sources={f'S{i:02d}':s for i,s in enumerate(r['shared_information'],1)}
        hidden={f'H{i:02d}':s for i,s in enumerate(r['hidden_information'],1)}
        assert len(hidden) in (3,4) and all(isinstance(s,str) and s.strip() for s in list(sources.values())+list(hidden.values()))
        task={'id':number,'name':r['name'],'description':r['description'],'shared':sources,'hidden':hidden,
              'options':{f'option_{i}':s for i,s in enumerate(choices,1)}}
        assert set(task).isdisjoint({'rationale','correct_answer'})
        tasks.append(task); labels[str(number)]={'correct':next(k for k,v in task['options'].items() if v==r['correct_answer']),
                                               'official_text':r['correct_answer']}
    write(HERE/'tasks.json',tasks); write(HERE/'labels.json',labels)
    write(HERE/'SELECTION.json',{'ids':IDS,'source_sha256':sha(HERE/'benchmark.json'),
          'rule':'Unattempted remainder of original fixed eleven development tasks; original task 7 remains failed and is not rerun or removed from original analysis denominator.',
          'not_unseen_or_holdout':True,'historical_split_manifest_unavailable':True,
          'predeclared_clearer_subset':[9,33,34],'n_distinct_source_ids':len(IDS),'strict_independence_not_established':True})

def visible(task,actor):
    hidden=list(task['hidden'])
    own=hidden if actor=='M1' else [hidden[(ACTORS.index(actor)-1) if len(hidden)==3 else ACTORS.index(actor)]]
    return dict(task['shared'],**{k:task['hidden'][k] for k in own})

def answer(text,task):
    # Exactly one distinct bounded option ID; repeated same ID accepted and recorded.
    ids=set(re.findall(r'\boption_\d+\b',text))
    return next(iter(ids)) if len(ids)==1 and ids<=set(task['options']) else None

def refs(text,catalogue):
    all_ids=re.findall(r'\b[SH]\d{2}\b',text)
    unknown=sorted(set(all_ids)-set(catalogue))
    selected=list(dict.fromkeys(all_ids))
    if unknown: return {'status':'INVALID_REFERENCE','unknown':unknown,'selected':[]}
    if not selected and text.strip().upper()!='NONE':
        return {'status':'UNREADABLE_REFERENCES','unknown':[],'selected':[]}
    exact=bool(re.fullmatch(r'(?:[SH]\d{2})(?:\s*,\s*[SH]\d{2})*',text.strip())) or text.strip().upper()=='NONE'
    return {'status':'OK','unknown':[],'selected':selected,'strict_id_format':exact}

def expected_vote(answers,gold):
    if len(answers)!=4 or any(x is None for x in answers): return None
    counts=collections.Counter(answers); winners=sorted(k for k,v in counts.items() if v==max(counts.values()))
    return {'expected_accuracy':sum(k==gold for k in winners)/len(winners),'winners':winners,'counts':dict(counts)}

def order(task,cfg):
    rng=random.Random(cfg['seed']+task['id']); first=ACTORS.copy();rng.shuffle(first); rounds=[]
    for _ in range(4):
        a=ACTORS.copy();rng.shuffle(a);rounds.append(a)
    return first,rounds

def packet(task,actor,stage,arm,initial='',own=None,public=None):
    own=own or [];public=public or []
    body=f'You are {actor}, one of four independent members M1/M2/M3/M4.\n'+task['description']
    body+='\n\nOPTIONS (use the option ID in your final answer):\n'+'\n'.join(f'{k}: {v}' for k,v in task['options'].items())
    body+='\n\nYOUR ORIGINAL SOURCE CATALOGUE:\n'+'\n'.join(f'[{k}] {v}' for k,v in visible(task,actor).items())
    if initial:body+='\n\nYour sealed independent initial response:\n'+initial
    if own:body+='\n\nYour own prior work:\n'+'\n\n'.join(own)
    if public:body+='\n\nPublic committee transcript:\n'+'\n\n'.join(f'{a}: {s}' for a,s in public)
    if stage=='facts':
        body+='\n\nBefore discussion, select the original source statements from YOUR catalogue that the team should examine to decide this task. Output only their IDs, separated by commas, or NONE. Do not give an option, conclusion, reasoning, or copy the statements. You may select any number of your visible statements; do not select IDs absent from your catalogue.'
    else:
        if arm=='A_private' and stage!='initial':body+='\n\nContinue working privately using only your own evidence and history. No teammate response is available.'
        elif stage=='initial':body+='\n\nAnswer independently before receiving any teammate opinion.'
        elif stage=='exchange':body+='\n\nPrepare your first message for the committee independently. Explain the evidence and your current choice as useful.'
        elif stage=='work':body+='\n\nIt is your discussion turn. Check the evidence and any disagreement, and revise or retain your choice as justified.'
        else:body+='\n\nSubmit your final answer privately. No other member will see this response.'
        if stage=='final':body+='\nOutput ONLY one option ID, for example option_1. Do not list alternatives.'
        else:body+='\nGive a concise explanation, then a line ANSWER: followed by exactly one option ID. Refer to other alternatives by their names, not option IDs.'
    return {'system':SYSTEM,'user':body}

def public_facts(task,selected,initials,include_opinions):
    # Deterministic original-text rendering only. No relevance/gold/answer-based fact selection.
    result=[]; catalogue=dict(task['shared'],**task['hidden'])
    for actor in ACTORS:
        r=selected[actor]
        assert r['status']=='OK'
        text='Selected original statements:\n'+'\n'.join(f'[{k}] {catalogue[k]}' for k in r['selected'])
        if not r['selected']:text+='(none selected)'
        if include_opinions:text+='\n\nInitial individual opinion:\n'+initials[actor]
        result.append((actor,text))
    return result

def freeze():
    paths=[HERE/n for n in ['experiment.py','config.json','tasks.json','labels.json','SELECTION.json','EXPERIMENT_REVIEW.md']]
    paths += [HERE.parent/'psych-sbp-pilot-20261108/pilot.py']
    paths += [ROOT/'tools'/n for n in ['b0_training.py','b0_answers.py','prepare_answer_only_expert.py']]
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}

def run(backend_factory=None):
    import fcntl
    cfg=load(HERE/'config.json'); tasks=load(HERE/'tasks.json'); labels=load(HERE/'labels.json')
    assert freeze()==load(HERE/'FREEZE.json') and load(HERE/'PREFLIGHT.json')['result']=='PASS'
    assert 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text(encoding='utf-8')
    if backend_factory and not cfg.get('fixture'):raise ValueError('fake_backend_only_for_explicit_fixture')
    out=ROOT/cfg['run_dir'];out.mkdir(parents=True,exist_ok=False)
    lock=(out/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    write(out/'manifest.json',{'config':cfg,'freeze':freeze(),'task_ids':[t['id'] for t in tasks],
                            'maximum_calls':96*len(tasks),'purpose':'DEVELOPMENT_INFORMATION_ADVANTAGE_NOT_HOLDOUT'})
    write(out/'PID.json',{'pid':os.getpid()});started=time.monotonic();calls=0;scores=[];fatal=None
    (out/'attempts.jsonl').touch();(out/'responses.jsonl').touch()
    write(out/'STATUS.json',{'status':'STARTING','calls':0,'maximum_calls':96*len(tasks)})
    try:backend=(backend_factory or backend_module.Backend)(cfg)
    except BaseException as exc:
        write(out/'STATUS.json',{'status':'FAILED','calls':0,'maximum_calls':96*len(tasks),
              'failure':{'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}})
        raise
    def call(task,actor,stage,arm,initial='',own=None,public=None,round_no=0):
        nonlocal calls
        stage_code={'initial':0,'exchange':100,'facts':200,'work':1000,'final':9000}[stage]
        seed=(cfg['seed']+task['id']*100000+stage_code+round_no*10+ACTORS.index(actor))%(2**32)
        cap=cfg['initial_tokens'] if stage=='initial' else cfg['final_tokens'] if stage=='final' else cfg['work_tokens']
        payload=packet(task,actor,stage,arm,initial,own,public)
        request={'call':calls,'task_id':task['id'],'actor':actor,'stage':stage,'arm':arm,
                 'round':round_no,'generation_seed':seed,'cap':cap,'payload':payload}
        append(out/'attempts.jsonl',request)
        result=backend.respond(payload,cap,seed);calls+=1
        parsed=answer(result['text'],task) if stage!='facts' else None
        row={**request,**result,'answer':parsed}
        if stage=='facts':row['references']=refs(result['text'],visible(task,actor))
        append(out/'responses.jsonl',row)
        write(out/'STATUS.json',{'status':'RUNNING','calls':calls,'maximum_calls':96*len(tasks),
              'task_id':task['id'],'arm':arm,'stage':stage,'elapsed_seconds':time.monotonic()-started})
        if result['status']!='OK' or not result['text'].strip():raise ValueError('INCOMPLETE_DEPENDENCY')
        return row
    consecutive_failed_tasks=0
    try:
        for task in tasks:
            first,orders=order(task,cfg);initials={};exchanges={};selected={};pre_failed={}
            try:
                for actor in first:initials[actor]=call(task,actor,'initial','COMMON')
            except ValueError as exc:
                if str(exc)!='INCOMPLETE_DEPENDENCY':raise
                failed_rows=[{'task_id':task['id'],'arm':arm,'complete':False,'reason':'COMMON_INITIAL_INCOMPLETE'} for arm in ARMS]
                scores.extend(failed_rows);write(out/'scores.json',scores)
                write(out/f'task-{task["id"]}.json',failed_rows)
                consecutive_failed_tasks+=1
                if consecutive_failed_tasks>=2:raise RuntimeError('SYSTEMIC_FAILURE_STOP_BATCH')
                continue
            initial_text={a:initials[a]['text'] for a in ACTORS}
            # Generate once, in parallel-information sense: these first exchanges see no peers.
            for arm in ['A_private','B_ordinary','FACTS_SHARED']:
                exchanges[arm]={}
                try:
                    for actor in first:
                        stage='facts' if arm=='FACTS_SHARED' else 'exchange'
                        r=call(task,actor,stage,arm,initial_text[actor])
                        exchanges[arm][actor]=r
                        if stage=='facts':
                            if r['references']['status']!='OK':raise ValueError('INVALID_FACT_SELECTION')
                            selected[actor]=r['references']
                except ValueError as exc:
                    if str(exc) not in ['INCOMPLETE_DEPENDENCY','INVALID_FACT_SELECTION']:raise
                    pre_failed[arm]=str(exc)
            failed=[]
            for arm in ARMS:
                try:
                    parent='FACTS_SHARED' if arm.startswith(('E_','F_')) else arm
                    if parent in pre_failed:raise ValueError(pre_failed[parent])
                    own={a:[exchanges[parent][a]['text']] for a in ACTORS}
                    public=[] if arm=='A_private' else [(a,exchanges[arm][a]['text']) for a in first] if arm=='B_ordinary' else public_facts(task,selected,initial_text,arm=='F_facts_opinions')
                    for round_no,actors in enumerate(orders,1):
                        for actor in actors:
                            r=call(task,actor,'work',arm,initial_text[actor],own[actor],public,round_no)
                            own[actor].append(r['text'])
                            if arm!='A_private':public.append((actor,r['text']))
                    finals=[call(task,a,'final',arm,initial_text[a],own[a],public) for a in ACTORS]
                    gold=labels[str(task['id'])]['correct']
                    item={'task_id':task['id'],'arm':arm,'complete':True,
                          'initial_answers':{a:initials[a]['answer'] for a in ACTORS},
                          'final_answers':{a:r['answer'] for a,r in zip(ACTORS,finals)},
                          'initial_vote':expected_vote([initials[a]['answer'] for a in ACTORS],gold),
                          'final_vote':expected_vote([r['answer'] for r in finals],gold),
                          'expert_initial_correct':None if initials['M1']['answer'] is None else initials['M1']['answer']==gold,
                          'expert_final_correct':None if finals[0]['answer'] is None else finals[0]['answer']==gold,
                          'gold':gold}
                    if arm.startswith(('E_','F_')):
                        item['selected_hidden_ids']=sorted({k for r in selected.values() for k in r['selected'] if k.startswith('H')})
                        item['all_hidden_ids']=sorted(task['hidden'])
                    scores.append(item)
                except ValueError as exc:
                    if str(exc) not in ['INCOMPLETE_DEPENDENCY','INVALID_FACT_SELECTION']:raise
                    failed.append(arm);scores.append({'task_id':task['id'],'arm':arm,'complete':False,'reason':str(exc)})
                write(out/'scores.json',scores)
            # E/F share one selection dependency: never count it as two independent faults.
            families={'FACTS_SHARED' if a.startswith(('E_','F_')) else a for a in failed}
            consecutive_failed_tasks=consecutive_failed_tasks+1 if families else 0
            if len(families)>=2 or consecutive_failed_tasks>=2:
                raise RuntimeError('SYSTEMIC_FAILURE_STOP_BATCH')
            write(out/f'task-{task["id"]}.json',[s for s in scores if s['task_id']==task['id']])
            if tasks.index(task)==1:write(out/'TECHNICAL_PREFIX.json',{'first_two_complete':True,'calls':calls,'accuracy_not_used_to_gate':True})
    except BaseException as exc:fatal={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    write(out/'STATUS.json',{'status':'FAILED' if fatal else 'COMPLETED','calls':calls,'maximum_calls':96*len(tasks),
          'elapsed_seconds':time.monotonic()-started,'failure':fatal,'complete_arms':sum(s['complete'] for s in scores),
          'freeze_unchanged':freeze()==load(HERE/'FREEZE.json')})
    print(json.dumps(load(out/'STATUS.json')))
    if fatal:raise SystemExit(1)

def preflight():
    prepare();cfg=load(HERE/'config.json');tasks=load(HERE/'tasks.json')
    for task in tasks:
        assert 'correct_answer' not in json.dumps(task) and 'rationale' not in task
        assert set(visible(task,'M1'))==set(task['shared'])|set(task['hidden'])
        for actor in ACTORS[1:]:assert len(set(visible(task,actor))&set(task['hidden']))==1
        selected={a:refs(','.join(visible(task,a)),visible(task,a)) for a in ACTORS}
        initial={a:'OPINION_MARKER '+a for a in ACTORS}
        ef=public_facts(task,selected,initial,False);fo=public_facts(task,selected,initial,True)
        assert all(s==t.split('\n\nInitial individual opinion:')[0] for (_,s),(_,t) in zip(ef,fo))
        assert 'OPINION_MARKER' not in str(ef) and 'OPINION_MARKER' in str(fo)
        private=packet(task,'M1','work','A_private','OWN',own=['SELF'],public=[])
        assert 'Public committee transcript' not in private['user']
        assert refs('H99',visible(task,'M1'))['status']=='INVALID_REFERENCE'
        assert refs('nonsense',visible(task,'M1'))['status']=='UNREADABLE_REFERENCES'
        assert refs('NONE',visible(task,'M1'))['status']=='OK'
        assert answer('ANSWER: option_1',task)=='option_1'
        assert answer('option_1 or option_2',task) is None
        assert answer('option_999',task) is None
    assert expected_vote(['a','b','a','b'],'a')['expected_accuracy']==.5
    assert expected_vote(['a',None,'a','a'],'a') is None
    sys.path.insert(0,str(ROOT/'tools'));from b0_training import load_tokenizer
    tok=load_tokenizer(cfg)
    # Replay complete real SBP texts to exercise actual envelope/history growth. Ranking is not choice-parser evidence.
    old=ROOT/'runs/psych-sbp-pilot-20261108-v1/responses.jsonl'
    real=[json.loads(s) for s in old.read_text().splitlines()]
    assert len(real)==224
    longest=sorted(real,key=lambda r:r['output_tokens'],reverse=True)[:16]
    max_tokens=0
    for task in tasks:
        for actor in ACTORS:
            public=[(ACTORS[i%4],r['text']) for i,r in enumerate(longest)]
            p=packet(task,actor,'final','B_ordinary',real[0]['text'],own=[r['text'] for r in longest[:5]],public=public)
            ids=tok.apply_chat_template([{'role':k,'content':p[k]} for k in ('system','user')],tokenize=True,
                add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
            backend_module.check_length(len(ids),cfg['final_tokens'],cfg['max_length'])
            max_tokens=max(max_tokens,len(ids)+cfg['final_tokens'])
    backend_module.check_length(16000,384,16384)
    try:backend_module.check_length(16001,384,16384)
    except ValueError:pass
    else:raise AssertionError('missing_overlength_guard')
    tests=load(HERE/'RUNNER_TESTS.json');assert all(t['pass'] for t in tests)
    hashes=freeze();write(HERE/'FREEZE.json',hashes)
    write(HERE/'PREFLIGHT.json',{'result':'PASS','freeze':hashes,'task_ids':IDS,'max_replayed_history_plus_cap':max_tokens,
          'real_history_source_sha256':sha(old),'real_prior_outputs':224,'new_choice_and_reference_parser_tests':'synthetic; first two tasks are technical development',
          'maximum_calls':96*len(tasks),'maximum_output_tokens':41984*len(tasks),'fault_tests':tests,
          'no_gold_in_payloads':True,'same_selected_fact_text_E_F':True})
    print(json.dumps(load(HERE/'PREFLIGHT.json')))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('mode',choices=['prepare','preflight','run']);args=a.parse_args()
    {'prepare':prepare,'preflight':preflight,'run':run}[args.mode]()
