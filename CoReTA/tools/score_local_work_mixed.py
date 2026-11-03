"""Offline scoring only, using unmodified official TAT-QA metric and utilities."""
import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def metric_class():
    directory = ROOT / 'data/source/tatqa-20261027/evaluator'
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    return importlib.import_module('tatqa_metric').TaTQAEmAndF1


def score(reference, delivery):
    metric = metric_class()()
    answer = delivery['answer']
    nonanswer = answer is None or isinstance(answer, str) and not answer.strip()
    # A list preserves numeric zero as an actual answer in the upstream API.
    prediction = [] if nonanswer else [answer]
    metric(reference, prediction, pred_scale=delivery.get('scale', ''))
    em, f1, scale, _ = metric.get_overall_metric()
    return dict(exact_match=em, f1=f1, scale_match=scale, nonanswer=nonanswer,
                evaluator='unmodified upstream TAT-QA', no_host_scale_correction=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text(encoding='utf-8'))
    if summary.get('status') != 'completed' or not summary.get('final'):
        print(json.dumps(dict(status='not_scored', reason='technical_incomplete')))
        return
    reference = json.loads(args.reference.read_text(encoding='utf-8'))
    print(json.dumps(score(reference, summary['final']['delivered'])))


if __name__ == '__main__':
    main()
