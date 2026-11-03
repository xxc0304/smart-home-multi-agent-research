"""Offline answer scoring only; source-faithful revision requires separate review."""
import argparse
import hashlib
import json
from pathlib import Path


def score(prepared, run):
    manifest = json.loads((run/'manifest.json').read_text())
    labels_file = prepared/'offline_labels.json'
    if hashlib.sha256(labels_file.read_bytes()).hexdigest() != manifest['files']['offline_labels.json']:
        raise ValueError('offline labels changed')
    labels = json.loads(labels_file.read_text())
    state = json.loads((run/'progress.json').read_text())
    completed = {(r['case'], r['repeat'], r['method']): r for r in state['completed']}
    rows = []
    for item in manifest['schedule']:
        row = dict(item)
        result = completed.get((item['case'], item['repeat'], item['method']))
        row.update(status='completed' if result else 'not_completed',
                   correct=result['answer']['choice'] in labels[item['case']] if result else None,
                   semantic_revision_correct=None)
        rows.append(row)
    pairs = []
    for case, repeat in sorted({(r['case'], r['repeat']) for r in rows}):
        group = [r for r in rows if r['case'] == case and r['repeat'] == repeat]
        if all(r['status'] == 'completed' for r in group):
            pairs.append(dict(case=case, repeat=repeat,
                **{r['method']: r['correct'] for r in group}))
    return dict(batch_status=state['status'], rows=rows, completed_pairs=pairs,
                warning='Scripted controls only. Choice correctness does not certify explanation or withdrawal correctness.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('prepared', type=Path)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    result = score(args.prepared, args.run)
    (args.run/'offline_scores.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
