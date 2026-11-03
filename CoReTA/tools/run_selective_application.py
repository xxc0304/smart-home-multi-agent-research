"""Execute only the frozen selective-application diagnostic, at most 24 requests."""
import argparse
import json
import os
import time
from pathlib import Path

from coreta.handoff.__main__ import PROJECT, load_counter
from coreta.handoff.contracts import HandoffContracts
from coreta.handoff.gateway import Journal, write_json
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
from prepare_selective_application import COMMON, DUTIES
from workboard_review_probe import hashes, read, packet_of, output_schema

PREPARED = PROJECT / 'runs/selective-application-prepared-20261023-r2'


def validate(prepared):
    prepared = Path(prepared)
    manifest = read(prepared / 'manifest.json')
    for key in ('source_hashes', 'payload_hashes'):
        if hashes(manifest[key]) != manifest[key]:
            raise ValueError('Frozen files changed: ' + key)
    config = manifest['config']
    if (manifest['candidate_max_model_requests'] != 24
            or manifest['candidate_max_output_tokens'] != 49152
            or len(manifest['calls']) != 24 or len(manifest['cases']) != 6
            or len({item['id'] for item in manifest['cases']}) != 6
            or config['base_url'] != 'https://api.deepseek.com'
            or config['model'] != 'deepseek-flash'
            or config['protocol']['transport_retries_per_request'] != 0):
        raise ValueError('Unexpected endpoint/configuration/budget')
    expected = {(item['id'], arm, repeat) for item in manifest['cases']
                for arm in ('F', 'K') for repeat in (1, 2)}
    if {(r['id'], r['condition'], r['repeat']) for r in manifest['calls']} != expected:
        raise ValueError('Unbalanced or duplicate schedule')
    counter = load_counter()
    client = DeepSeekClient(config, lambda *args: None, token_counter=counter)
    for item in manifest['cases']:
        f, k = [read(prepared / f"{item['id']}--{arm}.json") for arm in ('F', 'K')]
        if f['instructions'].replace(DUTIES['F'], DUTIES['K'], 1) != k['instructions']:
            raise ValueError('Unintended intervention')
        if packet_of(f) != packet_of(k) or output_schema(f) != output_schema(k):
            raise ValueError('Unequal input or schema')
        if {key: value for key, value in f.items() if key != 'instructions'} != \
           {key: value for key, value in k.items() if key != 'instructions'}:
            raise ValueError('Unequal generation envelope')
        for value in (f, k):
            schema = output_schema(value)
            if (value['max_output_tokens'] != 2048
                    or value['text']['format'] != {'type': 'json_object'}
                    or set(schema['required']) != {'artifact', 'work_text'}
                    or set(schema['properties']) != {'artifact', 'work_text'}
                    or schema['additionalProperties'] is not False
                    or client.size(value) > config['generation']['max_input_tokens']):
                raise ValueError('Output contract or context limit mismatch')
    for row in manifest['calls']:
        if row['payload_file'] != f"{row['id']}--{row['condition']}.json":
            raise ValueError('Call/payload mismatch')
    return manifest


def run(prepared, output, transport=None):
    prepared, output = Path(prepared), Path(output)
    manifest = validate(prepared)
    if output.exists():
        raise ValueError('New output directory required; no resume or automatic repair')
    if transport is None and not os.environ.get('DEEPSEEK_API_KEY'):
        raise ValueError('API credential unavailable')
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'manifest.json', manifest)
    write_json(output / 'execution.json', {
        'runner_hashes': hashes([Path(__file__), PROJECT / 'src/coreta/model_client.py',
                                PROJECT / 'src/coreta/handoff/contracts.py',
                                PROJECT / 'src/coreta/handoff/gateway.py']),
        'max_transport_attempts': 24, 'max_output_tokens': 49152,
        'format_repairs': 0, 'transport_retries': 0,
        'transport_mode': 'live' if transport is None else 'offline_fixture',
        'online_evaluator_access': False})
    journal = Journal(output)
    client = DeepSeekClient(manifest['config'], journal.log, transport=transport, token_counter=load_counter())
    progress = {'status': 'running', 'completed': 0, 'transport_attempts': 0,
                'actual_http_attempts': 0, 'unknown_usage_attempts': 0,
                'input_tokens': 0, 'output_tokens': 0,
                'transport_mode': 'live' if transport is None else 'offline_fixture',
                'rows': [dict(row, status='not_started') for row in manifest['calls']]}
    write_json(output / 'progress.json', progress)
    for ordinal, row in enumerate(progress['rows'], 1):
        journal.call_context = {key: value for key, value in row.items() if key != 'status'}
        journal.call_context['logical_call'] = ordinal
        row['status'] = 'running'
        write_json(output / 'progress.json', progress)
        try:
            if client.attempts >= 24 or progress['output_tokens'] + 2048 > 49152:
                raise ProtocolError('BUDGET', 'Cannot reserve next request')
            payload = read(prepared / row['payload_file'])
            raw = client.complete(payload, deadline=time.monotonic() + 120, logical_seed=row['repeat'])
            value = HandoffContracts.decode(raw, output_schema(payload))
            if len(journal.usage) != client.attempts or any(
                type(u.get(key)) is not int or u[key] < 0 for u in journal.usage
                for key in ('input_tokens', 'output_tokens')):
                raise ProtocolError('USAGE_UNKNOWN', 'Incomplete usage; raw log retained')
            if journal.usage[-1]['output_tokens'] > 2048:
                raise ProtocolError('OUTPUT_BUDGET', 'Server output exceeded stage cap')
            journal.log('stages.jsonl', {'output': value})
            progress['completed'] += 1
            row['status'] = 'completed'
        except Exception as exc:
            row['status'] = 'interrupted'
            row['error'] = {'code': getattr(exc, 'code', type(exc).__name__),
                            'detail': getattr(exc, 'detail', 'See raw trace')}
            progress['status'] = 'stopped_on_first_error'
        progress.update(
            transport_attempts=client.attempts,
            actual_http_attempts=client.attempts if transport is None else 0,
            unknown_usage_attempts=client.attempts - sum(
                all(type(u.get(key)) is int and u[key] >= 0 for key in ('input_tokens', 'output_tokens'))
                for u in journal.usage),
            input_tokens=sum(u['input_tokens'] for u in journal.usage if type(u.get('input_tokens')) is int),
            output_tokens=sum(u['output_tokens'] for u in journal.usage if type(u.get('output_tokens')) is int))
        write_json(output / 'progress.json', progress)
        if progress['status'] == 'stopped_on_first_error':
            break
    else:
        progress['status'] = 'completed'
        write_json(output / 'progress.json', progress)
    return progress


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, default=PREPARED)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    if args.validate_only:
        manifest = validate(args.prepared)
        print(json.dumps({'status': 'validated', 'calls': len(manifest['calls'])}))
    else:
        if not args.live or args.output is None:
            parser.error('--live and --output required for execution')
        progress = run(args.prepared, args.output)
        print(json.dumps({key: value for key, value in progress.items() if key != 'rows'}))
        raise SystemExit(0 if progress['status'] == 'completed' else 2)
