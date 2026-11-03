"""Bounded new-instance confirmation; same candidate, two isolated repeats, no retries."""
import argparse
import json
import time
from pathlib import Path
from tokenizers import Tokenizer
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import local_judgment_handle_contract as contract
import local_rule_frontend as frontend
import run_local_rule_frontend as base
import prepare_local_rule_confirmation as construction

ROOT=io.ROOT
TOKENIZER=ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'
DATA=construction.DATA
MAX_REQUESTS,CAP,TOTAL_CAP=144,1536,221184
child=base.child
RUBRIC=ROOT/'design/LOCAL_RULE_CONFIRMATION_PLAN_20261025.md'

def schedule():
    rows=[]
    for idx,n in enumerate(range(7,13)):
        for member in ('A1','A2','A3'):
            for repeat in (1,2):
                order=frontend.METHODS if (idx+repeat)%2 else frontend.METHODS[::-1]
                for method in order:
                    for stage in ('first','second'):
                        task=f'rule-confirm-{n:02d}'
                        rows.append(dict(task=task,member=member,repeat=repeat,method=method,stage=stage,
                            group=f'{task}/{member}/r{repeat}/{method}',context=f'contexts/{task}/{member}.json'))
    return rows

def freeze(output):
    p=Path(output)
    if p.exists():raise ValueError('new prepared directory required')
    source=io.read(DATA/'manifest.json')
    for name,sha in source['files'].items():
        if io.digest(child(DATA,name))!=sha:raise ValueError('source data changed')
    p.mkdir(parents=True)
    for row in schedule():
        packet=io.read(DATA/row['task']/'packets'/f"{row['member']}.json")
        io.write(p/row['context'],packet)
        if row['stage']=='first':io.write(p/'first_requests'/row['task']/row['member']/(row['method']+'.json'),frontend.request('first',row['method'],packet))
    io.write(p/'PLAN.json',dict(tasks=6,members=3,repeats=2,max_requests=144,schedule=schedule(),
        primary='Effective scoped local contribution, final delivery; correct-control behavior and harm separately.',
        effect_scope='New instances in same constructed task families; not team adoption or full-architecture accuracy.'))
    io.write(p/'config.json',dict(provider='deepseek',model='deepseek-flash',base_url='https://api.deepseek.com',
        generation=dict(reasoning_effort='none',temperature=0.7,max_input_tokens=8192),
        protocol=dict(transport_retries_per_request=0,max_format_repairs=0,request_timeout_seconds=120)))
    (p/'SCORING_AND_PLAN.md').write_bytes(RUBRIC.read_bytes())
    (p/'OFFLINE_REVIEW_POINTS.json').write_bytes((DATA/'offline/REVIEW_POINTS.json').read_bytes())
    code=[Path(__file__),Path(base.__file__),Path(construction.__file__),Path(frontend.__file__),Path(io.__file__),Path(contract.__file__),ROOT/'src/coreta/model_client.py',ROOT/'src/coreta/schemas.py']
    io.write(p/'manifest.json',dict(version='rule-local-confirmation/1',max_requests=MAX_REQUESTS,output_cap=CAP,total_output_cap=TOTAL_CAP,
        source_manifest_sha256=io.digest(DATA/'manifest.json'),tokenizer_sha256=io.digest(TOKENIZER),
        files={str(x.relative_to(p)).replace('\\','/'):io.digest(x) for x in p.rglob('*') if x.is_file()},
        code_sha256={str(x.relative_to(ROOT)).replace('\\','/'):io.digest(x) for x in code}))
    verify(p)
    return dict(status='FROZEN_NOT_AUTHORIZED',manifest_sha256=io.digest(p/'manifest.json'))

