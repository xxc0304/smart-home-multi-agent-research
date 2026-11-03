"""Zero-network qualification of fixed method on new packets and2repeats."""
import argparse
import json
import tempfile
import urllib.error
from pathlib import Path

from coreta.local_work.data import read, write
from run_local_work_handoff_confirm import freeze, verify, run, authorize, digest, ROOT, LIMITS, make_flow
from score_local_work_handoff_confirm import summarize


def check(data, output):
    data, output = Path(data), Path(output)
    if output.exists():
        raise ValueError('fresh check output required')
    output.mkdir(parents=True)
    old = ROOT / 'runs/local-work-handoff-pilot-live-20261027-v1/flows'
    historical = {path.name: read(path / 'EVENTS.json') for path in old.iterdir() if path.is_dir()}
    assert len(historical) == 12 and sum(len(events) for events in historical.values()) == 84
    expected = read(data / 'DRAFT_PLAN.json')['schedule']
    frozen_old = read(ROOT / 'runs/local-work-handoff-pilot-prepared-20261027-v1/manifest.json')
    for name, hash_value in frozen_old['source_sha256'].items():
        if name.startswith('src/'):
            assert digest(ROOT / name) == hash_value, 'Method/prompt changed after pilot: ' + name
    for cid in ('ordinary-01', 'ordinary-02', 'dependent-01', 'dependent-02'):
        case = read(data / 'cases' / (cid + '.json'))
        a, b = make_flow(case, 'ordinary').pending_requests(), make_flow(case, 'local_work').pending_requests()
        for actor in a:
            assert a[actor]['packet'] == b[actor]['packet'] and a[actor]['schema'] == b[actor]['schema']
            assert set(a[actor]['packet']['task']) == {'task_id', 'question'}
    fixtures = []
    with tempfile.TemporaryDirectory() as temp:
        prepared = Path(temp) / 'prepared'
        freeze(data, prepared)
        verify(prepared, require_gate=False)
        try:
            verify(prepared)
        except (ValueError, FileNotFoundError):
            pass
        else:
            raise AssertionError('Unreviewed release accepted')
        gate = dict(manifest_sha256=digest(prepared / 'manifest.json'), scope='local_fixture_only')
        write(prepared / 'EXPERIMENT_REVIEW.json', dict(**gate, science='PASS', readiness='PASS'))
        write(prepared / 'PREFLIGHT.json', dict(**gate, status='PASS', tests_passed=True))
        try:
            verify(prepared)
        except ValueError:
            pass
        else:
            raise AssertionError('Fixture gate accepted as live')
        write(Path(temp) / 'grant.json', dict(human_grant='not a real grant'))
        try:
            authorize(prepared, Path(temp) / 'grant.json')
        except ValueError:
            pass
        else:
            raise AssertionError('Unbound grant accepted')
        modes = ('full_natural_history', 'receipt_optional_error', 'one_core_invalid', 'two_core_invalid',
                 'missing_usage', 'over_output', 'transport_error', 'keyboard_second', 'keyboard_mid_receipt')
        for mode in modes:
            calls, optional_error = 0, False

            def transport(payload, timeout):
                nonlocal calls, optional_error
                calls += 1
                packet = json.loads(payload['instructions'].split('\nPACKET=', 1)[1])
                stage = 6 if packet['wave'] == 'final' else packet['wave'] * 2 + (packet['member'] == 'A2')
                spec = expected[(calls - 1) // 7] if mode in ('full_natural_history', 'receipt_optional_error') else None
                if mode in ('full_natural_history', 'receipt_optional_error', 'keyboard_mid_receipt'):
                    # Match calls by actual request task/arm; repeated flows still receive full original replies.
                    case_id = next(cid for cid in ('ordinary-01', 'ordinary-02', 'dependent-01', 'dependent-02')
                                   if read(data / 'cases' / (cid + '.json'))['task']['task_id'] == packet['task']['task_id'])
                    if 'receipts' not in packet:
                        arm = 'discussion'
                    else:
                        # In failure mode schedule positions prior to interruption are still complete7-slot blocks.
                        arm = expected[(calls - 1) // 7]['arm']
                    raw = historical[case_id + '-' + arm][stage]['raw']
                else:
                    raw = historical['dependent-01-local_work'][stage]['raw']
                if mode == 'receipt_optional_error' and 'receipts' in packet and packet['wave'] != 'final' and not optional_error:
                    value = json.loads(raw)
                    value['receipts'] = [dict(target='Invalid engineering carrier', expression='1+2')]
                    raw = json.dumps(value)
                    optional_error = True
                if mode == 'one_core_invalid' and calls == 1:
                    raw = '{"message":'
                if mode == 'two_core_invalid' and calls <= 2:
                    raw = '{"message":'
                if mode == 'transport_error' and calls == 1:
                    raise urllib.error.URLError('Offline injected failure')
                if mode == 'keyboard_second' and calls == 2:
                    raise KeyboardInterrupt('Offline interrupt')
                if mode == 'keyboard_mid_receipt' and calls == 46:
                    raise KeyboardInterrupt('Offline late consumer interrupt')
                envelope = dict(status='completed', output=[dict(type='message', content=[dict(type='output_text', text=raw)])],
                                usage=dict(input_tokens=100, output_tokens=100))
                if mode == 'missing_usage' and calls == 1:
                    envelope.pop('usage')
                if mode == 'over_output' and calls == 1:
                    envelope['usage']['output_tokens'] = payload['max_output_tokens'] + 1
                return envelope

            state = run(prepared, output / mode, transport=transport, fixture=True)
            assert len(state['flows']) == 24 and all(r['exact_match'] is None for r in state['flows'])
            if mode in ('full_natural_history', 'receipt_optional_error'):
                assert state['status'] == 'completed' and state['attempts'] == 168
            elif mode == 'one_core_invalid':
                assert state['status'] == 'completed_with_incomplete_flows' and state['attempts'] == 163
            elif mode in ('two_core_invalid', 'keyboard_second'):
                assert state['status'] == 'stopped' and state['attempts'] == 2
            elif mode == 'keyboard_mid_receipt':
                assert state['status'] == 'stopped' and state['attempts'] == 46 and state['unknown_usage']
            else:
                assert state['status'] == 'stopped' and state['attempts'] == 1
            assert calls == state['attempts']
            requests = [json.loads(line) for line in (output / mode / 'requests.jsonl').read_text(encoding='utf8').splitlines()]
            assert all(r['retry'] == 0 for r in requests)
            if mode in ('full_natural_history', 'keyboard_mid_receipt', 'transport_error'):
                from analyze_local_work_handoff_confirm import audit
                result = audit(prepared, output / mode)
                assert result['technical']['completed_flow_replays_match']
            from score_local_work_handoff_confirm import evaluate
            try:
                evaluate(prepared, output / mode)
            except ValueError as exc:
                assert 'Fixture outputs' in str(exc)
            else:
                raise AssertionError('Fixture scored as model result')
            fixtures.append(dict(mode=mode, status=state['status'], fixture_attempts=calls, model_calls=0,
                                 max_input=max(r['estimated_input_count'] for r in requests),
                                 total_input=sum(r['estimated_input_count'] for r in requests)))
        synthetic = []
        for spec in expected:
            group = read(data / 'cases' / (spec['case_id'] + '.json'))['group']
            synthetic.append(dict(**spec, group=group, status='completed' if spec['repeat'] == 1 else 'not_started',
                                  exact_match=1 if spec['repeat'] == 1 else None, nonanswer=False))
        summary = summarize(synthetic)
        for group in summary['groups'].values():
            for arm in group['arms'].values():
                assert arm['distinct_tasks'] == 2 and arm['planned_task_runs'] == 4
                assert arm['official_em_completed'] == 1 and arm['all_planned_success'] == .5
                assert all(r['correct_repeats'] == 1 for r in arm['task_repeat_matrix'])
        target = prepared / 'cases/ordinary-01.json'
        original = target.read_bytes()
        try:
            target.write_bytes(original + b' ')
            try:
                verify(prepared, fixture=True)
            except ValueError:
                pass
            else:
                raise AssertionError('Changed task accepted')
        finally:
            target.write_bytes(original)
        verify(prepared, fixture=True)
    report = dict(kind='offline_confirmation_preflight_not_model_results', model_calls=0,
                  actual_prior_natural_reply_files=84, replayed_request_slots=168, fixtures=fixtures,
                  method_unchanged_from_completed_pilot=True, same_tool_initial_packets_equal=True,
                  repeat_denominator_and_missing_export_checks_passed=True,
                  previous_replies_used_only_in_local_carriers=True, tests_passed=True,
                  live_status='No batch-specific authorization; DO_NOT_RUN until gates/release/grant')
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
