"""Offline audit of the completed, authorized 2026-10-27 calibration. No API calls."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from coreta.local_work.comparison import ComparisonFlow


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'runs/local-work-calibration-live-20261027-v1'
PREPARED = ROOT / 'runs/local-work-calibration-prepared-20261027-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(name, value):
    (RUN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    progress = read(RUN / 'progress.json')
    responses = [json.loads(line) for line in (RUN / 'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    manifest = read(PREPARED / 'manifest.json')
    source_changes = [name for name, expected in manifest['source_sha256'].items()
                      if sha(ROOT / name) != expected]
    preparation_changes = [name for name, expected in manifest['files'].items()
                           if sha(PREPARED / name) != expected]
    input_tokens = sum(row['response']['usage']['input_tokens'] for row in responses)
    output_tokens = sum(row['response']['usage']['output_tokens'] for row in responses)
    flow_rows = []
    offset = 0
    by_arm = {}
    all_reasons = Counter()
    for flow in progress['flows']:
        folder = RUN / 'flows' / flow['flow_id']
        events = read(folder / 'EVENTS.json')
        counts, reasons = Counter(), Counter()
        for event in events:
            engine = event.get('engine_event', {})
            counts['accepted_work_submissions_including_revisions'] += len(engine.get('accepted_work', []))
            for binding in engine.get('bindings', []):
                if binding.get('status') == 'accepted':
                    counts['accepted_nonnull_bindings' if binding.get('result_id') is not None
                           else 'accepted_null_unbindings'] += 1
            notices = event.get('notices', []) + engine.get('notices', [])
            counts['turns_with_optional_notices'] += bool(notices)
            for notice in notices:
                counts[notice['kind']] += 1
                if notice.get('reason'):
                    reasons[notice['reason']] += 1
        case = read(PREPARED / 'cases' / (flow['case_id'] + '.json'))
        replay = ComparisonFlow(case, flow['arm'], provenance='offline replay of this completed live batch')
        used = 0
        while replay.status == 'pending':
            pending = replay.pending_requests()
            wave_events = events[used:used + len(pending)]
            replay.submit({event['actor']: event['raw'] for event in wave_events})
            used += len(wave_events)
        assert used == len(events), 'Replay must consume every original reply'
        assert replay.answer == flow['final'], 'Offline replay changed delivered answer'
        assert replay.status == flow['status'], 'Offline replay changed flow status'
        subset = responses[offset:offset + len(events)]
        offset += len(events)
        usage = dict(input_tokens=sum(row['response']['usage']['input_tokens'] for row in subset),
                     output_tokens=sum(row['response']['usage']['output_tokens'] for row in subset),
                     latency_seconds=sum(row['latency_seconds'] for row in subset))
        totals = by_arm.setdefault(flow['arm'], dict(input_tokens=0, output_tokens=0, requests=0))
        for key in ('input_tokens', 'output_tokens'):
            totals[key] += usage[key]
        totals['requests'] += len(subset)
        final_packet = read(sorted((folder / 'requests').glob('*.json'))[-1])['packet']
        flow_rows.append(dict(flow_id=flow['flow_id'], counts=dict(counts), reasons=dict(reasons),
                              usage=usage, replay_matches=True,
                              final_result_id=flow['final']['delivered'].get('result_id'),
                              final_work_results={k: v for k, v in final_packet['results'].items()
                                                  if k.startswith('W')}))
        all_reasons.update(reasons)
    assert offset == len(responses) == 42
    assert input_tokens == progress['input_tokens'] and output_tokens == progress['output_tokens']
    assert not source_changes and not preparation_changes
    # The shared client records the cumulative attempt number, not per-slot retries.
    assert all(row['attempt'] == row['slot'] and row['response']['status'] == 'completed'
               and not row['uncertain_usage'] for row in responses)
    assert [row['slot'] for row in responses] == list(range(1, 43))
    counts = dict(request_records=len((RUN / 'requests.jsonl').read_text(encoding='utf-8').splitlines()),
                  response_records=len(responses), raw_text_files=len(list(RUN.glob('*.raw.txt'))),
                  http_body_files=len(list((RUN / 'http_bodies').glob('*.bytes'))),
                  actual_request_files=len(list((RUN / 'actual_requests').glob('*.json'))))
    assert set(counts.values()) == {42}
    technical = dict(status='completed', file_counts=counts, retries=0, unknown_usage=False,
                     input_tokens=input_tokens, output_tokens=output_tokens,
                     all_within_authorized_batch_limits=(input_tokens <= 688128 and output_tokens <= 82944),
                     source_changes=source_changes, preparation_changes=preparation_changes,
                     all_six_full_response_replays_match=True,
                     core_unreadable=sum(event['status'] == 'unreadable_core'
                                         for folder in (RUN / 'flows').iterdir()
                                         for event in read(folder / 'EVENTS.json')),
                     interpretation='Core completion does not imply successful optional tools or semantic correctness')
    write('TECHNICAL_AUDIT.json', technical)
    write('PROCESS_AUDIT.json', dict(flows=flow_rows, by_arm=by_arm, rejection_reasons=dict(all_reasons),
                                    attribution='Observed trace, not a causal ablation'))
    print(json.dumps(dict(technical=technical, by_arm=by_arm,
                          flows=[{k: v for k, v in row.items() if k not in ('final_work_results', 'reasons')}
                                 for row in flow_rows], rejection_reasons=dict(all_reasons)),
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
