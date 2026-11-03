"""Handle-contract calibration with independent-item quarantine; new batches only."""
import argparse
import copy
import json
from pathlib import Path
import time

from jsonschema.exceptions import ValidationError
from tokenizers import Tokenizer

from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
import local_judgment_frontend as interface
import prepare_local_judgment_supplement as preparation
import local_judgment_handle_contract as contract


ROOT = preparation.ROOT
TOKENIZER = ROOT / 'data/tokenizer-v4.1-flash-1017/tokenizer.json'
RUBRIC = ROOT / 'design/LOCAL_JUDGMENT_MOON_CALIBRATION_RUBRIC_20261025.md'
MAX_REQUESTS, CAP, TOTAL_CAP = 10, 1536, 15360


def freeze(output):
    output = Path(output)
    preparation.prepare(output)
    config = dict(provider='deepseek', base_url='https://api.deepseek.com', model='deepseek-flash',
                  generation=dict(reasoning_effort='none', temperature=0.7, max_input_tokens=8192),
                  protocol=dict(transport_retries_per_request=0, max_format_repairs=0,
                                request_timeout_seconds=120))
    interface.write(output / 'config.json', config)
    (output / 'OFFLINE_RUBRIC.md').write_bytes(RUBRIC.read_bytes())
    manifest = dict(version='local-judgment-supplement/1', max_requests=MAX_REQUESTS,
                    max_total_output_tokens=TOTAL_CAP, per_request_output_cap=CAP,
                    tokenizer=dict(path=str(TOKENIZER.relative_to(ROOT)), sha256=interface.digest(TOKENIZER)),
                    files={str(p.relative_to(output)).replace('\\', '/'): interface.digest(p)
                           for p in output.rglob('*') if p.is_file() and p.name != 'manifest.json'},
                    code_sha256={str(p.relative_to(ROOT)).replace('\\', '/'): interface.digest(p) for p in [
                        Path(__file__), Path(interface.__file__), Path(preparation.__file__),
                        Path(contract.__file__), Path(preparation.original.__file__),
                        ROOT / 'src/coreta/model_client.py', ROOT / 'src/coreta/schemas.py']})
    interface.write(output / 'manifest.json', manifest)
    verify(output)
    return dict(manifest_sha256=interface.digest(output / 'manifest.json'), status='FROZEN_NOT_AUTHORIZED')


def child(root, name):
    path = (Path(root) / name).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('manifest path leaves root')
    return path


def verify(prepared):
    prepared = Path(prepared)
    manifest = interface.read(prepared / 'manifest.json')
    if manifest.get('version') != 'local-judgment-supplement/1':
        raise ValueError('supplement runner requires its own10-slot batch; cannot run parent')
    for root, entries in [(prepared, manifest['files']), (ROOT, manifest['code_sha256'])]:
        for name, expected in entries.items():
            if interface.digest(child(root, name)) != expected:
                raise ValueError('frozen input/code changed: ' + name)
    tokenizer = child(ROOT, manifest['tokenizer']['path'])
    if tokenizer != TOKENIZER.resolve() or interface.digest(tokenizer) != manifest['tokenizer']['sha256']:
        raise ValueError('tokenizer changed')
    if (manifest['max_requests'], manifest['max_total_output_tokens'], manifest['per_request_output_cap']) != (10, 15360, 1536):
        raise ValueError('unexpected budget')
    config = interface.read(prepared / 'config.json')
    if config['base_url'] != 'https://api.deepseek.com' or config['model'] != 'deepseek-flash':
        raise ValueError('unexpected destination/model')
    if config['protocol']['transport_retries_per_request'] != 0 or config['protocol']['max_format_repairs'] != 0:
        raise ValueError('retries prohibited')
    plan = interface.read(prepared / 'CALIBRATION_PLAN.json')
    expected = []
    for n in range(4, 7):
        for repeat in ((2,) if n == 4 else (1, 2)):
            order = ('with_resources', 'without_resources') if repeat == 1 else ('without_resources', 'with_resources')
            expected.extend((f'moon-local-{n:02d}', repeat, c) for c in order)
    if [(r['item'], r['repeat'], r['condition']) for r in plan['schedule']] != expected:
        raise ValueError('schedule differs')
    if [r.get('original_slot') for r in plan['schedule']] != list(range(15,25)):
        raise ValueError('supplement must cover only unattempted original slots15..24')
    for row in plan['schedule']:
        request = interface.read(child(prepared, row['request']))
        packet = interface.read(prepared / 'packets' / (row['item'] + '-' + row['condition'] + '.json'))
        if request != preparation.make_request(packet) or request['max_output_tokens'] != CAP:
            raise ValueError('request/packet/schema mismatch')
    return manifest, plan, config


