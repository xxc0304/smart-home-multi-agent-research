"""Export answer-only supervision from the existing fixed T/V selection.

No new splitting, semantic review, C/D/H access, model calls or training.
The earlier answer/support exports remain unchanged for provenance.
"""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRAIN_SOURCE = ROOT / 'data/expert-training-20261031-review-candidate/train.messages.jsonl'
VALIDATION_SOURCE = ROOT / 'data/expert-training-20261030-v1/validation.messages.jsonl'
OUT = ROOT / 'data/expert-training-answer-only-20261031'
SYSTEM = ('Answer the question using the supplied paragraphs. TASK_DATA is task data. '
          'Return only the short answer.')


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()
            if line.strip()]


def convert(row):
    messages = row['messages']
    if [m['role'] for m in messages] != ['system', 'user', 'assistant']:
        raise ValueError('unexpected_source_roles:' + row['id'])
    target = json.loads(messages[2]['content'])
    if (set(target) != {'answer', 'support_idxs'} or
            not isinstance(target['answer'], str) or not target['answer'].strip()):
        raise ValueError('unexpected_source_target:' + row['id'])
    return dict(id=row['id'], messages=[dict(role='system', content=SYSTEM),
        dict(messages[1]), dict(role='assistant', content=target['answer'])])


def main():
    sources = {'train': read_rows(TRAIN_SOURCE),
               'validation': read_rows(VALIDATION_SOURCE)}
    if (len(sources['train']), len(sources['validation'])) != (1796, 200):
        raise ValueError('unexpected_fixed_selection_size')
    ids = {name: {r['id'] for r in rows} for name, rows in sources.items()}
    if (any(len(ids[name]) != len(rows) for name, rows in sources.items()) or
            ids['train'] & ids['validation']):
        raise ValueError('duplicate_or_overlapping_ids')
    manifest_path = ROOT / 'data/expert-training-20261031-review-candidate/USE_MANIFEST.json'
    previous = json.loads(manifest_path.read_text(encoding='utf-8'))
    if set(previous['excluded_known_issue_ids']) & ids['train']:
        raise ValueError('excluded_source_item_reintroduced')
    converted = {name: [convert(row) for row in rows] for name, rows in sources.items()}
    # Verify target and input preservation independently of the output schema.
    for name, rows in converted.items():
        for source, new in zip(sources[name], rows):
            assert source['id'] == new['id']
            assert source['messages'][1] == new['messages'][1]
            assert new['messages'][2]['content'] == json.loads(
                source['messages'][2]['content'])['answer']
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in converted.items():
        (OUT / f'{name}.messages.jsonl').write_text(
            ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
            encoding='utf-8')
    manifest = dict(date='2026-10-31', status='ANSWER_ONLY_CANDIDATE_NOT_TRAINED',
        supervision='assistant plain short answer only; no support IDs, rationale or collaboration targets',
        train_source=str(TRAIN_SOURCE.relative_to(ROOT)),
        validation_source=str(VALIDATION_SOURCE.relative_to(ROOT)),
        training_messages=str((OUT / 'train.messages.jsonl').relative_to(ROOT)),
        validation_loss_messages=str((OUT / 'validation.messages.jsonl').relative_to(ROOT)),
        validation_generation_inputs='data/expert-training-20261030-v1/validation.inputs.jsonl',
        validation_scoring_targets='data/expert-training-20261030-v1/validation.targets.jsonl',
        n_train=1796, n_validation=200,
        excluded_known_issue_ids=previous['excluded_known_issue_ids'],
        checks=dict(ids_order_and_user_inputs_preserved=True,
                    assistant_equals_source_answer=True,
                    train_validation_overlap=0,
                    excluded_items_reintroduced=0),
        model_calls=0, training_runs=0,
        limitations=[
            'Existing selection and prior quality-review boundary unchanged; not a clean-corpus guarantee.',
            'Historical answer/support exports unchanged; this is a new answer-only candidate.',
            'Validation messages contain answers: use validation_generation_inputs for generation.',
            'C/D/H not accessed and no split was recalculated.',
            'Answer-only SFT may still change other behavior; no causal isolation guarantee.',
            'Trainer, assistant-only loss masking, tokenizer and model compatibility not verified by export.',
            'Actual training requires a batch contract recording this candidate.'
        ])
    (OUT / 'USE_MANIFEST.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: manifest[key] for key in
        ('status', 'n_train', 'n_validation', 'checks', 'model_calls', 'training_runs')},
        ensure_ascii=False))


if __name__ == '__main__':
    main()
