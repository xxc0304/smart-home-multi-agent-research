"""Frozen receiver-side comparison with isolated failures; live execution is gated."""
import argparse
import copy
import hashlib
import json
import random
import time
from pathlib import Path

from tokenizers import Tokenizer
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
import prepare_receiver_baseline_20261026 as front
import minimal_final_answer_contract as terminal
import local_judgment_frontend as io

ROOT = front.ROOT
SPEC = ROOT/'research/receiver-baseline-20261026-v1'
TOKENIZER = ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'
VERSION = 'receiver-baseline/3'
DEFAULT = ROOT/'runs/receiver-baseline-prepared-20261026-r3'
LIMITS = dict(requests=64, per_output=1536, output=98304, per_input=16384, input=786432)
TASKS = ('010','023','027','011')
MEMBERS = ('A1','A2','A3','A4')


def schedule():
    rows=[]
    for ti,task in enumerate(TASKS):
        for mi,member in enumerate(MEMBERS):
            order=('ordinary','diagnose') if (ti+mi)%2==0 else ('diagnose','ordinary')
            for method in order:
                unit=f'{task}-{member}-{method}'
                for stage in ('first','final'):
                    rows.append(dict(slot=len(rows)+1,unit=unit,task=task,receiver=member,repeat=1,
                        method=method,stage=stage,depends_on=None if stage=='first' else unit+'-first'))
    return rows


def config():
    return dict(provider='deepseek', model='deepseek-flash', base_url='https://api.deepseek.com',
        generation=dict(reasoning_effort='none', temperature=0.7, max_input_tokens=LIMITS['per_input']),
        protocol=dict(transport_retries_per_request=0, max_format_repairs=0, request_timeout_seconds=120))


def child(root, rel):
    base = Path(root).resolve()
    path = (base/rel).resolve()
    if not path.is_relative_to(base):
        raise ValueError('path outside root')
    return path


def freeze(prepared):
    p = Path(prepared)
    if p.exists():
        raise ValueError('new prepared directory required')
    p.mkdir(parents=True)
    lineage = []
    historical_log=ROOT/'runs/candidate-screening-probe-live-20261025-r1/responses.jsonl'
    responses={r['attempt']:r for r in map(json.loads,historical_log.read_text(encoding='utf-8').splitlines())}
    for task in TASKS:
        origin = SPEC/'contexts'/f'{task}.json'
        base = io.read(origin)
        base.pop('field_meanings')
        base['historical_author']=base['member']
        first_slot={'010':1,'023':85,'027':115,'011':13}[task]
        for mi,member in enumerate(MEMBERS):
            own_slot=first_slot+mi
            extraction=io.strict_json(responses[own_slot]['response']['instructions'].split('PACKET=',1)[1])
            assert extraction['member']==member and extraction['task']==base['task']
            context=copy.deepcopy(base)
            context['member']=member
            context['own_sources']=copy.deepcopy(extraction['own_sources'])
            io.write(p/'contexts'/task/f'{member}.json',context)
            lineage.append(dict(task=task,receiver=member,historical_author=base['historical_author'],
                base_context_sha256=io.digest(origin),origin_extract_slot=own_slot,
                historical_log_sha256=io.digest(historical_log),
                transformation='remove field_meanings; fix historical_author; substitute current member and its actual historical own_sources only',
                shared_contributions_draft_and_report_unchanged=True))
    io.write(p/'CONTEXT_LINEAGE.json',lineage)
    io.write(p/'PLAN.json', dict(version=VERSION,schedule=schedule(),
        limits=LIMITS, status='frozen_not_authorized',scope='four receivers crossed with two methods on four fixed archived drafts; development only'))
    io.write(p/'config.json', config())
    labels = io.read(ROOT/'runs/candidate-screening-probe-prepared-20261025-r1/offline_labels.json')
    io.write(p/'OFFLINE_REFERENCE.json', {task: labels['candidate-'+task] for task in ('010','023','027','011')})
    (p/'SPEC.md').write_bytes((SPEC/'FOUR_RECEIVER_SPEC.md').read_bytes())
    (p/'DESIGN_CORRECTION.md').write_bytes((SPEC/'DESIGN_CORRECTION.md').read_bytes())
    io.write(p/'SEMANTIC_RUBRIC.json',io.read(SPEC/'SEMANTIC_RUBRIC.json'))
    code = [Path(__file__), Path(front.__file__), Path(terminal.__file__), Path(io.__file__),
            ROOT/'src/coreta/model_client.py', ROOT/'src/coreta/schemas.py', ROOT/'tools/check_receiver_baseline.py']
    hashes = {}
    for source in code:
        rel = source.relative_to(ROOT).as_posix()
        destination = p/'frozen_source'/rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        hashes[rel] = io.digest(source)
    io.write(p/'frozen_source/SHA256.json', hashes)
    files = {x.relative_to(p).as_posix(): io.digest(x) for x in p.rglob('*') if x.is_file()}
    io.write(p/'manifest.json', dict(version=VERSION, limits=LIMITS, files=files, code_sha256=hashes,
        tokenizer_sha256=io.digest(TOKENIZER)))
    verify(p)
    return dict(manifest_sha256=io.digest(p/'manifest.json'), status='frozen_not_authorized')


