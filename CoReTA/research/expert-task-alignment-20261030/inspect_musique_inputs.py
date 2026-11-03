"""Inspect sanitized task inputs with the official tokenizer only; no weights or generation."""
import hashlib
import json
from pathlib import Path
import statistics
import urllib.request

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
DATA = PROJECT / 'data/external/musique-inspection-20261030'
TOKENIZER = PROJECT / 'data/external/qwen3-4b-tokenizer-20261030'


def fetch_json(url, max_bytes):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'CoReTA-data-inspection/1.0'}), timeout=60) as response:
        value = response.read(max_bytes + 1)
    if len(value) > max_bytes:
        raise ValueError('Public file exceeds expected bound')
    json.loads(value)
    return value


def percentile(values, p):
    values = sorted(values)
    x = (len(values) - 1) * p
    lo = int(x)
    return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (x - lo)


def main():
    from tokenizers import Tokenizer
    TOKENIZER.mkdir(parents=True, exist_ok=True)
    meta_path = TOKENIZER / 'PROVENANCE.json'
    tokenizer_path = TOKENIZER / 'tokenizer.json'
    if not tokenizer_path.exists():
        metadata = json.loads(fetch_json('https://huggingface.co/api/models/Qwen/Qwen3-4B', 1024 * 1024))
        revision = metadata['sha']
        url = f'https://huggingface.co/Qwen/Qwen3-4B/resolve/{revision}/tokenizer.json'
        content = fetch_json(url, 25 * 1024 * 1024)
        tokenizer_path.write_bytes(content)
        meta_path.write_text(json.dumps({'model': 'Qwen/Qwen3-4B', 'revision': revision, 'url': url,
                                        'sha256': hashlib.sha256(content).hexdigest(), 'date': '2026-10-30',
                                        'scope': 'Tokenizer only; no model weights'}, indent=2), encoding='utf-8')
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    result = {'date': '2026-10-30', 'scope': 'First 30 raw records per split; not representative; base task text excludes chat wrapping, generated reasoning and discussion history',
              'tokenizer': json.loads(meta_path.read_text(encoding='utf-8')), 'splits': []}
    for split in ('train', 'dev'):
        values = [json.loads(s) for s in (DATA / (split + '_raw_prefix.jsonl')).read_text(encoding='utf-8').splitlines()]
        inputs, targets, lengths, step_checks, inspected = [], [], [], [], []
        for value in values:
            paragraphs = [{'idx': i, 'title': c['wikipedia_title'], 'text': c['paragraph_text']} for i, c in enumerate(value['contexts'])]
            question = value['composed_question_text']
            public = {'raw_id': value['id'], 'question': question, 'paragraphs': paragraphs}
            prompt = 'Answer the question using the supplied paragraphs. Return an answer and supporting paragraph IDs.\nQuestion: ' + question
            prompt += '\n' + '\n\n'.join(f"[P{p['idx']}] {p['title']}\n{p['text']}" for p in paragraphs)
            lengths.append(len(tokenizer.encode(prompt).ids))
            support = [i for i, c in enumerate(value['contexts']) if c['is_supporting']]
            step_indices = []
            for step in value['decomposed_instances']:
                support_text = step['contexts'][0]['paragraph_text']
                hits = [i for i, c in enumerate(value['contexts']) if c['paragraph_text'] == support_text]
                step_indices.append(hits)
            step_checks.append(all(len(v) == 1 for v in step_indices))
            inputs.append(public)
            targets.append({'raw_id': value['id'], 'answer': value['answer_text'], 'support_idxs': support,
                            'step_support_matches': step_indices, 'step_source_ids': [s['id'] for s in value['decomposed_instances']]})
            inspected.append({'raw_id': value['id'], 'question': question,
                              'normalized_question_sha256': hashlib.sha256(' '.join(question.lower().split()).encode()).hexdigest()})
        for suffix, rows in [('inputs', inputs), ('targets', targets), ('inspected_ids', inspected)]:
            (DATA / (split + '_' + suffix + '.jsonl')).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
        result['splits'].append({'split': split, 'records': len(values), 'context_counts': sorted({len(v['contexts']) for v in values}),
                                 'all_step_supports_uniquely_matched': all(step_checks),
                                 'base_input_tokens': {'min': min(lengths), 'median': statistics.median(lengths), 'p95': percentile(lengths, .95), 'max': max(lengths),
                                                       'over_4096': sum(x > 4096 for x in lengths), 'over_8192': sum(x > 8192 for x in lengths)},
                                 'first_input': inputs[0], 'first_target': targets[0]})
    (HERE / 'MUSIQUE_INPUT_INSPECTION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'tokenizer_revision': result['tokenizer']['revision'], 'splits': [{k:v for k,v in r.items() if not k.startswith('first_')} for r in result['splits']]}, ensure_ascii=True))


if __name__ == '__main__':
    main()
