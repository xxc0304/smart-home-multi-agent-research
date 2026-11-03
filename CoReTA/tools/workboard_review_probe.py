"""Prepare/replay fixed review inputs; no solution generation or online scoring."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import time
from pathlib import Path

from coreta.handoff.__main__ import PROJECT, DESIGN, configure, load_counter, DEFAULT_TOKENIZER
from coreta.handoff.contracts import HandoffContracts
from coreta.handoff.gateway import Journal, write_json
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
from coreta.workboard.prompts import STAGES

SOURCE = PROJECT / 'runs/workboard-d0-natural-live-20261022-r2'
PROPOSAL = PROJECT / 'refine-logs/workboard-d0-diagnostic-20261022/REVIEW_REPLACEMENT_DESIGN_20261023.md'
REVIEW_STAGES = ('CHECK_USE', 'CHECK_EFFECT')
TASKS = ('hb-dev-004-r1-c1', 'hb-dev-034-r1-c2')
SYSTEMS = ('v3_continuation', 'd0_continuation')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def hashes(paths):
    return {str(Path(p).resolve()): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}


def packet_of(payload):
    return json.loads(payload['instructions'].split('\nPACKET=', 1)[1].split('\nOUTPUT_SCHEMA=', 1)[0])


def output_schema(payload):
    """Keep local validation independent of the provider's format enforcement."""
    schema = json.loads(payload['instructions'].rsplit('\nOUTPUT_SCHEMA=', 1)[1])
    fmt = payload['text']['format']
    if fmt['type'] == 'json_schema':
        if fmt['schema'] != schema:
            raise ValueError('Provider/local output schema mismatch')
    elif fmt != {'type': 'json_object'}:
        raise ValueError('Unsupported output format')
    return schema


def candidate_duties():
    lines = PROPOSAL.read_text(encoding='utf-8').splitlines()
    starts = {'CHECK_USE': '> Evaluate the actual revision,',
              'CHECK_EFFECT': '> Independently compare BEFORE and AFTER'}
    result = {}
    for stage, prefix in starts.items():
        matches = [line[2:] for line in lines if line.startswith(prefix)]
        if len(matches) != 1:
            raise ValueError('Expected exactly one approved duty paragraph: ' + stage)
        result[stage] = matches[0]
    return result


def intervene(payload, stage, duty):
    result = copy.deepcopy(payload)
    prefix, body = payload['instructions'].split('\nPACKET=', 1)
    if prefix.count(STAGES[stage]) != 1:
        raise ValueError('Original base review duty not found exactly once')
    result['instructions'] = prefix.replace(STAGES[stage], duty, 1) + '\nPACKET=' + body
    return result


