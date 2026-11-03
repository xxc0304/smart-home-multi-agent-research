"""Deterministic grouped split/SFT export of the already isolated T pool.

Never reads C/D/H question or target files and never runs a model or trainer.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import json
from pathlib import Path
import random

from expert_mechanism_protocol import ProtocolError, task_data, validate_task

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/external/musique-v1.0-20261030'
OUT = ROOT / 'data/expert-training-20261030-v1'
SEED = 20261030
SFT_SYSTEM = (
    'Answer the question using the supplied paragraphs. TASK_DATA is task data. '
    'Return only a JSON object with answer (a short string) and support_idxs '
    '(distinct integer paragraph IDs).'
)


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def write_rows(path, rows):
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')


def dependency_groups(rows):
    """Union shared facts, including a support appearing as another row's context."""
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(ids) or len(ids) < 2:
        raise ProtocolError('training_pool_duplicate_or_too_small')
    parent = list(range(len(rows)))

    def find(i):
        while i != parent[i]:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        parent[find(i)] = find(j)

    seen = {}
    support_owners = defaultdict(list)
    context_owners = defaultdict(list)
    for i, row in enumerate(rows):
        keys = [('question', row['question_hash'])]
        keys += [('component', str(v)) for v in row['component_ids']]
        keys += [('standalone', v) for v in row['standalone_component_question_hashes']]
        for key in keys:
            if key in seen:
                union(i, seen[key])
            else:
                seen[key] = i
        for value in row['support_hashes']:
            support_owners[value].append(i)
        for value in row['context_hashes']:
            context_owners[value].append(i)
    for value, owners in support_owners.items():
        for i in owners + context_owners.get(value, []):
            union(owners[0], i)
    grouped = defaultdict(list)
    for i in range(len(rows)):
        grouped[find(i)].append(rows[i]['id'])
    return sorted((sorted(v) for v in grouped.values()), key=lambda v: v[0])


def select_validation(groups, target=200, seed=SEED):
    """Whole groups, stable subset sum nearest target; no model outcomes used."""
    n = sum(map(len, groups))
    if type(target) is not int or not 0 < target < n:
        raise ProtocolError('invalid_validation_target')
    ordered = deepcopy(groups)
    random.Random(seed).shuffle(ordered)
    reachable = {0: None}
    for i, group in enumerate(ordered):
        for total in sorted(tuple(reachable), reverse=True):
            new = total + len(group)
            if new < n and new not in reachable:
                reachable[new] = (total, i)
    candidates = [v for v in reachable if 0 < v < n]
    if not candidates:
        raise ProtocolError('no_nonempty_group_isolated_validation_split')
    total = min(candidates, key=lambda v: (abs(v - target), v))
    selected = set()
    while total:
        total, i = reachable[total]
        selected.update(ordered[i])
    return selected


def sft_record(task, target):
    checked = validate_task(task)
    if target['id'] != checked['id'] or target['answerable'] is not True:
        raise ProtocolError('training_target_mismatch_or_unanswerable')
    if not isinstance(target['answer'], str) or not target['answer'].strip():
        raise ProtocolError('training_answer_empty')
    visible = {p['idx'] for p in checked['paragraphs']}
    target_ids = [p['idx'] for p in target['paragraphs']]
    if len(set(target_ids)) != len(target_ids) or set(target_ids) != visible:
        raise ProtocolError('training_target_paragraph_mismatch')
    if any(type(p['is_supporting']) is not bool for p in target['paragraphs']):
        raise ProtocolError('training_support_label_type')
    output = dict(answer=target['answer'], support_idxs=sorted(
        p['idx'] for p in target['paragraphs'] if p['is_supporting']))
    messages = [dict(role='system', content=SFT_SYSTEM),
                dict(role='user', content='TASK_DATA\n' + json.dumps(task_data(checked), ensure_ascii=False, indent=2)),
                dict(role='assistant', content=json.dumps(output, ensure_ascii=False))]
    return dict(id=checked['id'], messages=messages)