def verify(prepared):
    p = Path(prepared)
    m = io.read(p/'manifest.json')
    if m['version'] != VERSION or m['limits'] != LIMITS:
        raise ValueError('version or budget changed')
    for rel, sha in m['files'].items():
        if io.digest(child(p, rel)) != sha:
            raise ValueError('frozen input changed: '+rel)
    for rel, sha in m['code_sha256'].items():
        if io.digest(child(ROOT, rel)) != sha:
            raise ValueError('runtime code changed: '+rel)
    if io.digest(TOKENIZER) != m['tokenizer_sha256'] or io.read(p/'config.json') != config():
        raise ValueError('tokenizer or config changed')
    plan = io.read(p/'PLAN.json')
    if plan['schedule'] != schedule() or plan['limits'] != LIMITS:
        raise ValueError('schedule changed')
    return m, plan


def gates(p):
    sha = io.digest(p/'manifest.json')
    for name, expected in [('PREFLIGHT.json',dict(status='passed')),
                           ('EXPERIMENT_REVIEW.json',dict(science='PASS', readiness='PASS',technical_launch='RUN_ALLOWED'))]:
        row = io.read(p/name)
        if row.get('manifest_sha256') != sha or any(row.get(k) != v for k,v in expected.items()):
            raise ValueError('fresh gate required: '+name)
    auth = io.read(p/'AUTHORIZATION.json')
    expected = dict(authorized=True,manifest_sha256=sha,max_requests=LIMITS['requests'],max_output_tokens=LIMITS['output'],
                    max_input_tokens=LIMITS['input'],destination='https://api.deepseek.com/responses')
    if any(auth.get(k) != v for k,v in expected.items()) or not auth.get('user_authorization_text'):
        raise ValueError('batch-specific user authorization required')


