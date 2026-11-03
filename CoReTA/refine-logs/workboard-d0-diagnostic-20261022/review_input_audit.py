"""Offline extraction of actual checker access; no client, scoring or network imports."""
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT / 'runs/workboard-d0-natural-live-20261022-r2'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    rows = []
    for task in ['hb-dev-004-r1-c1', 'hb-dev-034-r1-c2']:
        for system in ['v3_continuation', 'd0_continuation']:
            folder = ROOT / task / system
            requests = folder / 'requests.jsonl'
            stages = folder / 'stages.jsonl'
            outputs = {r['call_context']['logical_call']: r
                       for r in map(json.loads, stages.read_text(encoding='utf-8').splitlines())}
            for r in map(json.loads, requests.read_text(encoding='utf-8').splitlines()):
                ctx = r['call_context']
                if ctx['stage'] not in ['CHECK_USE', 'CHECK_EFFECT']:
                    continue
                prompt = r['payload']['instructions']
                packet = json.loads(prompt.split('\nPACKET=', 1)[1].split('\nOUTPUT_SCHEMA=', 1)[0])
                rows.append({
                    'task': task, 'system': system, 'call_context': ctx,
                    'request_file': str(requests.relative_to(PROJECT)),
                    'request_sha256': digest(requests),
                    'stage_file': str(stages.relative_to(PROJECT)),
                    'stage_sha256': digest(stages),
                    'self': packet['SELF'],
                    'direct_original_refs': packet['SOURCE_ACCESS']['direct_original_refs'],
                    'self_materials': packet['SELF_MATERIALS'],
                    'before': packet['BEFORE']['id'], 'after': packet['AFTER']['id'],
                    'input_fields': sorted(packet),
                    'prompt_characters_not_tokens': len(prompt),
                    'has_use_record': packet.get('USE_RECORD') is not None,
                    'output_cap': r['payload']['max_output_tokens'],
                    'output': outputs[ctx['logical_call']]['output'],
                })
    result = {'kind': 'offline_actual_checker_input_audit', 'http_calls': 0,
              'semantic_labels_automatic': False, 'rows': rows}
    target = Path(__file__).with_name('REVIEW_INPUT_AUDIT.json')
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(target), 'checker_inputs': len(rows), 'http_calls': 0}))


if __name__ == '__main__':
    main()