def verify(p):
    p=Path(p);m=io.read(p/'manifest.json')
    if m['version']!='rule-local-confirmation/1' or (m['max_requests'],m['output_cap'],m['total_output_cap'])!=(MAX_REQUESTS,CAP,TOTAL_CAP):raise ValueError('batch or budget differs')
    for root,files in [(p,m['files']),(ROOT,m['code_sha256'])]:
        for name,sha in files.items():
            if io.digest(child(root,name))!=sha:raise ValueError('frozen file changed: '+name)
    if io.digest(TOKENIZER)!=m['tokenizer_sha256']:raise ValueError('tokenizer changed')
    plan=io.read(p/'PLAN.json');config=io.read(p/'config.json')
    if plan['schedule']!=schedule():raise ValueError('schedule differs')
    for row in plan['schedule']:
        packet=io.read(child(p,row['context']))
        if packet['task']['task_id']!=row['task'] or packet['member']!=row['member']:raise ValueError('binding differs')
        if set(packet)!={'task','member','public_sources','own_sources','historical_work'}:raise ValueError('unexpected context keys')
        if any(s['ref']!=row['member']+'.S1' for s in packet['own_sources']):raise ValueError('foreign source')
        if row['stage']=='first' and io.read(p/'first_requests'/row['task']/row['member']/(row['method']+'.json'))!=frontend.request('first',row['method'],packet):raise ValueError('first request differs')
    if config!=dict(provider='deepseek',model='deepseek-flash',base_url='https://api.deepseek.com',
        generation=dict(reasoning_effort='none',temperature=0.7,max_input_tokens=8192),
        protocol=dict(transport_retries_per_request=0,max_format_repairs=0,request_timeout_seconds=120)):raise ValueError('config differs')
    return m,plan,config

def gates(p):
    p=Path(p);sha=io.digest(p/'manifest.json')
    pre=io.read(p/'PREFLIGHT.json');review=io.read(p/'EXPERIMENT_REVIEW.json');auth=io.read(p/'AUTHORIZATION.json')
    if pre.get('status')!='passed' or pre.get('manifest_sha256')!=sha:raise ValueError('fresh preflight required')
    if any(review.get(k)!=v for k,v in dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED',manifest_sha256=sha).items()):raise ValueError('fresh review required')
    if not (auth.get('authorized') is True and auth.get('max_requests')==144 and auth.get('max_output_tokens')==TOTAL_CAP and auth.get('manifest_sha256')==sha and auth.get('destination')=='https://api.deepseek.com/responses' and auth.get('user_authorization_text')):raise ValueError('specific batch authorization required')

def export(p,output,state,roster):
    base.export(p,output,state,roster)
    keys=io.read(output/'ANNOTATION_KEY.json');repeats={r['group']:r['repeat'] for r in roster}
    for key in keys:key['repeat']=repeats[key['group']]
    io.write(output/'ANNOTATION_KEY.json',keys)

def preflight(p):
    p=Path(p);_,plan,config=verify(p)
    history=io.read(construction.OLD/'review.json')['rows'];trace=[]
    tok=Tokenizer.from_file(str(TOKENIZER));count=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
    def replay(payload,timeout):
        row=plan['schedule'][len(trace)];oldtask='rule-dev-'+f"{int(row['task'].rsplit('-',1)[1])-6:02d}"
        old=next(x for x in history if x['task']==oldtask and x['member']==row['member'] and x['method']==row['method'] and x['stage']==row['stage'])
        path=construction.OLD/f"{old['slot']:02d}.raw.txt";raw=path.read_text(encoding='utf-8')
        trace.append(dict(slot=len(trace)+1,repeat=row['repeat'],original=str(path.relative_to(ROOT)),sha256=io.digest(path),
            input_estimate=count(json.dumps(payload,ensure_ascii=False))+256,output_tokens=count(raw),adapted=False))
        return dict(status='completed',usage=dict(input_tokens=count(json.dumps(payload)),output_tokens=count(raw)),output=[dict(type='message',content=[dict(type='output_text',text=raw)])])
    result=run(p,p/'history_replay',transport=replay,local_validation=True)
    assert result['status']=='completed' and result['attempts']==144
    assert not any(r['answer']['annotation_issues'] for r in result['rows'])
    assert max(x['input_estimate'] for x in trace)<8192 and max(x['output_tokens'] for x in trace)<=CAP
    report=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),model_requests=0,
        replay_attempts=144,unique_real_raw_responses=72,maximum_input_estimate=max(x['input_estimate'] for x in trace),
        maximum_output_tokens=max(x['output_tokens'] for x in trace),annotation_issues=0,trace=trace,
        limitations=['Old task content is not evidence of new task semantic correctness; this checks interfaces and full dynamic execution.',
                    'Observed replay sizes are not a bound on every future provider output.'])
    io.write(p/'PREFLIGHT.json',report)
    return {k:v for k,v in report.items() if k!='trace'}

