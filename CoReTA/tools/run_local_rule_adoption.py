"""24 bounded independent integrations of archived member contributions."""
import argparse
import json
from pathlib import Path
import time
from tokenizers import Tokenizer
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import prepare_local_rule_adoption as probe
import run_local_rule_frontend as common

ROOT=io.ROOT
TOKENIZER=ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'
MAX_REQUESTS,CAP,TOTAL_CAP=24,1536,36864

def freeze(output):
    p=Path(output);probe.build(p)
    io.write(p/'config.json',dict(provider='deepseek',model='deepseek-flash',base_url='https://api.deepseek.com',
        generation=dict(reasoning_effort='none',temperature=0.7,max_input_tokens=8192),
        protocol=dict(transport_retries_per_request=0,max_format_repairs=0,request_timeout_seconds=120)))
    # Replace the preparation manifest with a complete, separate launch manifest.
    old=io.read(p/'manifest.json')
    code=[Path(__file__),Path(probe.__file__),Path(io.__file__),Path(common.__file__),ROOT/'src/coreta/model_client.py',ROOT/'src/coreta/schemas.py']
    io.write(p/'manifest.json',dict(version='local-rule-adoption-live/1',max_requests=24,output_cap=CAP,total_output_cap=TOTAL_CAP,
        tokenizer_sha256=io.digest(TOKENIZER),source_preparation_manifest=old,
        files={str(x.relative_to(p)).replace('\\','/'):io.digest(x) for x in p.rglob('*') if x.is_file() and x.name!='manifest.json'},
        code_sha256={str(x.relative_to(ROOT)).replace('\\','/'):io.digest(x) for x in code}))
    verify(p)
    return dict(status='FROZEN_NOT_AUTHORIZED',manifest_sha256=io.digest(p/'manifest.json'))

def verify(p):
    p=Path(p);m=io.read(p/'manifest.json')
    if m['version']!='local-rule-adoption-live/1' or (m['max_requests'],m['output_cap'],m['total_output_cap'])!=(24,CAP,TOTAL_CAP):raise ValueError('wrong budget/version')
    for root,files in [(p,m['files']),(ROOT,m['code_sha256'])]:
        for name,sha in files.items():
            if io.digest(common.child(root,name))!=sha:raise ValueError('frozen file changed: '+name)
    if io.digest(TOKENIZER)!=m['tokenizer_sha256']:raise ValueError('tokenizer changed')
    plan=io.read(p/'PLAN.json');config=io.read(p/'config.json')
    if len(plan['schedule'])!=24 or len(set(r['group'] for r in plan['schedule']))!=24:raise ValueError('schedule differs')
    for idx,r in enumerate(plan['schedule'],1):
        if r['slot']!=idx:raise ValueError('slot differs')
        packet=io.read(common.child(p,r['packet']))
        if packet['task']['task_id']!=r['task']:raise ValueError('task differs')
        if io.read(common.child(p,r['request']))!=probe.request(packet):raise ValueError('request differs')
    return m,plan,config