def prepare(output):
    output = Path(output)
    if output.exists():
        raise ValueError('Preparation output must be new')
    config, _ = configure(PROJECT / 'config/deepseek_flash_inspection.json', DESIGN / 'runtime.defaults.json')
    config['protocol'] = {'transport_retries_per_request': 0, 'request_timeout_seconds': 120}
    counter = load_counter()
    client = DeepSeekClient(config, lambda *args: None, token_counter=counter)
    duties = candidate_duties()
    inputs, files = [], []
    for task in TASKS:
        for system in SYSTEMS:
            path = SOURCE / task / system / 'requests.jsonl'
            files.append(path)
            found = {}
            for row in map(json.loads, path.read_text(encoding='utf-8').splitlines()):
                stage = row['call_context']['stage']
                if stage not in REVIEW_STAGES:
                    continue
                if stage in found or row['retry'] != 0:
                    raise ValueError('Ambiguous original review request')
                payload = row['payload']
                p = packet_of(payload)
                schema = json.loads(payload['instructions'].split('\nOUTPUT_SCHEMA=', 1)[1])
                if payload != client.payload(payload['instructions'], schema, 3072):
                    raise ValueError('Original payload differs from approved configuration/schema/cap')
                direct = {'T', *(m['ref'] for m in p['SELF_MATERIALS'])}
                if (p['SELF']['agent_id'] != row['call_context']['member'] or p['STAGE'] != stage
                        or set(p['SOURCE_ACCESS']['direct_original_refs']) != direct):
                    raise ValueError('Original packet identity/access mismatch')
                found[stage] = row
            if set(found) != set(REVIEW_STAGES):
                raise ValueError('Missing review stage')
            for stage in REVIEW_STAGES:
                row = found[stage]
                original = row['payload']
                candidate = intervene(original, stage, duties[stage])
                estimates = {c: client.size(p) for c, p in [('A', original), ('B', candidate)]}
                if max(estimates.values()) > config['generation']['max_input_tokens']:
                    raise ValueError('Frozen payload exceeds input limit')
                inputs.append({'id': f'{task}--{system}--{stage}', 'task': task, 'system': system,
                               'stage': stage, 'member': row['call_context']['member'],
                               'historical_logical_call': row['call_context']['logical_call'],
                               'source': str(path.resolve()), 'input_estimates': estimates,
                               'payloads': {'A': original, 'B': candidate}})
    output.mkdir(parents=True, exist_ok=False)
    for item in inputs:
        for cond, payload in item.pop('payloads').items():
            write_json(output / f"{item['id']}--{cond}.json", payload)
    calls = []
    for ordinal in range(4):
        pair = inputs[ordinal * 2:ordinal * 2 + 2]
        for repeat in (1, 2):
            conditions = ('A', 'B') if (ordinal + repeat) % 2 else ('B', 'A')
            for cond in conditions:
                for item in pair:
                    calls.append({k: item[k] for k in ('id', 'task', 'system', 'stage', 'member')})
                    calls[-1].update(condition=cond, repeat=repeat,
                                     payload_file=f"{item['id']}--{cond}.json")
    dependencies = [Path(__file__), PROPOSAL, PROJECT / 'src/coreta/model_client.py',
                    PROJECT / 'src/coreta/schemas.py', PROJECT / 'src/coreta/handoff/contracts.py',
                    PROJECT / 'src/coreta/handoff/gateway.py', PROJECT / 'src/coreta/handoff/__main__.py',
                    PROJECT / 'src/coreta/workboard/prompts.py',
                    PROJECT / 'config/deepseek_flash_inspection.json', DESIGN / 'runtime.defaults.json',
                    DEFAULT_TOKENIZER, *files]
    manifest = {'kind': 'fixed_artifact_review_replacement_probe', 'scope': 'selected_development_inputs',
                'inputs': inputs, 'calls': calls, 'config': config, 'repeats': 2,
                'max_http_attempts': 32, 'max_output_tokens': 98304,
                'transport_retries': 0, 'format_repairs': 0, 'sampling_seed_sent': False,
                'online_gold_read': False, 'source_hashes': hashes(dependencies),
                'payload_hashes': hashes(output.glob('*.json'))}
    write_json(output / 'manifest.json', manifest)
    return manifest


def validate(prepared):
    prepared = Path(prepared)
    manifest = read(prepared / 'manifest.json')
    for key in ('source_hashes', 'payload_hashes'):
        if hashes(manifest[key]) != manifest[key]:
            raise ValueError('Frozen preparation changed: ' + key)
    if (len(manifest['calls']) != 32 or manifest['max_http_attempts'] != 32
            or manifest['max_output_tokens'] != 98304):
        raise ValueError('Unexpected frozen batch budget')
    for row in manifest['calls']:
        payload = read(prepared / row['payload_file'])
        output_schema(payload)
        if payload['text']['format']['type'] == 'json_object':
            policy = manifest.get('output_format_policy', {})
            if (policy.get('mode') != 'json_object_local_schema'
                    or payload['input'] != policy.get('input_instruction')):
                raise ValueError('Undeclared JSON object format policy')
    return manifest


