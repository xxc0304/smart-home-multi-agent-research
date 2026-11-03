"""Bounded two-stage diagnostic; immutable inputs and batch authorization gates."""
import argparse
import json
import time
from pathlib import Path

from tokenizers import Tokenizer
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import inference_link_probe_v1 as front
import local_reconstruction_probe as decoder
import receiver_question_context_v2 as handoff
import minimal_final_answer_contract as terminal
import prepare_inference_link_walkthrough_20261027 as preparation

ROOT = io.ROOT
SPEC = preparation.OUT
DEFAULT = ROOT/'runs/inference-link-prepared-20261027-r3'
TOKENIZER = ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'
VERSION = 'inference-link/1'
LIMITS = dict(requests=24, per_output=1536, output=36864, per_input=16384, input=262144)


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
    ids=['004-identity','023-notice','011-time-supported']
    rows=[]
    for repeat in (1,2):
        for i,case_id in enumerate(ids):
            methods=front.METHODS if (repeat+i)%2 else tuple(reversed(front.METHODS))
            for method in methods:
                unit=f'{case_id}/{repeat}/{method}'
                for stage in ('local','final'):
                    rows.append(dict(slot=len(rows)+1,unit=unit,case_id=case_id,method=method,stage=stage,repeat=repeat))
    return rows


def freeze(prepared):
    p=Path(prepared)
    if p.exists():raise ValueError('new preparation directory required; no overwrite')
    lineage=io.read(SPEC/'SOURCE_MANIFEST.json')
    for name,digest in lineage['code_sha256'].items():
        if io.digest(ROOT/name)!=digest:raise ValueError('prototype code changed: '+name)
    for name,digest in lineage['files'].items():
        if io.digest(SPEC/name)!=digest:raise ValueError('prototype file changed: '+name)
    index=io.read(SPEC/'EVIDENCE_INDEX.json')
    carriers={r['case_id']:r for r in io.read(SPEC/'LOCAL_CHECKS.json')['real_carrier_replays']}
    p.mkdir(parents=True)
    for row in index:
        for key in ('request','answer'):
            if io.digest(ROOT/row[key+'_path'])!=row[key+'_sha256']:raise ValueError('historical evidence changed')
        carrier=carriers[row['case_id']]
        if io.digest(ROOT/carrier['carrier_path'])!=carrier['carrier_sha256']:raise ValueError('carrier changed')
        io.write(p/'cases'/f"{row['case_id']}.json",io.read(SPEC/'cases'/f"{row['case_id']}.json"))
        row.update(carrier_raw=carrier['carrier_path'],carrier_sha256=carrier['carrier_sha256'])
    io.write(p/'CASE_INDEX.json',index)
    io.write(p/'SOURCE_LINEAGE.json',lineage)
    io.write(p/'PLAN.json',dict(version=VERSION,schedule=schedule(),limits=LIMITS,status='frozen_not_authorized',
        scope='Analyst-selected inference diagnostic: three old tasks, two repeats; not autonomous multi-agent efficacy.'))
    io.write(p/'config.json',config())
    io.write(p/'offline_only/EVALUATION_PROTOCOL.json',dict(
        primary='Paired case-level semantic audit of stage-one inference judgment and its actual use in final reasoning.',
        dimensions=['source-versus-added-link distinguished','selected link retained/narrowed/withdrawn with support',
                    'final answer applies the finding consistently','new unsupported link introduced','supported content damaged'],
        annotation='Each dimension true/false/unresolved with exact output spans; unavailable technical branches remain missing, not wrong.',
        secondary='Listed choice, change from historical answer, abstention and token usage; choice correctness alone does not prove repair.',
        aggregation='Report all three cases and both repeats separately, paired counts as descriptive only; repeats are not new tasks.',
        continuation='Mechanism signal requires a traceable better-supported application on an erroneous target and no demonstrated damage on supported guard; mixed outcomes require causal review, no automatic expansion.',
        no_gain='If only check prose changes or both methods behave alike, no incremental benefit established; preserve negative result.'))
    io.write(p/'offline_only/WALKTHROUGH_NOTES.json',io.read(SPEC/'offline_only/WALKTHROUGH_NOTES.json'))
    (p/'SPEC.md').write_bytes((SPEC/'SPEC_AND_WALKTHROUGH.md').read_bytes())
    code=[Path(__file__),Path(front.__file__),Path(decoder.__file__),Path(handoff.__file__),Path(terminal.__file__),Path(io.__file__),
          Path(preparation.__file__),ROOT/'src/coreta/model_client.py',ROOT/'src/coreta/schemas.py',ROOT/'tools/check_inference_link_runner.py']
    hashes={}
    for source in code:
        name=source.relative_to(ROOT).as_posix();dest=p/'frozen_source'/name
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes());hashes[name]=io.digest(source)
    io.write(p/'manifest.json',dict(version=VERSION,limits=LIMITS,code_sha256=hashes,tokenizer_sha256=io.digest(TOKENIZER),
        historical_sha256={r[k]:r[k.replace('_path','_sha256')] for r in index for k in ('request_path','answer_path')} | {r['carrier_raw']:r['carrier_sha256'] for r in index},
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
    for name,digest in manifest['historical_sha256'].items():
        if io.digest(child(ROOT,name))!=digest:raise ValueError('historical source changed: '+name)
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
    required=dict(authorized=True,manifest_sha256=digest,max_requests=24,max_output_tokens=36864,
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
            req=(front.first_request(case,row['method']) if row['stage']=='local' else
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
                answer=(decoder.decode_local(raw) if row['stage']=='local' else terminal.decode(raw,case['receiver_context']))
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
    for case_id,repeat in dict.fromkeys((row['case_id'],row['repeat']) for row in finals):
        group={row['method']:row for row in finals if row['case_id']==case_id and row['repeat']==repeat}
        pairs.append(dict(case_id=case_id,repeat=repeat,conditions=group,method_difference=None))
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
