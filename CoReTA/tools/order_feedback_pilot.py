"""Paired revision of all schema-valid archived drafts; not full collaboration."""
import argparse
import json
from pathlib import Path
import time
from jsonschema import validate
from coreta.model_client import DeepSeekClient
from coreta.workboard.order_constraints import violations
from order_calibration import ROOT, read, write, sha
from run_local_condition_pilot import strict_json

PACK=ROOT/'runs/distributed-order-tasks-prepared-20261024-r2'
ARCHIVES=['order-calibration-live-20261024-r1','order-calibration-live-20261024-r2']


def feedback(order,jobs,rules):
    positions={job:i+1 for i,job in enumerate(order)}
    end={};t=0
    for job in order:
        t+=jobs[job]['duration'];end[job]=t
    failed=violations(order,jobs,rules)
    return dict(positions=positions,completion_times=end,
        checks=[dict(rule=r['id'],status='violates' if r['id'] in failed else 'consistent') for r in rules],
        meaning='Checks refer to the supplied initial order only, not any alternative in its explanation. No corrected order is supplied.')


def prepare(output):
    if output.exists(): raise ValueError('new directory required')
    output.mkdir(parents=True)
    config=read(ROOT/'config/deepseek_flash_inspection.json')
    config['protocol']['transport_retries_per_request']=0
    write(output/'config.json',config)
    client=DeepSeekClient(config,lambda *a:None)
    schedule=[];labels={};sizes=[];archives={}
    for archive in ARCHIVES:
        path=ROOT/'runs'/archive/'progress.json';archives[str(path)]=sha(path)
        for original in read(path)['completed']:
            case=original['case'];folder=PACK/'calibration'/case
            task=read(folder/'task.json');rules=read(folder/'oracle_conditions.json')
            initial=original['answer']
            unit=f"b{ARCHIVES.index(archive)+1}-{case}-r{original['repeat']}"
            failed=violations(initial['order'],task['jobs'],rules)
            labels[unit]=dict(case=case,initial_correct=not failed,initial_violations=failed)
            packet=dict(task=task,source_sheets=[dict(member=a,sources=read(folder/f'{a}.json')['sources'])
                for a in ['A1','A2','A3']],initial=initial)
            schema=dict(type='object',additionalProperties=False,required=['reason','order'],properties=dict(
                reason=dict(type='string',minLength=1),order=dict(type='array',minItems=len(task['jobs']),
                maxItems=len(task['jobs']),items=dict(type='string',enum=list(task['jobs'])))))
            methods=['text','executed'] if len(labels)%2 else ['executed','text']
            for method in methods:
                item={**packet,'execution_feedback':feedback(initial['order'],task['jobs'],rules) if method=='executed' else None}
                instructions=('Review the archived draft against ALL source sheets. It may be correct or incorrect; '
                    'its explanation may disagree with its order. Retain a valid order or repair an invalid one. '
                    'Execution feedback, when supplied, is an exact check of the initial order under these requirements; '
                    'it does not supply a repaired order. Check your final order against all requirements. '
                    'Return one JSON object with a concise reason first and final corrected order LAST. '
                    'Aim for reason under 1600 characters; do not embed another JSON object. No external tools.\nPACKET='
                    +json.dumps(item,ensure_ascii=False))
                filename=unit+'-'+method+'.json'
                write(output/filename,dict(instructions=instructions,schema=schema,max_output_tokens=3072))
                sizes.append(client.size(client.payload(instructions,schema,3072)))
                schedule.append(dict(unit=unit,case=case,method=method,request=filename))
    assert len(labels)==13 and len(schedule)==26 and max(sizes)<32768
    write(output/'offline_initial_labels.json',labels)
    code=['tools/order_feedback_pilot.py','tools/order_calibration.py','tools/run_local_condition_pilot.py',
          'src/coreta/model_client.py','src/coreta/workboard/order_constraints.py']
    write(output/'manifest.json',dict(kind='paired_order_feedback',schedule=schedule,max_requests=26,
        max_output_tokens=79872,files={p.name:sha(p) for p in output.glob('*.json')},
        code_sha256={p:sha(ROOT/p) for p in code},archives=archives,
        pack=str(PACK),pack_manifest_sha256=sha(PACK/'manifest.json'),
        preflight=dict(max_input_count=max(sizes),initials=13,initial_correct=sum(r['initial_correct'] for r in labels.values()),
                       heldout_used=False,network_calls=0)))


