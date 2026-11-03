"""Offline full-history load and bounded-run failure checks. Never calls an API."""
import argparse
import copy
import json
import tempfile
import urllib.error
from pathlib import Path

from coreta.local_work.data import read, write
from run_local_work_v2 import freeze, verify, run, authorize
from run_local_work_calibration import digest, ROOT


def check(data, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    historical = read(ROOT / 'runs/local-work-calibration-live-20261027-v1/flows/diagnostic-01-local_work/EVENTS.json')
    fixtures = []
    with tempfile.TemporaryDirectory() as temp:
        prepared = Path(temp) / 'prepared'
        freeze(data, prepared)
        verify(prepared, require_gate=False)
        rejected_without_gate = False
        try:
            verify(prepared)
        except (ValueError, FileNotFoundError):
            rejected_without_gate = True
        assert rejected_without_gate
        write(prepared / 'EXPERIMENT_REVIEW.json',
              dict(manifest_sha256=digest(prepared / 'manifest.json'), scope='local_fixture_only',
                   science='PASS', readiness='PASS'))
        write(prepared / 'PREFLIGHT.json',
              dict(manifest_sha256=digest(prepared / 'manifest.json'), scope='local_fixture_only',
                   status='PASS', tests_passed=True))
        try:
            verify(prepared)
        except ValueError:
            pass
        else:
            raise AssertionError('Fixture-only gate must never authorize live')
        bad_auth = Path(temp) / 'bad_auth.json'
        write(bad_auth, dict(human_grant='fixture, not real user authorization'))
        try:
            authorize(prepared, bad_auth)
        except ValueError:
            pass
        else:
            raise AssertionError('Unbound authorization accepted')
        for mode in ('full_history', 'one_incomplete', 'two_incomplete', 'missing_usage', 'over_output', 'transport_error', 'keyboard_second'):
            counter = 0
            sizes = []

            def transport(payload, timeout):
                nonlocal counter
                counter += 1
                packet = json.loads(payload['instructions'].split('\nPACKET=', 1)[1])
                assert set(packet['task']) == {'task_id', 'question'}
                final = packet['wave'] == 'final'
                index = 6 if final else 2 * packet['wave'] + (0 if packet['member'] == 'A1' else 1)
                # Full actual prior model response; unrelated new-task semantics are NOT scored.
                raw = historical[index]['raw']
                envelope = dict(status='completed', output=[dict(type='message', content=[dict(type='output_text', text=raw)])],
                                usage=dict(input_tokens=100, output_tokens=100))
                if mode == 'transport_error' and counter == 1:
                    raise urllib.error.URLError('injected offline transport failure')
                if mode == 'keyboard_second' and counter == 2:
                    raise KeyboardInterrupt('injected offline operator interruption')
                if (mode == 'one_incomplete' and counter == 1) or (mode == 'two_incomplete' and counter <= 2):
                    envelope['status'] = 'incomplete'
                if mode == 'missing_usage' and counter == 1:
                    envelope.pop('usage')
                if mode == 'over_output' and counter == 1:
                    envelope['usage']['output_tokens'] = payload['max_output_tokens'] + 1
                return envelope

            state = run(prepared, output / mode, transport=transport, fixture=True)
            assert len(state['flows']) == 12
            assert all(row['exact_match'] is None for row in state['flows'])
            from score_local_work_v2 import evaluate
            try:
                evaluate(prepared, output / mode, prepared / 'offline')
            except ValueError as exc:
                assert 'Fixture outputs' in str(exc)
            else:
                raise AssertionError('Fixture predictions received model-result scores')
            if mode == 'full_history':
                assert state['status'] == 'completed' and state['attempts'] == 84
                assert all(row['network_calls'] == 0 and row['status'] == 'completed' for row in state['flows'])
            elif mode == 'one_incomplete':
                assert state['status'] == 'completed_with_incomplete_flows' and state['attempts'] == 79
                assert state['flows'][0]['status'] == 'technical_incomplete'
                assert not (output / mode / 'flows' / state['flows'][0]['flow_id'] / 'requests/01-A1.json').exists()
            elif mode == 'two_incomplete':
                assert state['status'] == 'stopped' and state['attempts'] == 2
            elif mode == 'keyboard_second':
                assert state['status'] == 'stopped' and state['attempts'] == 2 and state['unknown_usage']
                assert sum(row['status'] == 'not_started' for row in state['flows']) == 11
                events = read(output / mode / 'flows' / state['flows'][0]['flow_id'] / 'EVENTS.json')
                assert events[0]['status'] == 'readable' and events[1]['status'] == 'missing_response'
            else:
                assert state['status'] == 'stopped' and state['attempts'] == 1
            assert counter == state['attempts']
            requests = [json.loads(line) for line in (output / mode / 'requests.jsonl').read_text(encoding='utf8').splitlines()]
            assert all(row['retry'] == 0 for row in requests)
            sizes = [row['estimated_input_count'] for row in requests]
            fixtures.append(dict(mode=mode, fixture_attempts=counter, model_calls=0, status=state['status'],
                                 max_input=max(sizes), total_input=sum(sizes)))
        case_path = prepared / 'cases/ordinary-01.json'
        unchanged = case_path.read_bytes()
        try:
            case_path.write_bytes(unchanged + b' ')
            try:
                verify(prepared, fixture=True)
            except ValueError:
                pass
            else:
                raise AssertionError('Changed frozen case accepted')
        finally:
            case_path.write_bytes(unchanged)
        verify(prepared, fixture=True)
    report = dict(kind='offline_run_qualification_not_model_results', model_calls=0,
                  full_new_batch_history_carrier_slots=84,
                  source_of_history='all seven full replies from completed diagnostic-01-local_work',
                  scope='New task packet assembly and failure policy; not new model generation or source-correct reasoning',
                  fixtures=fixtures, gate_rejections=['no review', 'fixture gate cannot authorize live',
                                                     'unbound authorization', 'frozen case changed'],
                  readiness_checks_passed=True)
    write(output / 'CHECK.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.data, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
