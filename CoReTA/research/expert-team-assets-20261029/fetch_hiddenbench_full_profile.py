"""Fetch two official public full-profile result files and inspect their fields."""
import json
from collections import Counter
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
TARGET = HERE.parent.parent / 'data/external/hiddenbench-results-20261029'
BASE = 'https://huggingface.co/datasets/YuxuanLi1225/HiddenBench-results/resolve/main/'
FILES = ['paper/full_profile/full_profile_gemini-2.5-pro.json',
         'paper/full_profile/full_profile_gpt-4.1.json']


def download(relative, target, expected=None):
    if target.exists() and (expected is None or target.stat().st_size == expected):
        return
    partial = target.with_suffix(target.suffix + '.part')
    request = urllib.request.Request(BASE + relative, headers={'User-Agent': 'CoReTA-asset-audit/1.0'})
    total = 0
    with urllib.request.urlopen(request, timeout=60) as response, partial.open('wb') as output:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            total += len(block)
            if total > (expected or 1024 * 1024) + 1024:
                raise ValueError('Response exceeds expected public asset size')
            output.write(block)
    if expected is not None and total != expected:
        raise ValueError('File size differs from official manifest')
    partial.replace(target)


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    download('MANIFEST.json', TARGET / 'MANIFEST.json')
    manifest = json.loads((TARGET / 'MANIFEST.json').read_text(encoding='utf-8'))
    findings = []
    for relative in FILES:
        entry = next(item for item in manifest['files'] if item['path'] == relative)
        target = TARGET / Path(relative).name
        download(relative, target, entry['bytes'])
        value = json.loads(target.read_text(encoding='utf-8'))
        runs = [run for condition in value['conditions'] for run in condition['runs']]
        findings.append({'source_url': BASE + relative, 'file': str(target), 'bytes': target.stat().st_size,
                         'run_count': len(runs), 'unique_scenarios': len({r['scenario'] for r in runs}),
                         'round_count_distribution': dict(Counter(len(r['rounds']) for r in runs)),
                         'all_members_special_in_every_run': all(r['num_agents'] == r['num_special'] for r in runs),
                         'run_keys': sorted(set().union(*(r.keys() for r in runs))),
                         'condition_metadata': [{k: v for k, v in c.items() if k != 'runs'} for c in value['conditions']],
                         'first_run': runs[0]})
    (HERE / 'HIDDENBENCH_FULL_PROFILE_AUDIT.json').write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([{k: v for k, v in item.items() if k not in ('first_run', 'condition_metadata')} for item in findings], ensure_ascii=True))


if __name__ == '__main__':
    main()
