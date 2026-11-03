"""Single-call paired downstream diagnostic; all live requests require frozen gates."""
import argparse
import copy
import json
import time
from pathlib import Path
from tokenizers import Tokenizer
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
from coreta.constraint_commit import session_from_receiver
import coreta.constraint_commit as state_code
import local_judgment_frontend as io
import minimal_final_answer_contract as terminal
import constraint_commit_probe as front
import prepare_constraint_commit_20261027 as prototype

ROOT=io.ROOT
DEFAULT=ROOT/'runs/constraint-commit-prepared-20261027-r4'
TOKENIZER=ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'
VERSION='constraint-commit/1'
LIMITS=dict(requests=18,per_output=1536,output=27648,per_input=16384,input=262144)


def config():
    return dict(provider='deepseek',model='deepseek-flash',base_url='https://api.deepseek.com',
        generation=dict(reasoning_effort='none',temperature=0.7,max_input_tokens=LIMITS['per_input']),
        protocol=dict(transport_retries_per_request=0,max_format_repairs=0,request_timeout_seconds=120))


def child(root,name):
    base=Path(root).resolve();result=(base/name).resolve()
    if not result.is_relative_to(base):raise ValueError('path escapes root')
    return result


def schedule():
    rows=[]
    for repeat in (1,2):
        for i,cid in enumerate(['history-01','history-02','history-03']):
            for method in front.METHODS if (repeat+i)%2 else tuple(reversed(front.METHODS)):
                rows.append(dict(slot=len(rows)+1,case_id=cid,kind='historical_diagnostic',repeat=repeat,method=method))
    for i,cid in enumerate(['control-01','control-02','control-03']):
        for method in front.METHODS if i%2 else tuple(reversed(front.METHODS)):
            rows.append(dict(slot=len(rows)+1,case_id=cid,kind='fictional_control',repeat=1,method=method))
    return rows


def freeze(p):
    p=Path(p)
    if p.exists():raise ValueError('new frozen directory required')
    p.mkdir(parents=True);index=[];historical={}
    old_index={r['case_id']:r for r in io.read(prototype.SOURCE/'CASE_INDEX.json')}
    for i,(cid,types) in enumerate(prototype.SPECS,1):
        source=prototype.SOURCE/'cases'/(cid+'.json');value=io.read(source)['receiver_context']
        context={k:copy.deepcopy(value[k]) for k in ('task','member','public_sources','own_sources','shared_contributions')}
        new_id=f'history-{i:02d}'
        io.write(p/'cases'/(new_id+'.json'),dict(context=context,field_types=types))
        raw=old_index[cid]['answer_path'];historical[source.relative_to(ROOT).as_posix()]=io.digest(source)
        historical[raw]=io.digest(ROOT/raw)
        index.append(dict(case_id=new_id,origin=cid,carrier_raw=raw,carrier_kind='same-task full modern historical final'))
    for i in (1,2,3):
        cid=f'control-{i:02d}';source=prototype.OUT/'control_inputs'/(cid+'.json')
        io.write(p/'cases'/(cid+'.json'),io.read(source));historical[source.relative_to(ROOT).as_posix()]=io.digest(source)
        index.append(dict(case_id=cid,carrier_raw=old_index['011-time-supported']['answer_path'],
            carrier_kind='cross-task real modern final, interface only; no control semantic outcome'))
    io.write(p/'CASE_INDEX.json',index)
    io.write(p/'PLAN.json',dict(version=VERSION,schedule=schedule(),limits=LIMITS,
        scope='Fixed historical model-pool downstream receiver diagnostic; three old tasks twice plus three fictional guards once. No member regeneration.',
        allocation='12 historical requests and 6 control requests; no autonomous expansion',
        semantic_fallback='No consistent encoded choice yields null and counts as semantic unresolved, not format error. No arbitrary forced-choice override.'))
    io.write(p/'config.json',config())
    io.write(p/'offline_only/CONTROL_PURPOSES.json',io.read(prototype.OUT/'offline_only/CONTROL_PURPOSES.json'))
    (p/'offline_only/EVALUATION_PROTOCOL.md').write_bytes((prototype.OUT/'EVALUATION_PROTOCOL.md').read_bytes())
    for name in ['ASSUMPTIONS.md']:(p/name).write_bytes((prototype.OUT/name).read_bytes())
    (p/'ARCHITECTURE.md').write_bytes((ROOT/'research/constraint-collaboration-design-20261027-v1/ARCHITECTURE.md').read_bytes())
    code=[Path(__file__),Path(front.__file__),Path(state_code.__file__),Path(prototype.__file__),Path(io.__file__),Path(terminal.__file__),
        ROOT/'tools/check_constraint_commit_runner.py',ROOT/'tests/test_constraint_commit.py',ROOT/'src/coreta/workboard/candidate_probe.py',
        ROOT/'src/coreta/model_client.py',ROOT/'src/coreta/schemas.py']
    hashes={}
    for source in code:
        name=source.relative_to(ROOT).as_posix();dest=p/'frozen_source'/name
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes());hashes[name]=io.digest(source)
    io.write(p/'manifest.json',dict(version=VERSION,limits=LIMITS,code_sha256=hashes,historical_sha256=historical,
        tokenizer_sha256=io.digest(TOKENIZER),files={x.relative_to(p).as_posix():io.digest(x) for x in p.rglob('*') if x.is_file()}))
    verify(p)
    return dict(status='frozen_not_authorized',manifest_sha256=io.digest(p/'manifest.json'))


