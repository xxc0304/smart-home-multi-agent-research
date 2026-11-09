"""B1 preflight and fixed V20 matched solo diagnostic. No training/C/H tasks."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from b0_answers import read_jsonl,write_json,answer_score
from b0_training import load_tokenizer
from b1_controls import Trial,replay,summarize
from b1_runtime import POLICY,LocalBackend,validate_runtime,development_data,load_json

HERE=Path(__file__).resolve().parent
OUT=ROOT/'runs/b1-preflight-v20-20261103-v1'
VINPUT=ROOT/'data/expert-training-20261030-v1/validation.inputs.jsonl'
VTARGET=ROOT/'data/expert-training-20261030-v1/validation.targets.jsonl'
CONFIG=ROOT/'config/b1_lab3090_timing2_20261103_v1.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prompt_ids(tok,request,config):
    return tok.apply_chat_template([dict(role=k,content=request['payload'][k]) for k in ('system','user')],
        tokenize=True,add_generation_prompt=True,return_dict=False,**config['template_kwargs'])


def check_freeze():
    freeze=load_json(OUT/'FREEZE.json')
    for p,digest in freeze['files'].items():
        if sha(p)!=digest:raise ValueError('frozen_file_changed:'+p)
    return freeze


def prepare():
    c=load_json(ROOT/'config/b0_C160_20261103.json')
    c.update(generation=deepcopy(POLICY),expert_actor='M1',
        adapter_path=str(ROOT/'runs/b0-first-run-20261103-v2/attempt1/adapter'),
        baseline_C_score=str(ROOT/'runs/b0-C160-20261103/C_B_score.json'),
        expert_C_score=str(ROOT/'runs/b0-C160-20261103/C_E_score.json'),
        qualification_answer_tokens=256,qualification_answer_suffix=c['evaluation_answer_suffix'],
        answer_tokens=64,work_tokens=512,max_length=16384,wall_seconds=1800,
        purpose='B1_two_item_development_timing',reviewed_for_run=True)
    c.pop('evaluation_answer_suffix') # The B1 prompts are separately checked below.
    qualification=validate_runtime(c)
    tasks=read_jsonl(VINPUT)[:20]
    assert len(tasks)==len({t['id'] for t in tasks})==20
    d_tasks,d_groups,_=development_data(2)
    tok=load_tokenizer(c)
    assert load_json(Path(c['model_path'])/'config.json')['max_position_embeddings']>=16384
    v_lengths=[]
    v_prompt_hashes=[]
    for t in tasks:
        r=Trial(t,expert_actor='M1').next_request()
        ids=prompt_ids(tok,r,c)
        assert len(ids)+64<=c['max_length']
        v_lengths.append(len(ids))
        v_prompt_hashes.append(hashlib.sha256(json.dumps(ids).encode()).hexdigest())
    # Replay genuine complete old answer strings as protocol carriers, not work-semantic evidence.
    old=read_jsonl(ROOT/'runs/baseline-health-v20-20261103-v1/NF4/responses.jsonl')
    carrier=Trial(tasks[0],expert_actor='M1',fixture=True)
    n=0
    while (r:=carrier.next_request()) is not None:
        carrier.submit(r['request_id'],old[n%20]['raw_output'])
        n+=1
    assert n==52 and replay(carrier.export()).complete
    # Full histories stress two declared D inputs, with escape-heavy synthetic occupancy.
    lengths=[]
    for t in d_tasks:
        trial=Trial(t,expert_actor='M1',fixture=True)
        while (r:=trial.next_request()) is not None:
            length=len(prompt_ids(tok,r,c))
            assert length+r['max_new_tokens']<=c['max_length'], 'stress_history_overlength'
            lengths.append(length)
            if r['stage']=='work':
                text=tok.decode(tok.encode('Reasoning from the supplied material. "Check" \\ scope\n'*512,
                    add_special_tokens=False)[:512],skip_special_tokens=True)
            else:text=tok.decode(tok.encode('Short answer candidate. '*128,add_special_tokens=False)[:64],skip_special_tokens=True)
            trial.submit(r['request_id'],text)
        assert replay(trial.export()).complete
    failure=Trial(tasks[0],expert_actor='M1',fixture=True)
    failure.submit(failure.next_request()['request_id'],'partial',status='OUTPUT_LIMIT')
    failure_summary=summarize([failure.export()],{tasks[0]['id']:dict(id=tasks[0]['id'],answer='fixture')},
        [tasks[0]['id']],{tasks[0]['id']:'fixture'},repeats=10)
    assert failure_summary['status']=='INCOMPLETE' and not failure_summary['primary_enabled']
    import torch
    free,total=torch.cuda.mem_get_info()
    assert free>=20*1024**3,'GPU_not_idle'
    OUT.mkdir(parents=True,exist_ok=False)
    write_json(CONFIG,c)
    write_json(OUT/'REAL_RESPONSE_CARRIER_REPLAY.json',carrier.export())
    write_json(OUT/'FAILURE_EXPORT_CHECK.json',failure_summary)
    paths=[Path(__file__).resolve(),HERE/'PLAN.md',CONFIG,VINPUT,VTARGET,
        ROOT/'tools/b1_controls.py',ROOT/'tools/b1_runtime.py',ROOT/'tools/b1_experiment.py',
        ROOT/'tools/b0_training.py',ROOT/'tools/b0_answers.py',ROOT/'tools/prepare_answer_only_expert.py',
        ROOT/'tools/expert_mechanism_protocol.py',ROOT/'tools/prepare_expert_training.py',
        Path(c['baseline_C_score']),Path(c['expert_C_score']),
        ROOT/'implement-stage/expert-answer-only-20261101/C_GROUPS.json',
        ROOT/'research/musique-data-preparation-20261030/SPLIT_MANIFEST.json',
        ROOT/'data/external/musique-v1.0-20261030/inputs/D_development.jsonl',
        ROOT/'data/external/musique-v1.0-20261030/corpus_index.jsonl']
    # Bind every adapter tensor/config/origin; no other user's files or secrets.
    paths+=list(Path(c['adapter_path']).glob('*'))
    paths=[p for p in paths if p.is_file()]
    freeze=dict(files={str(p):sha(p) for p in paths},V_ids=[t['id'] for t in tasks],
        V_prompt_token_sha256=v_prompt_hashes,D_ids=[t['id'] for t in d_tasks],
        no_C_H_tasks_read=True,solo_generations_max=40,team_generations_max=104,
        config_path=str(CONFIG))
    write_json(OUT/'FREEZE.json',freeze)
    report=dict(status='PREPARED_NOT_GENERATED',qualification=qualification['qualification'],
        qualified_C_cap=256,B1_answer_cap=64,matched_V_n=20,D_n=2,
        max_V_input_tokens=max(v_lengths),max_synthetic_full_history_tokens=max(lengths),
        max_length=c['max_length'],synthetic_history_is_not_semantic_evidence=True,
        genuine_answer_carrier_replay=52,failure_export='PASS',GPU_free_bytes=free,
        freeze_sha256=sha(OUT/'FREEZE.json'))
    write_json(OUT/'PREFLIGHT.json',report)
    print(json.dumps(report),flush=True)


def solo():
    freeze=check_freeze()
    approve=load_json(OUT/'SOLO_APPROVAL.json')
    assert approve['freeze_sha256']==sha(OUT/'FREEZE.json') and approve['verdict']=='RUN_ALLOWED'
    dest=OUT/'solo'
    dest.mkdir(exist_ok=False)
    c=load_json(CONFIG)
    c['wall_seconds']=600
    tasks=read_jsonl(VINPUT)[:20]
    assert [t['id'] for t in tasks]==freeze['V_ids']
    path=dest/'responses.jsonl';path.touch()
    started=time.monotonic();fatal=None;backend=None
    try:
        backend=LocalBackend(c)
        import torch
        first=Trial(tasks[0],expert_actor='M1').next_request()
        x=torch.tensor([prompt_ids(backend.tokenizer,first,c)],device=c['device'])
        with torch.inference_mode():
            active=backend.model(input_ids=x).logits[0,-1].float().cpu()
            with backend.model.disable_adapter():
                disabled=backend.model(input_ids=x).logits[0,-1].float().cpu()
            restored=backend.model(input_ids=x).logits[0,-1].float().cpu()
        route=dict(active_disabled_max_logit_delta=float((active-disabled).abs().max()),
            active_restored_max_logit_delta=float((active-restored).abs().max()))
        assert route['active_disabled_max_logit_delta']>0
        assert torch.allclose(active,restored,rtol=1e-5,atol=1e-5)
        write_json(dest/'ADAPTER_ROUTE_WITNESS.json',route)
        del active,disabled,restored,x
        for i,t in enumerate(tasks):
            request=Trial(t,expert_actor='M1').next_request()
            assert hashlib.sha256(json.dumps(prompt_ids(backend.tokenizer,request,c)).encode()).hexdigest()==freeze['V_prompt_token_sha256'][i]
            for condition,actor in (('B','M2'),('E','M1')):
                remaining=600-(time.monotonic()-started)
                if remaining<=0:raise TimeoutError('solo_wall_budget')
                req=dict(request,actor=actor) # Same payload and seed; actor only selects adapter.
                response=backend.respond(req,remaining)
                record=dict(id=t['id'],condition=condition,request=req,**response)
                with path.open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
                print('V_SOLO',i+1,condition,response['status'],flush=True)
                if response['status']!='OK':raise RuntimeError('solo_incomplete_stop_no_retry')
    except Exception as exc:
        fatal=type(exc).__name__+':'+str(exc)
        raise
    finally:
        rows=read_jsonl(path)
        targets={r['id']:r for r in read_jsonl(VTARGET)}
        scored=[dict(r,metrics=answer_score(r['raw_output'],targets[r['id']]) if r['status']=='OK' else None) for r in rows]
        complete=fatal is None and len(scored)==40 and all(r['metrics'] is not None for r in scored)
        result=dict(status='COMPLETE' if complete else 'INCOMPLETE',fatal_error=fatal,
            planned_generations=40,actual_generations=len(rows),conditions={},
            evidence='V_DEVELOPMENT_TEAM_PROMPT_TRANSFER_NOT_C_QUALIFICATION',
            elapsed_seconds=time.monotonic()-started)
        if backend is not None:
            result['generation_config']=backend.generation_config.to_dict()
            result['peak_allocated_bytes']=torch.cuda.max_memory_allocated()
            result['peak_reserved_bytes']=torch.cuda.max_memory_reserved()
        for arm in ('B','E'):
            records=[r for r in scored if r['condition']==arm]
            result['conditions'][arm]=dict(n_recorded=len(records),n_valid=sum(r['metrics'] is not None for r in records),
                metrics={k:sum(r['metrics'][k] for r in records)/20 for k in ('em','f1')} if complete else None)
        if complete:
            result['em_difference']=result['conditions']['E']['metrics']['em']-result['conditions']['B']['metrics']['em']
        write_json(dest/'SCORED.json',dict(summary=result,records=scored))
        write_json(dest/'RESULTS.json',result)
        print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['prepare','solo'])
    args=parser.parse_args()
    (prepare if args.command=='prepare' else solo)()
