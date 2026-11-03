"""Offline build checks only. Does not import or call a model/network client."""
import argparse
import json
import os
import unittest
from pathlib import Path
from coreta.local_work.data import prepare, read, member_packet, swapped
from coreta.local_work.engine import WorkSession
from coreta.local_work.prompts import request, final_request
from local_work_offline_trace import trace
from replay_local_work_history import replay


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--stage', choices=('spine', 'data', 'engine', 'all'), default='all')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.stage == 'spine':
        write(args.output / 'SPINE_SMOKE.json', dict(
            artifact_type='engineering_smoke_not_model_result', stage='spine',
            network_calls=0, model_outputs=0, work=[]))
        print('F0 offline entrypoint -> SPINE_SMOKE.json; no model results')
        return
    tasks = prepare(Path('data/source/tatqa-20261027/tatqa_dataset_train.json'), args.output / 'tasks')
    assert len(tasks) == 6
    assert all(len(t['members']) == 2 for t in tasks)
    write(args.output / 'ADAPTER_SMOKE.json', dict(artifact_type='engineering_not_model_result', tasks=len(tasks)))
    if args.stage == 'data':
        print('F1 six official training questions adapted; full table/text, references isolated')
        return
    result = trace(tasks[4])
    write(args.output / 'SCRIPTED_TRACE.json', result)
    for index, req in enumerate(result['requests'], 1):
        write(args.output / 'scripted_requests' / f'{index:02d}.json', req)
    if args.stage == 'engine':
        print('F2 scripted real-source continuation 1344.1 - 1137.4 -> 206.7; NOT model success')
        return
    request_sizes = []
    for index, task in enumerate(tasks, 1):
        session = WorkSession(task)
        for actor in task['members']:
            req = request(session, actor, 0)
            write(args.output / 'initial_requests' / f'{index:02d}-{actor}.json', req)
            request_sizes.append(len(req['instructions']))
        # Test resource-preserving swap, not an additional task or generation.
        flipped = swapped(task)
        assert sorted(s['content'] for s in member_packet(task, 'A1')['sources']) == sorted(
            s['content'] for s in member_packet(flipped, 'A2')['sources'])
        assert not any(k in task for k in ('answer', 'derivation', 'scale', 'rel_paragraphs'))
    history = replay('runs/local-rule-confirmation-live-20261025-r1')
    write(args.output / 'HISTORY_REPLAY.json', history)
    assert history['all_refs_visible']
    assert history['all_new_schema_incompatible_as_expected']
    os.environ['CORETA_LOCAL_WORK_TASK'] = str((args.output / 'tasks/task-05/runtime.json').resolve())
    suite = unittest.defaultTestLoader.discover('tests', pattern='test_local_work.py')
    checked = unittest.TextTestRunner(verbosity=1).run(suite)
    audit = dict(artifact_type='offline_engineering_check_not_model_experiment',
                 model_calls=0, stage='all', tests_run=checked.testsRun,
                 tests_passed=checked.wasSuccessful(), official_development_tasks=len(tasks),
                 initial_request_max_characters=max(request_sizes),
                 scripted_fixture_final_value=result['final']['delivered']['answer'],
                 historical_old_contract_replays=history['count'],
                 natural_new_schema_outputs=0,
                 live_readiness='BLOCKED: no new-schema generation coverage, baseline runner or frozen authorized batch',
                 no_method_effectiveness_claim=True)
    write(args.output / 'OFFLINE_AUDIT.json', audit)
    if not checked.wasSuccessful():
        raise SystemExit(1)
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == '__main__':
    main()
