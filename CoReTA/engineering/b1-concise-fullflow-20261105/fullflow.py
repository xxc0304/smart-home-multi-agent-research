"""Fixed historical-failure technical validation; never bypasses the normal D CLI."""
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
HERE=Path(__file__).resolve().parent
OLD=ROOT/'runs/b1-dev32-final-20261104-v2'
V=ROOT/'runs/b1-concise-V8-20261105-v1'
TEAM=ROOT/'runs/b1-concise-tech6-20261105-v1'
INDEXES=(9,13,16,22,0,1)
def load(p):return json.loads(Path(p).read_text())
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snapshot():
    for name in ('b1_controls.py','b1_runtime.py'):
        dest=HERE/'prior'/name;dest.parent.mkdir(exist_ok=True)
        assert not dest.exists();shutil.copy2(ROOT/'tools'/name,dest)
    run=ROOT/'runs/b1-sampling-check-20261105-v2';freeze=load(run/'FREEZE.json');archive={}
    assert load(run/'RESULTS.json')['verdict']=='PASS_TECHNICAL_ONLY'
    for name,h in freeze['files'].items():
        assert sha(name)==h
        dest=run/'frozen_sources'/Path(name).relative_to(ROOT)
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(name,dest)
        archive[name]=dict(archive=str(dest),sha256=h)
    write(run/'SOURCE_ARCHIVE.json',archive)
    print('PRIOR_TOOLS_AND_COMPLETED_T2_SOURCES_ARCHIVED')
def config():
    c=load(OLD/'manifest.json')['config']
    c.update(answer_tokens=128,answer_suffix='',answer_policy_version='B1_CONCISE_V4',output_contract='B1_CONCISE_V4',work_tokens=768)
    return c
def preflight():
    from b1_controls import replay,summarize
    from b1_runtime import development_data
    from b1_output_contract import violation
    p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_b1*.py'],cwd=ROOT,capture_output=True,text=True)
    (HERE/'TESTS.txt').write_text(p.stdout+p.stderr);assert p.returncode==0,'B1 tests failed'
    traces=[load(p) for p in sorted((OLD/'trials').glob('*.json'))]
    for t in traces:assert replay(t).export()==t
    _,groups,targets=development_data(32,targets=True)
    m=load(OLD/'manifest.json');assert summarize(traces,targets,m['expected_ids'],groups)==load(OLD/'scores.json')
    checks=[dict(request_id=r['request_id'],stage=r['stage'],status_original=r['status'],new_format_violation=violation(r['raw_output'],r['stage'])) for t in traces for r in t['records'] if r['status']!='OK']
    assert len(checks)==4
    write(HERE/'HISTORICAL_FORMAT_CHECK.json',checks)
    write(HERE/'PREFLIGHT.json',dict(status='PASS',tests_returncode=0,original32_replay_and_scores_identical=True,historical_failed_texts_checked=4,technical_indexes=list(INDEXES),C_H_question_target_bodies_read=False,source_hashes={n:sha(ROOT/'tools'/n) for n in ('b1_controls.py','b1_runtime.py','b1_output_contract.py')}))
    print('PREFLIGHT_PASS: B1 tests; all32 exact replay and scores; four real old failure texts')
def prepare(mode):
    from b1_runtime import load_tokenizer,trial_parameters
    from b1_controls import Trial
    assert load(HERE/'PREFLIGHT.json')['status']=='PASS'
    assert all(sha(ROOT/'tools'/n)==h for n,h in load(HERE/'PREFLIGHT.json')['source_hashes'].items())
    c=config();out=V if mode=='v' else TEAM;c['wall_seconds']=600 if mode=='v' else 3600
    if mode=='v':
        with (ROOT/'data/expert-training-20261030-v1/validation.inputs.jsonl').open() as f:tasks=[json.loads(next(f)) for _ in range(8)]
        entries=[]
        for i,task in enumerate(tasks):
            req=Trial(task,**trial_parameters(c,i)).next_request()
            for actor in ('M2','M1'):
                r=dict(req,actor=actor,seed=c['seed']+i*10000+int(actor[1:])-1,request_id=task['id']+'|'+actor)
                entries.append(r)
    else:
        assert load(V/'RESULTS.json')['verdict']=='PASS_TECHNICAL_ONLY','V16 contract incomplete'
        entries=[dict(task_index=i,task=load(OLD/'trials'/f'{i:03d}.json')['task']) for i in INDEXES]
        assert len({e['task']['id'] for e in entries})==6
        assert all(not load(OLD/'trials'/f'{i:03d}.json')['complete'] for i in INDEXES[:4])
        assert all(load(OLD/'trials'/f'{i:03d}.json')['complete'] for i in INDEXES[4:])
    tok=load_tokenizer(c);lengths=[]
    initial_requests=entries if mode=='v' else [Trial(e['task'],**trial_parameters(c,e['task_index'])).next_request() for e in entries]
    for r in initial_requests:
        ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
        assert isinstance(ids,list) and all(isinstance(i,int) for i in ids)
        assert len(ids)+r['max_new_tokens']<=c['max_length']
        lengths.append(len(ids))
    out.mkdir(parents=True,exist_ok=False)
    write(out/'INPUTS.json',entries);write(out/'config.json',c)
    write(out/'manifest.json',dict(scope='FIXED_V_MIGRATION_TECHNICAL' if mode=='v' else 'HISTORICAL_FAILURE_SELECTED_TECHNICAL_NOT_POPULATION_ACCURACY',fixture=False,primary_enabled=False,technical_preflight=True,mode=mode,expected_generations=16 if mode=='v' else 312,expected_ids=[e['request_id'] for e in entries] if mode=='v' else [e['task']['id'] for e in entries],original_task_indexes=list(INDEXES) if mode=='team' else list(range(8)),max_initial_input_tokens=max(lengths),soft_seconds=c['wall_seconds'],hard_seconds=900 if mode=='v' else 4200))
    paths=[Path(__file__),HERE/'EXPERIMENT_REVIEW.md',HERE/'PREFLIGHT.json',HERE/'TESTS.txt',out/'INPUTS.json',out/'config.json',out/'manifest.json',OLD/'manifest.json',OLD/'scores.json']+[ROOT/'tools'/n for n in ('b1_controls.py','b1_runtime.py','b1_output_contract.py','b1_stop_status.py','b0_training.py')]
    write(out/'FREEZE.json',dict(files={str(p):sha(p) for p in paths}))
    print(json.dumps(dict(mode=mode,freeze_sha256=sha(out/'FREEZE.json'),max_initial_tokens=max(lengths))))
