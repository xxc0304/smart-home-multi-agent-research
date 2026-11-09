"""Frozen 2->8->32 supervisor. Normal runtime gates and immutable inheritance."""
import argparse,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
os.chdir(ROOT) # Cached C adapter paths are relative to the project root.
from b1_runtime import development_data,load_json,run_batch,score_batch,trial_parameters,validate_runtime
from b1_controls import Trial,replay
from b0_answers import write_json
HERE=Path(__file__).resolve().parent
OUT=ROOT/'runs/b1-dev32-20261105-v5'
TECH=ROOT/'runs/b1-concise-readable-tech6-20261105-v1'
SPEED=ROOT/'runs/b1-batch-speed-20261105-v1'
STAGES=((2,600,900),(8,1800,2100),(32,5400,5700))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ready(score,n):
    return score.get('n_expected')==n and score.get('n_complete')==n and score.get('status')=='COMPLETE' and score.get('primary_enabled') is True
def prepare():
    from b0_training import load_tokenizer
    speed=load_json(SPEED/'RESULTS.json')
    assert speed['selected_for_D32']=='EXISTING_SERIAL_V5','Candidate requires balanced executor validation; do not adopt automatically'
    oldfreeze=load_json(TECH/'FREEZE.json')
    for name in ('b1_runtime.py','b1_controls.py','b1_output_contract.py','b1_stop_status.py'):
        assert sha(ROOT/'tools'/name)==oldfreeze['files'][str(ROOT/'tools'/name)],'Previously tested serial runtime changed'
    for p in sorted((TECH/'trials').glob('*.json')):
        trace=load_json(p);assert replay(trace).export()==trace and trace['complete']
    c=load_json(TECH/'config.json');c.update(purpose='B1_V5_FIXED_D32_DEVELOPMENT',execution_engine='EXISTING_SERIAL_V5')
    audit=load_json(HERE/'QUALIFICATION_PATH_AUDIT.json')
    assert audit['all_original_qualification_hashes_match'] and audit['same_adapter_under_project_root']
    qualification=validate_runtime(c) # Existing cached C scores only; never launches C.
    assert qualification['qualification']=='SUPPORTED_TASK_ADVANTAGE'
    tasks,groups,_=development_data(32);tok=load_tokenizer(c)
    lengths=[];pressure=[]
    for i,t in enumerate(tasks):
        trial=Trial(t,**trial_parameters(c,i));r=trial.next_request()
        tokenlen=lambda r:len(tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']))
        lengths.append(tokenlen(r));assert lengths[-1]+128<=c['max_length']
        # Declared synthetic pressure only. Real historical six-task replay above.
        trial=Trial(t,**dict(trial_parameters(c,i),fixture=True))
        while (r:=trial.next_request()) is not None:
            pressure.append(tokenlen(r)+r['max_new_tokens'])
            assert pressure[-1]<=c['max_length'],'pressure_context_overlength'
            trial.submit(r['request_id'],'word '*120 if r['stage']=='work' else 'Unknown',source_kind='SYNTHETIC_PRESSURE_NOT_MODEL_EVIDENCE')
    assert not ready(load_json(ROOT/'runs/b1-dev32-final-20261104-v2/scores.json'),32)
    assert not ready(load_json(TECH/'scores.json'),2)
    OUT.mkdir(parents=True,exist_ok=False)
    write_json(OUT/'INPUTS.json',dict(tasks=tasks,groups=groups))
    for n,soft,hard in STAGES:write_json(OUT/f'config{n}.json',dict(c,wall_seconds=soft))
    write_json(OUT/'PREFLIGHT.json',dict(science='PASS',engineering='PASS',serial_sources_match_prior35_tests=True,real_V5_six_traces_replay=True,old_incomplete_and_nonprefix_scores_rejected=True,n=32,expected_new_generations=1664,max_initial_tokens=max(lengths),max_synthetic_pressure_context_plus_output=max(pressure),pressure_is_synthetic_not_model_evidence=True,qualification=qualification,chosen_engine='EXISTING_SERIAL_V5',stages=STAGES,total_hard_seconds=8400))
    paths=[Path(__file__),HERE/'EXPERIMENT_REVIEW.md',HERE/'QUALIFICATION_PATH_AUDIT.json',OUT/'INPUTS.json',OUT/'PREFLIGHT.json',SPEED/'RESULTS.json',TECH/'scores.json',ROOT/'runs/b1-dev32-final-20261104-v2/scores.json']
    paths += [OUT/f'config{n}.json' for n,_,_ in STAGES]
    paths += [ROOT/'tools'/name for name in ('b1_runtime.py','b1_controls.py','b1_output_contract.py','b1_stop_status.py','b0_answers.py','b0_training.py','expert_mechanism_protocol.py')]
    paths += [Path(c[k]) for k in ('baseline_C_score','expert_C_score')]
    paths += [ROOT/'runs/b1-concise-V8-20261105-v1'/n for n in ('RESULTS.json','scores.json','INPUTS.json')]
    paths += [p for p in Path(c['adapter_path']).iterdir() if p.is_file()]
    paths += list((ROOT/'research/musique-data-preparation-20261030/official_scorer/metrics').glob('*.py'))
    paths += [ROOT/'data/external/musique-v1.0-20261030'/n for n in ('inputs/D_development.jsonl','scoring/D_development.jsonl','corpus_index.jsonl')]
    paths += [ROOT/'research/musique-data-preparation-20261030/SPLIT_MANIFEST.json',ROOT/'implement-stage/expert-answer-only-20261101/C_GROUPS.json']
    write_json(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in paths},engine='EXISTING_SERIAL_V5',new_generations_max=1664,hard_seconds=8400))
    print(json.dumps(load_json(OUT/'PREFLIGHT.json')))
