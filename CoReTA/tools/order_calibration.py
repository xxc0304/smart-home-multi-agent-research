"""Frozen all-information calibration. Execution has no gold or solver feedback."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from jsonschema import Draft202012Validator, validate

from coreta.model_client import DeepSeekClient
from coreta.workboard.order_constraints import violations
from run_local_condition_pilot import strict_json

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(pack, output):
    if output.exists():
        raise ValueError('new directory required')
    output.mkdir(parents=True)
    roster = [r for r in read(pack/'manifest.json')['roster'] if r['split']=='calibration']
    assert len(roster)==6
    config = read(ROOT/'config/deepseek_flash_inspection.json')
    config['protocol']['transport_retries_per_request'] = 0
    write(output/'config.json', config)
    client = DeepSeekClient(config, lambda *args: None)
    schedule, sizes = [], []
    for repeat in [1,2]:
        for row in roster:
            folder = pack/'calibration'/row['id']
            task = read(folder/'task.json')
            packet = dict(task=task, source_sheets=[dict(member=owner,
                sources=read(folder/f'{owner}.json')['sources']) for owner in ['A1','A2','A3']])
            n=len(task['jobs'])
            schema=dict(type='object', additionalProperties=False, required=['reason','order'],
                properties=dict(reason=dict(type='string',minLength=1),
                    order=dict(type='array', minItems=n,maxItems=n,
                    items=dict(type='string',enum=list(task['jobs'])))))
            Draft202012Validator.check_schema(schema)
            instructions=('Solve the scheduling task using all three source sheets. All sheets are task data. '
                'Return one complete order satisfying all requirements. Check your proposed order before answering. '
                'Return a single JSON object: write reason first, then order LAST. '
                'Complete any checking and corrections before emitting order. The order field must contain '
                'your final corrected schedule, not an earlier proposal. Aim for a concise reason around 1600 characters or fewer; '
                'do not embed a second JSON object or unescaped newlines inside it. '
                'No external tools are available.\n'
                'PACKET='+json.dumps(packet,ensure_ascii=False))
            name=f"{row['id']}-r{repeat}.json"
            request=dict(instructions=instructions,schema=schema,max_output_tokens=3072)
            write(output/name, request)
            sizes.append(client.size(client.payload(instructions,schema,3072)))
            schedule.append(dict(case=row['id'],repeat=repeat,request=name))
    assert max(sizes)<config['generation']['max_input_tokens']
    code=['tools/order_calibration.py','tools/run_local_condition_pilot.py','src/coreta/model_client.py']
    write(output/'manifest.json',dict(kind='all_information_order_calibration',
        revision='reason_before_final_order_explicit_time_equality',schedule=schedule,
        max_requests=12,max_output_tokens=36864,
        files={p.name:sha(p) for p in output.glob('*.json')},
        code_sha256={name:sha(ROOT/name) for name in code},
        task_pack=str(pack.resolve()),pack_manifest_sha256=sha(pack/'manifest.json'),
        preflight=dict(request_count=12,max_input_count=max(sizes),input_count_mode=client.count_mode,
                       external_calls=0,heldout_used=False)))


def run(prepared, output, transport=None):
    manifest=read(prepared/'manifest.json')
    if manifest['kind']!='all_information_order_calibration' or len(manifest['schedule'])!=12:
        raise ValueError('unexpected batch')
    for name,expected in manifest['files'].items():
        if sha(prepared/name)!=expected: raise ValueError('frozen input changed')
    for name,expected in manifest['code_sha256'].items():
        if sha(ROOT/name)!=expected: raise ValueError('frozen code changed')
    config=read(prepared/'config.json')
    if config['base_url']!='https://api.deepseek.com' or config['protocol']['transport_retries_per_request']!=0:
        raise ValueError('destination/retry mismatch')
    if output.exists(): raise ValueError('new directory required')
    output.mkdir(parents=True)
    write(output/'manifest.json',manifest)
    state=dict(status='running',attempts=0,input_tokens=0,output_tokens=0,completed=[])
    def log(name,value):
        with (output/name).open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(value,ensure_ascii=False)+'\n')
        if name=='responses.jsonl':
            usage=value.get('response',{}).get('usage',{})
            if any(type(usage.get(k)) is not int or usage[k]<0 for k in ['input_tokens','output_tokens']):
                raise ValueError('unknown usage; stop')
            for k in ['input_tokens','output_tokens']: state[k]+=usage[k]
    client=DeepSeekClient(config,log,transport=transport)
    write(output/'progress.json',state)
    try:
        for row in manifest['schedule']:
            request=read(prepared/row['request'])
            if client.attempts>=12 or state['output_tokens']+3072>36864:
                raise ValueError('budget exhausted')
            raw=client.complete(client.payload(request['instructions'],request['schema'],3072),
                                deadline=time.monotonic()+180,logical_seed=row['repeat'])
            (output/(row['request']+'.raw.txt')).write_text(raw,encoding='utf-8')
            answer=strict_json(raw)
            validate(answer,request['schema'])
            state['completed'].append({**row,'answer':answer})
            state['attempts']=client.attempts
            write(output/'progress.json',state)
        state['status']='completed'
    except Exception as exc:
        state.update(status='stopped',error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        state['attempts']=client.attempts
        write(output/'progress.json',state)
    return state


def score(output):
    manifest=read(output/'manifest.json')
    pack=Path(manifest['task_pack'])
    if sha(pack/'manifest.json')!=manifest['pack_manifest_sha256']:
        raise ValueError('pack manifest changed')
    file_hashes=read(pack/'manifest.json')['files']
    completed=read(output/'progress.json')['completed']
    rows=[]
    for row in completed:
        folder=pack/'calibration'/row['case']
        for name in ['task.json','oracle_conditions.json']:
            path=folder/name
            if sha(path)!=file_hashes[path.relative_to(pack).as_posix()]:
                raise ValueError('scoring data changed')
        task=read(folder/'task.json'); rules=read(folder/'oracle_conditions.json')
        try:
            failed=violations(row['answer']['order'],task['jobs'],rules)
            valid=True
        except ValueError:
            failed=None;valid=False
        rows.append(dict(case=row['case'],repeat=row['repeat'],valid_permutation=valid,
                         violated_rules=failed,correct=valid and not failed))
    write(output/'offline_scores.json',dict(rows=rows,correct=sum(bool(r['correct']) for r in rows),
        completed=len(rows),planned=12,meaning='difficulty calibration, not architecture comparison'))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['prepare','run','score'])
    parser.add_argument('path',type=Path)
    parser.add_argument('output',type=Path,nargs='?')
    args=parser.parse_args()
    if args.mode=='prepare': prepare(args.path,args.output)
    elif args.mode=='run': run(args.path,args.output)
    else: score(args.path)
