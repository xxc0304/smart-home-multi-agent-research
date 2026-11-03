"""Offline official scores for all planned v2 flows; never consumed by live runner."""
import argparse
import hashlib
from pathlib import Path

from coreta.local_work.data import read, write
from score_local_work_mixed import score


ARMS = ('discussion', 'ordinary', 'local_work')
GROUPS = ('ordinary_regression', 'controlled_dependency')


def aggregate(rows):
    groups = {}
    for group in GROUPS:
        subset = [r for r in rows if r['group'] == group]
        arms = {}
        for arm in ARMS:
            planned = [r for r in subset if r['arm'] == arm]
            valid = [r for r in planned if r['status'] == 'completed' and r.get('exact_match') is not None]
            correct = sum(r['exact_match'] for r in valid)
            arms[arm] = dict(planned=len(planned), completed=len(valid), correct=correct,
                             official_em_completed=correct / len(valid) if valid else None,
                             all_planned_success=correct / len(planned) if planned else None,
                             incomplete=[r['case_id'] for r in planned if r not in valid],
                             nonanswers=sum(bool(r.get('nonanswer')) for r in valid))
        groups[group] = dict(arms=arms)
    return dict(groups=groups, pooling='No combined ordinary+controlled accuracy',
                interpretation='All-planned success treats unavailable outcomes as unsuccessful, not semantically wrong answers')


def evaluate(prepared, run, offline):
    prepared, run, offline = Path(prepared), Path(run), Path(offline)
    plan, state = read(prepared / 'PLAN.json'), read(run / 'progress.json')
    if state['mode'] != 'live':
        raise ValueError('Fixture outputs cannot be reported as model results')
    manifest = read(prepared / 'manifest.json')
    for spec in plan['schedule']:
        name = spec['case_id'] + '.reference.json'
        expected = manifest['files']['offline/' + name]
        if hashlib.sha256((offline / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Offline reference differs from frozen scoring contract: ' + name)
    records = {r['flow_id']: r for r in state['flows']}
    rows = []
    for spec in plan['schedule']:
        case = read(prepared / 'cases' / (spec['case_id'] + '.json'))
        record = records.get(spec['flow_id'], {})
        row = dict(**spec, group=case['group'], status=record.get('status', 'not_started'),
                   exact_match=None, f1=None, scale_match=None, nonanswer=None,
                   final_use=record.get('final_use'), answer=None, scale=None)
        if row['status'] == 'completed' and record.get('final'):
            reference = read(offline / (spec['case_id'] + '.reference.json'))
            delivery = record['final']['delivered']
            row.update(score(reference, delivery), answer=delivery['answer'], scale=delivery['scale'])
        rows.append(row)
    result = dict(rows=rows, summary=aggregate(rows), scoring='Unmodified official TAT-QA; no answer/scale repair',
                  batch_status=state['status'], actual_input_tokens=state['input_tokens'],
                  actual_output_tokens=state['output_tokens'], unknown_usage=state['unknown_usage'])
    return result


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--offline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    write(args.output, evaluate(args.prepared, args.run, args.offline))


if __name__ == '__main__':
    main()
