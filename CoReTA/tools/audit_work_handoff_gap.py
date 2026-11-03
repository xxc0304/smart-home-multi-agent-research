"""Read actual v2 replies: compare declared first-turn work with arithmetic already provided."""
import json
from pathlib import Path

from coreta.local_work.data import read, write
from coreta.local_work.engine import calculate, WorkError

ROOT = Path(__file__).resolve().parents[1]


def inspect():
    live = ROOT / 'runs/local-work-v2-mixed-live-20261027-v1/flows'
    rows = []
    for cid in ('dependent-01', 'dependent-02'):
        directory = live / (cid + '-local_work')
        for event in read(directory / 'EVENTS.json')[:2]:
            raw = json.loads(event['raw'])
            calculations = []
            for calculation in raw.get('calculations', []):
                try:
                    value = calculate(calculation['expression'], calculation['values'])
                    calculations.append(dict(**calculation, computed=value))
                except WorkError as exc:
                    calculations.append(dict(**calculation, rejected=str(exc)))
            rows.append(dict(case_id=cid, actor=event['actor'], wave=event['wave'],
                             work=raw.get('work', []), actual_model_calculations=calculations,
                             message=raw['message']))
    assert all(row['actual_model_calculations'] for row in rows)
    report = dict(kind='actual_prior_model_output_inspection_not_new_generation', model_calls=0, rows=rows,
                  finding='First-turn local arithmetic is already computable; W representation separately leaves its operands unbound',
                  boundary='This inspection does not infer the correct task answer or repair the prior outputs')
    write(ROOT / 'research/local-work-handoff-20261027/GAP_TRACE.json', report)
    return [dict(case_id=r['case_id'], actor=r['actor'], computed=[c.get('computed') for c in r['actual_model_calculations']],
                 declared_work_inputs=[len(w['inputs']) for w in r['work']]) for r in rows]


if __name__ == '__main__':
    print(json.dumps(inspect(), ensure_ascii=False))
