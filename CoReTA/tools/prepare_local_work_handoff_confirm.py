"""New project instances selected from a saved pre-model queue; no model calls."""
import argparse
import copy
import json
from pathlib import Path

from coreta.local_work.data import read, write, adapt
from run_local_work_calibration import ROOT, digest


SOURCE = ROOT / 'data/source/tatqa-20261027/tatqa_dataset_train.json'
QUEUE = ROOT / 'research/local-work-handoff-confirm-20261027/SELECTION_QUEUE.json'
DECISIONS = [
    dict(rank=1, context_index=1081, status='skip',
         reason='Three requested Americas values; a whole-year split leaves one member only one scalar. Does not provide substantive local multi-value work for both sides in this diagnostic.'),
    dict(rank=2, context_index=79, status='skip',
         reason='Requested rent line has two nonzero years and three dashes. Natural contiguous year split leaves one side only zeros, a degenerate contribution opportunity; not removed for model performance.'),
    dict(rank=3, context_index=106, status='accept',
         reason='Complete2019/2018 event row groups each contain four dividends; final overall mean requires both year totals/counts.'),
    dict(rank=4, context_index=1960, status='skip',
         reason='Reference derivation drops negative signs from all three total accumulated-loss balances; question does not specify magnitudes. Reference ambiguity/conflict retained, no relabeling.'),
    dict(rank=5, context_index=325, status='accept',
         reason='Complete recent-two/earlier-three-year column groups each support meaningful subtotal/count work; final mean needs both. Original units/adjustment footnote preserved publicly.')
]


def prepare(output):
    output = Path(output)
    if output.exists():
        raise ValueError('fresh output required')
    queue, contexts = read(QUEUE), read(SOURCE)
    cases, task_audit = [], []
    selections = [('ordinary-' + f'{n:02d}', 'ordinary_regression', row)
                  for n, row in enumerate(queue['ordinary'], 1)]
    decisions = {row['rank']: row for row in DECISIONS}
    for n, decision in enumerate([row for row in DECISIONS if row['status'] == 'accept'], 1):
        row = queue['dependency_queue'][decision['rank'] - 1]
        assert row['context_index'] == decision['context_index']
        selections.append((f'dependent-{n:02d}', 'controlled_dependency', row))
    seen = set()
    for cid, group, selection in selections:
        index = selection['context_index']
        assert index not in queue['excluded_contexts'] and index not in seen
        seen.add(index)
        context = contexts[index]
        question = next(q for q in context['questions'] if q['uid'] == selection['question_uid'])
        task, reference = adapt(context, question, index)
        partition = 'A1 complete native table, A2 all original paragraphs'
        reconstruction = True
        if group == 'controlled_dependency':
            table = context['table']['table']
            sources = []
            if index == 106:
                # Header rows repeated; complete event rows split by original declaration year.
                groups = [list(range(2, 6)), list(range(6, 10))]
                assert len(table) == 10
                for number, rows in enumerate(groups, 1):
                    projected = copy.deepcopy(table[:2] + [table[r] for r in rows])
                    sources.append(dict(id=f'T{number}', owner=f'A{number}', kind='table',
                                        upstream_uid=context['table']['uid'], original_row_indices=[0, 1] + rows,
                                        content=json.dumps(projected, ensure_ascii=False)))
                assert sorted(groups[0] + groups[1]) == list(range(2, len(table)))
                partition = 'Complete2019 dividend event rows / complete2018 dividend event rows; full original headers repeated'
            elif index == 325:
                groups = [[0, 1, 2], [0, 3, 4, 5]]
                for number, columns in enumerate(groups, 1):
                    sources.append(dict(id=f'T{number}', owner=f'A{number}', kind='table',
                                        upstream_uid=context['table']['uid'], column_indices=columns,
                                        content=json.dumps([[row[c] for c in columns] for row in table], ensure_ascii=False)))
                sources.append(dict(id='T0', owner='public', kind='table_header',
                                    upstream_uid=context['table']['uid'], content=json.dumps(table[:4], ensure_ascii=False)))
                for row_index, original in enumerate(table):
                    reconstructed = {}
                    for source in sources[:2]:
                        projected = json.loads(source['content'])[row_index]
                        for col, value in zip(source['column_indices'], projected):
                            assert col not in reconstructed or reconstructed[col] == value
                            reconstructed[col] = value
                    assert [reconstructed[c] for c in range(len(original))] == original
                partition = 'Complete2019/2018 columns versus2017/2016/2015 columns; full original header context public'
            else:
                raise ValueError('unexpected selected dependency')
            for source in task['sources'][1:]:
                source = copy.deepcopy(source)
                source['owner'] = 'public'
                sources.append(source)
            task['sources'] = sources
            task['origin']['allocation'] = partition
        final_member = 'A1' if cid.endswith('01') else 'A2'
        case = dict(case_id=cid, group=group, final_member=final_member, task=task)
        cases.append(case)
        write(output / 'cases' / (cid + '.json'), case)
        write(output / 'offline' / (cid + '.reference.json'), reference)
        write(output / 'offline' / (cid + '.original_context.json'), context)
        task_audit.append(dict(case_id=cid, context_index=index, question_uid=question['uid'],
                               question=question['question'], group=group, final_member=final_member,
                               partition=partition, original_cells_preserved=reconstruction,
                               reference_review='Offline source arithmetic checked before any model run'))
    schedule = []
    arms = ('discussion', 'ordinary', 'local_work')
    for repeat in (1, 2):
        for number, case in enumerate(cases):
            shift = (number + repeat - 1) % len(arms)
            for arm in arms[shift:] + arms[:shift]:
                schedule.append(dict(flow_id=f'{case["case_id"]}-{arm}-r{repeat}',
                                     case_id=case['case_id'], arm=arm, repeat=repeat))
    write(output / 'DRAFT_PLAN.json', dict(schedule=schedule, cases=4, repeats=2, calls=168,
          purpose='new project instances and repeated natural handoff confirmation; no population efficacy claim',
          limits=dict(requests=168, input=2752512, output=331776, per_input=16384, retries=0)))
    write(output / 'SELECTION_AUDIT.json', dict(kind='pre_model_data_preparation', model_calls=0,
          source_sha256=digest(SOURCE), queue_sha256=digest(QUEUE), excluded_contexts=queue['excluded_contexts'],
          ordinary_selection='first2distinct contexts in saved seeded arithmetic queue',
          dependency_decisions=DECISIONS, tasks=task_audit, groups_pooled=False,
          novelty_scope='No prior project task/inspection record; public train data may occur in model training'))
    return dict(status='data_prepared_not_authorized', cases=4, independent_task_runs=8,
                comparison_flows=24, max_requests=168, model_calls=0)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().output)))


if __name__ == '__main__':
    main()
