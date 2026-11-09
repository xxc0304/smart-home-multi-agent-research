"""Bounded technical sampling probe. Reuses actual backend; no training/C/H reads."""
import argparse, hashlib, inspect, json, math, sys, time
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import LocalBackend,load_json,prefix_rows
from b1_controls import replay
from b0_answers import write_json
from prepare_answer_only_expert import SYSTEM
from metrics.answer import normalize_answer
HERE=Path(__file__).resolve().parent
OLD=ROOT/'runs/b1-dev32-final-20261104-v2'
OUT=ROOT/'runs/b1-sampling-check-20261105-v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def offline():
    traces=[load_json(p) for p in sorted((OLD/'trials').glob('*.json'))]
    scores=load_json(OLD/'scores.json');complete=[r for r in scores['reports'] if r['complete']]
    for t in traces:
        replay(t)
        for r in t['records']:
            stage=r['stage'];stage_seed=0 if stage=='initial' else 1000+r['round']*100 if stage=='work' else 2000
            expected=t['config']['seed']+t['config']['task_index']*10000+stage_seed+int(r['actor'][1:])-1
            assert r['seed']==expected
            if r['status']=='OK':assert r['usage']['adapter_enabled']==(r['actor']=='M1')
    selected=[t for t in traces if t['complete']]
    same=sum(len({t['initials'][a] for a in ('M2','M3','M4')})==1 for t in selected)
    pairs={}
    for a,b in [('M2','M3'),('M2','M4'),('M3','M4')]:
        x=[r['initial']['members'][a]['em'] for r in complete];y=[r['initial']['members'][b]['em'] for r in complete]
        mx=sum(x)/len(x);my=sum(y)/len(y)
        den=math.sqrt(sum((v-mx)**2 for v in x)*sum((v-my)**2 for v in y))
        pairs[a+'_'+b]=dict(n=28,raw_equal=sum(t['initials'][a]==t['initials'][b] for t in selected),normalized_equal=sum(normalize_answer(t['initials'][a])==normalize_answer(t['initials'][b]) for t in selected),both_wrong=sum(u==v==0 for u,v in zip(x,y)),both_correct=sum(u==v==1 for u,v in zip(x,y)),correctness_phi=sum((u-mx)*(v-my) for u,v in zip(x,y))/den if den else None)
    result=dict(traces=len(traces),actual_records=sum(len(t['records']) for t in traces),replay_seed_and_declared_adapter_checks='PASS',complete_n=len(selected),ordinary_all3_raw_equal=same,pairs=pairs,seed_note='arm matched by design; different ordinary initial seeds, identical initial payloads',past_rng_not_logged=True)
    write_json(HERE/'OFFLINE_AUDIT.json',result);return result