def run(prepared, output, *, transport=None, local_validation=False):
    p, out = Path(prepared), Path(output)
    manifest, plan = verify(p)
    if local_validation:
        if transport is None:
            raise ValueError('explicit local fixture transport required')
    else:
        gates(p)
    if out.exists():
        raise ValueError('new output directory required; no resume')
    out.mkdir(parents=True)
    io.write(out/'manifest.json', manifest)
    state = dict(mode='local_fixture' if local_validation else 'live', status='running', attempts=0,
        input_tokens=0, output_tokens=0, reserved_input=0, reserved_output=0,
        unknown_usage=False, over_cap=False, consecutive_unreadable=0, rows=[], error=None)
    firsts = {}
    current = None
    client = None

    def save():
        if client is not None:
            state['attempts'] = client.attempts
        io.write(out/'progress.json', state)
        done = {r['slot']:r for r in state['rows']}
        io.write(out/'review.json', dict(mode=state['mode'],status=state['status'],rows=[
            done.get(r['slot'],dict(r,status='not_run',answer=None)) for r in plan['schedule']]))

    def log(name, value):
        with (out/name).open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(value,ensure_ascii=False)+'\n')
        if name != 'responses.jsonl':
            return
        response = value.get('response')
        if not isinstance(response,dict):
            state['unknown_usage'] = True
            return
        text = ''.join(c['text'] for m in response.get('output',[]) for c in m.get('content',[])
                       if c.get('type')=='output_text' and isinstance(c.get('text'),str))
        (out/f'{current:03d}.raw.txt').write_text(text,encoding='utf-8')
        for key in ('input_tokens','output_tokens'):
            amount = response.get('usage',{}).get(key)
            if type(amount) is not int or amount < 0:
                state['unknown_usage'] = True
            else:
                state[key] += amount
                if amount > LIMITS['per_input' if key=='input_tokens' else 'per_output']:
                    state['over_cap'] = True

    tok = Tokenizer.from_file(str(TOKENIZER))
    client = DeepSeekClient(config(),log,transport=transport,
        token_counter=lambda s:len(tok.encode(s,add_special_tokens=False).ids))
    save()
    try:
        for row in plan['schedule']:
            current = row['slot']
            context = io.read(p/'contexts'/row['task']/f"{row['receiver']}.json")
            if row['stage']=='final' and row['unit'] not in firsts:
                state['rows'].append(dict(row,status='blocked_upstream',answer=None)); save(); continue
            req = (front.first_request(context,row['method']) if row['stage']=='first'
                   else front.final_request(context,firsts[row['unit']]))
            payload = client.payload(req['instructions'],req['schema'],LIMITS['per_output'])
            size = client.size(payload)
            if (size > LIMITS['per_input'] or client.attempts >= LIMITS['requests'] or
                max(state['reserved_input'],state['input_tokens'])+size > LIMITS['input'] or
                state['reserved_output']+LIMITS['per_output'] > LIMITS['output']):
                raise RuntimeError('pre-request budget exceeded')
            io.write(out/'actual_requests'/f'{current:03d}.json',req)
            state['reserved_input'] += size
            state['reserved_output'] += LIMITS['per_output']
            try:
                raw = client.complete(payload,deadline=time.monotonic()+150,logical_seed=row['repeat'])
                if (state['unknown_usage'] or state['over_cap'] or state['input_tokens'] > LIMITS['input']
                    or state['output_tokens'] > LIMITS['output']):
                    raise RuntimeError('actual usage missing or over budget')
                answer = (front.decode_first(raw) if row['stage']=='first' else terminal.decode(raw,context))
            except (ValueError,ProtocolError) as exc:
                if state['unknown_usage'] or state['over_cap'] or (isinstance(exc,ProtocolError) and exc.code!='SCHEMA_ERROR'):
                    raise
                state['rows'].append(dict(row,status='quarantined',answer=None,error=str(exc)))
                state['consecutive_unreadable'] += 1
                save()
                if state['consecutive_unreadable'] >= 2:
                    raise RuntimeError('two consecutive unreadable core outputs') from exc
                continue
            if row['stage']=='first':
                firsts[row['unit']] = answer
            state['consecutive_unreadable'] = 0
            state['rows'].append(dict(row,status='readable',answer=answer)); save()
        state['status'] = 'completed_with_quarantine' if any(r['status']=='quarantined' for r in state['rows']) else 'completed'
    except Exception as exc:
        state['status'] = 'stopped'; state['error'] = f'{type(exc).__name__}: {exc}'
        if current is not None and not any(r['slot']==current for r in state['rows']):
            row = next(r for r in plan['schedule'] if r['slot']==current)
            state['rows'].append(dict(row,status='system_error',answer=None,error=state['error']))
    finally:
        save()
    return state


