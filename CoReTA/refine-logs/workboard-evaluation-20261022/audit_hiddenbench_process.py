"""Offline extraction only. Semantic findings are authored separately from this index."""
from pathlib import Path
import hashlib
import json
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'runs/hiddenbench-development-live-20261022-r1'
OUT = Path(__file__).parent / 'hiddenbench-process-audit'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def main():
    OUT.mkdir(exist_ok=True)
    index = {'kind': 'offline_process_extraction_not_semantic_validation', 'pairs': [], 'source_hashes': {},
             'request_identity_checks': [], 'summary': {}}
    transitions, check_findings, selections, totals = Counter(), Counter(), Counter(), Counter()
    for pair in sorted(RUN.glob('hb-dev-*')):
        task_id = pair.name.rsplit('-r', 1)[0]
        ep = ROOT / 'data/task-packs/hiddenbench-workboard-dev-v1' / task_id / 'offline/evaluation.json'
        gold = read(ep)['correct_option_id']
        row = {'pair': pair.name, 'gold': gold, 'methods': {}}
        for method in ['coreta_workboard', 'ordinary_discussion']:
            folder = pair / method
            state, result = read(folder / 'state.json'), read(folder / 'result.json')
            stages = lines(folder / 'stages.jsonl')
            events = lines(folder / 'events.jsonl')
            for request in lines(folder / 'requests.jsonl'):
                packet = json.loads(request['payload']['instructions'].split('\nPACKET=', 1)[1].rsplit('\nOUTPUT_SCHEMA=', 1)[0])
                expected_member = request['call_context']['member']
                expected_direct = sorted({'T', *(m['ref'] for m in packet['SELF_MATERIALS'])})
                identity_ok = packet['SELF']['agent_id'] == expected_member
                access_ok = sorted(packet['SOURCE_ACCESS']['direct_original_refs']) == expected_direct
                if not identity_ok or not access_ok:
                    raise ValueError(f'Identity/access mismatch: {pair.name}/{method}')
                index['request_identity_checks'].append({'pair': pair.name, 'method': method,
                    'logical_call': request['call_context']['logical_call'], 'member': expected_member,
                    'self_matches_call': identity_ok, 'access_matches_materials': access_ok})
            works = {w['id']: w for w in state['works']}
            timeline = []
            for e in events:
                if e['kind'] in {'trial_created', 'final_proposal', 'final_selection', 'offer_adopted', 'offer_not_adopted', 'selection_unchanged'}:
                    timeline.append(e)
            cycles = []
            for f in state['feedback']:
                if f['kind'] != 'application_feedback':
                    cycles.append(f)
                    continue
                b, a, c = f['before'], f['after'], f['decision']['candidate_id']
                cycles.append({
                    'offer': f['offer']['ref'], 'provider': f['offer']['author'],
                    'before': b, 'trial': a, 'chosen': c,
                    'before_correct': works[b]['artifact'] == gold,
                    'trial_correct': works[a]['artifact'] == gold,
                    'chosen_correct': works[c]['artifact'] == gold,
                    'checks': [{'stage': x['stage'], 'member': x['member'], 'finding': x['finding']} for x in f['checks']],
                })
                if method == 'coreta_workboard':
                    transitions[f"{int(works[b]['artifact'] == gold)}->{int(works[a]['artifact'] == gold)}"] += 1
                    selections['trial' if c == a else 'old'] += 1
            row['methods'][method] = {
                'editor': state['editor'], 'final_id': result['selected_work_id'],
                'final_correct': result['artifact'] == gold,
                'stage_counts': dict(Counter(s['stage'] for s in stages)),
                'works': [{'id': w['id'], 'author': w['author'], 'artifact': w['artifact'],
                           'correct': w['artifact'] == gold, 'initial': w['initial']} for w in state['works']],
                'cycles': cycles,
                'closing': [s for s in stages if s['stage'] in {'FINALIZE', 'FINAL_CHOOSE'}],
                'timeline': timeline,
            }
            if method == 'coreta_workboard':
                check_findings.update(f"{c['stage']}:{c['finding']}" for c in state['checks'])
                totals['cycles'] += len(cycles)
                totals['post_initial_calls'] += len(stages)
                totals['closing_calls'] += sum(s['stage'].startswith('FINAL') for s in stages)
                last = cycles[-1]['chosen'] if cycles else state['initials'][state['editor']]
                totals['closing_changed_answer'] += int(works[last]['artifact'] != result['artifact'])
                totals['finalize_reuse'] += sum(s['stage'] == 'FINALIZE' and s['output']['action'] == 'reuse' for s in stages)
            bundle = {'pair': pair.name, 'method': method, 'gold_offline_only': gold,
                      'state': state, 'stages': stages, 'events': events, 'final': result['selected_work_id']}
            (OUT / f'{pair.name}-{method}.json').write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding='utf-8')
            for p in [folder / 'state.json', folder / 'stages.jsonl', folder / 'events.jsonl', folder / 'result.json', folder / 'requests.jsonl', ep]:
                index['source_hashes'][str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ep.parent.parent / 'packets/distributed').glob('*.json'):
            index['source_hashes'][str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
        index['pairs'].append(row)
    index['summary'] = {'trial_exact_transitions': dict(transitions), 'cycle_selections': dict(selections),
                        'check_findings_not_validity': dict(check_findings), **dict(totals)}
    (OUT / 'PROCESS_INDEX.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
    for p in index['pairs']:
        c, d = p['methods']['coreta_workboard'], p['methods']['ordinary_discussion']
        print(p['pair'], 'coreta', c['final_id'], c['final_correct'], 'ordinary', d['final_id'], d['final_correct'])
        print(' cycles', [(x['offer'], x['before'], x['trial'], x['chosen'], x['before_correct'], x['trial_correct'], x['chosen_correct']) for x in c['cycles'] if 'trial' in x])
        print(' closure', [(x['stage'], x['output'].get('action'), x['output'].get('candidate_id')) for x in c['closing']])


if __name__ == '__main__':
    main()
