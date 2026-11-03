"""Prepare mixed tasks and offline flows. No network/model execution."""
import argparse
import copy
import json
import platform
import unittest
import importlib.metadata
from pathlib import Path
from coreta.local_work.data import write, read
from coreta.local_work.mixed_data import select, prepare
from coreta.local_work.comparison import ComparisonFlow, ARMS
from local_work_comparison_smoke import smoke_case
from coreta.local_work.evaluation import summarize
from replay_local_work_history import replay


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stage', choices=('spine', 'data', 'flow', 'all'), default='all')
    args = parser.parse_args()
    source = Path('data/source/tatqa-20261027/tatqa_dataset_train.json')
    if args.stage == 'spine':
        plan = select(source)
        write(args.output / 'SELECTION_SMOKE.json', plan)
        print('F0 selection: 12 unfiltered arithmetic main questions + 2 separately labelled diagnostics')
        return
    cases, plan = prepare(source, args.output / 'tasks')
    if args.stage == 'data':
        print('F1 runtime source packets exported, offline labels isolated')
        return
    request_rows = []
    for case in cases:
        for arm in ARMS:
            flow = ComparisonFlow(case, arm)
            current = flow.pending_requests()
            for actor, req in current.items():
                write(args.output / 'initial_requests' / case['case_id'] / arm / f'{actor}.json', req)
            request_rows.append(dict(case_id=case['case_id'], group=case['group'], arm=arm,
                                     initial_requests=len(current), planned_requests=len(flow.schedule()),
                                     output_cap=sum(cap for _, cap in flow.schedule())))
    write(args.output / 'REQUEST_PLAN.json', dict(rows=request_rows, network_calls=0,
          status='offline plan; not a paid batch or authorization'))
    old_task = read('runs/local-work-offline-20261027-v1/tasks/task-05/runtime.json')
    for arm in ARMS:
        write(args.output / 'engineering' / f'{arm}.json', smoke_case(old_task, arm))
    if args.stage == 'flow':
        print('F2 three common-tool flows replayed; 7 response slots and 13824 output cap per arm; no API')
        return
    history = replay('runs/local-rule-confirmation-live-20261025-r1')
    write(args.output / 'HISTORICAL_COMMON_REPLAY.json', history)
    assert history['all_refs_visible'] and history['all_new_schema_incompatible_as_expected']
    # A full historical carrier stresses packet assembly only. It is never part of
    # the prepared real-task request set, and never called new-schema model output.
    historical_text = Path(history['rows'][0]['raw_file']).read_text(encoding='utf-8')
    stress_lengths = []
    for case in cases:
        for arm in ARMS:
            flow = ComparisonFlow(case, arm)
            while flow.status == 'pending':
                reqs = flow.pending_requests()
                stress_lengths.extend(len(r['instructions']) for r in reqs.values())
                replies = {actor: json.dumps(dict(answer=0, result_id=None, scale='', reasoning='engineering carrier only'))
                           if req['final'] else json.dumps(dict(message=historical_text))
                           for actor, req in reqs.items()}
                flow.submit(replies)
            assert flow.status == 'completed'
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.discover('tests', pattern='test_local_work.py'))
    suite.addTests(unittest.defaultTestLoader.discover('tests', pattern='test_local_work_mixed.py'))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    write(args.output / 'NO_RESULTS.json', summarize(plan['rows'], []))
    audit = dict(kind='offline_preparation_not_model_results', python=platform.python_version(),
                 dependencies={m: importlib.metadata.version(m) for m in ('numpy', 'pandas', 'scipy', 'jsonschema')},
                 main_tasks=12, diagnostic_tasks=2, groups_pooled=False, model_calls=0,
                 flow_modes=list(ARMS), prepared_flows=len(request_rows),
                 maximum_planned_responses_per_flow=7, maximum_output_tokens_per_flow=13824,
                 planned_response_slots_all_flows=sum(r['planned_requests'] for r in request_rows),
                 planned_output_cap_all_flows=sum(r['output_cap'] for r in request_rows),
                 planned_counts_are_not_executed_or_authorized=True,
                 old_contract_replays=history['count'], new_schema_natural_generations=0,
                 stress_max_instruction_characters=max(stress_lengths),
                 stress_scope='all prepared cases/arms with full historical text carrier; not true new-format model generation or a token upper bound',
                 tests_run=result.testsRun, tests_passed=result.wasSuccessful(),
                 scorer='unmodified upstream TAT-QA; engineering zero/wrong-scale checks only',
                 live_status='DO_NOT_RUN: separate protocol qualification, transport/usage guards, frozen limits and authorization required')
    write(args.output / 'PREPARATION_AUDIT.json', audit)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == '__main__':
    main()