def run(mode):
    from b1_controls import Trial,summarize
    from b1_runtime import LocalBackend,trial_parameters,development_data
    from b1_output_contract import violation
    from b0_answers import answer_score
    out=V if mode=='v' else TEAM;f=load(out/'FREEZE.json');a=load(out/'APPROVAL.json');c=load(out/'config.json')
    assert a['verdict']=='RUN_ALLOWED' and a['freeze_sha256']==sha(out/'FREEZE.json')
    assert all(sha(p)==h for p,h in f['files'].items())
    if mode=='team':assert load(V/'RESULTS.json')['verdict']=='PASS_TECHNICAL_ONLY'
    (out/'LAUNCHED').touch(exist_ok=False)
    started=time.monotonic();rows=[];traces=[];fatal=None
    def save(row):
        rows.append(row)
        with (out/'responses.jsonl').open('a') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        print(json.dumps(dict(done=len(rows),request_id=row['request_id'],status=row['status'])),flush=True)
    try:
        backend=LocalBackend(c)
        write(out/'backend.json',dict(generation_config=backend.generation_config.to_dict()))
        if mode=='v':
            for req in load(out/'INPUTS.json'):
                remaining=c['wall_seconds']-(time.monotonic()-started)
                if remaining<=0:break
                response=backend.respond(req,remaining)
                reason=violation(response['raw_output'],req['stage']) if response['status']=='OK' else None
                row=dict(**req,**response,backend_status=response['status'],format_violation=reason)
                if reason:row['status']='FORMAT_VIOLATION'
                save(row)
                if sum(r['status']!='OK' for r in rows)>=2:break
        else:
            stop=False
            for entry in load(out/'INPUTS.json'):
                trial=Trial(entry['task'],**trial_parameters(c,entry['task_index']))
                try:
                    while (req:=trial.next_request()) is not None:
                        remaining=c['wall_seconds']-(time.monotonic()-started)
                        if remaining<=0:stop=True;break
                        response=backend.respond(req,remaining)
                        record=trial.submit(req['request_id'],**response,source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
                        save(dict(task_index=entry['task_index'],backend_status=response['status'],**record))
                        write(out/'trials'/f'{entry["task_index"]:03d}.json',trial.export())
                        if record['status']!='OK':stop=True;break
                finally:
                    traces.append(trial.export());write(out/'trials'/f'{entry["task_index"]:03d}.json',trial.export())
                if stop:break
    except Exception as exc:
        fatal=type(exc).__name__+':'+str(exc)
        raise
    finally:
        expected=16 if mode=='v' else 312
        result=dict(mode=mode,n_expected_requests=expected,n_generated=len(rows),n_ok=sum(r['status']=='OK' for r in rows),fatal=fatal,elapsed_seconds=time.monotonic()-started,n_expected_tasks=8 if mode=='v' else 6,n_complete_tasks=None if mode=='v' else sum(t['complete'] for t in traces),unknown_outputs=sum(r['stage']!='work' and r['raw_output'].strip().lower()=='unknown' for r in rows),primary_enabled=False,verdict='PASS_TECHNICAL_ONLY' if not fatal and len(rows)==expected and all(r['status']=='OK' for r in rows) else 'REVISE',original_scores_unchanged=sha(OLD/'scores.json')==f['files'][str(OLD/'scores.json')])
        write(out/'RESULTS.json',result);print(json.dumps(result),flush=True)
        if mode=='v' and rows:
            with (ROOT/'data/expert-training-20261030-v1/validation.targets.jsonl').open() as stream:targets={r['id']:r for r in [json.loads(next(stream)) for _ in range(8)]}
            scored=[dict(task_id=r['request_id'].rsplit('|',1)[0],actor=r['actor'],status=r['status'],metrics=answer_score(r['raw_output'],targets[r['request_id'].rsplit('|',1)[0]]) if r['status']=='OK' else None) for r in rows]
            write(out/'scores.json',dict(scope='V8_DEVELOPMENT_MIGRATION_NOT_INDEPENDENT_QUALIFICATION',primary_enabled=False,records=scored))
        if mode=='team' and traces:
            _,groups,targets=development_data(32,targets=True);ids=[e['task']['id'] for e in load(out/'INPUTS.json')]
            score=summarize(traces,{i:targets[i] for i in ids},ids,{i:groups[i] for i in ids})
            score.update(primary_enabled=False,scope='HISTORICAL_FAILURE_SELECTED_TECHNICAL_NOT_POPULATION_ACCURACY')
            for r in score['reports']:r['primary_enabled']=False
            write(out/'scores.json',score)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['snapshot','preflight','prepare-v','prepare-team','run-v','run-team']);a=p.parse_args()
    if a.command=='snapshot':snapshot()
    elif a.command=='preflight':preflight()
    elif a.command.startswith('prepare-'):prepare(a.command.split('-',1)[1])
    else:run(a.command.split('-',1)[1])
