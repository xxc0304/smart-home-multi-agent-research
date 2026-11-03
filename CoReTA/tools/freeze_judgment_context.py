"""Offline payload freezing and validation for the judgment-context diagnostic."""
import json
from pathlib import Path
from coreta.handoff.__main__ import PROJECT, load_counter
from coreta.handoff.gateway import write_json
from coreta.model_client import DeepSeekClient
from workboard_review_probe import hashes, read, output_schema

ROOT = PROJECT / 'refine-logs/judgment-context-design-20261023'
PREPARED = PROJECT / 'runs/judgment-context-prepared-20261024-r1'
ARMS = ('E', 'B', 'G', 'M')

def validate(prepared):
    prepared = Path(prepared)
    m = read(prepared / 'manifest.json')
    for key in ('source_hashes', 'payload_hashes'):
        if hashes(m[key]) != m[key]:
            raise ValueError('Frozen file mismatch: ' + key)
    cfg = m['config']
    if (cfg['base_url'] != 'https://api.deepseek.com' or cfg['model'] != 'deepseek-flash'
        or cfg['protocol']['transport_retries_per_request'] != 0
        or m['candidate_max_model_requests'] != 32 or m['candidate_max_output_tokens'] != 65536
        or len(m['calls']) != 32 or len(m['cases']) != 4):
        raise ValueError('Configuration or budget mismatch')
    source = read(ROOT / 'INPUTS_R3.json')
    expected = {(c['id'], a, r) for c in source['cases'] for a in ARMS for r in (1, 2)}
    if {(r['id'], r['condition'], r['repeat']) for r in m['calls']} != expected:
        raise ValueError('Schedule mismatch')
    client = DeepSeekClient(cfg, lambda *args: None, token_counter=load_counter())
    for case in source['cases']:
        if 'source_file' in case and hashes([case['source_file']])[case['source_file']] != case['source_sha256']:
            raise ValueError('Historical source changed')
        for a in ARMS:
            p = read(prepared / f"{case['id']}--{a}.json")
            packet = json.loads(p['instructions'].split('\nPACKET=', 1)[1].split('\nOUTPUT_SCHEMA=', 1)[0])
            wanted = dict(case['evidence'])
            if a != 'E':
                wanted['BEFORE'] = case['before']
            if a in ('G', 'M'):
                wanted['ADVICE'] = {'author': 'A2', 'text': case['good' if a == 'G' else 'bad']}
            if packet != wanted:
                raise ValueError('Unexpected information difference')
            schema = output_schema(p)
            if (p['max_output_tokens'] != 2048 or p['text']['format'] != {'type': 'json_object'}
                or set(schema['required']) != {'artifact', 'work_text'}
                or set(schema['properties']) != {'artifact', 'work_text'}
                or schema['additionalProperties'] is not False
                or not all(isinstance(v, str) for v in schema['properties']['artifact']['enum'])
                or client.size(p) > cfg['generation']['max_input_tokens']):
                raise ValueError('Output schema or context mismatch')
    for row in m['calls']:
        if row['payload_file'] != f"{row['id']}--{row['condition']}.json":
            raise ValueError('Payload routing mismatch')
    return m

def prepare():
    if PREPARED.exists():
        raise FileExistsError('Do not overwrite a frozen batch')
    data = read(ROOT / 'INPUTS_R3.json')
    cfg = read(PROJECT / 'config/deepseek_flash_inspection.json')
    cfg['protocol'] = {'transport_retries_per_request': 0, 'request_timeout_seconds': 120}
    client = DeepSeekClient(cfg, lambda *args: None, token_counter=load_counter())
    payloads = {}
    estimates = {}
    for item in data['inputs']:
        schema = item['output_schema']
        instructions = item['instructions'] + '\nPACKET=' + json.dumps(item['packet'], ensure_ascii=False) + '\nOUTPUT_SCHEMA=' + json.dumps(schema)
        p = client.payload(instructions, schema, 2048)
        p['text']['format'] = {'type': 'json_object'}
        p['input'] = 'Return exactly one JSON object with exactly artifact and work_text. artifact must be an allowed string ID. Put reasoning in work_text. No Markdown, extra keys or surrounding text.'
        name = f"{item['case']}--{item['condition']}.json"
        payloads[name] = p
        estimates[name] = client.size(p)
        if estimates[name] > cfg['generation']['max_input_tokens']:
            raise ValueError('Context exceeds budget')
    calls = []
    for repeat in (1, 2):
        for i, case in enumerate(data['cases']):
            order = ARMS[i:] + ARMS[:i]
            if repeat == 2:
                order = tuple(reversed(order))
            for a in order:
                calls.append({'id': case['id'], 'condition': a, 'repeat': repeat,
                              'payload_file': f"{case['id']}--{a}.json"})
    sources = [ROOT / 'INPUTS_R3.json', ROOT / 'PLAN.md', ROOT / 'RUBRIC.md',
               Path(__file__), PROJECT / 'tools/run_judgment_context.py',
               PROJECT / 'config/deepseek_flash_inspection.json',
               PROJECT / 'src/coreta/model_client.py', PROJECT / 'src/coreta/handoff/contracts.py',
               PROJECT / 'src/coreta/handoff/gateway.py', PROJECT / 'tools/workboard_review_probe.py']
    sources += [Path(c['source_file']) for c in data['cases'] if 'source_file' in c]
    PREPARED.mkdir(parents=True, exist_ok=False)
    for name, p in payloads.items():
        write_json(PREPARED / name, p)
    write_json(PREPARED / 'manifest.json', {'kind': 'judgment_context_diagnostic', 'config': cfg,
        'cases': [{'id': c['id'], 'origin': c['origin']} for c in data['cases']],
        'calls': calls, 'candidate_max_model_requests': 32, 'candidate_max_output_tokens': 65536,
        'actual_model_requests': 0, 'input_estimates': estimates,
        'source_hashes': hashes(sources), 'payload_hashes': hashes(PREPARED.glob('*.json'))})
    validate(PREPARED)
    print(json.dumps({'prepared': str(PREPARED), 'calls': len(calls),
                      'max_input_estimate': max(estimates.values()), 'actual_requests': 0}))

if __name__ == '__main__':
    prepare()
