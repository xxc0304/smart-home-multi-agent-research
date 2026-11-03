"""Bounded two-stage diagnostic; immutable inputs and batch authorization gates."""
import argparse
import json
import time
from pathlib import Path

from tokenizers import Tokenizer
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import local_reconstruction_probe as front
import minimal_final_answer_contract as terminal
import prepare_local_reconstruction_20261026 as preparation

ROOT = io.ROOT
SPEC = preparation.OUT
DEFAULT = ROOT/'runs/local-reconstruction-prepared-20261026-r1'
TOKENIZER = ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'
VERSION = 'local-reconstruction/1'
LIMITS = dict(requests=32, per_output=1536, output=49152, per_input=16384, input=262144)


def config():
    return dict(provider='deepseek', model='deepseek-flash', base_url='https://api.deepseek.com',
        generation=dict(reasoning_effort='none',temperature=0.7,max_input_tokens=LIMITS['per_input']),
        protocol=dict(transport_retries_per_request=0,max_format_repairs=0,request_timeout_seconds=120))


def child(root, rel):
    base=Path(root).resolve()
    result=(base/rel).resolve()
    if not result.is_relative_to(base):
        raise ValueError('path outside frozen root')
    return result


def schedule():
    rows=io.read(SPEC/'DESIGN_CONFIG.json')['schedule']
    return [dict(row,slot=i+1,repeat=1) for i,row in enumerate(rows)]


def freeze(prepared):
    p=Path(prepared)
    if p.exists():
        raise ValueError('new preparation directory required; no overwrite')
    lineage=io.read(SPEC/'SOURCE_MANIFEST.json')
    for name,digest in lineage['sources'].items():
        if io.digest(ROOT/name)!=digest:
            raise ValueError('historical source/builder changed: '+name)
    p.mkdir(parents=True)
    index=io.read(SPEC/'CASE_INDEX.json')
    for row in index:
        if row['scheduled']:
            name=f"cases/{row['case_id']}.json"
            if io.digest(SPEC/name)!=lineage['case_sha256'][name]:
                raise ValueError('case changed before freezing')
            io.write(p/name,io.read(SPEC/name))
    io.write(p/'CASE_INDEX.json',[r for r in index if r['scheduled']])
    io.write(p/'SOURCE_LINEAGE.json',lineage)
    io.write(p/'PLAN.json',dict(version=VERSION,schedule=schedule(),limits=LIMITS,
        status='frozen_not_authorized',scope='analyst-selected local component diagnostic; four old tasks, eight drafts'))
    io.write(p/'config.json',config())
    io.write(p/'offline_only/RUBRICS.json',[r for r in io.read(SPEC/'offline_only/RUBRICS.json')
        if r['case_id'] in {x['case_id'] for x in index if x['scheduled']}])
    (p/'SPEC.md').write_bytes((SPEC/'SPEC.md').read_bytes())
    code=[Path(__file__),Path(front.__file__),Path(terminal.__file__),Path(io.__file__),
          Path(preparation.__file__),ROOT/'src/coreta/model_client.py',ROOT/'src/coreta/schemas.py',
          ROOT/'tools/check_local_reconstruction_runner.py']
    hashes={}
    for source in code:
        name=source.relative_to(ROOT).as_posix()
        dest=p/'frozen_source'/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(source.read_bytes())
        hashes[name]=io.digest(source)
    io.write(p/'manifest.json',dict(version=VERSION,limits=LIMITS,code_sha256=hashes,
        tokenizer_sha256=io.digest(TOKENIZER),
        files={x.relative_to(p).as_posix():io.digest(x) for x in p.rglob('*') if x.is_file()}))
    verify(p)
    return dict(status='frozen_not_authorized',manifest_sha256=io.digest(p/'manifest.json'))


