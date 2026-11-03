"""Bounded H1 development runner. Dynamic stage2, no retries, no automatic expansion."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from tokenizers import Tokenizer
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import local_judgment_handle_contract as contract
import local_rule_frontend as frontend

ROOT=io.ROOT
TOKENIZER=ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'
MAX_REQUESTS,CAP,TOTAL_CAP=72,1536,110592
RUBRICS=[ROOT/'design/LOCAL_RULE_H1_SCORING_20261025.md',ROOT/'design/LOCAL_RULE_TASK_REVIEW_20261025.md']


def child(root,name):
    path=(Path(root)/name).resolve()
    if not path.is_relative_to(Path(root).resolve()):raise ValueError('path leaves root')
    return path


def freeze(output):
    p=Path(output);frontend.prepare(p)
    io.write(p/'config.json',dict(provider='deepseek',model='deepseek-flash',base_url='https://api.deepseek.com',
        generation=dict(reasoning_effort='none',temperature=0.7,max_input_tokens=8192),
        protocol=dict(transport_retries_per_request=0,max_format_repairs=0,request_timeout_seconds=120)))
    for source in RUBRICS:(p/source.name).write_bytes(source.read_bytes())
    # Evaluation points are frozen for offline scoring and never read by run().
    (p/'OFFLINE_REVIEW_POINTS.json').write_bytes((frontend.TASKS/'offline/REVIEW_POINTS.json').read_bytes())
    code=[Path(__file__),Path(frontend.__file__),Path(io.__file__),Path(contract.__file__),
          ROOT/'src/coreta/model_client.py',ROOT/'src/coreta/schemas.py']
    io.write(p/'manifest.json',dict(version='rule-local-frontend/1',max_requests=72,output_cap=1536,total_output_cap=110592,
        tokenizer_sha256=io.digest(TOKENIZER),
        files={str(x.relative_to(p)).replace('\\','/'):io.digest(x) for x in p.rglob('*') if x.is_file() and x.name!='manifest.json'},
        code_sha256={str(x.relative_to(ROOT)).replace('\\','/'):io.digest(x) for x in code}))
    verify(p)
    return dict(status='FROZEN_NOT_AUTHORIZED',manifest_sha256=io.digest(p/'manifest.json'))


def verify(p):
    p=Path(p);m=io.read(p/'manifest.json')
    if m.get('version')!='rule-local-frontend/1':raise ValueError('wrong batch version')
    if (m['max_requests'],m['output_cap'],m['total_output_cap'])!=(72,1536,110592):raise ValueError('budget differs')
    for root,files in [(p,m['files']),(ROOT,m['code_sha256'])]:
        for name,sha in files.items():
            if io.digest(child(root,name))!=sha:raise ValueError('frozen file changed: '+name)
    if io.digest(TOKENIZER)!=m['tokenizer_sha256']:raise ValueError('tokenizer changed')
    plan=io.read(p/'PLAN.json');expected=[]
    for n in range(1,7):
        for member in ('A1','A2','A3'):
            for method in frontend.METHODS if n%2 else frontend.METHODS[::-1]:
                for stage in ('first','second'):
                    expected.append((f'rule-dev-{n:02d}',member,method,stage))
    if [(r['task'],r['member'],r['method'],r['stage']) for r in plan['schedule']]!=expected:raise ValueError('schedule differs')
    for row in plan['schedule']:
        packet=io.read(child(p,row['context']))
        if packet['member']!=row['member'] or packet['task']['task_id']!=row['task']:raise ValueError('binding differs')
        if row['group']!='/'.join([row['task'],row['member'],row['method']]):raise ValueError('group differs')
        if row['stage']=='first':
            template=io.read(p/'first_requests'/row['task']/row['member']/(row['method']+'.json'))
            if template!=frontend.request('first',row['method'],packet):raise ValueError('template differs')
    config=io.read(p/'config.json')
    if config['base_url']!='https://api.deepseek.com' or config['model']!='deepseek-flash':raise ValueError('destination differs')
    if config['protocol']['transport_retries_per_request']!=0 or config['protocol']['max_format_repairs']!=0:raise ValueError('retry prohibited')
    return m,plan,config


def gates(p):
    p=Path(p);sha=io.digest(p/'manifest.json')
    pre=io.read(p/'PREFLIGHT.json');review=io.read(p/'EXPERIMENT_REVIEW.json')
    if pre.get('status')!='passed' or pre.get('manifest_sha256')!=sha:raise ValueError('fresh preflight required')
    if any(review.get(k)!=v for k,v in dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED',manifest_sha256=sha).items()):raise ValueError('fresh review required')
    auth=io.read(p/'AUTHORIZATION.json')
    if not (auth.get('authorized') is True and auth.get('max_requests')==72 and auth.get('manifest_sha256')==sha and
            auth.get('destination')=='https://api.deepseek.com/responses' and auth.get('user_authorization_text')):
        raise ValueError('specific batch authorization required')


def export(p,output,state,roster):
    io.write(output/'progress.json',state)
    lookup={r['slot']:r for r in state['rows']}
    rows=[lookup.get(i,dict(row,slot=i,status='not_run',answer=None)) for i,row in enumerate(roster,1)]
    io.write(output/'review.json',dict(mode=state['mode'],status=state['status'],rows=rows))
    views=[];keys=[]
    for row in roster[::2]:
        firstslot=roster.index(row)+1;first=lookup.get(firstslot);second=lookup.get(firstslot+1)
        tag=hashlib.sha256((row['group']+'/h1-review').encode()).hexdigest()[:16]
        context=io.read(child(p,row['context']))
        views.append(dict(id=tag,task=context['task'],public_sources=context['public_sources'],own_sources=context['own_sources'],
            historical_work=context['historical_work'],first_status=first.get('status') if first else 'not_run',
            first=first.get('answer') if first else None,second_status=second.get('status') if second else 'not_run',
            final=second.get('answer') if second else None,annotation=None))
        keys.append(dict(id=tag,group=row['group'],method=row['method'],member=row['member'],task=row['task']))
    io.write(output/'ANNOTATION_VIEWS.json',dict(mode=state['mode'],views=sorted(views,key=lambda x:x['id'])))
    io.write(output/'ANNOTATION_KEY.json',keys)


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
            if client.attempts>=72 or state['reserved_output']+CAP>TOTAL_CAP:raise ValueError('budget exhausted')
            request=frontend.request(row['stage'],row['method'],packet)
            io.write(out/'actual_requests'/f'{slot:02d}.json',request)
            payload=client.payload(request['instructions'],request['schema'],CAP);state['reserved_output']+=CAP
            try:
                raw=client.complete(payload,deadline=time.monotonic()+180,logical_seed=1)
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


def preflight(p):
    p=Path(p);verify(p)
    if (p/'mock_validation').exists():raise ValueError('new preflight directory required')
    history=[]
    for folder in ('local-judgment-moon-supplement-live-20261025-r1','local-rule-resource-calibration-live-20261025-r1'):
        live=ROOT/'runs'/folder
        for row in io.read(live/'progress.json')['completed']:
            history.append((live/f'{row["slot"]:02d}.raw.txt',row['answer']))
    trace=[];tok=Tokenizer.from_file(str(TOKENIZER));count=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
    def mock(payload,timeout):
        packet=io.strict_json(payload['instructions'].split('PACKET=',1)[1]);path,old=history[len(trace)%len(history)]
        raw_original=io.read(path);source=(packet['own_sources'] or packet['public_sources'])[0]['ref']
        if 'historical_work' in packet:
            value=dict(text=json.dumps(raw_original,ensure_ascii=False),status='proceed',source_ids=[source],target_ids=['new'])
        else:value=dict(conclusion=raw_original['conclusion'],status=raw_original.get('status','conditional'),source_ids=[source],scope=raw_original.get('scope',''),missing=raw_original.get('missing',[]))
        raw=json.dumps(value,ensure_ascii=False)
        if count(raw)>CAP:raise RuntimeError('adapted response exceeds cap')
        trace.append(dict(original=str(path),sha256=io.digest(path),input_estimate=count(json.dumps(payload,ensure_ascii=False))+256,output_tokens=count(raw),adapted=True))
        return dict(status='completed',usage=dict(input_tokens=count(json.dumps(payload)),output_tokens=count(raw)),output=[dict(type='message',content=[dict(type='output_text',text=raw)])])
    result=run(p,p/'mock_validation',transport=mock,local_validation=True)
    assert result['attempts']==72 and result['status']=='completed'
    report=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),mock_attempts=72,model_requests=0,
        real_history_inputs=len(history),maximum_input_estimate=max(x['input_estimate'] for x in trace),
        maximum_adapted_output_tokens=max(x['output_tokens'] for x in trace),adaptation_provenance=trace,
        real_first_stage_provider_outputs=0,limitations=['First-stage history is explicitly adapted, not autonomous question behavior.',
        'Synthetic new source handles do not certify new-task semantics.','All72 mock outputs are marked local_mock; not experiment results.'])
    io.write(p/'PREFLIGHT.json',report)
    return {k:v for k,v in report.items() if k!='adaptation_provenance'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['freeze','preflight','run']);parser.add_argument('--prepared',required=True,type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.command=='freeze':print(json.dumps(freeze(args.prepared)))
    elif args.command=='preflight':print(json.dumps(preflight(args.prepared)))
    else:
        if args.output is None:parser.error('--output required')
        run(args.prepared,args.output)
