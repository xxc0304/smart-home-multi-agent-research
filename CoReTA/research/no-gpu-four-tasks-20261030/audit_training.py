"""CPU-only audit of frozen T exports; never reads H or changes assignments."""
from pathlib import Path
from collections import Counter
import json
import statistics
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from expert_mechanism_protocol import validate_task
from prepare_expert_training import sft_record, dependency_groups
from tokenizers import Tokenizer


def read(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def norm(s):
    return ' '.join(unicodedata.normalize('NFKC', s).casefold().split())


def profile(values):
    v = sorted(values)
    return dict(n=len(v), min=v[0], median=statistics.median(v),
                p95=v[int((len(v)-1)*.95)], max=v[-1])


def main():
    folder = ROOT / 'data/expert-training-20261030-v1'
    tokenizer = Tokenizer.from_file(str(ROOT / 'data/external/qwen3-4b-tokenizer-20261030/tokenizer.json'))
    def count(s):
        return len(tokenizer.encode(s, add_special_tokens=False).ids)
    sets = {}
    for role in ('train', 'validation'):
        inputs = read(folder / f'{role}.inputs.jsonl')
        targets = read(folder / f'{role}.targets.jsonl')
        messages = read(folder / f'{role}.messages.jsonl')
        assert len(inputs) == len(targets) == len(messages)
        source_by_id = {r['id']: r for r in read(ROOT / 'data/external/musique-v1.0-20261030/inputs/T_optional_training.jsonl')}
        prompt_lengths, target_lengths = [], []
        answers, questions, supports = Counter(), Counter(), Counter()
        for task, target, record in zip(inputs, targets, messages):
            assert task['id'] == target['id'] == record['id']
            validate_task(task)
            assert task == source_by_id[task['id']]
            assert record == sft_record(task, target)
            prompt_lengths.append(count('\n'.join(m['content'] for m in record['messages'][:2])))
            target_lengths.append(count(record['messages'][2]['content']))
            assert set(json.loads(record['messages'][1]['content'].split('\n', 1)[1])) == {'question', 'paragraphs'}
            assert set(json.loads(record['messages'][2]['content'])) == {'answer', 'support_idxs'}
            questions[norm(task['question'])] += 1
            answers[norm(target['answer'])] += 1
            support_ids = {p['idx'] for p in target['paragraphs'] if p['is_supporting']}
            for p in task['paragraphs']:
                if p['idx'] in support_ids:
                    supports[norm(p['paragraph_text'])] += 1
        sets[role] = dict(n=len(inputs), unique_normalized_questions=len(questions),
            duplicated_question_extra_rows=sum(n-1 for n in questions.values()),
            unique_answer_strings=len(answers), max_answer_repetition=max(answers.values()),
            support_occurrences=sum(supports.values()), unique_support_texts=len(supports),
            largest_support_text_frequencies=sorted(supports.values(), reverse=True)[:10],
            prompt_tokens_without_chat_template=profile(prompt_lengths),
            supervised_completion_tokens_without_chat_template=profile(target_lengths),
            all_input_paragraphs_preserved=True, gold_fields_excluded_from_prompt=True,
            assistant_supervision_contains_no_synthetic_reasoning=True,
            first_three_ids=[r['id'] for r in inputs[:3]])
    assignments = read(folder / 'assignments.jsonl')
    active_ids = {r['id'] for r in assignments}
    indexed = [r for r in read(ROOT / 'data/external/musique-v1.0-20261030/corpus_index.jsonl') if r['id'] in active_ids]
    assert len(indexed) == 2000
    strict = dependency_groups(indexed)
    # Compare existing hard grouping with strict support-to-visible grouping.
    import importlib.util
    spec = importlib.util.spec_from_file_location('existing_musique_audit', ROOT / 'research/musique-data-preparation-20261030/audit_corpus.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = dict(date='2026-10-30', evidence_type='OFFLINE_DATA_AUDIT_NOT_MODEL_RESULTS',
        roles=sets, existing_hard_components=module.components(indexed),
        strict_components=dict(n=len(strict), largest=max(map(len, strict))),
        strict_largest_fraction=max(map(len, strict))/2000,
        source_split_report='data/expert-training-20261030-v1/SPLIT_REPORT.json',
        model_calls=0, training_runs=0,
        limits=['Exact repetition is not semantic duplication or full memorization testing.',
                'Gold metadata audits confirm boundaries, not that every annotation is semantically correct.',
                'Token counts omit actual chat template, hidden reasoning and discussion.',
                'No trainer is connected; assistant-only loss masking remains unverified.',
                'Task skill, openness to discussion and useful sharing require real held-out outputs.'])
    (HERE / 'TRAINING_DATA_AUDIT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