def run(prepared, output, *, transport=None):
    prepared, output = Path(prepared), Path(output)
    manifest = validate(prepared)
    if output.exists():
        raise ValueError('Run output must be new; no resume')
    if transport is None and not os.environ.get('DEEPSEEK_API_KEY'):
        raise ValueError('Approved API credential unavailable')
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'manifest.json', manifest)
    journal = Journal(output)
    client = DeepSeekClient(manifest['config'], journal.log, transport=transport, token_counter=load_counter())
    progress = {'kind': manifest['kind'], 'status': 'running',
                'transport_mode': 'live' if transport is None else 'scripted_fixture_not_live',
                'actual_http_attempts': 0, 'transport_attempts': 0, 'completed': 0,
                'input_tokens': 0, 'output_tokens': 0, 'unknown_usage_attempts': 0,
                'rows': [dict(row, status='not_started') for row in manifest['calls']]}
    write_json(output / 'progress.json', progress)
    for number, row in enumerate(progress['rows'], 1):
        row['status'] = 'running'
        journal.call_context = {k: row[k] for k in ('task', 'system', 'stage', 'member', 'condition', 'repeat')}
        journal.call_context.update(logical_call=number, input_id=row['id'])
        write_json(output / 'progress.json', progress)
        error = None
        try:
            if client.attempts >= 32 or progress['output_tokens'] + 3072 > 98304:
                raise ProtocolError('BUDGET', 'Cannot reserve next request')
            payload = read(prepared / row['payload_file'])
            raw = client.complete(payload, deadline=time.monotonic() + 120, logical_seed=16 + row['repeat'])
            value = HandoffContracts.decode(raw, output_schema(payload))
            if len(journal.usage) != client.attempts or any(
                    type(u.get(k)) is not int or u[k] < 0 for u in journal.usage
                    for k in ('input_tokens', 'output_tokens')):
                raise ProtocolError('USAGE_UNKNOWN', 'Incomplete usage; raw trace retained')
            if journal.usage[-1]['output_tokens'] > 3072:
                raise ProtocolError('OUTPUT_BUDGET', 'Server output exceeds stage cap')
            journal.log('stages.jsonl', {'output': value})
            journal.completed += 1
            row['status'] = 'completed'
        except ProtocolError as exc:
            error = {'code': exc.code, 'detail': exc.detail}
        except Exception as exc:
            error = {'code': 'EXECUTION_ERROR', 'detail': type(exc).__name__}
        row['error'] = error
        progress.update(transport_attempts=client.attempts,
                        actual_http_attempts=client.attempts if transport is None else 0,
                        completed=journal.completed,
                        input_tokens=sum(u.get('input_tokens', 0) for u in journal.usage
                                         if type(u.get('input_tokens')) is int),
                        output_tokens=sum(u.get('output_tokens', 0) for u in journal.usage
                                          if type(u.get('output_tokens')) is int),
                        unknown_usage_attempts=client.attempts - sum(
                            all(type(u.get(k)) is int and u[k] >= 0 for k in ('input_tokens', 'output_tokens'))
                            for u in journal.usage))
        if error:
            row['status'] = 'interrupted'
            progress['status'] = 'stopped_on_first_error'
            write_json(output / 'progress.json', progress)
            break
        write_json(output / 'progress.json', progress)
    else:
        progress['status'] = 'completed'
        write_json(output / 'progress.json', progress)
    return progress


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('--prepared', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if args.action == 'prepare':
        result = prepare(args.output)
        keys = ('kind', 'max_http_attempts', 'max_output_tokens')
    else:
        if not args.prepared or not args.live:
            parser.error('run requires --prepared and explicit --live')
        result = run(args.prepared, args.output)
        keys = ('kind', 'status', 'actual_http_attempts', 'completed')
    print(json.dumps({k: result[k] for k in keys}))
    return 2 if result.get('status') == 'stopped_on_first_error' else 0


if __name__ == '__main__':
    raise SystemExit(main())
