"""Export evidence and empty annotation rows; never auto-score semantic correctness."""
import argparse
from pathlib import Path

from prepare_issue_loop_comparison import read, digest
from coreta.handoff.gateway import write_json


def export(root, output):
    if output.exists():
        raise ValueError('Use a new review output')
    manifest = read(root/'manifest.json')
    if read(root/'progress.json')['manifest_sha256'] != digest(root/'manifest.json'):
        raise ValueError('Run manifest differs from executed freeze')
    output.mkdir(parents=True)
    rows, mapping, initial_rows = [], [], []
    for pair in manifest['pairs']:
        evaluation = Path(pair['pack'])/'offline/evaluation.json'
        if digest(evaluation) != manifest['offline_evaluation_hashes'][pair['task_id']]:
            raise ValueError('Offline evaluation changed')
        gold = read(evaluation)['correct_option_id']
        cache_path = root/pair['initial_cache']
        cache = read(cache_path) if cache_path.exists() else None
        for member in ('A'+str(i) for i in range(1, pair['members']+1)):
            work = cache['candidates'].get(member) if cache else None
            initial_rows.append(dict(pair=pair['id'], task_id=pair['task_id'], member=member,
                artifact=work['artifact'] if work else None,
                exact_match=int(work['artifact'] == gold) if work else None))
        for index, method in enumerate(pair['methods']):
            unit = pair['id']+f'-M{index+1}'
            folder = root/pair['id']/method
            record = dict(unit=unit, status='not_run', events=[], result=None)
            if (folder/'events.jsonl').exists():
                import json
                record['events'] = [json.loads(line) for line in
                    (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
            if (folder/'result.json').exists():
                record['result'] = read(folder/'result.json')
                record['status'] = record['result']['status']
            exact = (int(record['result']['selected_work']['artifact'] == gold)
                     if record['result'] and record['status'] == 'completed'
                     and record['result'].get('selected_work') else None)
            write_json(output/(unit+'.json'), record)
            mapping.append(dict(unit=unit, method=method, task_id=pair['task_id']))
            rows.append(dict(unit=unit, task_id=pair['task_id'], status=record['status'], claims=[],
                artifact_exact_match=exact, meaningful_corrections=None, harmful_edits=None,
                disputed_weighting_notes=[], annotation_status='unannotated'))
    write_json(output/'ANNOTATIONS.json', dict(rows=rows, semantic_scores_computed=False,
        instructions='Apply frozen RUBRIC.md; quote evidence; null means unannotated, not zero.'))
    write_json(output/'PRIVATE_METHOD_MAP.json', mapping)
    write_json(output/'INITIAL_REFERENCE.json', initial_rows)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    export(args.run, args.output)
