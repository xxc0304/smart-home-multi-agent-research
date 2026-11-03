"""Check extraction fidelity and annotation workflow boundaries; no human labels inferred."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
from build_annotation_pack import DATA, HERE, ROOT, SEED, REVIEW, TASKS
from validate_human_records import validate, citation, pointer


def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest=read(HERE/'PACK_MANIFEST.json')
    for item in manifest['source_files']+manifest['files']:
        assert sha(ROOT/item['path'])==item['sha256'],item['path']
    assert sha(HERE/'build_annotation_pack.py')==manifest['build_script_sha256']
    assert sha(HERE/'CODEBOOK.md')==manifest['codebook_sha256']
    source={r['id']:r for r in read(SEED)['cases']}
    admin=read(HERE/'admin/CASE_MAPPING_AND_PRIOR_REVIEW.json')
    assert sha(HERE/'admin/CASE_MAPPING_AND_PRIOR_REVIEW.json')==manifest['admin_mapping_sha256']
    canonical={int(t['id']):t for t in read(TASKS)}
    author_cache={}
    local=author=0
    for mapping in admin['cases']:
        cid=mapping['case_id'];case=source[mapping['original_case_id']]
        a,b,c=[read(DATA/'participant/cases'/cid/(p+'.json')) for p in 'ABC']
        assert all(k not in a for k in ('correct_answer','rationale','reference_score','finding'))
        assert a['hidden_information']==canonical[int(case['task'])]['hidden_information']
        assert c['benchmark_reference_answer']==canonical[int(case['task'])]['correct_answer']
        serialized=json.dumps(b,ensure_ascii=False)
        for key in ('reference_match','reference_score','interpretation_boundary','"finding"','expertise_status'):
            assert key not in serialized,(cid,key)
        if case.get('records'):
            assert len(b['records'])==len(case['records'])
            for src,event in zip(case['records'],b['records']):
                assert event['input']['parsed_packet']==src['packet']
                assert event['input']['instructions']==src['request_payload']['instructions']
                assert event['input']['input']==src['request_payload']['input']
                assert event['input']['response_format']==src['request_payload'].get('text')
                assert event['output']==json.loads(src['raw_text']) and event['raw_output']==src['raw_text']
                located=next(r for r in mapping['events'] if r['event_id']==event['event_id'])
                assert sha(ROOT/located['source_raw'])==located['source_raw_sha256']
                req=json.loads((ROOT/located['request_file']).read_text(encoding='utf-8').splitlines()[located['request_line']-1])
                assert req['payload']==src['request_payload']
                local+=1
        else:
            original=author_cache.setdefault(case['source_file'],read(ROOT/case['source_file']))
            prefix=f"/conditions/{case['condition_index']}/runs/{case['source_run_index']}"
            assert pointer(original,prefix)==case['run']
            for event,event_map in zip(b['records'],mapping['events']):
                src=pointer(original,event_map['author_pointer'])
                if event['stage']=='published_initial_vote':assert event['output']==src
                else:
                    assert event['input']['prompt']==src['prompt']
                    assert event['output']==src['response']
                author+=1
            assert b['recorded_round_votes']==[{'round':r['round'],'votes':r.get('votes')} for r in case['run']['rounds']]
    # Every previous evidence event still has a source; old interpretations stay in admin.
    evidence_events=0
    seed=read(SEED)
    for case in read(REVIEW)['cases']:
        for event in case['observations']:
            value=pointer(seed,event['seed_pointer']) if 'seed_pointer' in event else pointer(author_cache.setdefault(event['original_file'],read(ROOT/event['original_file'])),event['original_pointer'])
            assert event['matched_fragment'].casefold() in value.casefold()
            evidence_events+=1
    # Templates remain drafts. Falsely declaring empty forms complete is rejected.
    drafts=0
    for path in (DATA/'templates').rglob('*.json'):
        form=read(path);assert validate(form)['status']=='DRAFT_NOT_COUNTED';drafts+=1
    sample=read(DATA/'templates/reviewer_A/S01.json')
    sample['completion_status']='COMPLETE'
    try:validate(sample)
    except ValueError: rejected_blank_complete=True
    else:raise AssertionError('Empty form counted complete')
    docs={p:read(DATA/'participant/cases/S01'/(p+'.json')) for p in 'ABC'}
    good={'document':'A','pointer':'/description','quote':docs['A']['description'][:40]}
    citation(good,docs,{'A'})
    bad=deepcopy(good);bad['quote']='__NOT_PRESENT_CITATION_FIXTURE__'
    try:citation(bad,docs,{'A'})
    except ValueError: rejected_quote=True
    else:raise AssertionError('Invented quote accepted')
    later={'document':'C','pointer':'/benchmark_reference_answer','quote':docs['C']['benchmark_reference_answer']}
    try:citation(later,docs,{'A'})
    except ValueError: rejected_later=True
    else:raise AssertionError('A accepts C citation')
    result={'date':'2026-10-30','status':'PASS_MATERIAL_PREPARATION_ONLY','case_units':8,'unique_tasks':7,
       'local_events_exact':local,'author_events_exact':author,'previous_evidence_events_located':evidence_events,
       'blank_templates_verified_not_counted':drafts,'false_empty_completion_rejected':rejected_blank_complete,
       'invented_quote_rejected':rejected_quote,'later_stage_citation_in_A_rejected':rejected_later,
       'new_model_calls':0,'training_runs':0,'human_annotations_completed':0,'human_agreement':None,
       'review_type':'assistant self-check; no human annotation or independent advisor review',
       'remaining':['Human independent pilot and adjudication pending.',
                    'Masking is partial; prior exposure and protocol cues remain.',
                    'Old cases support information-contribution analysis, not demonstrated calibrated capability.',
                    'Case selection is purposive; no mechanism prevalence or causal effect estimated.']}
    (HERE/'STAGE_CHECKS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
