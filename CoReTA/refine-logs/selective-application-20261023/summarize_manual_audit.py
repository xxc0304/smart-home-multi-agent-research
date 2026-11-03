"""Summarize executor's explicit manual labels for this one already-read batch only."""
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parent
RUN = PROJECT / 'runs/selective-application-live-20261023-r1'
PREPARED = PROJECT / 'runs/selective-application-prepared-20261023-r2'
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
lines = lambda name: [json.loads(s) for s in (RUN / name).read_text(encoding='utf-8').splitlines()]
stages, requests, responses = map(lines, ('stages.jsonl', 'requests.jsonl', 'responses.jsonl'))
manifest, progress = read(RUN / 'manifest.json'), read(RUN / 'progress.json')
assert len(stages) == len(requests) == len(responses) == 24
assert progress['status'] == 'completed' and progress['unknown_usage_attempts'] == 0
for field in ('source_hashes', 'payload_hashes'):
    for path, digest in manifest[field].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest

# Labels assigned after the executor read all24 outputs. These are NOT a semantic classifier.
FAILED = {1, 2, 3, 4, 13, 14, 15, 16}
EXPECTED = {'application-004': 'option_3', 'application-034': 'option_2',
            'update-mixed': 'Elm', 'joint-mixed': 'P',
            'all-supported': 'River', 'all-unsupported': 'Oak'}
NOTES = {
    'application-004': 'Uses car constraint to exclude Z, but accepts unsupported passenger claim, '
                       'selects father despite age clue, and conflates car-owner alcohol with driver evidence.',
    'application-034': 'Adds communication resources and retains option_2, but explicitly denies '
                       'that S01 reported Pine dangerous and accepts the false correction.',
    'update-mixed': 'Applies explicit reopening and capacity while rejecting false Birch closure.',
    'joint-mixed': 'Combines blue and circular requirements while rejecting only-blue assertion.',
    'all-supported': 'Uses accessibility and radio information without rejecting supported contribution.',
    'all-unsupported': 'Preserves feasible larger room and rejects both unsupported changes.',
}
rows = []
for index, (stage, request, response) in enumerate(zip(stages, requests, responses), 1):
    context, value = stage['call_context'], stage['output']
    case = context['id']
    assert context == request['call_context'] == response['call_context']
    assert request['payload'] == read(PREPARED / context['payload_file'])
    usage = response['response']['usage']
    assert response['response']['status'] == 'completed' and usage['output_tokens'] <= 2048
    rows.append({'logical_call': index, 'case': case, 'condition': context['condition'],
                 'repeat': context['repeat'], 'artifact': value['artifact'],
                 'expected_artifact': EXPECTED[case],
                 'artifact_correct': value['artifact'] == EXPECTED[case],
                 'semantic_full_pass': index not in FAILED,
                 'useful_part_applied': None if case == 'all-unsupported' else True,
                 'bad_part_avoided': None if case == 'all-supported' else index not in FAILED,
                 'manual_note': NOTES[case], 'stage_output': value, 'usage': usage})

def aggregate(selected):
    return {'n': len(selected), 'artifact_correct': sum(r['artifact_correct'] for r in selected),
            'semantic_full_pass': sum(r['semantic_full_pass'] for r in selected),
            'input_tokens': sum(r['usage']['input_tokens'] for r in selected),
            'output_tokens': sum(r['usage']['output_tokens'] for r in selected)}

summary = {}
for arm in ('F', 'K'):
    selected = [r for r in rows if r['condition'] == arm]
    summary[arm] = aggregate(selected)
    summary[arm]['cases'] = {case: aggregate([r for r in selected if r['case'] == case])
                             for case in EXPECTED}
report = {'annotation': 'executor_manual_read_all24_not_independent_or_blind',
          'manual_failed_call_ids': sorted(FAILED),
          'source_stage_sha256': hashlib.sha256((RUN / 'stages.jsonl').read_bytes()).hexdigest(),
          'summary': summary, 'rows': rows}
(ROOT / 'SEMANTIC_AUDIT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