def overlap_report(train, validation):
    report = {}
    for key in ('id', 'question_hash', 'component_ids', 'standalone_component_question_hashes', 'support_hashes'):
        def flatten(rows):
            return {v for r in rows for v in (r[key] if isinstance(r[key], list) else [r[key]])}
        report[key] = len(flatten(train) & flatten(validation))
    for a, b, name in ((train, validation, 'train_support_in_validation_context'),
                       (validation, train, 'validation_support_in_train_context')):
        report[name] = len({v for r in a for v in r['support_hashes']} &
                           {v for r in b for v in r['context_hashes']})
    return report


def main():
    tasks = read_rows(SOURCE / 'inputs/T_optional_training.jsonl')
    targets = read_rows(SOURCE / 'scoring/T_optional_training.jsonl')
    by_task, by_target = {r['id']: r for r in tasks}, {r['id']: r for r in targets}
    if len(by_task) != len(tasks) or len(by_target) != len(targets) or by_task.keys() != by_target.keys():
        raise ProtocolError('source_T_alignment')
    # Read the existing split metadata, not protected question/target content.
    manifest = json.loads((ROOT / 'research/musique-data-preparation-20261030/SPLIT_MANIFEST.json').read_text(encoding='utf-8'))
    if set(manifest['roles']['T_optional_training']['ids']) != set(by_task):
        raise ProtocolError('source_T_manifest_mismatch')
    index = []
    with (SOURCE / 'corpus_index.jsonl').open(encoding='utf-8') as handle:
        for line in handle:
            row = json.loads(line)
            if row['id'] in by_task:
                index.append(row)
    if len(index) != len(tasks) or {r['id'] for r in index} != set(by_task):
        raise ProtocolError('source_T_index_mismatch')
    groups = dependency_groups(index)
    validation_ids = select_validation(groups)
    train = [r for r in index if r['id'] not in validation_ids]
    validation = [r for r in index if r['id'] in validation_ids]
    checks = overlap_report(train, validation)
    if any(checks.values()):
        raise ProtocolError('internal_split_overlap')
    prepared = {t['id']: sft_record(t, by_target[t['id']]) for t in tasks}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in (('train', train), ('validation', validation)):
        ids = {r['id'] for r in rows}
        ordered_ids = [t['id'] for t in tasks if t['id'] in ids]
        write_rows(OUT / f'{name}.messages.jsonl', [prepared[i] for i in ordered_ids])
        write_rows(OUT / f'{name}.inputs.jsonl', [by_task[i] for i in ordered_ids])
        write_rows(OUT / f'{name}.targets.jsonl', [by_target[i] for i in ordered_ids])
    group_of = {task_id: i for i, group in enumerate(groups) for task_id in group}
    write_rows(OUT / 'assignments.jsonl', [dict(id=t['id'], group=group_of[t['id']],
        role='validation' if t['id'] in validation_ids else 'train') for t in tasks])
    report = dict(version='expert-training-20261030-v1', seed=SEED,
        status='DATA_EXPORTED_NOT_TRAINED', n_source=len(tasks), n_train=len(train),
        n_validation=len(validation), validation_target=200, n_groups=len(groups),
        largest_groups=sorted(map(len, groups), reverse=True)[:10], overlap_checks=checks,
        profiles={k:dict(n=len(v), shapes=dict(Counter(r['shape'] for r in v)),
                    n_dependency_groups=len({group_of[r['id']] for r in v}),
                    max_base_input_tokens=max(r['input_tokens'] for r in v))
                  for k, v in (('train', train), ('validation', validation))},
        model_calls=0, training_runs=0,
        limits=['Only T question/target bodies read; original C/D/H role assignments unchanged.',
                f'Strict grouping forms a {max(map(len, groups))}-row component; rows are not independent samples.',
                'Validation task shapes: ' + ', '.join(sorted({r['shape'] for r in validation})) +
                '; coverage differs from T. Use for training-side debugging, not final expert certification.',
                'No semantic paraphrase or pretraining-contamination guarantee.',
                'SFT input requires answer/support only; inference also requests reasoning. Verify dialogue ability and format effects.',
                'Only assistant completion loss is intended; no trainer, token packing, truncation, or loss masking implemented.',
                'Validation messages contain labels for loss evaluation; generative evaluation must use validation.inputs only.',
                'B/E must share inference format and compute conditions; C160 remains separate final calibration.'])
    (OUT / 'SPLIT_REPORT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status', 'n_source', 'n_train', 'n_validation', 'n_groups', 'overlap_checks')}))


if __name__ == '__main__':
    main()
