"""Single-stage three-condition receiver diagnostic with batch-scoped live gates."""
import argparse
import json
import time
from pathlib import Path
from tokenizers import Tokenizer
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import minimal_final_answer_contract as terminal
import local_reconstruction_probe as earlier_front
import run_local_reconstruction as core
import example_adaptation_probe as front
import prepare_example_adaptation as prepare

ROOT=io.ROOT
DEFAULT=ROOT/'runs/example-adaptation-prepared-20261026-r1'
VERSION='example-adaptation/1'
LIMITS=dict(requests=72,per_output=1536,output=110592,per_input=16384,input=524288)


def freeze(p):
    p=Path(p)
    if p.exists():raise ValueError('new prepared directory required')
    src=prepare.SPEC
    lineage=io.read(src/'SOURCE_MANIFEST.json')
    for name,digest in lineage['files'].items():
        if io.digest(src/name)!=digest:raise ValueError('specification changed: '+name)
    for name,digest in lineage['parent_files'].items():
        if io.digest(ROOT/name)!=digest:raise ValueError('historical input changed')
    p.mkdir(parents=True)
    for rel in lineage['files']:
        target=p/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((src/rel).read_bytes())
    io.write(p/'config.json',core.config())
    design=io.read(p/'DESIGN.json')
    io.write(p/'PLAN.json',dict(version=VERSION,schedule=design['schedule'],limits=LIMITS,status='frozen_not_authorized'))
    code=[Path(__file__),Path(front.__file__),Path(prepare.__file__),Path(terminal.__file__),Path(io.__file__),
          Path(earlier_front.__file__),Path(core.__file__),ROOT/'src/coreta/model_client.py',ROOT/'src/coreta/schemas.py',
          ROOT/'tools/check_example_adaptation.py']
    hashes={}
    for source in code:
        rel=source.relative_to(ROOT).as_posix();target=p/'frozen_source'/rel
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes());hashes[rel]=io.digest(source)
    io.write(p/'manifest.json',dict(version=VERSION,limits=LIMITS,code_sha256=hashes,
        tokenizer_sha256=io.digest(core.TOKENIZER),
        files={x.relative_to(p).as_posix():io.digest(x) for x in p.rglob('*') if x.is_file()}))
    verify(p)
    return dict(status='frozen_not_authorized',manifest_sha256=io.digest(p/'manifest.json'))


def verify(p):
    p=Path(p);m=io.read(p/'manifest.json')
    if m['version']!=VERSION or m['limits']!=LIMITS:raise ValueError('version/limit mismatch')
    for rel,digest in m['files'].items():
        if io.digest(core.child(p,rel))!=digest:raise ValueError('frozen file changed: '+rel)
    for rel,digest in m['code_sha256'].items():
        if io.digest(core.child(ROOT,rel))!=digest:raise ValueError('runtime code changed: '+rel)
    if io.digest(core.TOKENIZER)!=m['tokenizer_sha256'] or io.read(p/'config.json')!=core.config():raise ValueError('config/tokenizer mismatch')
    plan=io.read(p/'PLAN.json')
    if plan['limits']!=LIMITS or plan['schedule']!=io.read(p/'DESIGN.json')['schedule'] or len(plan['schedule'])!=72:raise ValueError('plan mismatch')
    return m,plan


