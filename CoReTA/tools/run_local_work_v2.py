"""Bounded mixed v2 development runner. Freeze/verify never make model calls."""
import argparse
import json
import time
from pathlib import Path

from tokenizers import Tokenizer
from coreta.local_work.comparison_v2 import make_flow
from coreta.local_work.data import read, write
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
from run_local_work_calibration import digest, config, official_transport, readable_core, TOKENIZER, ROOT


VERSION = 'local-work-mixed-v2/1'
LIMITS = dict(requests=84, input=1376256, output=165888, per_input=16384, retries=0)
FILES = [
    'src/coreta/local_work/__init__.py', 'src/coreta/local_work/engine.py',
    'src/coreta/local_work/data.py', 'src/coreta/local_work/prompts.py',
    'src/coreta/local_work/comparison.py', 'src/coreta/local_work/comparison_v2.py',
    'src/coreta/model_client.py', 'src/coreta/schemas.py', 'src/coreta/handoff/contracts.py',
    'tools/run_local_work_calibration.py', 'tools/run_local_work_v2.py',
    'tools/prepare_local_work_v2_tasks.py', 'tools/check_local_work_v2_batch.py',
    'tools/score_local_work_v2.py',
]


def freeze(data, prepared):
    data, prepared = Path(data), Path(prepared)
    if prepared.exists():
        raise ValueError('fresh prepared directory required')
    draft = read(data / 'DRAFT_PLAN.json')
    schedule = draft['schedule']
    expected_cases = {'ordinary-01', 'ordinary-02', 'dependent-01', 'dependent-02'}
    if len(schedule) != 12 or {(r['case_id'], r['arm']) for r in schedule} != {
            (cid, arm) for cid in expected_cases for arm in ('discussion', 'ordinary', 'local_work')}:
        raise ValueError('unexpected development schedule')
    prepared.mkdir(parents=True)
    for cid in sorted(expected_cases):
        case = read(data / 'cases' / (cid + '.json'))
        if set(case) != {'case_id', 'group', 'final_member', 'task'} or case['case_id'] != cid:
            raise ValueError('unexpected runtime case fields')
        if set(case['task']) != {'task_id', 'question', 'members', 'sources', 'origin'}:
            raise ValueError('unexpected task fields / possible labels')
        write(prepared / 'cases' / (cid + '.json'), case)
        # Evaluation labels are frozen separately and never read by the run loop.
        reference_path = prepared / 'offline' / (cid + '.reference.json')
        reference_path.parent.mkdir(parents=True, exist_ok=True)
        reference_path.write_bytes((data / 'offline' / (cid + '.reference.json')).read_bytes())
    write(prepared / 'PLAN.json', dict(version=VERSION, schedule=schedule, limits=LIMITS,
          repeats=1, purpose='Mixed developmental mechanism diagnostic, not stable efficacy confirmation',
          allocation='ordinary_regression versus controlled_dependency reported separately',
          endpoint='https://api.deepseek.com/responses'))
    write(prepared / 'config.json', config())
    for name in FILES:
        destination = prepared / 'frozen_source' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / name).read_bytes())
    write(prepared / 'manifest.json', dict(version=VERSION, limits=LIMITS,
          source_sha256={name: digest(ROOT / name) for name in FILES},
          tokenizer_sha256=digest(TOKENIZER),
          files={path.relative_to(prepared).as_posix(): digest(path)
                 for path in prepared.rglob('*') if path.is_file()}))
    return dict(status='frozen_not_authorized', manifest_sha256=digest(prepared / 'manifest.json'))


