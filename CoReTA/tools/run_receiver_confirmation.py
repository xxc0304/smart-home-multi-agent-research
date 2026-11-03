"""New-instance confirmation with shared setup, native-member pairing and separate controls."""
import argparse
import copy
import json
import random
import time
from pathlib import Path
from tokenizers import Tokenizer
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import prepare_receiver_baseline_20261026 as contract
import minimal_final_answer_contract as terminal
import receiver_target_view as view

ROOT=io.ROOT
SOURCE=ROOT/'research/receiver-confirmation-20261026-v1'
DEFAULT=ROOT/'runs/receiver-confirmation-prepared-20261026-r3'
TOKENIZER=ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'
VERSION='receiver-confirmation/1'
TASKS=('030','033','control-correct-with-wrong-report','control-genuinely-underdetermined')
MEMBERS=('A1','A2','A3')
LIMITS=dict(requests=56,output=86016,input=786432,per_output=1536,per_input=16384)


def config():
    return dict(provider='deepseek',model='deepseek-flash',base_url='https://api.deepseek.com',
        generation=dict(reasoning_effort='none',temperature=0.7,max_input_tokens=16384),
        protocol=dict(transport_retries_per_request=0,max_format_repairs=0,request_timeout_seconds=120))


def schedule():
    rows=[]
    for ti,task in enumerate(TASKS):
        kind='benchmark' if ti<2 else 'control'
        if kind=='benchmark':
            rows.append(dict(task=task,kind=kind,stage='draft',receiver='PUBLIC_SOLVER',method='shared_setup',unit=task+'-draft'))
            for member in MEMBERS:
                rows.append(dict(task=task,kind=kind,stage='contribute',receiver=member,method='shared_setup',unit=task+'-contribute-'+member))
        for mi,member in enumerate(MEMBERS):
            methods=('ordinary','diagnose') if (ti+mi)%2==0 else ('diagnose','ordinary')
            for method in methods:
                for stage in ('first','final'):
                    rows.append(dict(task=task,kind=kind,receiver=member,method=method,stage=stage,unit=f'{task}-{member}-{method}'))
    return [dict(row,slot=i) for i,row in enumerate(rows,1)]


def child(root,relative):
    base=Path(root).resolve();path=(base/relative).resolve()
    if not path.is_relative_to(base):raise ValueError('path escape')
    return path


def freeze(prepared):
    p=Path(prepared)
    if p.exists():raise ValueError('new preparation directory required')
    source_manifest=io.read(SOURCE/'SOURCE_MANIFEST.json')
    for rel,sha in source_manifest['files'].items():
        if io.digest(child(SOURCE,rel))!=sha:raise ValueError('source packet changed: '+rel)
    p.mkdir(parents=True)
    for task in TASKS:
        if task in TASKS[:2]:
            for member in MEMBERS:
                io.write(p/'members'/task/f'{member}.json',io.read(SOURCE/'benchmark'/task/'members'/f'{member}.json'))
            io.write(p/'public'/f'{task}.json',io.read(SOURCE/'benchmark'/task/'public_draft_input.json'))
            io.write(p/'offline'/f'{task}.json',io.read(SOURCE/'benchmark'/task/'offline/reference.json'))
        else:
            for member in MEMBERS:
                context=io.read(SOURCE/'controls'/task/f'{member}.json')
                context['task']['task_id']='receiver-case-'+str(TASKS.index(task)+1).zfill(2)
                context['historical_author']='ARCHIVED_AUTHOR'
                io.write(p/'controls'/task/f'{member}.json',context)
            io.write(p/'offline'/f'{task}.json',io.read(SOURCE/'offline_controls'/f'{task}.json'))
    for name in ['PLAN.md','READINESS_CONTRACT.md','SEMANTIC_RUBRIC.json','EXPOSURE_AUDIT.json']:
        (p/name).write_bytes((SOURCE/name).read_bytes())
    io.write(p/'PLAN.json',dict(version=VERSION,schedule=schedule(),limits=LIMITS,
        setup_calls=8,paired_calls=48,status='frozen_not_authorized'))
    io.write(p/'config.json',config())
    code=[Path(__file__),Path(view.__file__),Path(contract.__file__),Path(terminal.__file__),Path(io.__file__),
          ROOT/'src/coreta/model_client.py',ROOT/'src/coreta/schemas.py',ROOT/'tools/check_receiver_confirmation.py']
    hashes={}
    for file in code:
        rel=file.relative_to(ROOT).as_posix();dest=p/'frozen_source'/rel
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(file.read_bytes());hashes[rel]=io.digest(file)
    io.write(p/'frozen_source/SHA256.json',hashes)
    io.write(p/'manifest.json',dict(version=VERSION,limits=LIMITS,code_sha256=hashes,
        source_manifest_sha256=io.digest(SOURCE/'SOURCE_MANIFEST.json'),tokenizer_sha256=io.digest(TOKENIZER),
        files={x.relative_to(p).as_posix():io.digest(x) for x in p.rglob('*') if x.is_file()}))
    verify(p)
    return dict(status='frozen_not_authorized',manifest_sha256=io.digest(p/'manifest.json'))