def gates(p):
    digest=io.digest(p/'manifest.json')
    for name,expected in [('PREFLIGHT.json',dict(status='passed')),('EXPERIMENT_REVIEW.json',dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED'))]:
        row=io.read(p/name)
        if row.get('manifest_sha256')!=digest or any(row.get(k)!=v for k,v in expected.items()):raise ValueError('fresh '+name+' required')
    auth=io.read(p/'AUTHORIZATION.json')
    expected=dict(authorized=True,manifest_sha256=digest,max_requests=72,max_output_tokens=110592,max_input_tokens=524288,destination='https://api.deepseek.com/responses')
    if any(auth.get(k)!=v for k,v in expected.items()) or not auth.get('user_authorization_text'):raise ValueError('explicit batch authorization required')


def run(p,out,*,transport=None,local_validation=False):
    p,out=Path(p),Path(out);manifest,plan=verify(p)
    if local_validation:
        if transport is None:raise ValueError('explicit fixture transport required')
    else:gates(p)
    if out.exists():raise ValueError('new output directory required; no resume')
    out.mkdir(parents=True);io.write(out/'manifest.json',manifest)
    examples=io.read(p/'EXAMPLES.json')
    state=dict(mode='local_fixture' if local_validation else 'live',status='running',attempts=0,
        input_tokens=0,output_tokens=0,reserved_input=0,reserved_output=0,unknown_usage=False,
        over_cap=False,consecutive_unreadable=0,rows=[],error=None)
    client=None;current=None
    def save():
        state['attempts']=client.attempts if client else 0
        io.write(out/'progress.json',state)
        done={r['slot']:r for r in state['rows']}
        io.write(out/'review.json',dict(mode=state['mode'],status=state['status'],rows=[done.get(r['slot'],dict(r,status='not_run',answer=None)) for r in plan['schedule']]))
    def log(name,value):
        with (out/name).open('a',encoding='utf-8') as stream:stream.write(json.dumps(value,ensure_ascii=False)+'\n')
        if name!='responses.jsonl':return
        response=value.get('response')
        if not isinstance(response,dict):state['unknown_usage']=True;return
        text=''.join(c['text'] for item in response.get('output',[]) for c in item.get('content',[]) if c.get('type')=='output_text' and isinstance(c.get('text'),str))
        (out/f'{current:03d}.raw.txt').write_text(text,encoding='utf-8')
        for key in ['input_tokens','output_tokens']:
            amount=response.get('usage',{}).get(key)
            if type(amount) is not int or amount<0:state['unknown_usage']=True
            else:
                state[key]+=amount
                if amount>LIMITS['per_input' if key=='input_tokens' else 'per_output']:state['over_cap']=True
    tokenizer=Tokenizer.from_file(str(core.TOKENIZER))
    client=core.DeepSeekClient(core.config(),log,transport=transport,token_counter=lambda s:len(tokenizer.encode(s,add_special_tokens=False).ids))
    save()
    try:
        for row in plan['schedule']:
            current=row['slot'];case=io.read(p/'cases'/f"{row['case_id']}.json")
            req=front.request(case,row['method'],examples);payload=client.payload(req['instructions'],req['schema'],1536);size=client.size(payload)
            if (size>LIMITS['per_input'] or client.attempts>=72 or max(state['input_tokens'],state['reserved_input'])+size>LIMITS['input']
                or max(state['output_tokens'],state['reserved_output'])+1536>LIMITS['output']):raise RuntimeError('pre-request budget exceeded')
            io.write(out/'actual_requests'/f'{current:03d}.json',req)
            state['reserved_input']+=size;state['reserved_output']+=1536
            try:
                raw=client.complete(payload,deadline=time.monotonic()+150,logical_seed=row['repeat'])
                if state['unknown_usage'] or state['over_cap'] or state['input_tokens']>LIMITS['input'] or state['output_tokens']>LIMITS['output']:raise RuntimeError('usage missing or over budget')
                answer=terminal.decode(raw,case['packet'])
            except (ValueError,ProtocolError) as exc:
                if state['unknown_usage'] or state['over_cap'] or (isinstance(exc,ProtocolError) and exc.code!='SCHEMA_ERROR'):raise
                state['rows'].append(dict(row,status='quarantined',answer=None,error=str(exc)));state['consecutive_unreadable']+=1;save()
                if state['consecutive_unreadable']>=2:raise RuntimeError('two consecutive unreadable core outputs') from exc
                continue
            state['consecutive_unreadable']=0;state['rows'].append(dict(row,status='readable',answer=answer));save()
        state['status']='completed_with_quarantine' if any(r['status']=='quarantined' for r in state['rows']) else 'completed'
    except Exception as exc:
        state['status']='stopped';state['error']=f'{type(exc).__name__}: {exc}'
        if current is not None and not any(r['slot']==current for r in state['rows']):
            state['rows'].append(dict(next(r for r in plan['schedule'] if r['slot']==current),status='system_error',answer=None,error=state['error']))
    finally:
        save()
        io.write(out/'EVALUATION_TEMPLATE.json',dict(mode=state['mode'],status=state['status'],semantic_scoring=None,
            rows=[dict(r,semantic_application=None,reference_match=None) for r in io.read(out/'review.json')['rows']]))
    return state


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','verify','run']);parser.add_argument('--prepared',type=Path,default=DEFAULT);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.action=='freeze':result=freeze(args.prepared)
    elif args.action=='verify':verify(args.prepared);result=dict(status='verified')
    elif not args.output:parser.error('--output required')
    else:result=run(args.prepared,args.output)
    print(json.dumps(result,ensure_ascii=False))
