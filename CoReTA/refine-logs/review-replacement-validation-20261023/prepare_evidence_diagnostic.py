"""Offline visible-evidence extraction; hand-selected diagnostic excerpts are not autonomous retrieval."""
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
PREPARED = PROJECT / 'runs/review-replacement-prepared-20261023-r1'
LIVE = PROJECT / 'runs/review-replacement-live-20261023-r1'


def main():
    manifest = json.loads((PREPARED/'manifest.json').read_text(encoding='utf-8'))
    rows = []
    for item in manifest['inputs']:
        if '034' not in item['task']:
            continue
        payload = json.loads((PREPARED/(item['id']+'--B.json')).read_text(encoding='utf-8'))
        packet = json.loads(payload['instructions'].split('\nPACKET=',1)[1].split('\nOUTPUT_SCHEMA=',1)[0])
        old, new = packet['BEFORE'], packet['AFTER']
        # This is a human-chosen diagnostic target, not a general evidence locator.
        start = old['work_text'].index('My own direct original S01')
        end = old['work_text'].index('Cedar Station is therefore', start)
        old_excerpt = old['work_text'][start:end].strip()
        if item['system'] == 'd0_continuation':
            start = new['work_text'].index('Pine Retreat (option_3) is rejected')
            end = new['work_text'].index('I also preserve', start)
        else:
            start = new['work_text'].index('Second, the plume:')
            end = new['work_text'].index('I restore', start)
        new_excerpt = new['work_text'][start:end].strip()
        fields = [k for k,v in packet.items()
                  if 'making Pine Retreat dangerous' in json.dumps(v,ensure_ascii=False)]
        rows.append({'input_id': item['id'], 'system': item['system'], 'stage': item['stage'],
            'checker': packet['SELF']['agent_id'],
            'direct_original_refs': packet['SOURCE_ACCESS']['direct_original_refs'],
            'key_sentence_visible_in_packet_fields': fields,
            'human_selected_public_excerpts': [
                {'version': old['id'], 'author': old['author'], 'field': 'work_text',
                 'access': 'visible_public_report_not_S01_original', 'text': old_excerpt},
                {'version': new['id'], 'author': new['author'], 'field': 'work_text',
                 'access': 'visible_public_report_not_S01_original', 'text': new_excerpt}],
            'safety_control': {'version': old['id'],
                'text': 'it is not in the reported northward plume path',
                'object': 'Cedar Station',
                'source': 'exact substring of same BEFORE work_text',
                'visible': 'it is not in the reported northward plume path' in old['work_text']}})
    outputs = []
    for line in (LIVE/'stages.jsonl').read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        if '034' not in row['call_context']['task']:
            continue
        text = row['output']['observation']+' '+row['output']['scope']
        outputs.append({**row['call_context'],
            'contains_danger_word_lexical_only_not_semantic_score': bool(re.search('danger',text,re.I)),
            'explicit_Pine_danger_report_discussed_manual': False})
    result = {'kind': 'offline_evidence_visibility_diagnostic', 'http_calls': 0,
        'human_chosen_target': True, 'original_private_materials_shared': False,
        'original_artifacts_modified': False, 'inputs': rows, 'outputs': outputs,
        'interpretation_limit': 'Visibility and output omission do not prove an attention or retrieval cause.'}
    target = Path(__file__).with_name('EVIDENCE_VISIBILITY_DIAGNOSTIC.json')
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'inputs':len(rows),'outputs':len(outputs),'all_key_sentences_visible':all(r['key_sentence_visible_in_packet_fields'] for r in rows),'all_excerpts_nonempty':all(x['text'] for r in rows for x in r['human_selected_public_excerpts']),'http_calls':0}))


if __name__ == '__main__':
    main()
