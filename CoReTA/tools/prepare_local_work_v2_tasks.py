"""Prepare mixed developmental cases; faithful column groups, no oracle work or API."""
import argparse
import copy
import json
from pathlib import Path

from coreta.local_work.data import read, write, adapt
from coreta.local_work.comparison_v2 import make_flow


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/source/tatqa-20261027/tatqa_dataset_train.json'
SPLITS = [
    dict(case_id='dependent-01', context_index=257, uid='e29d9cdc-7f13-41b9-a17f-43701624e7a1',
         columns=[[0, 1, 2], [0, 3, 4]], final_member='A1', partition='whole stock-settled / cash-settled column groups'),
    dict(case_id='dependent-02', context_index=1038, uid='cf23cf43-ba81-4525-9cde-e61d8e5ce16b',
         columns=[[0, 1, 2], [0, 3, 4, 5, 6]], final_member='A2', partition='whole 2019 / earlier-year column groups'),
]


def prepare(output):
    output = Path(output)
    if output.exists():
        raise ValueError('fresh preparation output required')
    contexts = read(SOURCE)
    cases, audit = [], []
    for number, original_id in enumerate(('main-02', 'main-07'), 1):
        original = ROOT / 'runs/local-work-mixed-prepared-20261027-v1/tasks' / original_id
        case = read(original / 'runtime.json')
        case.update(case_id=f'ordinary-{number:02d}', group='ordinary_regression')
        reference = read(original / 'offline/reference.json')
        write(output / 'offline' / (case['case_id'] + '.reference.json'), reference)
        cases.append(case)
        audit.append(dict(case_id=case['case_id'], original_case_id=original_id, group=case['group'],
                          allocation='unchanged complete table to A1, original paragraphs to A2',
                          question_unchanged=True, sources_unchanged=True))
    for spec in SPLITS:
        context = contexts[spec['context_index']]
        question = next(q for q in context['questions'] if q['uid'] == spec['uid'])
        task, reference = adapt(context, question, spec['context_index'])
        original_table = context['table']['table']
        width = len(original_table[0])
        assert all(len(row) == width for row in original_table)
        assert set().union(*map(set, spec['columns'])) == set(range(width))
        assert set(spec['columns'][0]) & set(spec['columns'][1]) == {0}
        sources = []
        for number, columns in enumerate(spec['columns'], 1):
            projected = [[row[column] for column in columns] for row in original_table]
            sources.append(dict(id=f'T{number}', owner=f'A{number}', kind='table',
                                upstream_uid=context['table']['uid'], column_indices=columns,
                                content=json.dumps(projected, ensure_ascii=False)))
        for source in task['sources'][1:]:
            source = copy.deepcopy(source)
            source['owner'] = 'public'
            sources.append(source)
        # Reconstruct every original cell, including blank headers and labels.
        for row_index, row in enumerate(original_table):
            reconstructed = {}
            for source in sources[:2]:
                for col, value in zip(source['column_indices'], json.loads(source['content'])[row_index]):
                    assert col not in reconstructed or reconstructed[col] == value
                    reconstructed[col] = value
            assert [reconstructed[col] for col in range(width)] == row
        task['sources'] = sources
        task['origin']['allocation'] = spec['partition']
        case = dict(case_id=spec['case_id'], group='controlled_dependency',
                    final_member=spec['final_member'], task=task)
        write(output / 'offline' / (case['case_id'] + '.reference.json'), reference)
        write(output / 'offline' / (case['case_id'] + '.original_table.json'), original_table)
        cases.append(case)
        audit.append(dict(case_id=case['case_id'], group=case['group'],
                          context_index=spec['context_index'], question_uid=spec['uid'],
                          allocation=spec['partition'], paragraphs='all original paragraphs public',
                          question_unchanged=True, original_cells_preserved=True,
                          partition_uses='original category/year headers, not a gold-derived row/operand mask',
                          model_results_used_for_selection=False,
                          explicit_work_or_bindings_injected=False))
    schedule = []
    for index, case in enumerate(cases):
        write(output / 'cases' / (case['case_id'] + '.json'), case)
        all_arms = ('discussion', 'ordinary', 'local_work')
        offset = index % 3
        arms = all_arms[offset:] + all_arms[:offset]
        for arm in arms:
            flow = make_flow(case, arm)
            for actor, request in flow.pending_requests().items():
                write(output / 'initial_requests' / case['case_id'] / arm / (actor + '.json'), request)
            schedule.append(dict(flow_id=f'{case["case_id"]}-{arm}', case_id=case['case_id'], arm=arm))
    write(output / 'TASK_AUDIT.json', dict(kind='offline_development_preparation_not_model_results',
          dataset='TAT-QA train', source=str(SOURCE), model_calls=0, cases=audit,
          groups_pooled=False, total_cases=4, total_flows=12,
          fit_limit='Source allocation establishes dependency opportunities, not ordinary-baseline failure or treatment benefit'))
    write(output / 'DRAFT_PLAN.json', dict(schedule=schedule, calls=84, repeats=1,
          arms=['discussion', 'ordinary', 'local_work'], per_input_cap=16384,
          input_cap=1376256, output_cap=165888, retries=0,
          status='data_prepared_not_authorized; batch-specific runner/preflight required',
          grouping='ordinary_regression and controlled_dependency reported separately'))
    return dict(status='data_prepared', cases=4, planned_calls=84, model_calls=0)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().output)))


if __name__ == '__main__':
    main()
