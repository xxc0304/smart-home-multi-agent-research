"""Read historical pre-TRY packets and audit a field projection; no model/network."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'refine-logs/evidence-before-application-20261024'
HISTORY = ROOT / 'runs/workboard-d0-natural-live-20261022-r2'
PACKS = ROOT / 'data/task-packs/hiddenbench-workboard-dev-v1'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def audit():
    rows = []
    sources = {}
    for task in ('hb-dev-004-r1-c1', 'hb-dev-034-r1-c2'):
        for variant in ('v3_continuation', 'd0_continuation'):
            path = HISTORY / task / variant / 'requests.jsonl'
            sources[str(path)] = digest(path)
            for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                request = json.loads(line)
                ins = request.get('payload', {}).get('instructions', '')
                if 'PACKET=' not in ins:
                    continue
                packet = json.JSONDecoder().raw_decode(ins.split('PACKET=', 1)[1])[0]
                if packet.get('STAGE') != 'TRY':
                    continue
                selected = packet['TARGET_OFFER']
                auditor = next(a for a in packet['SELF']['team']
                               if a not in (packet['SELF']['agent_id'], selected['author']))
                member_path = PACKS / task[:10] / 'packets/distributed' / f'{auditor}.json'
                member = read(member_path)
                sources[str(member_path)] = digest(member_path)
                evidence = []
                for offer in packet['PUBLIC_EVIDENCE']:
                    for n, support in enumerate(offer['support']):
                        evidence.append({'carrier': offer['ref'], 'author': offer['author'],
                                         'support_index': n, 'reported_ref': support['ref'],
                                         'text': support['excerpt'],
                                         'access': 'published_excerpt_not_original_access'})
                view = {'TASK': packet['TASK'], 'SELF': member['SELF'],
                        'SELF_MATERIALS': member['SELF_MATERIALS'], 'PUBLIC_EXCERPTS': evidence}
                raw = json.dumps(view, ensure_ascii=False)
                works = json.dumps(packet['CANDIDATES'], ensure_ascii=False)
                # Literal probes describe text visibility only, never semantic correctness.
                probes = {s: {'in_projection': s in raw, 'in_visible_work_history': s in works}
                          for s in ('making Pine Retreat dangerous', 'less than 30 years old',
                                    'guilty person is a man', 'son is described as a passenger')}
                rows.append({'history': task, 'variant': variant, 'request_line': line_no,
                    'editor': packet['SELF']['agent_id'], 'provider': selected['author'],
                    'auditor': auditor, 'selected_offer': selected,
                    'public_offer_ids_at_time': [o['ref'] for o in packet['PUBLIC_EVIDENCE']],
                    'field_projection_not_approved_input': view,
                    'omitted_public_content': [{'ref': o['ref'], 'knowledge': o['knowledge'],
                                                'proposed_use': o['proposed_use']}
                                               for o in packet['PUBLIC_EVIDENCE']],
                    'literal_visibility_probes': probes,
                    'has_autonomous_claim_list': 'claims' in selected,
                    'readiness': 'not_ready_semantic_coverage_unverified'})
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'VIEW_AUDIT.json'
    if target.exists():
        raise FileExistsError('Do not overwrite audit')
    target.write_text(json.dumps({'scope': 'four pre-TRY snapshots, no future evidence',
         'new_model_requests': 0, 'source_hashes': sources, 'rows': rows},
         ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([{'history': r['history'], 'variant': r['variant'], 'auditor': r['auditor'],
                      'original_refs': [s['ref'] for s in r['field_projection_not_approved_input']['SELF_MATERIALS']],
                      'public_excerpt_count': len(r['field_projection_not_approved_input']['PUBLIC_EXCERPTS']),
                      'visibility': r['literal_visibility_probes']} for r in rows], ensure_ascii=False))

if __name__ == '__main__':
    audit()