def run(prepared,output,*,transport=None,local_validation=False):
    p,out=Path(prepared),Path(output);manifest,plan,config=verify(p)
    if local_validation:
        if transport is None:raise ValueError('explicit mock required')
    else:gates(p)
    if out.exists():raise ValueError('new directory required; no resume')
    out.mkdir(parents=True);io.write(out/'manifest.json',manifest)
    state=dict(mode='local_mock' if local_validation else 'live',status='running',attempts=0,input_tokens=0,output_tokens=0,
               unknown_usage=False,reserved_output=0,rows=[],consecutive_unreadable=0,error=None)
    previous={};current=None;roster=plan['schedule']
    def save():export(p,out,state,roster)
    def log(name,value):
        with (out/name).open('a',encoding='utf-8') as stream:stream.write(json.dumps(value,ensure_ascii=False)+'\n')
        if name!='responses.jsonl':return
        response=value.get('response')
        if response is None:state['unknown_usage']=True;return
        text=''.join(part['text'] for item in response.get('output',[]) if item.get('type')=='message'
                     for part in item.get('content',[]) if part.get('type')=='output_text' and isinstance(part.get('text'),str))
        if text:(out/f'{current:02d}.raw.txt').write_text(text,encoding='utf-8')
        for key in ('input_tokens','output_tokens'):
            amount=response.get('usage',{}).get(key)
            if type(amount) is not int or amount<0:state['unknown_usage']=True
            else:
                state[key]+=amount
                if key=='output_tokens' and amount>CAP:state['over_cap']=True
    tok=Tokenizer.from_file(str(TOKENIZER));counter=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
    client=DeepSeekClient(config,log,transport=transport,token_counter=counter);save()
    try:
        for slot,row in enumerate(roster,1):
            current=slot;identity=dict(row,slot=slot);packet=io.read(child(p,row['context']))
            if row['stage']=='second':
                first=previous.get(row['group'])
                if first is None or first['status']=='pass':
                    state['rows'].append(dict(identity,status='blocked_upstream' if first is None else 'skipped_pass',answer=None));save();continue
                packet=frontend.second_packet(packet,first)
            if client.attempts>=MAX_REQUESTS or state['reserved_output']+CAP>TOTAL_CAP:raise ValueError('budget exhausted')
            request=frontend.request(row['stage'],row['method'],packet)
            io.write(out/'actual_requests'/f'{slot:02d}.json',request)
            payload=client.payload(request['instructions'],request['schema'],CAP);state['reserved_output']+=CAP
            try:
                raw=client.complete(payload,deadline=time.monotonic()+180,logical_seed=row['repeat'])
                if state['unknown_usage']:raise RuntimeError('unknown usage')
                if state.get('over_cap') or state['output_tokens']>state['reserved_output']:raise RuntimeError('output budget violation')
                answer=frontend.decode_first(raw,packet) if row['stage']=='first' else contract.decode(raw,'second',packet)[0]
            except (ValueError,ProtocolError) as exc:
                unreadable=(isinstance(exc,ValueError) and not isinstance(exc,ProtocolError)) or (isinstance(exc,ProtocolError) and exc.code=='SCHEMA_ERROR')
                if not unreadable or state['unknown_usage'] or state.get('over_cap'):raise
                state['rows'].append(dict(identity,status='quarantined',answer=None,error_type=type(exc).__name__,error=str(exc)))
                state['consecutive_unreadable']+=1;state['attempts']=client.attempts;save()
                if state['consecutive_unreadable']>=2:raise RuntimeError('two consecutive unreadable outputs') from exc
                continue
            state['consecutive_unreadable']=0
            if row['stage']=='first':previous[row['group']]=answer
            state['rows'].append(dict(identity,status='readable',answer=answer));state['attempts']=client.attempts;save()
        state['status']='completed_with_quarantine' if any(r['status']=='quarantined' for r in state['rows']) else 'completed'
    except Exception as exc:
        if not any(r['slot']==current for r in state['rows']):state['rows'].append(dict(roster[current-1],slot=current,status='failed',answer=None))
        state.update(status='stopped',error_type=type(exc).__name__,error=str(exc));raise
    finally:state['attempts']=client.attempts;save()
    return state



if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['freeze','preflight','run']);parser.add_argument('--prepared',required=True,type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.command=='freeze':print(json.dumps(freeze(args.prepared)))
    elif args.command=='preflight':print(json.dumps(preflight(args.prepared)))
    else:
        if args.output is None:parser.error('--output required')
        run(args.prepared,args.output)
