"""Offline technical/process audit for a finished handoff batch. Does not score semantics."""
import argparse
import json
from collections import Counter
from pathlib import Path

from coreta.local_work.data import read, write
from run_local_work_handoff import make_flow, verify


def audit(prepared, run):
    prepared, run = Path(prepared), Path(run)
    state = read(run / 'progress.json')
    fixture = state['mode'] == 'local_fixture'
    plan = verify(prepared, fixture=fixture)
    if state['status'] == 'running':
        raise ValueError('Wait for the frozen batch to finish before final auditing')
    requests = [json.loads(line) for line in (run / 'requests.jsonl').read_text(encoding='utf8').splitlines()]
    responses = [json.loads(line) for line in (run / 'responses.jsonl').read_text(encoding='utf8').splitlines()]
    assert len(requests) == state['attempts']
    assert all(row['retry'] == 0 for row in requests)
    assert [row['slot'] for row in requests] == list(range(1, state['attempts'] + 1))
    assert len(state['flows']) == len(plan['schedule']) == 12
    rows, by_arm = [], {}
    unknown = 0
    for specification, record in zip(plan['schedule'], state['flows']):
        assert specification['flow_id'] == record['flow_id']
        flow_responses = [r for r in responses if r['flow_id'] == record['flow_id']]
        usage = dict(input_tokens=0, output_tokens=0, cached_input_tokens=0, latency_seconds=0)
        for row in flow_responses:
            usage['latency_seconds'] += row.get('latency_seconds', 0)
            detail = row.get('response', {}).get('usage')
            if not isinstance(detail, dict):
                unknown += 1
                continue
            for name in ('input_tokens', 'output_tokens'):
                if type(detail.get(name)) is int:
                    usage[name] += detail[name]
            usage['cached_input_tokens'] += (detail.get('input_tokens_details') or {}).get('cached_tokens', 0)
        arm = record['arm']
        totals = by_arm.setdefault(arm, dict(input_tokens=0, output_tokens=0, cached_input_tokens=0, requests=0))
        for name in ('input_tokens', 'output_tokens', 'cached_input_tokens'):
            totals[name] += usage[name]
        totals['requests'] += len([r for r in requests if r['flow_id'] == record['flow_id']])
        folder = run / 'flows' / record['flow_id']
        if not (folder / 'EVENTS.json').exists():
            rows.append(dict(flow_id=record['flow_id'], status=record['status'], usage=usage,
                             technical_incomplete=True, counts={}, final_use=None))
            continue
        events = read(folder / 'EVENTS.json')
        attempted_stages = {(request['actor'], request['wave'])
                            for log in requests if log['flow_id'] == record['flow_id']
                            for request in [read(run / 'actual_requests' / f'{log["slot"]:03d}.json')]}
        counts, reasons, trace = Counter(), Counter(), []
        following = [read(path) for path in sorted((folder / 'requests').glob('*.json'))]
        observed_owners = {work['id']: work['owner'] for request in following for work in request['packet'].get('receipts', [])}
        feedback_checked = 0
        for event in events:
            engine = event.get('engine_event', {})
            notices = event.get('notices', []) + engine.get('notices', [])
            if event['wave'] != 3:
                counts['scheduled_member_response_events'] += 1
                counts['attempted_member_calls'] += (event['actor'], event['wave']) in attempted_stages
                counts['member_texts_in_events'] += event['raw'] is not None
                counts['readable_member_messages'] += event['status'] == 'readable'
            counts['turns_with_optional_notices'] += bool(notices)
            counts['accepted_work_submissions_including_revisions'] += len(engine.get('accepted_work', []))
            for key in engine.get('accepted_work', []):
                assert observed_owners.setdefault(key, event['actor']) == event['actor']
            for binding in engine.get('bindings', []):
                counts['accepted_nonnull_bindings' if binding.get('result_id') is not None else 'accepted_null_unbindings'] += 1
                if binding.get('result_id') is not None:
                    consumer, provider = observed_owners[binding['work_id']], observed_owners[binding['result_id']]
                    counts['cross_member_nonnull_bindings' if consumer != provider else 'same_member_nonnull_bindings'] += 1
            for notice in notices:
                counts[notice['kind']] += 1
                if notice.get('reason'):
                    reasons[notice['reason']] += 1
            candidates = [request for request in following
                          if request['actor'] == event['actor'] and request['wave'] > event['wave']]
            if candidates and event['status'] == 'readable':
                feedback = min(candidates, key=lambda request: request['wave'])['packet']['tool_feedback']
                assert feedback is not None and feedback['from_wave'] == event['wave']
                assert feedback['notices'] == notices
                feedback_checked += 1
            trace.append(dict(wave=event['wave'], actor=event['actor'], status=event['status'],
                              accepted_work=engine.get('accepted_work', []), accepted_bindings=engine.get('bindings', []),
                              rejection_kinds=[notice['kind'] for notice in notices]))
        case = read(prepared / 'cases' / (record['case_id'] + '.json'))
        replay = make_flow(case, record['arm'], provenance='offline replay of actual handoff model replies')
        used = 0
        while replay.status == 'pending' and used < len(events):
            pending = replay.pending_requests()
            selected = events[used:used + len(pending)]
            replay.submit({event['actor']: event['raw'] for event in selected if event['raw'] is not None})
            used += len(selected)
        assert used == len(events)
        assert replay.answer == record['final']
        if record['status'] == 'completed':
            assert replay.status == 'completed' and replay.final_use() == record['final_use']
        final_packet = following[-1]['packet'] if record['status'] == 'completed' else None
        rows.append(dict(flow_id=record['flow_id'], group=case['group'], status=record['status'],
                         usage=usage, counts=dict(counts), reasons=dict(reasons), trace=trace,
                         own_turn_feedback_verified=feedback_checked, replay_delivery_matches=True,
                         final_use=record.get('final_use'), final=record.get('final'),
                         final_work=[dict(id=k, **v) for k, v in (final_packet or {}).get('results', {}).items()
                                     if k.startswith('W')]))
    assert sum(r['input_tokens'] for r in by_arm.values()) == state['input_tokens']
    assert sum(r['output_tokens'] for r in by_arm.values()) == state['output_tokens']
    files = dict(actual_requests=len(list((run / 'actual_requests').glob('*.json'))),
                 raw_texts=len(list(run.glob('*.raw.txt'))), http_bodies=len(list((run / 'http_bodies').glob('*.bytes'))))
    if state['status'] == 'completed':
        assert len(responses) == state['attempts'] == 84
        assert files['actual_requests'] == files['raw_texts'] == 84
        if not fixture:
            assert files['http_bodies'] == 84
        assert unknown == 0 and not state['unknown_usage'] and not state['over_cap']
    technical = dict(status=state['status'], mode=state['mode'], attempts=state['attempts'], retries=0, files=files,
                     all_planned_rows_retained=True, unknown_usage=state['unknown_usage'],
                     input_tokens=state['input_tokens'], output_tokens=state['output_tokens'],
                     frozen_sources_verified=True,
                     completed_flow_replays_match=all(r.get('replay_delivery_matches') for r in rows if r['status'] == 'completed'))
    write(run / 'TECHNICAL_AUDIT.json', technical)
    write(run / 'PROCESS_AUDIT.json', dict(rows=rows, usage_by_arm=by_arm,
                                          interpretation='Counts/references are not semantic correctness or causal necessity'))
    return dict(technical=technical, usage_by_arm=by_arm,
                flows=[dict(flow_id=r['flow_id'], status=r['status'], counts=r['counts'],
                            final_use=r.get('final_use')) for r in rows])


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.prepared, args.run), ensure_ascii=False))


if __name__ == '__main__':
    main()
