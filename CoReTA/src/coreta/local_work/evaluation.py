"""Summarize scored replies; keep main/supplement and failures separate."""
from .comparison import ARMS


def summarize(expected, rows):
    groups = {case['case_id']: case['group'] for case in expected}
    indexed = {}
    for row in rows:
        key = (row['case_id'], row['arm'])
        if key in indexed or key[0] not in groups or key[1] not in ARMS:
            raise ValueError('duplicate or unscheduled score row')
        if row.get('group') != groups[key[0]]:
            raise ValueError('score group disagrees with frozen selection')
        if row['status'] == 'completed' and row.get('exact_match') not in (0, 1):
            raise ValueError('completed row needs official exact-match score')
        indexed[key] = row
    output = {}
    for group in ('main', 'diagnostic'):
        ids = [cid for cid, g in groups.items() if g == group]
        arms = {}
        for arm in ARMS:
            attempted = [indexed[(cid, arm)] for cid in ids if (cid, arm) in indexed]
            valid = [r for r in attempted if r['status'] == 'completed']
            correct = sum(r['exact_match'] for r in valid)
            arms[arm] = dict(planned=len(ids), recorded=len(attempted), completed=len(valid), correct=correct,
                             official_em_completed=correct / len(valid) if valid else None,
                             end_to_end_success_all_planned=correct / len(ids) if attempted and ids else None,
                             incomplete_or_missing=[cid for cid in ids if
                                 indexed.get((cid, arm), {}).get('status') != 'completed'],
                             semantic_nonanswers=sum(bool(r.get('nonanswer')) for r in valid))
        paired = dict(both_correct=0, local_work_only=0, ordinary_only=0, both_wrong=0,
                      incomplete_or_missing=[])
        for cid in ids:
            old, new = indexed.get((cid, 'ordinary')), indexed.get((cid, 'local_work'))
            if not old or not new or old['status'] != 'completed' or new['status'] != 'completed':
                paired['incomplete_or_missing'].append(cid)
                continue
            a, b = old['exact_match'], new['exact_match']
            key = 'both_correct' if a and b else 'local_work_only' if b else 'ordinary_only' if a else 'both_wrong'
            paired[key] += 1
        output[group] = dict(arms=arms, paired=paired)
    return dict(status='not_run' if not rows else 'scored_records', groups=output,
                pooling='no pooled main+diagnostic accuracy',
                technical_failure_policy='completed accuracy and all-planned operational success separate')