def verify(prepared):
    p=Path(prepared);m=io.read(p/'manifest.json')
    if m['version']!=VERSION or m['limits']!=LIMITS:raise ValueError('wrong batch version or limits')
    for root,files in [(p,m['files']),(ROOT,m['code_sha256'])]:
        for rel,sha in files.items():
            if io.digest(child(root,rel))!=sha:raise ValueError('frozen file changed: '+rel)
    if io.digest(TOKENIZER)!=m['tokenizer_sha256']:raise ValueError('tokenizer changed')
    plan=io.read(p/'PLAN.json')
    if plan['schedule']!=schedule() or plan['limits']!=LIMITS or io.read(p/'config.json')!=config():
        raise ValueError('plan/config changed')
    return m,plan


def gates(p):
    sha=io.digest(p/'manifest.json')
    for name,required in [('PREFLIGHT.json',dict(status='passed')),
                          ('EXPERIMENT_REVIEW.json',dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED'))]:
        value=io.read(p/name)
        if value.get('manifest_sha256')!=sha or any(value.get(k)!=v for k,v in required.items()):
            raise ValueError('fresh gate missing: '+name)
    a=io.read(p/'AUTHORIZATION.json')
    expected=dict(authorized=True,manifest_sha256=sha,max_requests=56,max_output_tokens=86016,
        max_input_tokens=786432,destination='https://api.deepseek.com/responses')
    if any(a.get(k)!=v for k,v in expected.items()) or not a.get('user_authorization_text'):
        raise ValueError('specific batch authorization required')


def assemble(p,row,drafts,contributions):
    if row['kind']=='control':
        return io.read(p/'controls'/row['task']/f"{row['receiver']}.json")
    if row['task'] not in drafts or set(contributions.get(row['task'],{}))!=set(MEMBERS):return None
    base=io.read(p/'members'/row['task']/f"{row['receiver']}.json")
    reports={}
    for member in MEMBERS:
        original=io.read(p/'members'/row['task']/f'{member}.json')
        reports[member]=dict(text=contributions[row['task']][member]['text'],
            disclosed_originals=original['own_sources'],disclosure='host-attached full assigned original; not semantic certification')
    return dict(**base,shared_contributions=reports,execution_report=None,
                historical_work=copy.deepcopy(drafts[row['task']]),historical_author='PUBLIC_SOLVER')


def request_for(p,row,drafts,contributions,firsts):
    if row['stage']=='draft':
        packet=io.read(p/'public'/f"{row['task']}.json")
        instruction=('Solve the task using only the supplied public information. No private reports have been provided. '
            'Do not invent those reports. Return exactly one JSON object with choice (listed ID, or null if genuinely unresolved) '
            'and reasoning (your substantive explanation).\nPACKET=')
        return dict(instructions=instruction+json.dumps(packet,ensure_ascii=False),schema=terminal.schema(packet),max_output_tokens=1536),None
    if row['stage']=='contribute':
        packet=io.read(p/'members'/row['task']/f"{row['receiver']}.json")
        instruction=('Use the task, public information and only your own supplied original to provide useful local evidence or reasoning. '
            'No team draft or peer private material is available. Explain scope and unresolved conditions, do not invent facts, '
            'and do not assume that your local knowledge must settle the entire task. Your assigned source will be disclosed '
            'verbatim by the host; do not recopy it merely for formatting. Return one JSON object with nonempty text.\nPACKET=')
        schema=dict(type='object',additionalProperties=False,required=['text'],properties=dict(text=dict(type='string',minLength=1)))
        return dict(instructions=instruction+json.dumps(packet,ensure_ascii=False),schema=schema,max_output_tokens=1536),None
    context=assemble(p,row,drafts,contributions)
    if context is None:return None,'blocked_setup'
    if row['stage']=='final' and row['unit'] not in firsts:return None,'blocked_upstream'
    return (view.first_request(context,row['method']) if row['stage']=='first'
            else view.final_request(context,firsts[row['unit']])),None


def run(prepared,output,*,transport=None,local_validation=False):
    p,out=Path(prepared),Path(output);manifest,plan=verify(p)
    if local_validation:
        if transport is None:raise ValueError('explicit local fixture transport required')
    else:gates(p)
    if out.exists():raise ValueError('new output required; no resume')
    out.mkdir(parents=True);io.write(out/'manifest.json',manifest)
    state=dict(mode='local_fixture' if local_validation else 'live',status='running',attempts=0,
        input_tokens=0,output_tokens=0,reserved_input=0,reserved_output=0,unknown_usage=False,
        over_cap=False,consecutive_unreadable=0,rows=[],error=None)
    drafts,contributions,firsts={},{},{}
    current=None;client=None
    def save():
        if client:state['attempts']=client.attempts
        io.write(out/'progress.json',state);done={r['slot']:r for r in state['rows']}
        io.write(out/'review.json',dict(mode=state['mode'],status=state['status'],rows=[
            done.get(r['slot'],dict(r,status='not_run',answer=None)) for r in plan['schedule']]))
    def log(name,value):
        value=dict(value,slot=current)
        with (out/name).open('a',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False)+'\n')
        if name!='responses.jsonl':return
        response=value.get('response')
        if not isinstance(response,dict):state['unknown_usage']=True;return
        text=''.join(c['text'] for item in response.get('output',[]) for c in item.get('content',[])
                     if c.get('type')=='output_text' and isinstance(c.get('text'),str))
        (out/f'{current:03d}.raw.txt').write_text(text,encoding='utf-8')
        for key,limit in [('input_tokens','per_input'),('output_tokens','per_output')]:
            amount=response.get('usage',{}).get(key)
            if type(amount) is not int or amount<0:state['unknown_usage']=True
            else:
                state[key]+=amount
                if amount>LIMITS[limit]:state['over_cap']=True
    tok=Tokenizer.from_file(str(TOKENIZER))
    client=DeepSeekClient(config(),log,transport=transport,token_counter=lambda s:len(tok.encode(s,add_special_tokens=False).ids))
    save()
    try:
        for row in plan['schedule']:
            current=row['slot'];req,blocked=request_for(p,row,drafts,contributions,firsts)
            if blocked:state['rows'].append(dict(row,status=blocked,answer=None));save();continue
            payload=client.payload(req['instructions'],req['schema'],1536);size=client.size(payload)
            if (size>LIMITS['per_input'] or client.attempts>=56 or
                max(state['reserved_input'],state['input_tokens'])+size>LIMITS['input'] or
                state['reserved_output']+1536>LIMITS['output']):raise RuntimeError('pre-request budget exceeded')
            io.write(out/'actual_requests'/f'{current:03d}.json',req)
            state['reserved_input']+=size;state['reserved_output']+=1536
            try:
                raw=client.complete(payload,deadline=time.monotonic()+150,logical_seed=1)
                if state['unknown_usage'] or state['over_cap'] or state['input_tokens']>LIMITS['input'] or state['output_tokens']>LIMITS['output']:
                    raise RuntimeError('unknown or excessive actual usage')
                packet=io.strict_json(req['instructions'].split('PACKET=',1)[1])
                answer=terminal.decode(raw,packet) if row['stage'] in {'draft','final'} else contract.decode_first(raw)
            except (ValueError,ProtocolError) as exc:
                if state['unknown_usage'] or state['over_cap'] or (isinstance(exc,ProtocolError) and exc.code!='SCHEMA_ERROR'):raise
                state['rows'].append(dict(row,status='quarantined',answer=None,error=str(exc)))
                state['consecutive_unreadable']+=1;save()
                if state['consecutive_unreadable']>=2:raise RuntimeError('two consecutive unreadable core outputs') from exc
                continue
            if row['stage']=='draft':drafts[row['task']]=answer
            elif row['stage']=='contribute':contributions.setdefault(row['task'],{})[row['receiver']]=answer
            elif row['stage']=='first':firsts[row['unit']]=answer
            state['rows'].append(dict(row,status='readable',answer=answer));state['consecutive_unreadable']=0;save()
        state['status']='completed_with_quarantine' if any(r['status']=='quarantined' for r in state['rows']) else 'completed'
    except Exception as exc:
        state['status']='stopped';state['error']=f'{type(exc).__name__}: {exc}'
        if current is not None and not any(r['slot']==current for r in state['rows']):
            row=next(r for r in plan['schedule'] if r['slot']==current)
            state['rows'].append(dict(row,status='system_error',answer=None,error=state['error']))
    finally:save()
    return state


def export(prepared,output):
    """Offline evaluation only; do not call this function inside the model-generation loop."""
    p,out=Path(prepared),Path(output);review=io.read(out/'review.json');rubrics=io.read(p/'SEMANTIC_RUBRIC.json')
    firsts={r['unit']:r for r in review['rows'] if r['stage']=='first'}
    finals=[]
    for row in review['rows']:
        if row['stage']!='final':continue
        evaluation=io.read(p/'offline'/f"{row['task']}.json")
        choice=row['answer']['choice'] if row['status']=='readable' else None
        expected=evaluation['correct_option_id'] if row['kind']=='benchmark' else evaluation['expected_choice']
        match=(choice==expected if row['status']=='readable' else None)
        finals.append(dict(row,choice_match=match,unresolved=row['status']=='readable' and choice is None,
                          semantic_application=None,metric='benchmark_reference_choice' if row['kind']=='benchmark' else 'authored_control_choice'))
    io.write(out/'SCORES.json',dict(mode=review['mode'],benchmark=[r for r in finals if r['kind']=='benchmark'],
        controls=[r for r in finals if r['kind']=='control'],warning='Do not combine controls and benchmark as one accuracy; null may be the expected control choice.'))
    pairs=[]
    for task in TASKS:
        for receiver in MEMBERS:
            matches={r['method']:r for r in finals if r['task']==task and r['receiver']==receiver}
            pairs.append(dict(task=task,receiver=receiver,kind='benchmark' if task in TASKS[:2] else 'control',
                              ordinary=matches['ordinary'],diagnose=matches['diagnose'],semantic_difference=None))
    io.write(out/'RECEIVER_PAIRS.json',dict(mode=review['mode'],pairs=pairs))
    shuffled=list(finals);random.Random(20261026).shuffle(shuffled);forms=[];mapping=[]
    for i,row in enumerate(shuffled,1):
        ref=f'R{i:02d}';mapping.append(dict(id=ref,task=row['task'],receiver=row['receiver'],method=row['method'],slot=row['slot']))
        forms.append(dict(id=ref,task=row['task'],receiver=row['receiver'],status=row['status'],answer=row['answer'],
            first_analysis=firsts[row['unit']].get('answer'),rubric=rubrics[row['task']],
            target_alignment=None,diagnosis_quality=None,evidence_application=None,decision_quality=None,
            new_error=None,evidence_quotes=[],notes=None))
    io.write(out/'SEMANTIC_REVIEW_FORM.json',dict(mode=review['mode'],independent_blind=False,rows=forms))
    io.write(out/'OFFLINE_REVIEW_MAPPING.json',mapping)
    progress=io.read(out/'progress.json')
    usage={k:progress[k] for k in ['input_tokens','output_tokens']}
    roster={r['slot']:r for r in io.read(p/'PLAN.json')['schedule']}
    groups={m:dict(requests=0,input_tokens=0,output_tokens=0,unknown_usage=False)
            for m in ['shared_setup','ordinary','diagnose']}
    request_log=out/'requests.jsonl'
    response_log=out/'responses.jsonl'
    if request_log.exists():
        for row in map(json.loads,request_log.read_text(encoding='utf-8').splitlines()):
            groups[roster[row['slot']]['method']]['requests']+=1
    if response_log.exists():
        for row in map(json.loads,response_log.read_text(encoding='utf-8').splitlines()):
            group=groups[roster[row['slot']]['method']]
            quantities=(row.get('response') or {}).get('usage') or {}
            for field in ['input_tokens','output_tokens']:
                amount=quantities.get(field)
                if type(amount) is int and amount>=0:group[field]+=amount
                else:group['unknown_usage']=True
    io.write(out/'COSTS.json',dict(mode=review['mode'],groups=groups,
        note='Shared setup counted once; known usage only. Unknown usage is explicit, not zero-cost certification.'))
    io.write(out/'EXPORT_SUMMARY.json',dict(mode=review['mode'],final_units=len(finals),benchmark_units=12,control_units=12,
        setup_calls_observed=groups['shared_setup']['requests'],
        missing_final_units=sum(r['status']!='readable' for r in finals),observed_usage=usage,
        unknown_usage=progress['unknown_usage'],attempts=progress['attempts']))
    return dict(final_units=len(finals),benchmark_units=12,control_units=12,missing_final_units=sum(r['status']!='readable' for r in finals))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['freeze','verify','run','export']);a.add_argument('--prepared',type=Path,default=DEFAULT);a.add_argument('--output',type=Path)
    args=a.parse_args()
    if args.command=='freeze':result=freeze(args.prepared)
    elif args.command=='verify':result=verify(args.prepared)[0]
    else:
        if args.output is None:a.error('--output required')
        result=run(args.prepared,args.output) if args.command=='run' else export(args.prepared,args.output)
    print(json.dumps(result,ensure_ascii=False))