def export(prepared, output):
    """Post-run evaluator; this function alone reads the offline references."""
    p,out = Path(prepared),Path(output)
    review = io.read(out/'review.json')
    first_rows={r['unit']:r for r in review['rows'] if r['stage']=='first'}
    labels = io.read(p/'OFFLINE_REFERENCE.json')
    rubric = io.read(p/'SEMANTIC_RUBRIC.json')
    rows = []
    for row in review['rows']:
        if row['stage']!='final':
            continue
        choice = row['answer']['choice'] if row['status']=='readable' else None
        match = (choice == labels[row['task']]['correct_option_id']
                 if row['status']=='readable' and choice is not None else None)
        rows.append(dict(row,reference_match=match,semantic_application=None,
                         unresolved=row['status']=='readable' and choice is None))
    io.write(out/'SCORES.json',dict(mode=review['mode'],rows=rows,
        primary_outcome='case-specific semantic application, manually reviewed; no automated overall effectiveness score',
        caveat='Reference choice only; semantic application requires review. Technical missing and unresolved remain null.'))
    pairs=[]
    for task in TASKS:
        for receiver in MEMBERS:
            group={r['method']:r for r in rows if r['task']==task and r['receiver']==receiver}
            pairs.append(dict(task=task,receiver=receiver,
                ordinary=dict(status=group['ordinary']['status'],choice=group['ordinary']['answer']['choice']
                    if group['ordinary']['status']=='readable' else None,reference_match=group['ordinary']['reference_match']),
                diagnose=dict(status=group['diagnose']['status'],choice=group['diagnose']['answer']['choice']
                    if group['diagnose']['status']=='readable' else None,reference_match=group['diagnose']['reference_match']),
                semantic_method_difference=None))
    io.write(out/'RECEIVER_PAIRS.json',dict(mode=review['mode'],pairs=pairs,
        independent_tasks=4,repeated_sampling_per_condition=1,
        caveat='Receiver views include own-source completeness/ownership/salience, not isolated identity effects.'))
    shuffled = list(rows); random.Random(20261026).shuffle(shuffled)
    mapping, forms = [], []
    for i,row in enumerate(shuffled,1):
        name = f'R{i:02d}'
        mapping.append(dict(id=name,task=row['task'],receiver=row['receiver'],method=row['method'],repeat=row['repeat'],slot=row['slot']))
        first=first_rows[row['unit']]
        forms.append(dict(id=name,task=row['task'],receiver=row['receiver'],status=row['status'],answer=row['answer'],
            first_analysis=first.get('answer'),first_analysis_status=first['status'],diagnosis_quality=None,
            evidence_context=f"contexts/{row['task']}/{row['receiver']}.json",evidence_fidelity=None,actual_application=None,
            case_rubric=rubric['cases'][row['task']],new_error=None,reason_choice_consistency=None,
            evidence_quotes=[],review_notes=None))
    io.write(out/'SEMANTIC_REVIEW_FORM.json',dict(mode=review['mode'],independent_blind=False,rows=forms))
    io.write(out/'OFFLINE_REVIEW_MAPPING.json',mapping)
    return dict(final_units=len(rows),known_matches=sum(r['reference_match'] is True for r in rows),
                missing_or_unresolved=sum(r['reference_match'] is None for r in rows))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['freeze','verify','run','export'])
    parser.add_argument('--prepared',type=Path,default=DEFAULT)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.command=='freeze': result=freeze(args.prepared)
    elif args.command=='verify': result=verify(args.prepared)[0]
    else:
        if args.output is None: parser.error('--output required')
        result=run(args.prepared,args.output) if args.command=='run' else export(args.prepared,args.output)
    print(json.dumps(result,ensure_ascii=False))
