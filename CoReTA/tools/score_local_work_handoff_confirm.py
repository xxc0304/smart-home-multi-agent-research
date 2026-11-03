"""Official scores and per-task repeat matrix, separate strata and missing results."""
import argparse
from pathlib import Path

from coreta.local_work.data import read, write
from run_local_work_handoff_confirm import verify, digest
from score_local_work_mixed import score


ARMS = ('discussion', 'ordinary', 'local_work')
GROUPS = ('ordinary_regression', 'controlled_dependency')


def summarize(rows):
    indexed = {(r['case_id'], r['arm'], r['repeat']): r for r in rows}
    if len(indexed) != len(rows):
        raise ValueError('duplicate task/arm/repeat score row')
    groups = {}
    for group in GROUPS:
        selected = [r for r in rows if r['group'] == group]
        arms = {}
        for arm in ARMS:
            planned = [r for r in selected if r['arm'] == arm]
            completed = [r for r in planned if r['status'] == 'completed' and r['exact_match'] is not None]
            correct = sum(r['exact_match'] for r in completed)
            matrix = []
            for cid in sorted({r['case_id'] for r in planned}):
                task_runs = sorted([r for r in planned if r['case_id'] == cid], key=lambda r: r['repeat'])
                matrix.append(dict(case_id=cid, planned_repeats=len(task_runs),
                     correct_repeats=sum(r['exact_match'] or 0 for r in task_runs),
                     repeats=[dict(repeat=r['repeat'], status=r['status'], exact_match=r['exact_match']) for r in task_runs]))
            arms[arm] = dict(distinct_tasks=len(matrix), planned_task_runs=len(planned),
                 completed_task_runs=len(completed), correct_task_runs=correct,
                 official_em_completed=correct / len(completed) if completed else None,
                 all_planned_success=correct / len(planned) if planned else None,
                 incomplete=[dict(case_id=r['case_id'], repeat=r['repeat'], status=r['status'])
                             for r in planned if r not in completed],
                 semantic_nonanswers=sum(bool(r.get('nonanswer')) for r in completed), task_repeat_matrix=matrix)
        paired = []
        for cid, repeat in sorted({(r['case_id'], r['repeat']) for r in selected}):
            paired.append(dict(case_id=cid, repeat=repeat,
                 outcomes={arm: dict(status=indexed[(cid, arm, repeat)]['status'],
                                      exact_match=indexed[(cid, arm, repeat)]['exact_match']) for arm in ARMS}))
        groups[group] = dict(arms=arms, paired_task_runs=paired)
    return dict(groups=groups, pooling='No pooling ordinary and controlled dependency',
                inference='Two generated repeats per task are not independent new tasks; no significance/population claim')


def evaluate(prepared, run):
    prepared, run = Path(prepared), Path(run)
    state = read(run / 'progress.json')
    if state['mode'] != 'live':
        raise ValueError('Fixture outputs cannot be scored as model results')
    plan = verify(prepared)
    if digest(prepared / 'manifest.json') != digest(run / 'manifest.json'):
        raise ValueError('Run and evaluation release differ')
    if state['status'] == 'running':
        raise ValueError('Wait for batch termination before final scoring')
    records = {r['flow_id']: r for r in state['flows']}
    if len(records) != len(state['flows']):
        raise ValueError('duplicate flow records')
    rows = []
    for spec in plan['schedule']:
        case = read(prepared / 'cases' / (spec['case_id'] + '.json'))
        record = records.get(spec['flow_id'], {})
        row = dict(**spec, group=case['group'], status=record.get('status', 'not_started'),
                   exact_match=None, f1=None, scale_match=None, nonanswer=None,
                   answer=None, scale=None, final_use=record.get('final_use'))
        if row['status'] == 'completed' and record.get('final'):
            reference = read(prepared / 'offline' / (spec['case_id'] + '.reference.json'))
            delivery = record['final']['delivered']
            row.update(score(reference, delivery), answer=delivery['answer'], scale=delivery['scale'])
        rows.append(row)
    return dict(rows=rows, summary=summarize(rows), status=state['status'],
                attempts=state['attempts'], input_tokens=state['input_tokens'], output_tokens=state['output_tokens'],
                unknown_usage=state['unknown_usage'], scoring='unmodified official TAT-QA, no host answer/scale repair')


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    write(args.output, evaluate(args.prepared, args.run))


if __name__ == '__main__':
    main()