def verify(prepared, require_gate=True, fixture=False):
    prepared = Path(prepared)
    manifest = read(prepared / 'manifest.json')
    if manifest['version'] != VERSION or manifest['limits'] != LIMITS or set(manifest['source_sha256']) != set(FILES):
        raise ValueError('version, limits or source list changed')
    for name, expected in manifest['files'].items():
        if digest(prepared / name) != expected:
            raise ValueError('frozen file changed: ' + name)
    for name, expected in manifest['source_sha256'].items():
        if digest(ROOT / name) != expected:
            raise ValueError('active source changed: ' + name)
    plan = read(prepared / 'PLAN.json')
    if digest(TOKENIZER) != manifest['tokenizer_sha256'] or read(prepared / 'config.json') != config():
        raise ValueError('tokenizer/config changed')
    if plan['limits'] != LIMITS or len(plan['schedule']) != 12:
        raise ValueError('plan differs from bounded batch')
    if require_gate:
        scope = 'local_fixture_only' if fixture else 'bounded_mixed_development'
        gate = dict(manifest_sha256=digest(prepared / 'manifest.json'), scope=scope,
                    science='PASS', readiness='PASS')
        if read(prepared / 'EXPERIMENT_REVIEW.json') != gate:
            raise ValueError('missing/mismatched scientific and execution review')
        if read(prepared / 'PREFLIGHT.json') != dict(manifest_sha256=gate['manifest_sha256'],
                                                   scope=scope, status='PASS', tests_passed=True):
            raise ValueError('missing/mismatched local preflight evidence')
    return plan


def authorize(prepared, path):
    record = read(path)
    expected = dict(manifest_sha256=digest(Path(prepared) / 'manifest.json'),
                    endpoint='https://api.deepseek.com/responses', requests=84,
                    input_tokens=1376256, output_tokens=165888)
    if not isinstance(record, dict) or any(record.get(key) != value for key, value in expected.items()):
        raise ValueError('authorization does not cover this batch')
    if not isinstance(record.get('human_grant'), str) or not record['human_grant'].strip():
        raise ValueError('explicit batch human grant required')
    return record