def verify(prepared):
    p=Path(prepared)
    manifest=io.read(p/'manifest.json')
    if manifest['version']!=VERSION or manifest['limits']!=LIMITS:
        raise ValueError('version/budget mismatch')
    for name,digest in manifest['files'].items():
        if io.digest(child(p,name))!=digest:
            raise ValueError('frozen file changed: '+name)
    for name,digest in manifest['code_sha256'].items():
        if io.digest(child(ROOT,name))!=digest:
            raise ValueError('runtime code changed: '+name)
    if io.digest(TOKENIZER)!=manifest['tokenizer_sha256'] or io.read(p/'config.json')!=config():
        raise ValueError('tokenizer/config mismatch')
    plan=io.read(p/'PLAN.json')
    if plan['limits']!=LIMITS or plan['schedule']!=schedule():
        raise ValueError('schedule mismatch')
    if len(plan['schedule'])!=LIMITS['requests']:
        raise ValueError('unexpected request count')
    return manifest,plan


def gates(p):
    digest=io.digest(p/'manifest.json')
    for name,expected in [('PREFLIGHT.json',dict(status='passed')),
                          ('EXPERIMENT_REVIEW.json',dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED'))]:
        value=io.read(p/name)
        if value.get('manifest_sha256')!=digest or any(value.get(k)!=v for k,v in expected.items()):
            raise ValueError('fresh '+name+' required')
    auth=io.read(p/'AUTHORIZATION.json')
    required=dict(authorized=True,manifest_sha256=digest,max_requests=32,max_output_tokens=49152,
                  max_input_tokens=262144,destination='https://api.deepseek.com/responses')
    if any(auth.get(k)!=v for k,v in required.items()) or not auth.get('user_authorization_text'):
        raise ValueError('explicit batch/data/destination authorization required')


def run(prepared,output,*,transport=None,local_validation=False):
    p,out=Path(prepared),Path(output)
    manifest,plan=verify(p)
    if local_validation:
        if transport is None:
            raise ValueError('local mode requires an explicit fixture transport')
    else:
        gates(p)
    if out.exists():
        raise ValueError('new output directory required; no resume')
    out.mkdir(parents=True)
    io.write(out/'manifest.json',manifest)
    state=dict(mode='local_fixture' if local_validation else 'live',status='running',attempts=0,
        input_tokens=0,output_tokens=0,reserved_input=0,reserved_output=0,unknown_usage=False,
        over_cap=False,consecutive_unreadable=0,rows=[],error=None)
    locals_by_unit={}
    current=None
    client=None

    def save():
        state['attempts']=client.attempts if client is not None else 0
        io.write(out/'progress.json',state)
        done={r['slot']:r for r in state['rows']}
        io.write(out/'review.json',dict(mode=state['mode'],status=state['status'],rows=[
            done.get(row['slot'],dict(row,status='not_run',answer=None)) for row in plan['schedule']]))

    def log(name,value):
        with (out/name).open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(value,ensure_ascii=False)+'\n')
        if name!='responses.jsonl':
            return
        response=value.get('response')
        if not isinstance(response,dict):
            state['unknown_usage']=True
            return
        text=''.join(part['text'] for item in response.get('output',[]) for part in item.get('content',[])
                     if part.get('type')=='output_text' and isinstance(part.get('text'),str))
        (out/f'{current:03d}.raw.txt').write_text(text,encoding='utf-8')
        for key in ('input_tokens','output_tokens'):
            amount=response.get('usage',{}).get(key)
            if type(amount) is not int or amount<0:
                state['unknown_usage']=True
            else:
                state[key]+=amount
                if amount>LIMITS['per_input' if key=='input_tokens' else 'per_output']:
                    state['over_cap']=True

    tok=Tokenizer.from_file(str(TOKENIZER))
    client=DeepSeekClient(config(),log,transport=transport,
        token_counter=lambda text:len(tok.encode(text,add_special_tokens=False).ids))
    save()
    try:
        for row in plan['schedule']:
            current=row['slot']
            case=io.read(p/'cases'/f"{row['case_id']}.json")
            if row['stage']=='final' and row['unit'] not in locals_by_unit:
                state['rows'].append(dict(row,status='blocked_upstream',answer=None));save();continue
            req=(front.local_request(case,row['method']) if row['stage']=='local' else
                 front.final_request(case,locals_by_unit[row['unit']]))
            payload=client.payload(req['instructions'],req['schema'],LIMITS['per_output'])
            size=client.size(payload)
            if (size>LIMITS['per_input'] or client.attempts>=LIMITS['requests'] or
                max(state['input_tokens'],state['reserved_input'])+size>LIMITS['input'] or
                max(state['output_tokens'],state['reserved_output'])+LIMITS['per_output']>LIMITS['output']):
                raise RuntimeError('pre-request budget exceeded')
            io.write(out/'actual_requests'/f'{current:03d}.json',req)
            state['reserved_input']+=size
            state['reserved_output']+=LIMITS['per_output']
            try:
                raw=client.complete(payload,deadline=time.monotonic()+150,logical_seed=1)
                if state['unknown_usage'] or state['over_cap'] or state['input_tokens']>LIMITS['input'] or state['output_tokens']>LIMITS['output']:
                    raise RuntimeError('usage missing or over budget')
                answer=(front.decode_local(raw) if row['stage']=='local' else terminal.decode(raw,case['receiver_context']))
            except (ValueError,ProtocolError) as exc:
                if state['unknown_usage'] or state['over_cap'] or (isinstance(exc,ProtocolError) and exc.code!='SCHEMA_ERROR'):
                    raise
                state['rows'].append(dict(row,status='quarantined',answer=None,error=str(exc)))
                state['consecutive_unreadable']+=1
                save()
                if state['consecutive_unreadable']>=2:
                    raise RuntimeError('two consecutive unreadable core outputs') from exc
                continue
            if row['stage']=='local':
                locals_by_unit[row['unit']]=answer
            state['consecutive_unreadable']=0
            state['rows'].append(dict(row,status='readable',answer=answer));save()
        state['status']='completed_with_quarantine' if any(r['status']=='quarantined' for r in state['rows']) else 'completed'
    except Exception as exc:
        state['status']='stopped';state['error']=f'{type(exc).__name__}: {exc}'
        if current is not None and not any(r['slot']==current for r in state['rows']):
            row=next(r for r in plan['schedule'] if r['slot']==current)
            state['rows'].append(dict(row,status='system_error',answer=None,error=state['error']))
    finally:
        save()
        export(p,out)
    return state


def export(prepared,output):
    p,out=Path(prepared),Path(output)
    review=io.read(out/'review.json')
    finals=[dict(row,semantic_local=None,semantic_application=None,decision_quality=None,
        unresolved=(row['answer']['choice'] is None if row['status']=='readable' else None))
        for row in review['rows'] if row['stage']=='final']
    pairs=[]
    for case_id in dict.fromkeys(row['case_id'] for row in finals):
        group={row['method']:row for row in finals if row['case_id']==case_id}
        pairs.append(dict(case_id=case_id,conditions=group,method_difference=None))
    summary=dict(mode=review['mode'],status=review['status'],scheduled_requests=len(review['rows']),
        final_units=len(finals),readable_finals=sum(r['status']=='readable' for r in finals),
        technical_missing=sum(r['status']!='readable' for r in finals),
        unresolved=sum(r['unresolved'] is True for r in finals),
        semantic_scoring='not automatically scored; analyst rubrics remain offline')
    io.write(out/'EVALUATION_TEMPLATE.json',dict(summary=summary,pairs=pairs))
    return summary


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['freeze','verify','run','export'])
    parser.add_argument('--prepared',type=Path,default=DEFAULT)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.action=='freeze':result=freeze(args.prepared)
    elif args.action=='verify':result=dict(manifest_sha256=io.digest(args.prepared/'manifest.json'),status='verified') if verify(args.prepared) else None
    elif args.output is None:parser.error('--output required')
    elif args.action=='run':result=run(args.prepared,args.output)
    else:result=export(args.prepared,args.output)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
