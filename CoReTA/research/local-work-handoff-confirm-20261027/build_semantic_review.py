"""Post-run evidence extraction with explicitly manual semantic annotations. No API."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'runs/local-work-handoff-confirm-live-20261027-v1'
OUT = Path(__file__).parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def evidence(path):
    return path.relative_to(ROOT).as_posix()


rows = []
for case in ('dependent-01', 'dependent-02'):
    for arm in ('discussion', 'ordinary', 'local_work'):
        for rep in (1, 2):
            folder = RUN / 'flows' / f'{case}-{arm}-r{rep}'
            events = read(folder / 'EVENTS.json')
            first_packet = read(folder / 'requests/01-A1.json')['packet']
            final_path = next((folder / 'requests').glob('03-*.json'))
            final_packet = read(final_path)['packet']
            summary = read(folder / 'SUMMARY.json')
            initial = []
            for event in events:
                if event['wave'] != 0:
                    continue
                obj = json.loads(event['raw'])
                accepted = event.get('engine_event', {}).get('accepted_work', [])
                snapshots = {key: first_packet['results'][key] for key in accepted}
                # Manual review: dividend partials are correct in all arms/repeats.
                # Equity ordinary A1 supplies facts but no completed numeric subresult.
                numeric_partial = not (case == 'dependent-02' and arm == 'ordinary'
                                       and event['actor'] == 'A1')
                initial.append({
                    'actor': event['actor'], 'wave': 0,
                    'message': obj['message'], 'calculations': obj.get('calculations', []),
                    'submitted_receipts': obj.get('receipts', []),
                    'accepted_work_snapshots_after_first_wave': snapshots,
                    'manual_correct_numeric_partial_in_message_calculator_or_work': numeric_partial,
                    'ready_work_receipt_exists': any(v['status'] == 'ready' for v in snapshots.values()),
                    'evidence': evidence(folder / 'EVENTS.json'),
                    'snapshot_evidence': evidence(folder / 'requests/01-A1.json'),
                })
            owners = summary['final_use'].get('owners', [])
            rows.append({
                'flow_id': folder.name, 'case_id': case, 'arm': arm, 'repeat': rep,
                'initial_member_opportunities': initial,
                'final': summary['final'], 'final_use': summary['final_use'],
                'final_work_values': {key: value for key, value in final_packet['results'].items()
                                      if key.startswith('W')},
                'final_evidence': evidence(folder / 'SUMMARY.json'),
                'final_snapshot_evidence': evidence(final_path),
                'structural_cross_member_final_graph': len(owners) > 1,
                'manual_official_target_correct_combination_and_final_adoption': case == 'dependent-02',
                'manual_official_target_classification': (
                    'not_matched; annual-total mean versus official per-payment mean; grain ambiguity'
                    if case == 'dependent-01' else 'confirmed numeric five-year mean; explanation errors separately noted'),
                'first_correct_numeric_integration_wave': 1 if case == 'dependent-02' else None,
                'technical_missing': False,
            })

sign_rows = []
for rep in (1, 2):
    folder = RUN / 'flows' / f'ordinary-01-local_work-r{rep}'
    final = read(folder / 'SUMMARY.json')['final']
    assert final['model_answer']['answer'] == final['delivered']['answer'] == -1.92
    sign_rows.append({'repeat': rep, 'final': final, 'evidence': evidence(folder / 'SUMMARY.json'),
                      'manual_interpretation': 'Model explicitly chose vested minus granted; no host overwrite. Official answer +1.92. Direction ambiguity was recorded before running.'})

by_arm = {}
for arm in ('discussion', 'ordinary', 'local_work'):
    subset = [r for r in rows if r['arm'] == arm]
    initial = [i for r in subset for i in r['initial_member_opportunities']]
    by_arm[arm] = {
        'planned_dependency_flows': 4, 'evaluable_dependency_flows': 4,
        'technical_missing': 0,
        'first_wave_member_opportunities': 8,
        'manual_correct_numeric_partial_any_available_channel': sum(i['manual_correct_numeric_partial_in_message_calculator_or_work'] for i in initial),
        'ready_work_receipt_members': None if arm == 'discussion' else sum(i['ready_work_receipt_exists'] for i in initial),
        'structural_cross_member_final_graphs': sum(r['structural_cross_member_final_graph'] for r in subset),
        'confirmed_official_target_correct_combination_and_adoption': 2,
        'official_target_not_matched_with_grain_ambiguity': 2,
    }

critical = next(r for r in rows if r['flow_id'] == 'dependent-02-local_work-r1')
assert critical['final_work_values']['W3']['value'] == 690221.04
assert critical['final']['delivered']['answer'] == 659439.4

result = {
    'review_type': 'executor post-run nonblind manual semantic review with source extraction; no model judge',
    'method_changed': False, 'new_api_requests': 0,
    'scoring_policy': 'Original upstream EM/scale unchanged; no exclusion or ambiguity rescore',
    'metric_distinction': 'A valid numeric partial in text/C is distinct from a ready W receipt. Discussion has no W interface. Structural graph is not semantic success.',
    'summary': by_arm, 'dependency_flows': rows, 'ordinary_sign_cases': sign_rows,
    'critical_misapplication': {
        'flow_id': critical['flow_id'],
        'sequence': [
            'wave0 A2 message/C supports three-year partial 608136.6667, but W2 actually declares full five-year work and is waiting',
            'wave1 A1 creates W3 treating W2 as a three-year average; W3 waits because W2 waits',
            'wave1 A2 tries to bind W1 two-year average into individual annual inputs; period mismatch rejects this revision',
            'wave2 A2 revises W2 from original five-year values to ready 659439.4; W3 recomputes to 690221.04 under its mistaken three-year interpretation',
            'final A2 selects correct W2=659439.4; wrong W3 remains ready and is not finally adopted',
        ],
        'interpretation': 'Mechanical dependency and arithmetic work; model confuses claimed partial work with actual receipt semantics. No evidence that check-back repaired W3.',
        'evidence': critical['final_snapshot_evidence'],
    },
    'reference_preflight_gap': 'Dividend reference arithmetic was checked but annual versus payment grain ambiguity was not sufficiently surfaced before launch. Ordinary sign direction boundary was already recorded.',
}
(OUT / 'SEMANTIC_REVIEW.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(by_arm, ensure_ascii=False))
