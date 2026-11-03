"""Strict protocol validation, then the unchanged upstream MuSiQue-Ans scorer.

No failed/missing records are silently omitted. Invalid batches have no aggregate
score; this is an offline scoring contract, not a model-generation failure policy.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'official_scorer'))
spec = importlib.util.spec_from_file_location('musique_official_eval', HERE / 'official_scorer/evaluate_v1.0.py')
official = importlib.util.module_from_spec(spec)
spec.loader.exec_module(official)


def read(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(s) for s in handle if s.strip()]


def validate(predictions, targets):
    target_ids = [r['id'] for r in targets]
    pred_ids = [r.get('id') for r in predictions]
    if not targets: raise ValueError('Empty evaluation set')
    if len(set(target_ids)) != len(target_ids): raise ValueError('Duplicate target IDs')
    if any(not isinstance(v, str) for v in pred_ids): raise ValueError('Prediction IDs must be strings')
    if len(set(pred_ids)) != len(pred_ids): raise ValueError('Duplicate prediction IDs')
    if set(pred_ids) != set(target_ids): raise ValueError('Missing or extra prediction IDs')
    by_id = {r['id']:r for r in predictions}
    aligned = []
    for target in targets:
        p = by_id[target['id']]
        required = {'id','predicted_answer','predicted_support_idxs','predicted_answerable'}
        if set(p) != required: raise ValueError('Unexpected prediction fields')
        if not isinstance(p['predicted_answer'], str): raise ValueError('Answer must be a string')
        if type(p['predicted_answerable']) is not bool: raise ValueError('Answerability must be bool')
        supports = p['predicted_support_idxs']
        valid_idxs = {item['idx'] for item in target['paragraphs']}
        if not isinstance(supports, list) or any(type(v) is not int or v not in valid_idxs for v in supports):
            raise ValueError('Supporting indices must be actual integer paragraph IDs')
        if len(set(supports)) != len(supports): raise ValueError('Duplicate supporting indices')
        aligned.append(p)
    return aligned


def score(predictions_path, targets_path):
    targets = read(targets_path)
    aligned = validate(read(predictions_path), targets)
    # Preserve the official scorer's same-order requirement after explicit ID join.
    with tempfile.TemporaryDirectory(prefix='coreta-musique-score-') as folder:
        ordered = Path(folder) / 'aligned_predictions.jsonl'
        ordered.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in aligned),encoding='utf-8')
        result = official.evaluate(str(ordered),str(targets_path))
    return {'status':'VALID', 'n_expected':len(targets), 'n_scored':len(aligned),
            'metrics':result, 'metric_precision':'official aggregate rounding to 3 decimal places'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--predictions', required=True)
    parser.add_argument('--targets', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(score(args.predictions,args.targets),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({'status':'INVALID_NO_AGGREGATE_SCORE','error':str(exc)},ensure_ascii=False))
        sys.exit(2)


if __name__ == '__main__':
    main()