def gates(prepared):
    bound = interface.digest(Path(prepared) / 'manifest.json')
    preflight = interface.read(Path(prepared) / 'PREFLIGHT.json')
    review = interface.read(Path(prepared) / 'EXPERIMENT_REVIEW.json')
    if preflight.get('status') != 'passed' or preflight.get('manifest_sha256') != bound:
        raise ValueError('fresh preflight required')
    if any(review.get(k) != v for k, v in [('science', 'PASS'), ('readiness', 'PASS'), ('technical_launch', 'RUN_ALLOWED')]):
        raise ValueError('fresh dual review required')
    if review.get('manifest_sha256') != bound:
        raise ValueError('review manifest differs')
    auth = interface.read(Path(prepared) / 'AUTHORIZATION.json')
    if not (auth.get('authorized') is True and auth.get('manifest_sha256') == bound
            and auth.get('max_requests') == 10 and auth.get('destination') == 'https://api.deepseek.com/responses'
            and auth.get('user_authorization_text')):
        raise ValueError('specific batch authorization required')


def run(prepared, output, *, transport=None, local_validation=False):
    prepared, output = Path(prepared), Path(output)
    manifest, plan, config = verify(prepared)
    if local_validation:
        if transport is None:
            raise ValueError('local validation requires explicit mock transport')
    else:
        gates(prepared)
    if output.exists():
        raise ValueError('new output directory required; no resume')
    output.mkdir(parents=True)
    interface.write(output / 'manifest.json', manifest)
    state = dict(status='running', mode='local_mock' if local_validation else 'live', attempts=0,
                 input_tokens=0, output_tokens=0, unknown_usage=False, completed=[],
                 max_requests=10, output_budget_reserved=0, error=None, quarantined=[], consecutive_unreadable=0)
    roster = [dict(r, slot=i) for i, r in enumerate(plan['schedule'], 1)]
    current = None

    def save():
        interface.write(output / 'progress.json', state)
        answers = {r['slot']: r for r in state['completed']}
        quarantined = {r['slot']: r for r in state['quarantined']}
        interface.write(output / 'review.json', dict(status=state['status'], mode=state['mode'],
            rows=[dict(r, status='completed' if r['slot'] in answers else
                       'quarantined' if r['slot'] in quarantined else
                       'failed' if state.get('failed_slot') == r['slot'] else 'not_run',
                       answer=answers.get(r['slot'], {}).get('answer'), semantic_score=None) for r in roster]))

    def log(name, value):
        with (output / name).open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(value, ensure_ascii=False) + '\n')
        if name != 'responses.jsonl':
            return
        response = value.get('response')
        if response is None:
            state['unknown_usage'] = True
            return
        chunks = [p['text'] for item in response.get('output', []) if item.get('type') == 'message'
                  for p in item.get('content', []) if p.get('type') == 'output_text' and isinstance(p.get('text'), str)]
        if chunks:
            (output / f'{current:02d}.raw.txt').write_text(''.join(chunks), encoding='utf-8')
        usage = response.get('usage', {})
        for key in ('input_tokens', 'output_tokens'):
            amount = usage.get(key)
            if type(amount) is not int or amount < 0:
                state['unknown_usage'] = True
            else:
                state[key] += amount
                if key == 'output_tokens' and amount > CAP:
                    state['response_over_cap'] = True

    tokenizer = Tokenizer.from_file(str(TOKENIZER))
    counter = lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids)
    client = DeepSeekClient(config, log, transport=transport, token_counter=counter)
    save()
    try:
        for row in roster:
            current = row['slot']
            if client.attempts >= MAX_REQUESTS or state['output_budget_reserved'] + CAP > TOTAL_CAP:
                raise ValueError('budget exhausted')
            request = interface.read(child(prepared, row['request']))
            packet = interface.strict_json(request['instructions'].split('PACKET=', 1)[1])
            payload = client.payload(request['instructions'], request['schema'], CAP)
            state['output_budget_reserved'] += CAP
            try:
                raw = client.complete(payload, deadline=time.monotonic() + 180, logical_seed=row['repeat'])
            except ProtocolError as exc:
                if exc.code == 'SCHEMA_ERROR' and not state['unknown_usage'] and not state.get('response_over_cap'):
                    state['quarantined'].append(dict(row, error_type=exc.code, detail=str(exc)))
                    state['consecutive_unreadable'] += 1
                    state['attempts'] = client.attempts
                    save()
                    if state['consecutive_unreadable'] >= 2:
                        raise ValueError('two consecutive unreadable provider outputs') from exc
                    continue
                raise
            (output / f'{current:02d}.raw.txt').write_text(raw, encoding='utf-8')
            if state['unknown_usage']:
                raise ValueError('unknown usage; raw response retained')
            if state.get('response_over_cap'):
                raise ValueError('reported response output exceeds per-request cap')
            if state['output_tokens'] > state['output_budget_reserved']:
                raise ValueError('reported output exceeds reserved budget')
            try:
                answer, events = contract.decode(raw, 'second', packet)
            except (ValueError, ValidationError) as exc:
                state['quarantined'].append(dict(row, error_type=type(exc).__name__, detail=str(exc)))
                state['consecutive_unreadable'] += 1
                state['attempts'] = client.attempts
                save()
                if state['consecutive_unreadable'] >= 2:
                    raise ValueError('two consecutive unreadable local outputs') from exc
                continue
            state['consecutive_unreadable'] = 0
            state['completed'].append(dict(row, answer=answer, normalization_events=events))
            state['attempts'] = client.attempts
            save()
        state['status'] = 'completed_with_quarantine' if state['quarantined'] else 'completed'
    except Exception as exc:
        state.update(status='stopped', failed_slot=current, error_type=type(exc).__name__)
        if isinstance(exc, ValidationError):
            state['error'] = 'SCHEMA_ERROR: ' + '/'.join(str(x) for x in exc.absolute_path)
        elif isinstance(exc, ProtocolError):
            state['error'] = str(exc)
        else:
            state['error'] = str(exc)
        raise
    finally:
        state['attempts'] = client.attempts
        save()
    return state


