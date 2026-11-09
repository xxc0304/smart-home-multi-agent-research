"""One finite, frozen final-answer adapter diagnostic; no training or team replay."""
import argparse,copy,hashlib,json,os,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
os.chdir(ROOT)  # C qualification manifest stores its adapter path relative to project.
sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import validate_runtime
from b1_multi_backend import MultiBackend
from b0_answers import answer_score
OUT=ROOT/'runs/b1-terminal-adapter-20261107-v1'
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def atomic(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp')
    with q.open('w',encoding='utf-8') as f:
        f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    os.replace(q,p)

def append(p,v):
    with Path(p).open('a',encoding='utf-8') as f:
        f.write(json.dumps(v,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

def decode(payload):
    t=payload['user'];return json.loads(t[t.index('{'):t.rindex('}')+1])

def validate_pack(pack,source_check=True):
    cases=pack['cases'];ss=pack['schedule']
    assert len(cases)==12 and len({p['sourceGroup'] for p in cases})==12
    assert sum(p['stratum']=='original_private_terminal_failure' for p in cases)==6
    assert len(ss)==48 and len({r['id'] for r in ss})==48
    for p in cases:
        assert p['sourceArm'] in ('A','C')
        d=decode(p['request']['payload']);assert d['own_actor']=='M1'
        assert len(d['history'])==3 and all(h['sender']=='M1' for h in d['history'])
        assert d['history'][-1]['phase']=='work' and d['history'][-1]['round']==2
        expected={'question','paragraphs','own_actor','history','work_visibility'}
        if p['sourceArm']=='C':expected.add('team_information')
        assert set(d)==expected
        assert hashlib.sha256(d['history'][-1]['text'].encode()).hexdigest()==p['workSHA256']
        assert p['request']['max_new_tokens']==256
        if source_check:
            assert sha(ROOT/p['sourcePath'])==p['sourceSHA256']
            trial=load(ROOT/p['sourcePath']);r=next(r for r in trial['branches'][p['sourceArm']]['records'] if r['request_id']==p['sourceFinalRequestId'])
            assert p['request']=={k:r[k] for k in ('payload','seed','max_new_tokens')}
        for rep in (0,1):
            pair=[r for r in ss if r['case_id']==p['id'] and r['rep']==rep]
            assert len(pair)==2 and {r['adapter'] for r in pair}=={'on','off'}
            assert pair[0]['payload']==pair[1]['payload']==p['request']['payload']
            assert pair[0]['seed']==pair[1]['seed']==p['request']['seed']+rep*100000000
            assert all(r['max_new_tokens']==256 and r['actor']==('M1' if r['adapter']=='on' else 'M2') for r in pair)
    return cases

def execute(pack,backend,directory):
    directory=Path(directory);started=time.monotonic();done=[];failure=None
    for req in pack['schedule']:
        append(directory/'ATTEMPTS.jsonl',dict(event='START',request=req))
        try:
            # Finite output cap48x256, no wall-clock killer or generation retry.
            res=backend.respond_many([req],1e12)[0]
            if res['status'] not in ('OK','OUTPUT_LIMIT'):raise RuntimeError('Unexpected backend status '+res['status'])
            u=res['usage'];expected=req['adapter']=='on'
            assert u['adapter_enabled']==expected and u['lora_layers']==252
            assert u['disabled_layers']==(0 if expected else 252) and u['batch_size']==1
            record=dict(request=req,response=res)
            append(directory/'responses.jsonl',record);done.append(record)
            append(directory/'ATTEMPTS.jsonl',dict(event='RETURN',request_id=req['id'],status=res['status']))
        except Exception as exc:
            failure=dict(request_id=req['id'],type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
            append(directory/'ATTEMPTS.jsonl',dict(event='SYSTEM_ERROR',**failure))
        status=dict(status='SYSTEM_ERROR' if failure else 'RUNNING',completed=len(done),planned=48,ok=sum(r['response']['status']=='OK' for r in done),output_limit=sum(r['response']['status']=='OUTPUT_LIMIT' for r in done),seconds=time.monotonic()-started,failure=failure)
        atomic(directory/'STATUS.json',status)
        if failure:break
    status.update(status='SYSTEM_ERROR' if failure else 'COMPLETE',seconds=time.monotonic()-started,output_tokens=sum(r['response']['usage']['output_tokens'] for r in done))
    atomic(directory/'STATUS.json',status)
    return done,status

def score_records(pack,records,labels):
    byid={r['request']['id']:r for r in records};scored=[]
    for req in pack['schedule']:
        rec=byid.get(req['id']);p=next(p for p in pack['cases'] if p['id']==req['case_id']);lab=labels[p['id']]
        ans=rec['response']['raw_output'] if rec else None
        ok=bool(rec and rec['response']['status']=='OK')
        scored.append(dict(id=req['id'],case_id=p['id'],key=p['key'],stratum=p['stratum'],adapter=req['adapter'],rep=req['rep'],status=rec['response']['status'] if rec else 'NOT_COMPLETED',answer=ans,score=answer_score(ans,lab['target']) if ok else None,originalFinalMatch=(ans==lab['originalFinal']) if ok else None))
    return dict(scope='PURPOSEFUL_FIXED_PREFIX_LOCAL_ADAPTER_EFFECT_NOT_PREVALENCE_OR_TEAM_GAIN',rows=scored,new_model_calls=len(records))

def selftest():
    import tempfile
    pack=load(HERE/'DIAGNOSTIC_INPUTS.json');labels=load(HERE/'DIAGNOSTIC_LABELS.json')['labels'];validate_pack(pack)
    class Fixture:
        def __init__(self,limit=None,crash=None):self.n=0;self.limit=limit;self.crash=crash
        def respond_many(self,rs,remaining):
            r=rs[0];self.n+=1
            if self.n==self.crash:raise RuntimeError('injected_runtime_failure')
            return [dict(raw_output=labels[r['case_id']]['originalFinal'],status='OUTPUT_LIMIT' if self.n==self.limit else 'OK',usage=dict(adapter_enabled=r['adapter']=='on',lora_layers=252,disabled_layers=0 if r['adapter']=='on' else 252,batch_size=1,output_tokens=2))]
    checks=[]
    with tempfile.TemporaryDirectory() as temp:
        d=Path(temp);rs,status=execute(pack,Fixture(),d);s=score_records(pack,rs,labels)
        assert len(rs)==48 and status['status']=='COMPLETE' and all(r['originalFinalMatch'] for r in s['rows'])
        checks+=['real_full_inputs_and_original_response_fixture_48','on_off_payload_and_seed_identity','source_private_history_and_original_request_exact','scorer_original_answers_replay']
    with tempfile.TemporaryDirectory() as temp:
        rs,status=execute(pack,Fixture(limit=2),temp);s=score_records(pack,rs,labels)
        assert len(rs)==48 and status['output_limit']==1 and sum(r['score'] is None for r in s['rows'])==1
        checks+=['independent_output_limit_isolated_without_retry']
    with tempfile.TemporaryDirectory() as temp:
        f=Fixture(crash=3);rs,status=execute(pack,f,temp);s=score_records(pack,rs,labels)
        assert f.n==3 and len(rs)==2 and status['status']=='SYSTEM_ERROR' and sum(r['score'] is None for r in s['rows'])==46
        checks+=['system_failure_preserved_unfinished_exported_no_retry']
    bad=copy.deepcopy(pack);bad['schedule'][0]['payload']['system']='Changed'
    try:validate_pack(bad)
    except AssertionError:checks+=['mutated_payload_rejected']
    else:raise AssertionError('bad payload accepted')
    out=dict(verdict='PASS',checks=checks,n=len(checks),fixture_only=True,new_model_calls=0)
    atomic(HERE/'TESTS.json',out);print(json.dumps(out),flush=True)

def prepare():
    from b0_training import load_tokenizer
    assert load(HERE/'TESTS.json')['verdict']=='PASS'
    assert load(HERE/'SCIENCE_REVIEW.json')['verdict']=='PASS'
    pack=load(HERE/'DIAGNOSTIC_INPUTS.json');validate_pack(pack)
    config=load(HERE/'diagnostic_config.json');qualification=validate_runtime(config);tok=load_tokenizer(config)
    lengths=[]
    for req in pack['schedule']:
        ids=tok.apply_chat_template([dict(role=k,content=req['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**config['template_kwargs'])
        assert len(ids)+256<=config['max_length']
        lengths.append(dict(id=req['id'],input_tokens=len(ids),plus_cap=len(ids)+256))
    OUT.mkdir(exist_ok=False)
    for name in ('DIAGNOSTIC_INPUTS.json','DIAGNOSTIC_LABELS.json','diagnostic_config.json'):(OUT/name).write_bytes((HERE/name).read_bytes())
    atomic(OUT/'LENGTHS.json',lengths)
    budget=dict(max_calls=48,max_output_tokens=12288,wall_clock_cutoff=None,generation_retry=False,execution='SERIAL_SINGLETON',training=False)
    atomic(OUT/'BUDGET.json',budget)
    pre=dict(science='PASS',engineering='PASS',max_calls=48,max_input_plus_cap=max(x['plus_cap'] for x in lengths),context=config['max_length'],qualification=qualification['qualification'],fixture_tests=load(HERE/'TESTS.json')['n'],reviewer='assistant',independence='none/provisional',new_model_calls=0)
    atomic(OUT/'PREFLIGHT.json',pre)
    files=[HERE/n for n in ('runner.py','launch.py','DIAGNOSTIC_INPUTS.json','DIAGNOSTIC_LABELS.json','diagnostic_config.json','TESTS.json','SCIENCE_REVIEW.json','EXPERIMENT_REVIEW.md')]
    files += [ROOT/'tools'/n for n in ('b1_runtime.py','b1_multi_backend.py','b0_training.py','b0_answers.py','b1_stop_status.py')]
    files += [Path(config['adapter_path'])/n for n in ('adapter_model.safetensors','adapter_config.json','b0_origin.json')]
    files += [Path(config['model_path'])/n for n in ('config.json','tokenizer_config.json','tokenizer.json')]
    files += [ROOT/p['sourcePath'] for p in pack['cases']]
    files += [OUT/n for n in ('DIAGNOSTIC_INPUTS.json','DIAGNOSTIC_LABELS.json','diagnostic_config.json','LENGTHS.json','BUDGET.json','PREFLIGHT.json')]
    atomic(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in dict.fromkeys(files)}))
    atomic(OUT/'STATUS.json',dict(status='PREPARED_NOT_LAUNCHED',completed=0,planned=48,new_model_calls=0))
    print(json.dumps(pre),flush=True)

def verify_freeze():
    assert all(sha(p)==h for p,h in load(OUT/'FREEZE.json')['files'].items())

def run():
    verify_freeze();pre=load(OUT/'PREFLIGHT.json');assert pre['science']==pre['engineering']=='PASS'
    (OUT/'STARTED').touch(exist_ok=False)
    try:
        config=load(OUT/'diagnostic_config.json');pack=load(OUT/'DIAGNOSTIC_INPUTS.json');validate_pack(pack)
        backend=MultiBackend(config)
        records,status=execute(pack,backend,OUT)
        scores=score_records(pack,records,load(OUT/'DIAGNOSTIC_LABELS.json')['labels'])
        atomic(OUT/'scores.json',scores);verify_freeze();print(json.dumps(status),flush=True)
    except Exception as exc:
        atomic(OUT/'STATUS.json',dict(status='SYSTEM_ERROR',type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()));raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['test','prepare','run']);args=parser.parse_args()
    {'test':selftest,'prepare':prepare,'run':run}[args.action]()
