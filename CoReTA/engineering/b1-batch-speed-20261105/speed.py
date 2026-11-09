"""One bounded paired-batch probe: 4 fixed requests x 2 engines x 2 repeats."""
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import LocalBackend,load_json
from b1_batch_backend import PairedBackend
from b1_controls import replay
from b0_answers import write_json
HERE=Path(__file__).resolve().parent
OLD=ROOT/'runs/b1-concise-readable-tech6-20261105-v1'
OUT=ROOT/'runs/b1-batch-speed-20261105-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare():
    from b0_training import load_tokenizer
    t=load_json(OLD/'trials/000.json');assert replay(t).export()==t
    req=[]
    for actor in ('M2','M1'):
        for arm in ('A','B'):
            r=next(r for r in t['records'] if r['stage']=='work' and r['round']==1 and r['actor']==actor and r['arm']==arm)
            req.append({k:r[k] for k in ('request_id','stage','round','actor','arm','seed','max_new_tokens','payload')})
    c=load_json(OLD/'config.json');c['wall_seconds']=900;tok=load_tokenizer(c)
    lengths=[]
    for r in req:
        ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
        assert isinstance(ids,list) and len(ids)+r['max_new_tokens']<=c['max_length'];lengths.append(len(ids))
    # These guard checks run without allocating/loading a model.
    stub=PairedBackend.__new__(PairedBackend);stub.config=c
    for bad in ([req[0],req[2]],[dict(req[0],max_new_tokens=128),req[1]]):
        try:stub.respond_many(bad,10)
        except ValueError:pass
        else:raise AssertionError('invalid_batch_not_rejected')
    OUT.mkdir(parents=True,exist_ok=False)
    write_json(OUT/'REQUESTS.json',req);write_json(OUT/'config.json',c)
    write_json(OUT/'PREFLIGHT.json',dict(science='PASS',engineering='PASS',n_requests=16,input_tokens=lengths,actual_prior_trace_replayed=True,CUDA_probe_pending=True))
    paths=[Path(__file__),HERE/'EXPERIMENT_REVIEW.md',OUT/'REQUESTS.json',OUT/'config.json',OUT/'PREFLIGHT.json',ROOT/'tools/b1_batch_backend.py',ROOT/'tools/b1_runtime.py',ROOT/'tools/b1_controls.py',ROOT/'tools/b1_output_contract.py',ROOT/'tools/b1_stop_status.py',OLD/'scores.json',ROOT/'runs/b1-dev32-final-20261104-v2/scores.json']
    write_json(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in paths}))
    print(json.dumps(dict(prepared=True,lengths=lengths,freeze_sha256=sha(OUT/'FREEZE.json'))))
def run():
    import torch
    from peft.tuners.lora.layer import LoraLayer
    f=load_json(OUT/'FREEZE.json');a=load_json(OUT/'APPROVAL.json')
    assert all(sha(p)==h for p,h in f['files'].items())
    assert a['verdict']=='RUN_ALLOWED' and a['freeze_sha256']==sha(OUT/'FREEZE.json')
    (OUT/'LAUNCHED').touch(exist_ok=False)
    started=time.monotonic();rows=[];timings=[];fatal=None
    try:
        backend=PairedBackend(load_json(OUT/'config.json'));load_seconds=time.monotonic()-started
        requests=load_json(OUT/'REQUESTS.json')
        for repeat,order in enumerate((('serial','batch2'),('batch2','serial'))):
            for engine in order:
                torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();begin=time.monotonic()
                for start in (range(4) if engine=='serial' else (0,2)):
                    rem=900-(time.monotonic()-started);assert rem>0,'soft_budget'
                    selected=requests[start:start+(1 if engine=='serial' else 2)]
                    observed={};original_generate=backend.model.generate
                    def capture(*args,**kwargs):
                        layers=[m for m in backend.model.modules() if isinstance(m,LoraLayer)]
                        disabled=sum(bool(m.disable_adapters) for m in layers)
                        assert layers and disabled==(0 if selected[0]['actor']=='M1' else len(layers))
                        observed.update(lora_layers=len(layers),disabled_layers=disabled)
                        y=original_generate(*args,**kwargs)
                        observed['output_ids']=y[0,kwargs['input_ids'].shape[-1]:].tolist();return y
                    try:
                        if engine=='serial':backend.model.generate=capture
                        responses=backend.respond_many(selected,rem)
                    finally:backend.model.generate=original_generate
                    if engine=='serial':responses[0]['usage'].update(observed)
                    for request,response in zip(selected,responses):
                        # Validate actual adapter flags for the legacy serial path too.
                        row=dict(engine=engine,repeat=repeat,request=request,**response)
                        rows.append(row)
                        with (OUT/'responses.jsonl').open('a') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
                        print(json.dumps(dict(done=len(rows),engine=engine,status=row['status'])),flush=True)
                        assert response['status']=='OK','non_eos_response'
                torch.cuda.synchronize()
                timings.append(dict(repeat=repeat,engine=engine,seconds=time.monotonic()-begin,output_tokens=sum(r['usage']['output_tokens'] for r in rows if r['repeat']==repeat and r['engine']==engine),peak_bytes=torch.cuda.max_memory_allocated()))
                write_json(OUT/'TIMINGS.json',timings)
    except Exception as exc:
        fatal=type(exc).__name__+':'+str(exc);raise
    finally:
        cross=[];stable=[]
        for i in range(4):
            rid=requests[i]['request_id'] if 'requests' in locals() else None
            find=lambda e,r:next((x for x in rows if x['engine']==e and x['repeat']==r and x['request']['request_id']==rid),None)
            for rep in (0,1):
                x,y=find('serial',rep),find('batch2',rep)
                if x and y:cross.append(dict(request_id=rid,repeat=rep,same_text=x['raw_output']==y['raw_output'],same_output_ids=x['usage']['output_ids']==y['usage']['output_ids']))
            for engine in ('serial','batch2'):
                x,y=find(engine,0),find(engine,1)
                if x and y:stable.append(dict(request_id=rid,engine=engine,same_text=x['raw_output']==y['raw_output'],same_output_ids=x['usage']['output_ids']==y['usage']['output_ids']))
        serial=sum(x['seconds'] for x in timings if x['engine']=='serial');batch=sum(x['seconds'] for x in timings if x['engine']=='batch2')
        speedup=serial/batch if batch else None
        candidate=(len(rows)==16 and not fatal and len(cross)==8 and len(stable)==8 and all(x['same_text'] and x['same_output_ids'] for x in cross+stable) and speedup is not None and speedup>=1.15)
        result=dict(n_expected=16,n_generated=len(rows),fatal=fatal,elapsed_seconds=time.monotonic()-started,load_seconds=locals().get('load_seconds'),timings=timings,speedup=speedup,cross=cross,within_engine_repeats=stable,candidate_for_integration=candidate,selected_for_D32='PENDING_BALANCED_EXECUTOR_VALIDATION' if candidate else 'EXISTING_SERIAL_V5',scope='SMALL_TECHNICAL_SPEED_PROBE_NOT_QUALITY_EVIDENCE')
        write_json(OUT/'RESULTS.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);a=p.parse_args();(prepare if a.command=='prepare' else run)()