def run(prepared, output, authorization=None, *, transport=None, fixture=False):
    prepared, output = Path(prepared), Path(output)
    plan = verify(prepared, fixture=fixture)
    if fixture:
        if transport is None:
            raise ValueError('fixture requires injected offline transport')
    elif transport is not None:
        raise ValueError('live transport cannot be overridden')
    elif authorization is None:
        raise ValueError('batch authorization is required')
    else:
        authorize(prepared, authorization)
    if output.exists():
        raise ValueError('fresh run required; no resume or retry')
    output.mkdir(parents=True)
    write(output / 'manifest.json', read(prepared / 'manifest.json'))
    if not fixture:
        write(output / 'AUTHORIZATION.json', read(authorization))
    tokenizer = Tokenizer.from_file(str(TOKENIZER))
    state = dict(status='running', mode='local_fixture' if fixture else 'live', attempts=0,
                 input_tokens=0, output_tokens=0, reserved_input=0, reserved_output=0,
                 unknown_usage=False, over_cap=False, consecutive_unreadable=0,
                 flows=[dict(**spec, group=read(prepared / 'cases' / (spec['case_id'] + '.json'))['group'],
                             status='not_started', attempts=0, final=None, exact_match=None)
                        for spec in plan['schedule']], error=None)
    current = {}

    def save():
        state['attempts'] = client.attempts
        write(output / 'progress.json', state)

    def log(name, record):
        with (output / name).open('a', encoding='utf8') as stream:
            stream.write(json.dumps(dict(slot=current['slot'], flow_id=current['flow_id'], **record), ensure_ascii=False) + '\n')
        if name != 'responses.jsonl':
            return
        response = record.get('response')
        if not isinstance(response, dict):
            state['unknown_usage'] = True
            return
        text = ''.join(part['text'] for item in (response.get('output') or []) if isinstance(item, dict)
                       for part in (item.get('content') or []) if isinstance(part, dict)
                       and part.get('type') == 'output_text' and isinstance(part.get('text'), str))
        (output / f'{current["slot"]:03d}.raw.txt').write_text(text, encoding='utf8')
        for field, cap in [('input_tokens', 16384), ('output_tokens', current['cap'])]:
            usage = response.get('usage')
            number = usage.get(field) if isinstance(usage, dict) else None
            if type(number) is not int or number < 0:
                state['unknown_usage'] = True
            else:
                state[field] += number
                if number > cap:
                    state['over_cap'] = True

    selected = transport if fixture else lambda payload, timeout: official_transport(payload, timeout, output, current['slot'])
    client = DeepSeekClient(config(), log, transport=selected,
                            token_counter=lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids))
    active, folder, record, replies = None, None, None, {}
    save()

    def summary():
        value = active.summary()
        value.update(flow_id=record['flow_id'], transport_attempts=record['attempts'],
                     network_calls=0 if fixture else record['attempts'], final_use=active.final_use())
        return value

    try:
        for index, spec in enumerate(plan['schedule']):
            active = make_flow(read(prepared / 'cases' / (spec['case_id'] + '.json')), spec['arm'],
                                      provenance='scripted_offline_fixture' if fixture else 'live_official_deepseek_responses')
            folder = output / 'flows' / spec['flow_id']
            record = state['flows'][index]
            record['status'] = 'running'
            current['flow_id'] = spec['flow_id']
            while active.status == 'pending':
                pending, replies = active.pending_requests(), {}
                for actor, request in pending.items():
                    write(folder / 'requests' / f'{active.wave:02d}-{actor}.json', request)
                for actor, request in pending.items():
                    payload = client.payload(request['instructions'], request['schema'], request['max_output_tokens'])
                    size, cap = client.size(payload), request['max_output_tokens']
                    if (size > 16384 or client.attempts >= LIMITS['requests'] or
                            max(state['input_tokens'], state['reserved_input']) + size > LIMITS['input'] or
                            max(state['output_tokens'], state['reserved_output']) + cap > LIMITS['output']):
                        raise RuntimeError('pre-request budget exceeded')
                    current.update(slot=client.attempts + 1, cap=cap)
                    state['reserved_input'] += size
                    state['reserved_output'] += cap
                    write(output / 'actual_requests' / f'{current["slot"]:03d}.json', request)
                    save()
                    try:
                        raw = client.complete(payload, deadline=time.monotonic() + 125, logical_seed=1)
                    except KeyboardInterrupt:
                        log('responses.jsonl', dict(status='interrupted', error_type='KeyboardInterrupt', uncertain_usage=True))
                        raise
                    except ProtocolError as exc:
                        if exc.code != 'SCHEMA_ERROR' or state['unknown_usage'] or state['over_cap']:
                            raise
                        raw = None
                        write(folder / 'envelope_errors' / f'{active.wave:02d}-{actor}.json',
                              dict(slot=current['slot'], code=exc.code, reason=exc.detail))
                    finally:
                        record['attempts'] += 1
                    if state['unknown_usage'] or state['over_cap'] or state['input_tokens'] > LIMITS['input'] or state['output_tokens'] > LIMITS['output']:
                        raise RuntimeError('actual usage unknown or over budget')
                    replies[actor] = raw
                    if raw is not None:
                        (folder / f'{active.wave:02d}-{actor}.raw.txt').write_text(raw, encoding='utf8')
                    state['consecutive_unreadable'] = 0 if readable_core(raw, request['final']) else state['consecutive_unreadable'] + 1
                    if state['consecutive_unreadable'] >= 2:
                        raise RuntimeError('two consecutive unreadable cores')
                active.submit(replies)
                write(folder / 'EVENTS.json', active.events)
                record.update(summary())
                write(folder / 'SUMMARY.json', record)
                save()
            record.update(summary())
        state['status'] = 'completed' if all(row['status'] == 'completed' for row in state['flows']) else 'completed_with_incomplete_flows'
    except (Exception, KeyboardInterrupt) as exc:
        state.update(status='stopped', error=f'{type(exc).__name__}: {exc}')
        if active is not None:
            if active.current is not None:
                active.submit(replies)
            write(folder / 'EVENTS.json', active.events)
            record.update(summary())
            record.update(status='system_stopped', error=state['error'])
            write(folder / 'SUMMARY.json', record)
    finally:
        save()
    return state


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('action', choices=('freeze', 'verify', 'run'))
    parser.add_argument('--data', type=Path)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args()
    if args.action == 'freeze':
        if args.data is None:
            parser.error('freeze requires --data')
        result = freeze(args.data, args.prepared)
    elif args.action == 'verify':
        result = dict(status='verified_not_authorized', plan=verify(args.prepared))
    else:
        if args.output is None or args.authorization is None:
            parser.error('run requires output and explicit authorization file')
        result = run(args.prepared, args.output, args.authorization)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