def run(prepared,output,transport=None):
    m=read(prepared/'manifest.json')
    if m['kind']!='paired_order_feedback' or len(m['schedule'])!=26: raise ValueError('unexpected batch')
    for name,expected in m['files'].items():
        if name=='offline_initial_labels.json': continue
        if sha(prepared/name)!=expected: raise ValueError('frozen input changed')
    for name,expected in m['code_sha256'].items():
        if sha(ROOT/name)!=expected: raise ValueError('frozen code changed')
    config=read(prepared/'config.json')
    if config['base_url']!='https://api.deepseek.com' or config['protocol']['transport_retries_per_request']!=0:
        raise ValueError('destination/retry mismatch')
    if output.exists(): raise ValueError('new directory required')
    output.mkdir(parents=True);write(output/'manifest.json',m)
    state=dict(status='running',attempts=0,input_tokens=0,output_tokens=0,completed=[])
    def log(name,value):
        with (output/name).open('a',encoding='utf-8') as stream: stream.write(json.dumps(value,ensure_ascii=False)+'\n')
        if name=='responses.jsonl':
            u=value.get('response',{}).get('usage',{})
            if any(type(u.get(k)) is not int or u[k]<0 for k in ['input_tokens','output_tokens']):
                raise ValueError('usage unknown')
            for k in ['input_tokens','output_tokens']:state[k]+=u[k]
    client=DeepSeekClient(config,log,transport=transport)
    write(output/'progress.json',state)
    try:
        for row in m['schedule']:
            request=read(prepared/row['request'])
            if client.attempts>=26 or state['output_tokens']+3072>79872: raise ValueError('budget exhausted')
            raw=client.complete(client.payload(request['instructions'],request['schema'],3072),
                                deadline=time.monotonic()+180,logical_seed=1)
            (output/(row['request']+'.raw.txt')).write_text(raw,encoding='utf-8')
            answer=strict_json(raw);validate(answer,request['schema'])
            state['completed'].append({**row,'answer':answer})
            state['attempts']=client.attempts;write(output/'progress.json',state)
        state['status']='completed'
    except Exception as exc:
        state.update(status='stopped',error=f'{type(exc).__name__}: {exc}');raise
    finally:
        state['attempts']=client.attempts;write(output/'progress.json',state)
    return state


def score(prepared,output):
    m=read(output/'manifest.json');pack=Path(m['pack'])
    if sha(pack/'manifest.json')!=m['pack_manifest_sha256']:raise ValueError('pack changed')
    if sha(prepared/'offline_initial_labels.json')!=m['files']['offline_initial_labels.json']:raise ValueError('labels changed')
    labels=read(prepared/'offline_initial_labels.json'); hashes=read(pack/'manifest.json')['files']
    rows=[]
    for row in read(output/'progress.json')['completed']:
        folder=pack/'calibration'/row['case']
        for name in ['task.json','oracle_conditions.json']:
            if sha(folder/name)!=hashes[(folder/name).relative_to(pack).as_posix()]:raise ValueError('scoring file changed')
        task=read(folder/'task.json');rules=read(folder/'oracle_conditions.json')
        try:failed=violations(row['answer']['order'],task['jobs'],rules);valid=True
        except ValueError:failed=None;valid=False
        rows.append({**{k:row[k] for k in ['unit','case','method']},**labels[row['unit']],
                     'correct':valid and not failed,'violated_rules':failed})
    pairs=[dict(unit=unit,results=[r for r in rows if r['unit']==unit])
           for unit in labels if len([r for r in rows if r['unit']==unit])==2]
    write(output/'offline_scores.json',dict(rows=rows,complete_pairs=pairs,planned_pairs=13))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run','score'])
    parser.add_argument('path',type=Path);parser.add_argument('output',type=Path,nargs='?')
    args=parser.parse_args()
    if args.mode=='prepare':prepare(args.path)
    elif args.mode=='run':run(args.path,args.output)
    else:score(args.path,args.output)
