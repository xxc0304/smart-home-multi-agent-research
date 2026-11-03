"""Answer-only scoring. No model, gold-based extraction, or support-field gate."""
import argparse
import json
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/musique-data-preparation-20261030/official_scorer'))
from metrics.answer import compute_exact, compute_f1


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def answer_text(raw):
    if not isinstance(raw, str):
        raise ValueError('answer_must_be_text')
    return re.sub(r'^(?:answer|答案)\s*[:：]\s*', '', raw.strip(), count=1, flags=re.I).strip()


def answer_score(raw, target):
    answer = answer_text(raw)
    golds = [target['answer']] + target.get('answer_aliases', [])
    return dict(answer=answer, em=max(compute_exact(g, answer) for g in golds),
                f1=max(compute_f1(g, answer) for g in golds))


def score_run(directory, targets):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    expected = manifest['expected_ids']
    if not expected or len(set(expected)) != len(expected):
        raise ValueError('empty_or_duplicate_expected_ids')
    records = read_jsonl(directory / 'responses.jsonl')
    by_id = {r['id']: r for r in records}
    if len(by_id) != len(records) or set(by_id) - set(expected):
        raise ValueError('duplicate_or_extra_response')
    if not set(expected) <= set(targets):
        raise ValueError('targets_missing_expected_items')
    scored = []
    for task_id in expected:
        record = by_id.get(task_id, dict(id=task_id, status='MISSING'))
        metrics = answer_score(record['raw_output'], targets[task_id]) if record['status'] == 'OK' else None
        scored.append(dict(**record, metrics=metrics))
    complete = all(r['metrics'] is not None for r in scored)
    means = {key: sum(r['metrics'][key] for r in scored) / len(expected)
             for key in ('em', 'f1')} if complete else None
    return dict(manifest=manifest, status='COMPLETE' if complete else 'INCOMPLETE',
        n_expected=len(expected), n_valid=sum(r['metrics'] is not None for r in scored),
        metrics=means, records=scored, primary_enabled=complete and not manifest['fixture'])


def percentile(values, p):
    values = sorted(values)
    index = (len(values) - 1) * p
    lo = int(index)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (index - lo)


def paired_interval(values, groups, repeats=10000, seed=20261102):
    if set(values) != set(groups):
        raise ValueError('group_mapping_must_cover_exact_expected_ids')
    buckets = {}
    for task_id, value in values.items():
        buckets.setdefault(groups[task_id], []).append(value)
    blocks = [(sum(v), len(v)) for v in buckets.values()]
    if len(blocks) < 2:
        return None
    rng = random.Random(seed)
    samples = []
    for _ in range(repeats):
        draw = rng.choices(blocks, k=len(blocks))
        samples.append(sum(v for v, n in draw) / sum(n for v, n in draw))
    return [percentile(samples, .025), percentile(samples, .975)]


def compare_runs(baseline, expert, groups, repeats=10000, seed=20261102):
    a, b = baseline['manifest'], expert['manifest']
    fields = ('role', 'expected_ids', 'fixture', 'inference')
    if any(a[k] != b[k] for k in fields) or a['condition'] != 'B' or b['condition'] != 'E':
        raise ValueError('unpaired_roles_or_inference_conditions')
    report = dict(status='INCOMPLETE', primary_enabled=False, qualification='NOT_ASSESSED',
                  n_expected=len(a['expected_ids']), difference=None, cluster_ci95=None)
    if baseline['status'] != 'COMPLETE' or expert['status'] != 'COMPLETE':
        return report
    by_a = {r['id']: r['metrics']['em'] for r in baseline['records']}
    by_b = {r['id']: r['metrics']['em'] for r in expert['records']}
    differences = {task_id: by_b[task_id] - by_a[task_id] for task_id in a['expected_ids']}
    ci = paired_interval(differences, groups, repeats, seed)
    n_groups = len(set(groups.values()))
    delta = sum(differences.values()) / len(differences)
    warnings = ['TOO_FEW_GROUPS_FOR_STRONG_QUALIFICATION'] if n_groups < 10 else []
    largest = max(list(groups.values()).count(g) for g in set(groups.values()))
    if largest / len(groups) > .5:
        warnings.append('ONE_GROUP_DOMINATES_PRECISION')
    enabled = baseline['primary_enabled'] and expert['primary_enabled']
    qualifies = enabled and a['role'] == 'C' and ci is not None and ci[0] > 0 and delta > 0 and not warnings
    report.update(status='COMPLETE', primary_enabled=enabled, difference=delta,
        cluster_ci95=ci, item_ci95=paired_interval(differences,
            {k:k for k in differences}, repeats, seed),
        n_groups=n_groups, largest_group_n=largest, warnings=warnings,
        paired_counts=dict(both_correct=sum(by_a[k] == by_b[k] == 1 for k in by_a),
            only_expert=sum(v == 1 for v in differences.values()),
            only_baseline=sum(v == -1 for v in differences.values()),
            both_wrong=sum(by_a[k] == by_b[k] == 0 for k in by_a)),
        qualification='SUPPORTED_TASK_ADVANTAGE' if qualifies else 'NOT_ESTABLISHED',
        evidence_type='FIXTURE_NOT_RESEARCH_RESULT' if a['fixture'] else 'ACTUAL_MODEL_RESPONSES',
        bootstrap=dict(repeats=repeats, seed=seed, unit='predeclared_dependency_group'))
    return report


def select_candidate(reports):
    if not 1 <= len(reports) <= 2 or any(r['manifest']['role'] != 'V' or r['manifest']['condition'] != 'E'
                          or r['status'] != 'COMPLETE' for r in reports):
        raise ValueError('selection_requires_complete_expert_V_reports')
    first = reports[0]['manifest']
    if any(any(r['manifest'][k] != first[k] for k in ('role', 'expected_ids', 'inference', 'fixture'))
           for r in reports):
        raise ValueError('candidate_V_conditions_differ')
    # Caller order is the preregistered candidate order, not result ranking.
    index = max(range(len(reports)), key=lambda i: (reports[i]['metrics']['em'], reports[i]['metrics']['f1'], -i))
    return dict(selected_index=index, selected_adapter=reports[index]['manifest']['adapter'],
                ordering='EM_then_F1_then_earlier_registered_candidate', fixture=first['fixture'])


def smoke(output):
    target = dict(answer='New York City', answer_aliases=['NYC'])
    report = dict(evidence_type='FIXTURE_NOT_RESEARCH_RESULT', primary_enabled=False,
                  example=answer_score('Answer: NYC', target), model_calls=0)
    write_json(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', type=Path)
    args = parser.parse_args()
    if args.smoke:
        print(json.dumps(smoke(args.smoke)))
    else:
        parser.error('choose --smoke')


if __name__ == '__main__':
    main()
