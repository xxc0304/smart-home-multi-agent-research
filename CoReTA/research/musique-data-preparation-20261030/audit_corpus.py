"""Offline audit only. Gold-bearing index is for splitting/scoring, never model input."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import statistics
import unicodedata
import re
from tokenizers import Tokenizer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = ROOT / 'data/external/musique-v1.0-20261030'
TOKENIZER = ROOT / 'data/external/qwen3-4b-tokenizer-20261030/tokenizer.json'


def norm(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def digest(text):
    return hashlib.sha256(norm(text).encode('utf-8')).hexdigest()


def paragraph_hash(p):
    # Text-only key conservatively groups identical text even when titles differ.
    return digest(p['paragraph_text'])


def sanitize(row):
    return {'id': row['id'], 'question': row['question'], 'paragraphs': [
        {k: p[k] for k in ('idx', 'title', 'paragraph_text')} for p in row['paragraphs']]}


def prompt(row):
    # id is log metadata, deliberately excluded from the prompt.
    paragraphs = '\n\n'.join(f"[P{p['idx']}] {p['title']}\n{p['paragraph_text']}" for p in row['paragraphs'])
    return 'Answer the question using the supplied paragraphs. Return an answer and supporting paragraph IDs.\nQuestion: ' + row['question'] + '\n' + paragraphs


def keys(row):
    return {('q', row['question_hash'])} | {('s', str(v)) for v in row['component_ids']} | {('p', v) for v in row['support_hashes']} | {('u',v) for v in row['standalone_component_question_hashes']}


def summary(values):
    values = sorted(values)
    def percentile(p):
        return values[min(len(values)-1, max(0, int((len(values)-1)*p)))]
    return {'n': len(values), 'min': min(values), 'median': statistics.median(values),
            'p90_floor_rank': percentile(.90), 'p95_floor_rank': percentile(.95), 'max': max(values),
            'over_4096': sum(v > 4096 for v in values), 'over_8192': sum(v > 8192 for v in values)}


def overlaps(a, b, field):
    left = set(v for r in a for v in (r[field] if isinstance(r[field], list) else [r[field]]))
    right = set(v for r in b for v in (r[field] if isinstance(r[field], list) else [r[field]]))
    shared = left & right
    return {'shared_keys': len(shared),
            'left_rows': sum(bool(set(r[field] if isinstance(r[field], list) else [r[field]]) & shared) for r in a),
            'right_rows': sum(bool(set(r[field] if isinstance(r[field], list) else [r[field]]) & shared) for r in b)}


def components(rows):
    parent = list(range(len(rows)))
    def find(a):
        while a != parent[a]:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    seen = {}
    for i, row in enumerate(rows):
        for key in keys(row):
            if key in seen:
                parent[find(i)] = find(seen[key])
            else:
                seen[key] = i
    sizes = Counter(find(i) for i in range(len(rows)))
    return {'components': len(sizes), 'largest_10': sorted(sizes.values(), reverse=True)[:10],
            'singletons': sum(v == 1 for v in sizes.values())}


def main():
    tokenizer = Tokenizer.from_file(str(TOKENIZER))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    indexed, reports = {}, {}
    index_path = DATA / 'corpus_index.jsonl'
    with index_path.open('w', encoding='utf-8') as index_out:
        for split in ('train', 'dev'):
            rows, issues = [], []
            alias_counts, hop_counts, shape_counts, paragraph_counts = Counter(), Counter(), Counter(), Counter()
            with (DATA / f'musique_ans_v1.0_{split}.jsonl').open(encoding='utf-8') as handle:
                for line_number, line in enumerate(handle, 1):
                    row = json.loads(line)
                    pars, steps = row['paragraphs'], row['question_decomposition']
                    errors = []
                    if row['answerable'] is not True: errors.append('not_answerable')
                    if not 1 <= len(pars) <= 20 or [p['idx'] for p in pars] != list(range(len(pars))): errors.append('paragraph_indices')
                    if not isinstance(row['answer'], str) or not row['answer'].strip(): errors.append('answer')
                    if not isinstance(row['answer_aliases'], list) or not all(isinstance(s, str) for s in row['answer_aliases']): errors.append('aliases')
                    if len(steps) not in (2, 3, 4): errors.append('hop_count')
                    if any(type(p['is_supporting']) is not bool for p in pars): errors.append('support_type')
                    if any(type(s['paragraph_support_idx']) is not int or s['paragraph_support_idx'] not in range(len(pars)) for s in steps): errors.append('step_support_index')
                    support_idxs = {p['idx'] for p in pars if p['is_supporting']}
                    if {s['paragraph_support_idx'] for s in steps} != support_idxs: errors.append('support_union_mismatch')
                    if any(not isinstance(p[k], str) for p in pars for k in ('title','paragraph_text')): errors.append('paragraph_text_type')
                    if errors: issues.append({'id': row['id'], 'line': line_number, 'issues': errors})
                    alias_counts[len(row['answer_aliases'])] += 1
                    paragraph_counts[len(pars)] += 1
                    hop_counts[len(steps)] += 1
                    shape_counts[row['id'].split('__')[0]] += 1
                    record = {'id': row['id'], 'source_split': split, 'source_line': line_number,
                        'shape': row['id'].split('__')[0], 'hops': len(steps), 'question_hash': digest(row['question']),
                        'component_ids': [s['id'] for s in steps],
                        'component_question_hashes': [digest(s['question']) for s in steps],
                        'standalone_component_question_hashes': [digest(s['question']) for s in steps if not re.search(r'#\d+',s['question'])],
                        'component_answer_hashes': [digest(s['answer']) for s in steps],
                        'final_answer_hash': digest(row['answer']),
                        'support_hashes': sorted({paragraph_hash(p) for p in pars if p['is_supporting']}),
                        'context_hashes': sorted({paragraph_hash(p) for p in pars}),
                        'input_tokens': len(tokenizer.encode(prompt(sanitize(row)), add_special_tokens=False).ids),
                        'duplicate_context_texts': len(pars)-len({paragraph_hash(p) for p in pars})}
                    rows.append(record)
                    index_out.write(json.dumps(record, ensure_ascii=False)+'\n')
                    if line_number % 2000 == 0: print(split, line_number, flush=True)
            id_counts = Counter(r['id'] for r in rows)
            qcounts = Counter(r['question_hash'] for r in rows)
            reports[split] = {'n': len(rows), 'schema_issues': issues,
                'duplicate_ids': {k:v for k,v in id_counts.items() if v>1},
                'duplicate_question_groups': sum(v>1 for v in qcounts.values()),
                'rows_with_duplicate_context_text': sum(r['duplicate_context_texts']>0 for r in rows),
                'hops': dict(hop_counts), 'shapes': dict(shape_counts), 'paragraph_count_distribution': dict(paragraph_counts), 'alias_count_distribution': dict(alias_counts),
                'input_tokens': summary([r['input_tokens'] for r in rows]), 'hard_key_components': components(rows)}
            indexed[split] = rows
    reports['official_train_dev_overlap'] = {field: overlaps(indexed['train'], indexed['dev'], field) for field in
        ('id','question_hash','component_ids','component_question_hashes','standalone_component_question_hashes','component_answer_hashes','support_hashes','context_hashes','final_answer_hash')}
    reports['cross_gold_to_visible_context'] = {}
    for a,b in (('train','dev'),('dev','train')):
        support = set(p for r in indexed[a] for p in r['support_hashes'])
        affected = [r['id'] for r in indexed[b] if support & set(r['context_hashes'])]
        reports['cross_gold_to_visible_context'][a+'_gold_in_'+b+'_context'] = {'rows':len(affected), 'example_ids':affected[:5]}
    reports['tokenization'] = {'tokenizer': str(TOKENIZER.relative_to(ROOT)),
        'tokenizer_sha256': hashlib.sha256(TOKENIZER.read_bytes()).hexdigest(),
        'special_tokens': False, 'truncation': False, 'scope': 'base task prompt only; no chat wrapper, output, reasoning or discussion history'}
    reports['limits'] = ['Exact normalized text and published component IDs only; semantic near-duplicates and pretraining contamination not ruled out.',
                         'Connected components use component IDs, standalone component question text (without #N references), supporting paragraph text and composed question; answer overlap is audited separately, not claimed absent.']
    (HERE / 'CORPUS_AUDIT.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(reports,ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