def prepare():
    from b0_training import load_tokenizer
    rejected=ROOT/'runs/b1-sampling-check-20261105-v1'
    if rejected.exists():
        assert not (rejected/'LAUNCHED').exists()
        write_json(rejected/'REJECTED.json',dict(verdict='DO_NOT_RUN',reason='Tokenizer mapping length was not token count; superseded by v2',generations=0))
    audit=offline();assert audit['complete_n']==28 and audit['ordinary_all3_raw_equal']==23
    cfg=load_json(OLD/'manifest.json')['config'];cfg['wall_seconds']=600
    origin=load_json(Path(cfg['adapter_path'])/'b0_origin.json')
    assert origin['model_path']==cfg['model_path'] and origin['revision']==cfg['revision'] and not origin['fixture']
    vpath=ROOT/'data/expert-training-20261030-v1/validation.inputs.jsonl'
    with vpath.open() as f:tasks=[json.loads(next(f)) for _ in range(2)]
    tok=load_tokenizer(cfg);requests=[]
    for task in tasks:
        payload=dict(system=SYSTEM,user='TASK_DATA\n'+json.dumps(dict(question=task['question'],paragraphs=task['paragraphs']),ensure_ascii=False,indent=2)+cfg['answer_suffix'])
        ids=tok.apply_chat_template([dict(role=k,content=payload[k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
        assert isinstance(ids,list) and len(ids)>20 and all(isinstance(x,int) for x in ids)
        assert len(ids)+256<=cfg['max_length']
        for seed in (20261102,20261103,20261104):
            for repeat,actor in ((0,'M2'),(0,'M1'),(1,'M2'),(1,'M1')):
                requests.append(dict(request_id=f'{task["id"]}|{actor}|{seed}|{repeat}',task_id=task['id'],actor=actor,stage='initial',arm=None,round=0,seed=seed,repeat=repeat,max_new_tokens=256,payload=payload,input_tokens=len(ids)))
    OUT.mkdir(parents=True,exist_ok=False)
    write_json(OUT/'REQUESTS.json',requests);write_json(OUT/'config.json',cfg)
    write_json(OUT/'PREFLIGHT.json',dict(science='PASS',engineering='PASS',requests=24,max_input_tokens=max(r['input_tokens'] for r in requests),C_H_bodies_read=False,offline_audit=audit))
    files=[Path(__file__),HERE/'EXPERIMENT_REVIEW.md',OUT/'REQUESTS.json',OUT/'config.json',OUT/'PREFLIGHT.json',ROOT/'tools/b1_runtime.py',ROOT/'tools/b1_controls.py',ROOT/'tools/b1_stop_status.py',ROOT/'tools/b0_training.py',OLD/'manifest.json',OLD/'scores.json',OLD/'backend.json']
    write_json(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in files},requests_max=24,soft_seconds=600,hard_seconds=900))
    print(json.dumps(dict(prepared=True,freeze_sha256=sha(OUT/'FREEZE.json'),max_input_tokens=max(r['input_tokens'] for r in requests))))
def run():
    import torch
    from peft.tuners.lora.layer import LoraLayer
    freeze=load_json(OUT/'FREEZE.json');assert all(sha(p)==h for p,h in freeze['files'].items())
    approval=load_json(OUT/'APPROVAL.json');assert approval['verdict']=='RUN_ALLOWED' and approval['freeze_sha256']==sha(OUT/'FREEZE.json')
    (OUT/'LAUNCHED').touch(exist_ok=False)
    started=time.monotonic();rows=[];fatal=None
    def state():return dict(cpu=hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest(),cuda=hashlib.sha256(torch.cuda.get_rng_state().cpu().numpy().tobytes()).hexdigest())
    try:
        backend=LocalBackend(load_json(OUT/'config.json'))
        write_json(OUT/'BACKEND.json',dict(generation_config=backend.generation_config.to_dict(),multinomial_in_generate_source='torch.multinomial' in inspect.getsource(backend.model.base_model.model._sample)))
        for request in load_json(OUT/'REQUESTS.json'):
            remaining=600-(time.monotonic()-started)
            if remaining<=0:break
            details=dict(sampling_calls=0,samples=[],first_steps=[])
            original_multi=torch.multinomial;original_generate=backend.model.generate
            def observed_multinomial(probs,*args,**kwargs):
                details['sampling_calls']+=1
                if len(details['first_steps'])<4:
                    p=probs[0].detach().float();positive=p[p>0];v,k=torch.topk(p,5)
                    details['first_steps'].append(dict(rng=state(),top_ids=k.tolist(),top_probabilities=v.tolist(),entropy_nats=(-(positive*positive.log()).sum()).item()))
                result=original_multi(probs,*args,**kwargs);details['samples'].extend(result.detach().flatten().tolist());return result
            def observed_generate(*args,**kwargs):
                layers=[m for m in backend.model.modules() if isinstance(m,LoraLayer)]
                details['lora_layers']=len(layers);details['disabled_layers']=sum(bool(m.disable_adapters) for m in layers)
                assert layers and details['disabled_layers']==(0 if request['actor']=='M1' else len(layers))
                cfg=kwargs['generation_config'];details['effective_policy']={k:getattr(cfg,k) for k in ('do_sample','temperature','top_p','top_k')}
                assert details['effective_policy']==dict(do_sample=True,temperature=.7,top_p=.95,top_k=0)
                y=original_generate(*args,**kwargs);tail=y[0,kwargs['input_ids'].shape[-1]:].tolist();details['output_ids']=tail;return y
            try:
                torch.multinomial=observed_multinomial;backend.model.generate=observed_generate
                response=backend.respond(request,remaining)
            finally:
                torch.multinomial=original_multi;backend.model.generate=original_generate
            row=dict(request=request,response=response,instrumentation=details)
            rows.append(row)
            with (OUT/'responses.jsonl').open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
            print(json.dumps(dict(done=len(rows),request_id=request['request_id'],status=response['status'],sampling_calls=details['sampling_calls'])),flush=True)
            assert details['sampling_calls']>0 and details['samples']==details['output_ids']
            if sum(r['response']['status']!='OK' for r in rows)>=2:break
    except Exception as exc:
        fatal=type(exc).__name__+':'+str(exc)
        raise
    finally:
        comparisons=[]
        for r in rows:
            q=r['request']
            if q['repeat']!=1:continue
            a=next(x for x in rows if all(x['request'][k]==q[k] for k in ('task_id','actor','seed')) and x['request']['repeat']==0)
            af=a['instrumentation']['first_steps'];rf=r['instrumentation']['first_steps']
            comparisons.append(dict(task_id=q['task_id'],actor=q['actor'],seed=q['seed'],same_output_ids=a['instrumentation'].get('output_ids')==r['instrumentation'].get('output_ids'),same_first_rng=bool(af and rf and af[0]['rng']==rf[0]['rng'])))
        first_rng={r['request']['seed']:r['instrumentation']['first_steps'][0]['rng']['cuda'] for r in rows if r['instrumentation']['first_steps']}
        result=dict(n_expected=24,n_generated=len(rows),n_ok=sum(r['response']['status']=='OK' for r in rows),fatal=fatal,elapsed_seconds=time.monotonic()-started,repeats=comparisons,different_seed_rng_distinct=len(first_rng)==3 and len(set(first_rng.values()))==3,verdict='PASS_TECHNICAL_ONLY' if len(rows)==24 and not fatal and all(r['response']['status']=='OK' for r in rows) and len(first_rng)==3 and len(set(first_rng.values()))==3 and all(c['same_first_rng'] for c in comparisons) else 'REVISE',original_scores_unchanged=sha(OLD/'scores.json')==freeze['files'][str(OLD/'scores.json')])
        write_json(OUT/'RESULTS.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);a=p.parse_args();(prepare if a.command=='prepare' else run)()