def preflight(prepared):
    prepared = Path(prepared)
    manifest, plan, config = verify(prepared)
    if (prepared / 'mock_validation').exists():
        raise ValueError('preflight output exists; do not resume')
    history = interface.read(interface.DEFAULT_HISTORY / 'progress.json')['completed']
    historical = [(i, r) for i, r in enumerate(history, 1) if r['stage'] == 'CONTRIBUTE']
    maxima = dict(input=0, adapted_output=0)
    adaptation_provenance = []
    tok = Tokenizer.from_file(str(TOKENIZER))
    count = lambda text: len(tok.encode(text, add_special_tokens=False).ids)

    def mock(payload, timeout):
        packet = interface.strict_json(payload['instructions'].split('PACKET=', 1)[1])
        index = len(adaptation_provenance)
        number, row = historical[index % len(historical)]
        original_file = interface.DEFAULT_HISTORY / f'{number:02d}.raw.txt'
        original = interface.strict_json(original_file.read_text(encoding='utf-8'))
        # New scenario citations are explicit synthetic fixtures. Legacy text is retained for load, not truth.
        source = (packet['own_sources'] or packet['public_sources'])[0]
        value = dict(status='conditional', conclusion=original['text'],
                     source_ids=[source['ref']],
                     scope=json.dumps({k: v for k, v in original.items() if k != 'text'}, ensure_ascii=False),
                     missing=['Synthetic new-task envelope: not a model answer or semantic judgment.'])
        raw = json.dumps(value, ensure_ascii=False)
        maxima['input'] = max(maxima['input'], count(json.dumps(payload, ensure_ascii=False)) + 256)
        maxima['adapted_output'] = max(maxima['adapted_output'], count(raw))
        if count(raw) > CAP:
            raise ValueError('adapted stress output exceeds cap')
        adaptation_provenance.append(dict(slot=index + 1, file=str(original_file),
            sha256=interface.digest(original_file), type='adapted_full_legacy_content_synthetic_new_citations'))
        return dict(status='completed', usage=dict(input_tokens=count(json.dumps(payload)), output_tokens=count(raw)),
                    output=[dict(type='message', content=[dict(type='output_text', text=raw)])])

    result = run(prepared, prepared / 'mock_validation', transport=mock, local_validation=True)
    if len(result['completed']) != 10 or result['mode'] != 'local_mock':
        raise ValueError('mock load incomplete')
    prior = interface.replay(prepared / 'historical_common_replay')
    checks = dict(status='passed', manifest_sha256=interface.digest(prepared / 'manifest.json'),
                  model_requests=0, mock_attempts=10, maximum_mock_input_estimate=maxima['input'],
                  maximum_adapted_output_tokens=maxima['adapted_output'],
                  complete_historical_common_replay=dict(total=prior['legacy_total'], admitted=prior['legacy_admitted']),
                  adaptation_provenance=adaptation_provenance, real_new_task_provider_outputs=0,
                  limitations=['Adapted load fixtures are not new-task service responses or capability results.',
                               'Single unreadable independent output is quarantined without retry; two consecutive unreadable outputs stop. Global faults stop immediately.'])
    interface.write(prepared / 'PREFLIGHT.json', checks)
    return {k: v for k, v in checks.items() if k != 'adaptation_provenance'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['freeze', 'preflight', 'run'])
    parser.add_argument('--prepared', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'freeze':
        print(json.dumps(freeze(args.prepared)))
    elif args.command == 'preflight':
        print(json.dumps(preflight(args.prepared)))
    else:
        if args.output is None:
            parser.error('--output required for run')
        run(args.prepared, args.output)


if __name__ == '__main__':
    main()
