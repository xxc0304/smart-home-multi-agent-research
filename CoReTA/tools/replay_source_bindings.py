"""Offline provenance replay of saved v1 responses, with an explicit schema migration.

No model call, runtime repair, scoring, or inferred atomicity of legacy facts.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from coreta.state import write_json
from coreta.task_audit_binding import FactBindingSession, SourceBindingContracts, source_registry


ROOT = Path(__file__).resolve().parents[1]


def migrate_legacy_for_binding(task, legacy):
    """Discard model offsets explicitly. Do not normalize unknown pointer prefixes."""
    facts, excluded, migrated = [], [], []
    registry = source_registry(task)
    for fact in legacy['facts']:
        old = fact['source_locator']
        source_id = 'prompt' if old['kind'] == 'prompt_span' else {
            '/prompt': 'prompt', '/entry_point': 'entry_point'}.get(old['pointer'])
        if source_id not in registry:
            excluded.append({'original_fact': copy.deepcopy(fact),
                             'reason': 'No exact supported public source mapping; task metadata and null entry points are not extracted.'})
            continue
        item_id = fact['fact_id'] + ':legacy'
        facts.append({'fact_id': fact['fact_id'], 'source_id': source_id,
                      'quoted_text': fact['quoted_text'], 'normalized_fact': fact['normalized_fact'],
                      'kind': fact['kind'], 'check_items': [{'item_id': item_id, 'description': fact['normalized_fact']}]})
        migrated.append({'fact_id': fact['fact_id'], 'original_source_locator': copy.deepcopy(old),
                         'new_source_id': source_id, 'added_item_id': item_id,
                         'atomicity': 'not_established; legacy grouping retained for binding-only replay'})
    return {'facts': facts, 'coverage_status': 'partial'}, {'migrated': migrated, 'excluded': excluded}


def replay():
    folder = ROOT / 'runs/math140-task-audit-20261020/4276ec64c178dafa'
    task = json.loads((folder / 'public_task.json').read_text(encoding='utf-8'))
    raw_rows = [json.loads(x) for x in (folder / 'audit_responses.jsonl').read_text(encoding='utf-8').splitlines()]
    contracts = SourceBindingContracts(ROOT / 'design/v0.3/coreta.schema.json')
    rows, sessions, payloads = [], [], []
    for row in raw_rows:
        legacy = json.loads(row['raw'])
        payload, migration = migrate_legacy_for_binding(task, legacy)
        contracts.validate('TaskFacts', payload)
        session = FactBindingSession(task, payload)
        rows.append({'original_attempt': row['attempt'], 'migration': migration,
                     'raw_quotes_changed': False, 'source_fact_count': len(payload['facts']),
                     'bound_fact_count': len(payload['facts']) - len(session.pending),
                     'pending_fact_ids': session.pending, 'state': session.snapshot()})
        payloads.append(payload)
        sessions.append(session)
    first = sessions[0]
    locked = {key: copy.deepcopy(value) for key, value in first.current.items() if key not in first.pending}
    second = {fact['fact_id']: fact for fact in payloads[1]['facts']}
    patch = {'replacements': [{'fact_id': key, 'source_id': second[key]['source_id'],
                               'quoted_text': second[key]['quoted_text']} for key in first.pending]}
    contracts.validate('TaskFactsPatch', patch)
    first.apply_patch(patch)
    bound = first.bound_payload()
    contracts.validate('BoundTaskFacts', bound)
    plan = json.loads((ROOT / 'engineering/MATH140_TASK_AUDIT_PLAN_20261020.json').read_text(encoding='utf-8'))
    unchanged = all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
                    for path, expected in plan['source_hashes'].items())
    return {'scope': 'Offline source binding only. Explicit old-to-new schema migration, not a new model trajectory.',
            'external_model_requests': 0, 'original_frozen_files_unchanged': unchanged,
            'legacy_atomicity_or_semantics_validated': False, 'attempts': rows,
            'incremental_repair': {'patch_from_second_saved_response': patch,
                                   'locked_facts_unchanged': all(first.current[key] == fact for key, fact in locked.items()),
                                   'final_bound_fact_count': len(bound['facts']), 'pending_fact_ids': first.pending,
                                   'bound_payload': bound}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Replay exact source binding locally; sends no model requests')
    parser.add_argument('--output', type=Path, default=ROOT / 'engineering/SOURCE_BINDING_REPLAY_20261020.json')
    args = parser.parse_args()
    result = replay()
    write_json(args.output, result)
    print(json.dumps({'attempts': [{'original_attempt': row['original_attempt'], 'bound': row['bound_fact_count'],
                                    'pending': row['pending_fact_ids']} for row in result['attempts']],
                      'repair_bound_count': result['incremental_repair']['final_bound_fact_count'],
                      'locked_facts_unchanged': result['incremental_repair']['locked_facts_unchanged'],
                      'original_frozen_files_unchanged': result['original_frozen_files_unchanged']}))
