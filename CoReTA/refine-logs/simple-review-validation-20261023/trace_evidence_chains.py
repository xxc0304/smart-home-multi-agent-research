"""Offline extraction of existing artifacts; never imports a model client."""
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
HISTORY = PROJECT / 'runs/workboard-d0-natural-live-20261022-r2'
REPLAY = PROJECT / 'runs/simple-review-live-20261023-r2'
OUT = Path(__file__).parent
files = {}


def read(path):
    files[str(path.relative_to(PROJECT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path):
    files[str(path.relative_to(PROJECT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]


def node(path, pointer, value, phase):
    return {'path': str(path.relative_to(PROJECT)), 'pointer': pointer,
            'phase': phase, 'raw_value': value}


def originals(task):
    result = []
    for member in ('A1', 'A2', 'A3'):
        path = PROJECT / f'data/task-packs/hiddenbench-workboard-dev-v1/{task}/packets/distributed/{member}.json'
        p = read(path)
        result.append(node(path, '/SELF_MATERIALS', p['SELF_MATERIALS'], 'original_material'))
    return result


chains = []
for task in ('hb-dev-034-r1-c2', 'hb-dev-004-r1-c1'):
    for system in ('v3_continuation', 'd0_continuation'):
        folder = HISTORY / task / system
        state_path = folder / 'state.json'
        state = read(state_path)
        stage_path = folder / 'stages.jsonl'
        stages = lines(stage_path)
        request_path = folder / 'requests.jsonl'
        requests = lines(request_path)
        first_packet = json.loads(requests[0]['payload']['instructions'].split('\nPACKET=', 1)[1].split('\nOUTPUT_SCHEMA=', 1)[0])
        # W4/W5 and O3/O4 may be historical checkpoint inputs, not generated in this run.
        seeded_works = {w['id'] for w in first_packet.get('CANDIDATES', [])}
        seeded_offers = {o['ref'] for o in first_packet.get('PUBLIC_EVIDENCE', [])}
        nodes = originals(task[:10])
        for kind, key in [('works', 'id'), ('offers', 'ref')]:
            seeded = seeded_works if kind == 'works' else seeded_offers
            for i, value in enumerate(state[kind]):
                if value[key] in seeded:
                    nodes.append(node(state_path, f'/{kind}/{i}', value, 'checkpoint_history'))
        for i, row in enumerate(stages, 1):
            nodes.append(node(stage_path, f'JSONL line {i}', row, 'historical_continuation_generated'))
            if row['stage'] in ('TRY', 'CHECK_USE', 'CHECK_EFFECT', 'CHOOSE'):
                matching = [r for r in requests if r['call_context']['logical_call'] == row['call_context']['logical_call']]
                assert len(matching) == 1
                packet = json.loads(matching[0]['payload']['instructions'].split('\nPACKET=', 1)[1].split('\nOUTPUT_SCHEMA=', 1)[0])
                nodes.append(node(request_path, f"logical_call={row['call_context']['logical_call']}/PACKET/SELF_MATERIALS",
                                  {'self': packet['SELF'], 'materials': packet['SELF_MATERIALS']},
                                  'historical_stage_access'))
        result_path = folder / 'result.json'
        result = read(result_path)
        assert result['selected_work_id'] == state['current']
        nodes.append(node(result_path, '/selected_work_id', result['selected_work_id'], 'historical_selection'))
        chains.append({'id': task + '--' + system, 'selected_work_id': result['selected_work_id'],
                       'selected_artifact': result['selected_work']['artifact'], 'nodes': nodes})

replay_rows = lines(REPLAY / 'stages.jsonl')
illustrations = []
for n in (7, 13, 14, 25, 26, 27, 30, 31, 32):
    r = replay_rows[n - 1]
    assert r['call_context']['logical_call'] == n
    illustrations.append(node(REPLAY / 'stages.jsonl', f'JSONL line {n}', r, 'fixed_review_replay_only_no_downstream_selection'))

guidance = PROJECT / 'src/coreta/workboard/provenance.py'
files[str(guidance.relative_to(PROJECT))] = hashlib.sha256(guidance.read_bytes()).hexdigest()
assert 'not its inaccessible original ID' in guidance.read_text(encoding='utf-8')

# Verify the important correction: the S01 owner is present with its original at CHOOSE.
for chain in chains:
    if chain['id'].startswith('hb-dev-034'):
        accesses = [n['raw_value'] for n in chain['nodes'] if n['phase'] == 'historical_stage_access']
        assert all(a['self']['agent_id'] == 'A1' for a in (accesses[0], accesses[-1]))
        assert all(any(m['ref'] == 'S01' and 'making Pine Retreat dangerous' in m['content']
                       for m in a['materials']) for a in (accesses[0], accesses[-1]))

document = {'kind': 'offline_existing_evidence_trace',
            'scope': 'four historical continuations and selected current replay observations',
            'new_model_requests': 0, 'source_hashes': files, 'chains': chains,
            'replay_illustrations': illustrations,
            'caveat': 'Historical continuation and new fixed-review replay are distinct. Replay outputs were not fed into historical selection. Checkpoint history is not newly generated here. Extraction verifies provenance, not every semantic judgment.'}
(OUT / 'EVIDENCE_CHAINS_R2.json').write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'chains': len(chains), 'replay_illustrations': len(illustrations), 'new_model_requests': 0}))
