"""Read-only structural audit and extraction of existing research records; no inference."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def relative(path):
    return path.relative_to(PROJECT).as_posix()


def packet_from(instructions):
    if 'PACKET=' in instructions:
        return json.loads(instructions.split('PACKET=', 1)[1])
    decoder = json.JSONDecoder()
    for position, char in enumerate(instructions):
        if char != '{':
            continue
        try:
            value, _ = decoder.raw_decode(instructions[position:])
            if isinstance(value, dict) and ('task' in value or 'own_sources' in value):
                return value
        except ValueError:
            pass
    raise ValueError('No task packet found')


def audit_run(folder):
    base = PROJECT / 'runs' / folder
    progress, scores = read_json(base / 'progress.json'), read_json(base / 'SCORES.json')
    requests, responses = read_jsonl(base / 'requests.jsonl'), read_jsonl(base / 'responses.jsonl')
    request_map = {record.get('slot', record['attempt']): record for record in requests}
    response_map = {record.get('slot', record['attempt']): record for record in responses}
    findings, records = [], []
    for row in progress['rows']:
        slot = row['slot']
        raw_path = base / f'{slot:03}.raw.txt'
        request, response = request_map.get(slot), response_map.get(slot)
        checks = {'request_present': request is not None, 'response_present': response is not None,
                  'raw_present': raw_path.exists()}
        raw_text, raw_value, payload, packet = None, None, None, None
        if raw_path.exists():
            raw_text = raw_path.read_text(encoding='utf-8')
            try:
                raw_value = json.loads(raw_text)
                checks['raw_json_parse'] = True
                keys = [key for key in ('choice', 'reasoning', 'text') if key in raw_value]
                checks['progress_core_fields_match_raw'] = all(row['answer'].get(key) == raw_value[key] for key in keys)
            except ValueError:
                checks['raw_json_parse'] = False
        if response is not None:
            output = response['response'].get('output', [])
            text = ''.join(part.get('text', '') for item in output for part in item.get('content', []) if part.get('type') == 'output_text')
            try:
                checks['provider_output_matches_raw_json'] = json.loads(text) == raw_value
            except ValueError:
                checks['provider_output_matches_raw_json'] = False
        if request is not None:
            payload = request['payload']
            try:
                packet = packet_from(payload['instructions'])
                checks['packet_parse'] = True
            except (KeyError, ValueError):
                checks['packet_parse'] = False
            canonical = base / 'actual_requests' / f'{slot:03}.json'
            if canonical.exists():
                checks['canonical_instructions_match_request'] = read_json(canonical)['instructions'] == payload['instructions']
        if not all(checks.values()):
            findings.append({'slot': slot, 'checks': checks})
        records.append({'row': row, 'request_payload': payload, 'packet': packet,
                        'provider_model_alias': response['response'].get('model') if response else None,
                        'raw_path': relative(raw_path), 'raw_text': raw_text, 'checks': checks})
    summary = {'folder': relative(base), 'progress_rows': len(progress['rows']), 'request_records': len(requests),
               'response_records': len(responses), 'task_or_case_ids': sorted({str(row.get('task', row.get('case_id'))) for row in progress['rows']}),
               'benchmark_task_ids': sorted({f"{int(row.get('task', str(row.get('case_id', '')).split('-')[0])):03}" for row in progress['rows']}),
               'core_field_failures': findings, 'provider_model_aliases': sorted({r['provider_model_alias'] for r in records if r['provider_model_alias']}),
               'scope': 'Structural and core-text correspondence only; not a causal or semantic validity audit'}
    return summary, records, scores


def main():
    run_names = ['imp-adaptation-live-20261026-r1', 'imp-confirmation-live-20261026-r1', 'local-reconstruction-live-20261026-r1']
    audited = {name: audit_run(name) for name in run_names}
    cases = []
    specifications = [
        ('C01', run_names[0], '030', 1, 'Correct candidate preserved by information routing; ordinary branch loses a correct update'),
        ('C02', run_names[0], '033', 1, 'No initial reference match; distributed information routing leads to the reference option'),
        ('C03', run_names[1], '007', 2, 'Correct choice preservation differs; ordinary result is a 2:2 tie, not a full error'),
        ('C04', run_names[1], '008', 1, 'All raw information delivered; a correct intermediate choice changes without peer recommendations'),
    ]
    for case_id, folder, task, repeat, description in specifications:
        _, records, scores = audited[folder]
        selected = [r for r in records if r['row'].get('task') == task and r['row']['repeat'] == repeat]
        cases.append({'id': case_id, 'source_type': 'project_actual_team_run', 'folder': 'runs/' + folder,
                      'task': task, 'repeat': repeat, 'description': description,
                      'expertise_status': 'Information-distribution advantage; no calibrated stable ability expert',
                      'records': selected,
                      'published_group_scores': [r for r in scores['groups'] if r['task'] == task and r['repeat'] == repeat]})
    for case_id, original_id, description in [
        ('C05', '004-age-10', 'Age contribution visible but conflicting reported role and historical draft remain'),
        ('C06', '023-road-89', 'Same task with local source reconstruction; different branches make different final choices'),
    ]:
        folder = run_names[2]
        _, records, scores = audited[folder]
        pair = next(r for r in scores['pairs'] if r['case_id'] == original_id)
        cases.append({'id': case_id, 'source_type': 'project_actual_receiver_probe', 'folder': 'runs/' + folder,
                      'task': f"{pair['task']:03}", 'original_case_id': original_id, 'description': description,
                      'expertise_status': 'Source-holder/local reconstruction; historical draft is not an independent baseline for this run',
                      'records': [r for r in records if r['row'].get('case_id') == original_id], 'published_pair_score': pair})
    old = PROJECT / 'research' / 'expertise-literature-survey-20261028'
    extracted = read_json(old / 'HIDDENBENCH_AUTHOR_019_EXTRACT.json')
    authors = {}
    for model, value in extracted['models'].items():
        original = read_json(old / value['file'])
        all_runs = [run for condition in original['conditions'] for run in condition['runs']]
        authors[model] = {
            'file': relative(old / value['file']), 'runs': len(all_runs),
            'scenarios': len({run['scenario'] for run in all_runs}),
            'rows_with_initial_rounds_final': sum(all(key in run for key in ('initial_votes', 'rounds', 'final_votes', 'majority_vote')) for run in all_runs),
            'round_count_distribution': dict(Counter(len(run.get('rounds', [])) for run in all_runs)),
            '019_count': len(value['runs']),
            'prompt_field_present_in_every_message': all('prompt' in message for run in all_runs for rd in run.get('rounds', []) for message in rd.get('messages', [])),
            'top_level_run_keys': sorted(set().union(*(run.keys() for run in all_runs))),
        }
        for item in value['runs']:
            assert original['conditions'][item['condition_index']]['runs'][item['source_run_index']] == item['run']
        for case_id, desired_model, index, description in [
            ('C07', 'gpt-4.1', 104, 'Road-block statement in discussion is followed by open-road claims; final Greenfield'),
            ('C08', 'gemini-2.5-pro', 100, 'Final reference matches but purported external confirmation has no separate tool receipt in released record'),
        ]:
            if model != desired_model:
                continue
            item = next(item for item in value['runs'] if item['source_run_index'] == index)
            cases.append({'id': case_id, 'source_type': 'author_published_actual_dialogue', 'task': '019', 'model': model,
                          'source_file': relative(old / value['file']), 'source_url': value['source'],
                          'condition_index': item['condition_index'], 'source_run_index': index,
                          'reference_answer': extracted['reference_answer'], 'description': description,
                          'expertise_status': 'Distributed information; exact original agent assignment/system inputs not fully logged',
                          'record_equals_original_author_file': True, 'run': item['run']})
    cases.sort(key=lambda row: row['id'])
    assert len(cases) == 8
    c04 = next(case for case in cases if case['id'] == 'C04')
    packets = {r['row']['slot']: r['packet'] for r in c04['records'] if r['row']['slot'] in (29, 32)}
    c04_check = {'slots': [29, 32], 'packet_keys': sorted(packets[29]),
                 'different_packet_keys': sorted(key for key in packets[29].keys() | packets[32].keys()
                                               if packets[29].get(key) != packets[32].get(key))}
    inventory = {'date': '2026-10-29', 'local_runs': [audited[name][0] for name in run_names],
                 'author_files': authors, 'case_count': 8, 'unique_task_ids': sorted({case['task'] for case in cases}),
                 'case_specific_checks': {'C04': c04_check},
                 'selection': 'Purposeful, non-blind starter cases for schema/analysis development; not a representative sample or independent annotation',
                 'new_model_calls': 0}
    (HERE / 'LOCAL_ASSET_AUDIT.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
    (HERE / 'CASE_SEED_8.json').write_text(json.dumps({'selection': inventory['selection'], 'cases': cases}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(inventory, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
