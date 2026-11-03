"""Fixed-prefix, gold-side review packet; no inference or data modification."""
from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'data/external/musique-v1.0-20261030'


def rows(path):
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main():
    cases = []
    for role, n, ip, tp in (
        ('D', 8, SOURCE/'inputs/D_development.jsonl', SOURCE/'scoring/D_development.jsonl'),
        ('T', 12, ROOT/'data/expert-training-20261030-v1/train.inputs.jsonl',
         ROOT/'data/expert-training-20261030-v1/train.targets.jsonl')):
        inputs = rows(ip)[:n]
        targets = {r['id']: r for r in rows(tp)}
        for i, task in enumerate(inputs, 1):
            cases.append(dict(case=f'{role}{i:02d}', role=role, frozen_position=i,
                              input=task, target=targets[task['id']], source_input=str(ip.relative_to(ROOT))))
    selected = {c['input']['id']: c for c in cases}
    assert len(selected) == 20
    canonical_matches = 0
    with (SOURCE/'musique_ans_v1.0_train.jsonl').open(encoding='utf-8') as handle:
        for line_no, line in enumerate(handle, 1):
            raw = json.loads(line)
            if raw['id'] not in selected:
                continue
            case = selected[raw['id']]
            task = dict(id=raw['id'], question=raw['question'], paragraphs=[
                {k:p[k] for k in ('idx', 'title', 'paragraph_text')} for p in raw['paragraphs']])
            assert task == case['input']
            for key in ('answer', 'answer_aliases', 'answerable', 'question_decomposition'):
                assert raw[key] == case['target'][key]
            assert [{'idx':p['idx'], 'is_supporting':p['is_supporting']} for p in raw['paragraphs']] == case['target']['paragraphs']
            case.update(canonical_line=line_no, canonical_match=True)
            canonical_matches += 1
    manifest = json.loads((ROOT/'research/musique-data-preparation-20261030/SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
    expected = next(r['sha256'] for r in manifest['extracted'] if r['file']=='musique_ans_v1.0_train.jsonl')
    with (SOURCE/'musique_ans_v1.0_train.jsonl').open('rb') as handle:
        actual = hashlib.file_digest(handle, 'sha256').hexdigest()
    assert actual == expected and canonical_matches == 20
    result = dict(date='2026-10-31', kind='GOLD_SIDE_REVIEW_ONLY_NEVER_MODEL_INPUT',
        selection='Frozen first 8 D rows and first 12 training-export rows; cumulative audit cap.',
        source_manifest='research/musique-data-preparation-20261030/SOURCE_MANIFEST.json',
        original_train_matches_registered_digest=True, canonical_matches=canonical_matches,
        cases=cases, experimental_model_calls=0, training_runs=0, H_content_used=0)
    (HERE/'CASE_PACKET_GOLD_SIDE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(n_cases=len(cases),canonical_matches=canonical_matches,
                         registered_digest_match=actual==expected)))


if __name__ == '__main__':
    main()