def verify(p):
    p=Path(p);m=io.read(p/'manifest.json')
    if m['version']!=VERSION or m['limits']!=LIMITS:raise ValueError('version or limits changed')
    for root,hashes in [(p,m['files']),(ROOT,m['code_sha256']),(ROOT,m['historical_sha256'])]:
        for name,digest in hashes.items():
            if io.digest(child(root,name))!=digest:raise ValueError('frozen input/code changed: '+name)
    if io.digest(TOKENIZER)!=m['tokenizer_sha256'] or io.read(p/'config.json')!=config():raise ValueError('tokenizer/config changed')
    plan=io.read(p/'PLAN.json')
    if plan['schedule']!=schedule() or plan['limits']!=LIMITS:raise ValueError('plan changed')
    return m,plan


def gates(p):
    digest=io.digest(p/'manifest.json')
    for name,expected in [('PREFLIGHT.json',dict(status='passed')),
        ('EXPERIMENT_REVIEW.json',dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED'))]:
        v=io.read(p/name)
        if v.get('manifest_sha256')!=digest or any(v.get(k)!=x for k,x in expected.items()):raise ValueError('fresh '+name+' required')
    v=io.read(p/'AUTHORIZATION.json')
    expected=dict(authorized=True,manifest_sha256=digest,limits=LIMITS,destination='https://api.deepseek.com/responses')
    if any(v.get(k)!=x for k,x in expected.items()) or not v.get('user_authorization_text'):raise ValueError('explicit batch authorization required')


def run(p,out,*,transport=None,local_validation=False):
    p,out=Path(p),Path(out);manifest,plan=verify(p)
    if local_validation:
        if transport is None:raise ValueError('explicit fixture transport required')
    else:gates(p)
    if out.exists():raise ValueError('new output directory required; no resume')
    out.mkdir(parents=True);io.write(out/'manifest.json',manifest)
    s=dict(mode='local_fixture' if local_validation else 'live',status='running',attempts=0,input_tokens=0,output_tokens=0,
        reserved_input=0,reserved_output=0,unknown_usage=False,over_cap=False,consecutive_unreadable=0,rows=[],error=None)
    client=None;current=None
    def save():
        s['attempts']=client.attempts if client else 0;io.write(out/'progress.json',s)
        done={r['slot']:r for r in s['rows']}
        io.write(out/'review.json',dict(mode=s['mode'],status=s['status'],rows=[done.get(r['slot'],dict(r,status='not_run',answer=None)) for r in plan['schedule']]))
    def log(name,value):
        with (out/name).open('a',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False)+'\n')
        if name!='responses.jsonl':return
        response=value.get('response')
        if not isinstance(response,dict):s['unknown_usage']=True;return
        raw=''.join(c['text'] for item in response.get('output',[]) for c in item.get('content',[]) if c.get('type')=='output_text' and isinstance(c.get('text'),str))
        (out/f'{current:03d}.raw.txt').write_text(raw,encoding='utf-8')
        for key,cap in [('input_tokens','per_input'),('output_tokens','per_output')]:
            n=response.get('usage',{}).get(key)
            if type(n) is not int or n<0:s['unknown_usage']=True
            else:
                s[key]+=n
                if n>LIMITS[cap]:s['over_cap']=True
    tok=Tokenizer.from_file(str(TOKENIZER))
    client=DeepSeekClient(config(),log,transport=transport,token_counter=lambda x:len(tok.encode(x,add_special_tokens=False).ids))
    save()
    try:
        for row in plan['schedule']:
            current=row['slot'];case=io.read(p/'cases'/(row['case_id']+'.json'));context=case['context']
            session=session_from_receiver(context,case['field_types']);req=front.request(context,session,row['method'])
            payload=client.payload(req['instructions'],req['schema'],LIMITS['per_output']);size=client.size(payload)
            if (size>LIMITS['per_input'] or client.attempts>=LIMITS['requests'] or
                max(s['input_tokens'],s['reserved_input'])+size>LIMITS['input'] or
                max(s['output_tokens'],s['reserved_output'])+LIMITS['per_output']>LIMITS['output']):raise RuntimeError('pre-request budget exceeded')
            io.write(out/'actual_requests'/f'{current:03d}.json',req)
            s['reserved_input']+=size;s['reserved_output']+=LIMITS['per_output']
            try:
                raw=client.complete(payload,deadline=time.monotonic()+150,logical_seed=row['repeat'])
                if s['unknown_usage'] or s['over_cap'] or s['input_tokens']>LIMITS['input'] or s['output_tokens']>LIMITS['output']:raise RuntimeError('usage missing or over cap')
                answer=front.process(raw,context,session,row['method'],1)
            except (ValueError,ProtocolError) as exc:
                if s['unknown_usage'] or s['over_cap'] or isinstance(exc,ProtocolError) and exc.code!='SCHEMA_ERROR':raise
                s['rows'].append(dict(row,status='quarantined',answer=None,error=str(exc)));s['consecutive_unreadable']+=1;save()
                if s['consecutive_unreadable']>=2:raise RuntimeError('two consecutive unreadable cores') from exc
                continue
            s['consecutive_unreadable']=0;s['rows'].append(dict(row,status='readable',answer=answer));save()
        s['status']='completed_with_quarantine' if any(r['status']=='quarantined' for r in s['rows']) else 'completed'
    except Exception as exc:
        s['status']='stopped';s['error']=f'{type(exc).__name__}: {exc}'
        if current and not any(r['slot']==current for r in s['rows']):
            row=next(r for r in plan['schedule'] if r['slot']==current)
            s['rows'].append(dict(row,status='system_error',answer=None,error=s['error']))
    finally:save();export(out)
    return s


def export(out):
    out=Path(out);review=io.read(out/'review.json');rows=[]
    for row in review['rows']:
        answer=row.get('answer')
        rows.append(dict(**row,delivered_choice=answer['delivery']['choice'] if answer else None,
            model_choice=answer['model_answer']['choice'] if answer else None,
            semantic_unresolved=answer['delivery']['unresolved'] if answer else None,
            host_changed_choice=answer['delivery']['host_changed_choice'] if answer else None,
            final_quality=None,reason_quality=None,wrong_exclusion=None,update_entailment=None))
    summary=dict(mode=review['mode'],status=review['status'],scheduled=len(rows),readable=sum(r['status']=='readable' for r in rows),
        technical_missing=sum(r['status']!='readable' for r in rows),semantic_unresolved=sum(r['semantic_unresolved'] is True for r in rows),
        scoring='No automatic semantic truth or gold. Host changes are not model adoption evidence. Controls separate from historical tasks.')
    io.write(out/'EVALUATION_TEMPLATE.json',dict(summary=summary,rows=rows))
    return summary


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','verify','run','export'])
    parser.add_argument('--prepared',type=Path,default=DEFAULT);parser.add_argument('--output',type=Path);args=parser.parse_args()
    if args.action=='freeze':result=freeze(args.prepared)
    elif args.action=='verify':verify(args.prepared);result=dict(status='verified',manifest_sha256=io.digest(args.prepared/'manifest.json'))
    elif args.output is None:parser.error('--output required')
    elif args.action=='export':result=export(args.output)
    else:
        s=run(args.prepared,args.output);result={k:s[k] for k in ['status','attempts','input_tokens','output_tokens','error']}
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