def gates(p):
    p=Path(p);sha=io.digest(p/'manifest.json')
    pre=io.read(p/'PREFLIGHT.json');review=io.read(p/'EXPERIMENT_REVIEW.json');auth=io.read(p/'AUTHORIZATION.json')
    if pre.get('status')!='passed' or pre.get('manifest_sha256')!=sha:raise ValueError('fresh preflight required')
    if any(review.get(k)!=v for k,v in dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED',manifest_sha256=sha).items()):raise ValueError('fresh review required')
    if not(auth.get('authorized') is True and auth.get('max_requests')==24 and auth.get('max_output_tokens')==TOTAL_CAP and auth.get('destination')=='https://api.deepseek.com/responses' and auth.get('manifest_sha256')==sha and auth.get('user_authorization_text')):raise ValueError('specific new batch authorization required')

def run(prepared,output,*,transport=None,local_validation=False):
    p=Path(prepared);out=Path(output);manifest,plan,config=verify(p)
    if local_validation:
        if transport is None:raise ValueError('explicit local transport required')
    else:gates(p)
    if out.exists():raise ValueError('new output required; no resume')
    out.mkdir(parents=True);io.write(out/'manifest.json',manifest)
    state=dict(mode='local_mock' if local_validation else 'live',status='running',attempts=0,input_tokens=0,output_tokens=0,
        reserved_output=0,unknown_usage=False,consecutive_unreadable=0,rows=[],error=None)
    roster=plan['schedule'];current=None
    def save():
        io.write(out/'progress.json',state)
        done={r['slot']:r for r in state['rows']}
        io.write(out/'review.json',dict(mode=state['mode'],status=state['status'],rows=[done.get(r['slot'],dict(r,status='not_run',answer=None)) for r in roster]))
    def log(name,value):
        with (out/name).open('a',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False)+'\n')
        if name!='responses.jsonl':return
        response=value.get('response')
        if response is None:state['unknown_usage']=True;return
        text=''.join(part['text'] for item in response.get('output',[]) if item.get('type')=='message' for part in item.get('content',[]) if part.get('type')=='output_text' and isinstance(part.get('text'),str))
        if text:(out/f'{current:02d}.raw.txt').write_text(text,encoding='utf-8')
        for field in ('input_tokens','output_tokens'):
            amount=response.get('usage',{}).get(field)
            if type(amount) is not int or amount<0:state['unknown_usage']=True
            else:
                state[field]+=amount
                if field=='output_tokens' and amount>CAP:state['over_cap']=True
    tok=Tokenizer.from_file(str(TOKENIZER));client=DeepSeekClient(config,log,transport=transport,token_counter=lambda s:len(tok.encode(s,add_special_tokens=False).ids))
    save()
    try:
        for row in roster:
            current=row['slot']
            if client.attempts>=MAX_REQUESTS or state['reserved_output']+CAP>TOTAL_CAP:raise RuntimeError('budget exceeded')
            packet=io.read(p/row['packet']);req=io.read(p/row['request'])
            io.write(out/'actual_requests'/f'{current:02d}.json',req)
            payload=client.payload(req['instructions'],req['schema'],CAP);state['reserved_output']+=CAP
            try:
                raw=client.complete(payload,deadline=time.monotonic()+180,logical_seed=row['repeat'])
                if state['unknown_usage']:raise RuntimeError('unknown usage')
                if state.get('over_cap') or state['output_tokens']>state['reserved_output']:raise RuntimeError('output budget exceeded')
                answer=probe.decode(raw,packet)
            except (ValueError,ProtocolError) as exc:
                unreadable=isinstance(exc,ValueError) or (isinstance(exc,ProtocolError) and exc.code=='SCHEMA_ERROR')
                if not unreadable or state['unknown_usage'] or state.get('over_cap'):raise
                state['rows'].append(dict(row,status='quarantined',answer=None,error=str(exc)))
                state['consecutive_unreadable']+=1;state['attempts']=client.attempts;save()
                if state['consecutive_unreadable']>=2:raise RuntimeError('two consecutive unreadable outputs') from exc
                continue
            state['rows'].append(dict(row,status='readable',answer=answer));state['consecutive_unreadable']=0;state['attempts']=client.attempts;save()
        state['status']='completed_with_quarantine' if any(r['status']=='quarantined' for r in state['rows']) else 'completed'
    except Exception as exc:
        if current is not None and not any(r['slot']==current for r in state['rows']):state['rows'].append(dict(roster[current-1],status='failed',answer=None))
        state.update(status='stopped',error_type=type(exc).__name__,error=str(exc));raise
    finally:state['attempts']=client.attempts;save()
    return state

def preflight(p):
    p=Path(p);_,plan,_=verify(p);trace=[]
    history=[r for r in io.read(probe.HISTORY/'review.json')['rows'] if r['stage']=='second']
    def replay(payload,timeout):
        row=plan['schedule'][len(trace)]
        old=next(r for r in history if r['task']==row['task'] and r['repeat']==row['repeat'] and r['method']==row['method'] and r['member']=='A1')
        path=probe.HISTORY/f"{old['slot']:02d}.raw.txt";a=io.read(path)
        # Explicit adaptation: preserve complete actual local conclusion; no old team choice exists.
        value=dict(choice=None,reasoning=a['conclusion'],used_contributions=[]);raw=json.dumps(value,ensure_ascii=False)
        trace.append(dict(slot=row['slot'],original=str(path.relative_to(ROOT)),sha256=io.digest(path),adapted=True,adaptation='conclusion -> reasoning; choice=null; no historical team choice claimed'))
        return dict(status='completed',usage=dict(input_tokens=10,output_tokens=10),output=[dict(type='message',content=[dict(type='output_text',text=raw)])])
    result=run(p,p/'history_replay',transport=replay,local_validation=True)
    assert result['attempts']==24 and result['status']=='completed'
    requests=[io.strict_json(x) for x in (p/'history_replay/requests.jsonl').read_text(encoding='utf-8').splitlines()]
    maximum=max(x['estimated_input_count'] for x in requests);assert maximum<8192
    report=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),model_requests=0,adapted_real_replay_attempts=24,
        maximum_input_estimate=maximum,input_limit=8192,trace=trace,
        limitations=['Historical local conclusions are adapted, not real final-team answers.',
                    'Choice-field and boundary handling additionally tested with explicit local fixtures.',
                    'No semantic outcome or final performance measured by local replay.'])
    io.write(p/'PREFLIGHT.json',report)
    return {k:v for k,v in report.items() if k!='trace'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['freeze','preflight','run']);parser.add_argument('--prepared',required=True,type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.command=='freeze':print(json.dumps(freeze(args.prepared)))
    elif args.command=='preflight':print(json.dumps(preflight(args.prepared)))
    else:
        if args.output is None:parser.error('--output required')
        run(args.prepared,args.output)