def stage(n):
    c=load_json(OUT/f'config{n}.json');tasks,groups,_=development_data(n)
    frozen=load_json(OUT/'INPUTS.json')
    assert tasks==frozen['tasks'][:n] and groups=={t['id']:frozen['groups'][t['id']] for t in tasks}
    prior=None if n==2 else OUT/('stage2' if n==8 else 'stage8')
    output=OUT/f'stage{n}'
    try:run_batch(c,tasks,groups,output,resume_from=prior)
    finally:
        if (output/'manifest.json').exists():score_batch(output)
def finalize(status,error,started):
    phases={}
    for n,_,_ in STAGES:
        folder=OUT/f'stage{n}'
        if (folder/'scores.json').exists():
            score=load_json(folder/'scores.json');exe=load_json(folder/'execution.json') if (folder/'execution.json').exists() else None
            phases[n]=dict(n_expected=n,n_complete=score['n_complete'],status=score['status'],execution=exe)
    result=dict(status=status,error=error,elapsed_seconds=time.monotonic()-started,stages=phases,total_new_requests=sum((v['execution'] or {}).get('new_backend_requests',0) for v in phases.values()),scientific_scope='DEVELOPMENT_NOT_INDEPENDENT_CONFIRMATION')
    write_json(OUT/'PIPELINE_RESULT.json',result)
    entry=f"## 2026-11-05 完整V5 D32监督执行：{status}\n\n见runs/b1-dev32-20261105-v5/PIPELINE_RESULT.json。阶段完成数{ {k:v['n_complete'] for k,v in phases.items()} }，新请求{result['total_new_requests']}，错误{error}。原串行V5，固定2→8→32，旧批与技术题不拼接；本批为开发诊断，非独立确认。详细scores/原响应留存，无自动新训练/C-H/更大批。助手自审none/provisional。\n\n"
    (OUT/'FINAL_STAGE_ENTRY.md').write_text(entry)
    for name in ('handoff.md','CURRENT_STATE.md','experiment/results.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
        p=ROOT/name;p.write_text(entry+p.read_text())
    print(json.dumps(result),flush=True)
def supervise():
    freeze=load_json(OUT/'FREEZE.json');approval=load_json(OUT/'APPROVAL.json')
    assert all(sha(p)==h for p,h in freeze['files'].items())
    assert approval['verdict']=='RUN_ALLOWED' and approval['freeze_sha256']==sha(OUT/'FREEZE.json')
    (OUT/'LAUNCHED').touch(exist_ok=False)
    started=time.monotonic();status='RUNNING';error=None;child=None
    def interrupted(*_):raise KeyboardInterrupt('supervisor_hard_timeout_or_interrupt')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        for n,soft,hard in STAGES:
            assert all(sha(p)==h for p,h in freeze['files'].items()),'frozen_source_changed'
            if n!=2:
                previous=2 if n==8 else 8
                assert ready(load_json(OUT/f'stage{previous}/scores.json'),previous),'incomplete_stage_no_continuation'
            phase=OUT/f'phase{n}';phase.mkdir(exist_ok=False)
            review=dict(science='PASS',engineering='PASS',verdict='RUN_ALLOWED',reviewer='assistant',independence='none/provisional',freeze_sha256=sha(OUT/'FREEZE.json'),n_expected=n,new_items=2 if n==2 else 6 if n==8 else 24,soft_seconds=soft,hard_seconds=hard,complete_prior_stage_checked=True)
            write_json(phase/'APPROVAL.json',review)
            (phase/'EXPERIMENT_REVIEW.md').write_text(f"# V5 D{n}当批复核\n\n科学/工程PASS，助手自审none/provisional。固定输入/代码/配置以总FREEZE绑定；上一阶段完整门槛通过，原运行器再次检查配置/字节继承/前缀。新题数{review['new_items']}，软{soft}/硬{hard}秒，READABLE V5不变。RUN_ALLOWED，失败不进入下一阶段。\n")
            write_json(OUT/'STATUS.json',dict(status='RUNNING',stage=n,started_unix=time.time(),elapsed_seconds=time.monotonic()-started))
            with (phase/'run.log').open('x') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__)),'stage','--n',str(n)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                write_json(phase/'PROCESS.json',dict(pid=child.pid))
                try:rc=child.wait(timeout=hard)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    try:child.wait(timeout=15)
                    except subprocess.TimeoutExpired:child.kill();child.wait()
                    raise RuntimeError(f'phase{n}_hard_timeout')
            assert rc==0,f'phase{n}_exit_{rc}'
            score=load_json(OUT/f'stage{n}/scores.json')
            traces=[load_json(p) for p in sorted((OUT/f'stage{n}/trials').glob('*.json'))]
            warnings=sum(bool((r.get('usage') or {}).get('format_warning')) for t in traces for r in t['records'])
            post=dict(verdict='PASS' if ready(score,n) else 'REVISE',reviewer='assistant',independence='none/provisional',scope='DEVELOPMENT_COMPLETE_PREFIX_NOT_CAUSAL_CONFIRMATION',n_expected=n,n_complete=score['n_complete'],format_warnings=warnings,primary_enabled=score['primary_enabled'],next_stage_allowed=ready(score,n) and n!=32,execution=load_json(OUT/f'stage{n}/execution.json'))
            write_json(phase/'POST_RUN_REVIEW.json',post)
            assert ready(score,n),f'phase{n}_incomplete'
            if n!=2:
                previous=2 if n==8 else 8
                for i in range(previous):assert (OUT/f'stage{n}/trials/{i:03d}.json').read_bytes()==(OUT/f'stage{previous}/trials/{i:03d}.json').read_bytes()
            print(json.dumps(dict(stage=n,n_complete=score['n_complete'],elapsed=time.monotonic()-started)),flush=True)
        status='COMPLETE'
    except BaseException as exc:
        status='STOPPED';error=type(exc).__name__+':'+str(exc)
        if child and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=15)
            except subprocess.TimeoutExpired:child.kill();child.wait()
    finally:
        write_json(OUT/'STATUS.json',dict(status=status,error=error))
        finalize(status,error,started)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','supervise','stage']);p.add_argument('--n',type=int,choices=[2,8,32]);a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='supervise':supervise()
    else:stage(a.n)
