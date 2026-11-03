"""Extract existing paired trajectories. Offline only; no method edits or API calls."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
RUN = ROOT / 'runs/local-work-handoff-confirm-live-20261027-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def reference(path):
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def packet(folder, stage):
    path = next((folder / 'requests').glob(stage + '-*.json'))
    return read(path), reference(path)


comparisons = []
for case in ('ordinary-01', 'ordinary-02', 'dependent-01', 'dependent-02'):
    for rep in (1, 2):
        ordinary = RUN / 'flows' / f'{case}-ordinary-r{rep}'
        local = RUN / 'flows' / f'{case}-local_work-r{rep}'
        left, lp = packet(ordinary, '00')
        right, rp = packet(local, '00')
        assert left['packet'] == right['packet'] and left['schema'] == right['schema']
        lf, lfp = packet(ordinary, '03')
        rf, rfp = packet(local, '03')
        final_equal = lf['instructions'].split('\nPACKET=', 1)[0] == rf['instructions'].split('\nPACKET=', 1)[0]
        assert final_equal
        comparisons.append({'case_id': case, 'repeat': rep,
                            'A1_initial_packet_and_schema_equal': True,
                            'final_instruction_prefix_equal': True,
                            'evidence': [lp, rp, lfp, rfp]})

traces = []
for arm in ('discussion', 'ordinary', 'local_work'):
    folder = RUN / 'flows' / f'dependent-02-{arm}-r1'
    events = read(folder / 'EVENTS.json')
    selected = []
    for event in events:
        if event['wave'] not in (0, 1, 2):
            continue
        obj = json.loads(event['raw'])
        selected.append({'wave': event['wave'], 'actor': event['actor'],
                         'message': obj['message'], 'source_ids': obj.get('source_ids', []),
                         'receipts': obj.get('receipts', []),
                         'calculations': obj.get('calculations', []),
                         'accepted_work': event.get('engine_event', {}).get('accepted_work', []),
                         'rejections': event.get('engine_event', {}).get('notices', [])})
    snapshots = []
    for wave in ('01', '02', '03'):
        request, proof = packet(folder, wave)
        p = request['packet']
        snapshots.append({'stage': wave, 'actor': request['actor'],
                          'visible_sources': [s['id'] for s in p['sources']],
                          'work': p.get('receipts', []), 'results': p['results'],
                          'calculator_results': p.get('calculator_results', []),
                          'evidence': proof})
    traces.append({'arm': arm, 'events': selected, 'snapshots': snapshots,
                   'event_evidence': reference(folder / 'EVENTS.json'),
                   'final': read(folder / 'SUMMARY.json')['final'],
                   'final_evidence': reference(folder / 'SUMMARY.json')})

candidate = next(t for t in traces if t['arm'] == 'local_work')
initial = candidate['snapshots'][0]
last = candidate['snapshots'][-1]
assert initial['results']['W2']['status'] == 'waiting'
assert initial['results']['W2']['metadata'] == last['results']['W2']['metadata']
assert initial['results']['C2']['value'] == 608136.6666666666
assert {'T1', 'T2'} <= set(initial['visible_sources'])
assert last['results']['W3']['value'] == 690221.04
assert candidate['final']['delivered']['answer'] == 659439.4
assert last['results']['W3']['status'] == 'ready'

audit = read(RUN / 'AUDIT_SUMMARY.json')
scores = read(RUN / 'OFFLINE_SCORES.json')
result = {'review_type': 'executor retrospective nonblind paired case review',
          'new_api_calls': 0, 'architecture_edits': False, 'official_rescoring_changes': False,
          'pair_checks': comparisons, 'equity_first_repeat_paired_traces': traces,
          'official_rows': scores['rows'], 'usage_by_arm': audit['usage_by_arm'],
          'correction': 'W2 always declared the full five-year average. Its output metadata did not change during completion. The consumer misinterpreted it from the outset; this is not an unhandled metadata-change bug.',
          'causal_limit': 'Paired cases share task/permissions/budgets, not identical generated messages. No within-trajectory intervention identifies the causal effect of stage guidance or receipt visibility.',
          'additional_sources': [reference(ROOT / 'src/coreta/local_work/handoff_flow.py'),
                                 reference(ROOT / 'src/coreta/local_work/engine.py'),
                                 reference(ROOT / 'research/local-work-handoff-confirm-20261027/REFERENCE_REVIEW.md'),
                                 reference(ROOT / 'research/local-work-handoff-pilot-20261027/RESULTS.md')]}
(OUT / 'EVIDENCE.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'existing_pair_checks': len(comparisons), 'paired_equity_traces': len(traces),
                  'W2_output_metadata_changed': False, 'new_api_calls': 0, 'assertions': 'passed'}))
