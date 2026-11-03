"""Frozen bounded calibration. No live calls from freeze/verify; live requires gates."""
import argparse
import hashlib
import http.client
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

from tokenizers import Tokenizer
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
from coreta.handoff.contracts import HandoffContracts
from coreta.local_work.engine import obj, TEXT

from coreta.local_work.data import read, write
from coreta.local_work.comparison import ComparisonFlow

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'runs/local-work-mixed-prepared-20261027-v1/tasks'
TOKENIZER = ROOT / 'data/tokenizer-v4.1-flash-1017/tokenizer.json'
VERSION = 'local-work-calibration/1'
LIMITS = dict(requests=42, input=688128, output=82944, per_input=16384,
              per_output=2048, final_output=1536, retries=0)
SOURCE_FILES = [
    'src/coreta/local_work/__init__.py', 'src/coreta/local_work/engine.py',
    'src/coreta/local_work/comparison.py', 'src/coreta/local_work/data.py',
    'src/coreta/local_work/prompts.py', 'src/coreta/handoff/contracts.py',
    'src/coreta/schemas.py', 'src/coreta/model_client.py',
    'tools/run_local_work_calibration.py', 'tools/check_local_work_calibration.py',
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def config():
    return dict(provider='deepseek', model='deepseek-flash', base_url='https://api.deepseek.com',
                generation=dict(reasoning_effort='none', temperature=0.7, max_input_tokens=LIMITS['per_input']),
                protocol=dict(transport_retries_per_request=0, max_format_repairs=0, request_timeout_seconds=120))


def schedule():
    return [dict(flow_id=f'{cid}-{arm}', case_id=cid, arm=arm)
            for cid, arms in [('main-01', ('ordinary', 'local_work', 'single')),
                              ('diagnostic-01', ('local_work', 'ordinary', 'single'))]
            for arm in arms]


def freeze(prepared):
    prepared = Path(prepared)
    if prepared.exists():
        raise ValueError('fresh prepared directory required')
    prepared.mkdir(parents=True)
    for cid in ('main-01', 'diagnostic-01'):
        case = read(SOURCE / cid / 'runtime.json')
        if case['case_id'] != cid or set(case['task']) != {'task_id', 'question', 'members', 'sources', 'origin'}:
            raise ValueError('runtime task fields changed or labels included')
        write(prepared / 'cases' / f'{cid}.json', case)
    write(prepared / 'PLAN.json', dict(version=VERSION, schedule=schedule(), limits=LIMITS,
          purpose='First natural-schema protocol/behavior calibration, not stable efficacy confirmation',
          endpoint='https://api.deepseek.com/responses', label_policy='no gold/oracle operation in runtime'))
    write(prepared / 'config.json', config())
    hashes = {}
    for name in SOURCE_FILES:
        source = ROOT / name
        if not source.exists():
            raise ValueError('required source missing: ' + name)
        destination = prepared / 'frozen_source' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        hashes[name] = digest(source)
    write(prepared / 'manifest.json', dict(version=VERSION, limits=LIMITS,
          source_sha256=hashes, tokenizer_sha256=digest(TOKENIZER),
          files={p.relative_to(prepared).as_posix(): digest(p)
                 for p in prepared.rglob('*') if p.is_file()}))
    return dict(status='frozen_not_authorized', manifest_sha256=digest(prepared / 'manifest.json'))


def verify(prepared, require_preflight=True, allow_fixture_gate=False):
    prepared = Path(prepared)
    manifest = read(prepared / 'manifest.json')
    if manifest['version'] != VERSION or manifest['limits'] != LIMITS:
        raise ValueError('version or budget changed')
    if set(manifest['source_sha256']) != set(SOURCE_FILES):
        raise ValueError('release source list incomplete')
    for name, expected in manifest['files'].items():
        if digest(prepared / name) != expected:
            raise ValueError('frozen runtime/source file changed: ' + name)
    for name, expected in manifest['source_sha256'].items():
        if digest(ROOT / name) != expected:
            raise ValueError('active code changed: ' + name)
    if digest(TOKENIZER) != manifest['tokenizer_sha256'] or read(prepared / 'config.json') != config():
        raise ValueError('tokenizer/config changed')
    plan = read(prepared / 'PLAN.json')
    if plan['schedule'] != schedule() or plan['limits'] != LIMITS:
        raise ValueError('schedule/limits changed')
    if require_preflight:
        preflight = read(prepared / 'PREFLIGHT.json')
        if preflight.get('manifest_sha256') != digest(prepared / 'manifest.json') or preflight.get('status') != 'PASS':
            raise ValueError('missing/mismatched preflight gate')
        scopes = {'bounded_protocol_calibration'} | ({'local_fixture_only'} if allow_fixture_gate else set())
        if preflight.get('scope') not in scopes:
            raise ValueError('preflight scope does not permit this execution mode')
        review = read(prepared / 'EXPERIMENT_REVIEW.json')
        if review != dict(manifest_sha256=digest(prepared / 'manifest.json'),
                          science='PASS', readiness='PASS', scope=preflight['scope']):
            raise ValueError('scientific/readiness review gate not passed')
    return manifest, plan


def authorization_record(prepared, path):
    record = read(path)
    expected = dict(manifest_sha256=digest(Path(prepared) / 'manifest.json'),
                    endpoint='https://api.deepseek.com/responses', requests=LIMITS['requests'],
                    input_tokens=LIMITS['input'], output_tokens=LIMITS['output'])
    if not isinstance(record, dict) or any(record.get(k) != v for k, v in expected.items()):
        raise ValueError('authorization does not cover this frozen batch/endpoint/budget')
    if not isinstance(record.get('human_grant'), str) or not record['human_grant'].strip():
        raise ValueError('authorization requires recorded human grant, not an inferred default')
    return record


def readable_core(raw, final):
    if raw is None:
        return False
    try:
        value = HandoffContracts.decode(raw, dict(type='object'))
        fields = ('answer', 'scale', 'reasoning') if final else ('message',)
        core = {k: value[k] for k in fields if k in value}
        schema = obj(dict(answer=dict(type=['number', 'string', 'null']), scale=dict(type='string'), reasoning=TEXT)) if final else obj(dict(message=TEXT))
        HandoffContracts.decode(json.dumps(core), schema)
        return bool(core['reasoning' if final else 'message'].strip())
    except (ProtocolError, ValueError, TypeError, AttributeError):
        return False


def official_transport(payload, timeout, output, slot):
    """Save body before decoding; shared historical client remains unchanged."""
    key = os.environ.get('DEEPSEEK_API_KEY')
    if not key:
        raise ProtocolError('MODEL_UNAVAILABLE', 'DEEPSEEK_API_KEY is not configured')
    request = urllib.request.Request('https://api.deepseek.com/responses',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method='POST')
    path = Path(output) / 'http_bodies' / f'{slot:03d}.bytes'
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
    except http.client.IncompleteRead as exc:
        path.write_bytes(exc.partial)
        raise
    except urllib.error.HTTPError as exc:
        path.write_bytes(exc.read())
        raise
    path.write_bytes(body)
    try:
        return json.loads(body.decode('utf-8'))
    except UnicodeError as exc:
        raise json.JSONDecodeError('HTTP body is not UTF-8', '', 0) from exc
def run(prepared, output, *, transport=None, local_fixture=False, authorization=None):
    prepared, output = Path(prepared), Path(output)
    _, plan = verify(prepared, allow_fixture_gate=local_fixture)
    if local_fixture:
        if transport is None:
            raise ValueError('local fixture requires an explicitly injected transport')
    else:
        if transport is not None:
            raise ValueError('live run cannot override transport')
        if authorization is None:
            raise ValueError('batch-specific authorization file required')
        authorization_record(prepared, authorization)
    if output.exists():
        raise ValueError('fresh output required; no resume/retry')
    output.mkdir(parents=True)
    write(output / 'manifest.json', read(prepared / 'manifest.json'))
    tokenizer = Tokenizer.from_file(str(TOKENIZER))
    state = dict(mode='local_fixture' if local_fixture else 'live', status='running', attempts=0,
                 input_tokens=0, output_tokens=0, reserved_input=0, reserved_output=0,
                 unknown_usage=False, over_cap=False, consecutive_unreadable=0,
                 flows=[dict(**row, status='not_run', final=None) for row in plan['schedule']], error=None)
    current = dict(slot=None, cap=None)

    def save():
        state['attempts'] = client.attempts
        write(output / 'progress.json', state)
        write(output / 'FLOW_RESULTS.json', dict(mode=state['mode'], status=state['status'],
              manifest_sha256=digest(prepared / 'manifest.json'), flows=state['flows'],
              method_accuracy=None, costs={k: state[k] for k in ('attempts', 'input_tokens', 'output_tokens',
                    'reserved_input', 'reserved_output', 'unknown_usage')}))

    def log(name, value):
        with (output / name).open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(slot=current['slot'], **value), ensure_ascii=False) + '\n')
        if name != 'responses.jsonl':
            return
        response = value.get('response')
        if not isinstance(response, dict):
            state['unknown_usage'] = True
            return
        text = ''.join(part['text'] for item in response.get('output', []) if isinstance(item, dict)
                       for part in item.get('content', []) if isinstance(part, dict)
                       and part.get('type') == 'output_text' and isinstance(part.get('text'), str))
        (output / f"{current['slot']:03d}.raw.txt").write_text(text, encoding='utf-8')
        for field, cap in [('input_tokens', LIMITS['per_input']), ('output_tokens', current['cap'])]:
            number = response.get('usage', {}).get(field) if isinstance(response.get('usage'), dict) else None
            if type(number) is not int or number < 0:
                state['unknown_usage'] = True
            else:
                state[field] += number
                if number > cap:
                    state['over_cap'] = True

    selected_transport = transport if local_fixture else lambda payload, timeout: official_transport(
        payload, timeout, output, current['slot'])
    client = DeepSeekClient(config(), log, transport=selected_transport,
                            token_counter=lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids))
    if not local_fixture:
        write(output / 'AUTHORIZATION.json', read(authorization))
    save()
    active_flow, flow_directory, flow_record, flow_start_attempts = None, None, None, 0

    def flow_summary():
        summary = active_flow.summary()
        attempts = client.attempts - flow_start_attempts
        summary.update(transport_attempts=attempts, network_calls=0 if local_fixture else attempts)
        return summary
    try:
        for index, specification in enumerate(plan['schedule']):
            case = read(prepared / 'cases' / (specification['case_id'] + '.json'))
            active_flow = ComparisonFlow(case, specification['arm'],
                provenance='scripted_transport_engineering_fixture' if local_fixture else 'live_official_deepseek_responses')
            flow_directory = output / 'flows' / specification['flow_id']
            flow_record = state['flows'][index]
            flow_record['status'] = 'running'
            flow_start_attempts = client.attempts
            while active_flow.status == 'pending':
                pending = active_flow.pending_requests()
                # Every same-wave request is stored before the first API attempt.
                for actor, req in pending.items():
                    write(flow_directory / 'requests' / f'{active_flow.wave:02d}-{actor}.json', req)
                replies = {}
                for actor, req in pending.items():
                    payload = client.payload(req['instructions'], req['schema'], req['max_output_tokens'])
                    size, cap = client.size(payload), req['max_output_tokens']
                    if (size > LIMITS['per_input'] or client.attempts >= LIMITS['requests'] or
                        max(state['input_tokens'], state['reserved_input']) + size > LIMITS['input'] or
                        max(state['output_tokens'], state['reserved_output']) + cap > LIMITS['output']):
                        raise RuntimeError('pre-request input/output/attempt budget exceeded')
                    current.update(slot=client.attempts + 1, cap=cap)
                    state['reserved_input'] += size
                    state['reserved_output'] += cap
                    write(output / 'actual_requests' / f"{current['slot']:03d}.json", req)
                    save()
                    try:
                        raw = client.complete(payload, deadline=time.monotonic() + 125, logical_seed=1)
                    except ProtocolError as exc:
                        if exc.code != 'SCHEMA_ERROR' or state['unknown_usage'] or state['over_cap']:
                            raise
                        path = output / f"{current['slot']:03d}.raw.txt"
                        raw = path.read_text(encoding='utf-8') if path.exists() else ''
                        # Incomplete envelope cannot become a valid completed core merely
                        # because its prefix looks like valid JSON.
                        replies[actor] = None
                        write(flow_directory / 'envelope_errors' / f'{active_flow.wave:02d}-{actor}.json',
                              dict(slot=current['slot'], code=exc.code, reason=exc.detail, raw=raw))
                    else:
                        replies[actor] = raw
                    if (state['unknown_usage'] or state['over_cap'] or state['input_tokens'] > LIMITS['input'] or
                            state['output_tokens'] > LIMITS['output']):
                        raise RuntimeError('actual usage missing or over frozen limits')
                    if replies[actor] is not None:
                        (flow_directory / f'{active_flow.wave:02d}-{actor}.raw.txt').parent.mkdir(parents=True, exist_ok=True)
                        (flow_directory / f'{active_flow.wave:02d}-{actor}.raw.txt').write_text(raw, encoding='utf-8')
                    if readable_core(replies[actor], req['final']):
                        state['consecutive_unreadable'] = 0
                    else:
                        state['consecutive_unreadable'] += 1
                    if state['consecutive_unreadable'] >= 2:
                        raise RuntimeError('two consecutive unreadable cores; batch stopped')
                active_flow.submit(replies)
                write(flow_directory / 'EVENTS.json', active_flow.events)
                flow_record.update(flow_summary())
                write(flow_directory / 'SUMMARY.json', flow_record)
                save()
            flow_record.update(flow_summary())
            save()
        state['status'] = ('completed_with_incomplete_flows' if any(r['status'] != 'completed' for r in state['flows'])
                           else 'completed')
    except Exception as exc:
        state['status'] = 'stopped'
        state['error'] = f'{type(exc).__name__}: {exc}'
        if active_flow is not None and flow_record is not None:
            # Consume already received siblings only to preserve them; never schedule
            # any further request after a system failure.
            if active_flow.current is not None:
                active_flow.submit(locals().get('replies', {}))
            write(flow_directory / 'EVENTS.json', active_flow.events)
            flow_record.update(flow_summary())
            flow_record['status'] = 'system_stopped'
            flow_record['error'] = state['error']
            write(flow_directory / 'SUMMARY.json', flow_record)
    finally:
        save()
    return state


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('action', choices=('freeze', 'verify', 'run'))
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args()
    if args.action == 'freeze':
        result = freeze(args.prepared)
    elif args.action == 'verify':
        result = dict(status='verified_not_authorized', plan=verify(args.prepared)[1])
    else:
        if args.output is None or args.authorization is None:
            parser.error('run requires --output and --authorization')
        result = run(args.prepared, args.output, authorization=args.authorization)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
