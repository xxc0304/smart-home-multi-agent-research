"""Extract exact 019 records from author-published HiddenBench result files."""
import collections
import hashlib
import json
from pathlib import Path

base = Path(__file__).parent
files = {
    'gemini-2.5-pro': 'hidden_generated_gemini-2.5-pro.json',
    'gpt-4.1': 'hidden_generated_gpt-4.1.json',
}
result = {'scenario': 'city_storm_shelter_decision', 'reference_answer': 'Oakridge Library',
          'selection': 'all matching runs in each named author result file, original order', 'models': {}}
for expected_model, filename in files.items():
    path = base / filename
    raw = path.read_bytes()
    data = json.loads(raw.decode('utf-8'))
    matches = []
    for condition_i, condition in enumerate(data['conditions']):
        for run_i, run in enumerate(condition['runs']):
            if run.get('scenario') == result['scenario']:
                assert run.get('model') == expected_model
                matches.append({'condition_index': condition_i, 'source_run_index': run_i, 'run': run})
    distribution = collections.Counter(x['run'].get('majority_vote') for x in matches)
    result['models'][expected_model] = {
        'file': filename, 'sha256': hashlib.sha256(raw).hexdigest(),
        'source': 'https://huggingface.co/datasets/YuxuanLi1225/HiddenBench-results/resolve/main/paper/hidden_generated/' + filename,
        'matching_runs': len(matches), 'published_majority_vote_counts': dict(distribution), 'runs': matches,
    }
out = base / 'HIDDENBENCH_AUTHOR_019_EXTRACT.json'
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for model, value in result['models'].items():
    print(model, value['matching_runs'], value['published_majority_vote_counts'])
