"""Verify the produced offline package, real-data isolation and non-result labels."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import json
import sys
from prepare_expert_mechanism import DATA,HERE,ROOT,MUSIQUE,read,readl,write
from expert_mechanism_protocol import ARMS,ACTORS,APPLICATION_CUE,GENERIC_CUE,render_replay,load_frozen_bundle,ProtocolError


def unpack(row):
    user=row['payload']['user']
    assert user.startswith('TASK_DATA\n')
    return json.loads(user[len('TASK_DATA\n'):].split('\nREVIEW_INSTRUCTION\n',1)[0])


def main():
    independent=readl(DATA/'independent_inputs.jsonl')
    pending=readl(DATA/'pending_replay_dependencies.jsonl')
    demos=readl(DATA/'demos/HAND_AUTHORED_replay_inputs.jsonl')
    semantic=readl(DATA/'demos/HAND_AUTHORED_semantic_replay_inputs.jsonl')
    inputs={r['id']:r for split in ('C_calibration','D_development') for r in readl(MUSIQUE/'inputs'/(split+'.jsonl'))}
    first_d=readl(MUSIQUE/'inputs/D_development.jsonl')[:8]
    assert len(independent)==352 and len(pending)==56 and len(demos)==56 and len(semantic)==7
    ids=[r['request_id'] for r in independent]
    assert len(set(ids))==352
    for row in independent:
        data=unpack(row);origin=inputs[row['task_id']]
        assert data=={k:origin[k] for k in ('question','paragraphs')}
        assert row['task_id'] not in row['payload']['user']
        assert row['backend'] is None and row['execution_allowed'] is False
        assert row['payload']['response_schema']['properties']['support_idxs']['items']['enum']==[p['idx'] for p in origin['paragraphs']]
    for row in pending:
        assert row['payload'] is None and row['status']=='WAITING_FOR_ACTUAL_FROZEN_INITIAL_OUTPUTS'
        assert set(row['depends_on'])<=set(ids) and len(row['depends_on'])==4
    by_task={}
    for row in demos+semantic:
        assert row['execution_allowed'] is False and row['initial_bundle_kind']=='HAND_AUTHORED_PIPELINE_FIXTURE'
        data=unpack(row);origin=inputs[row['task_id']]
        assert data==row['task_data']
        assert data['question']==origin['question'] and data['paragraphs']==origin['paragraphs']
        assert set(data)<= {'question','paragraphs','previous_answer','messages','citation_locators'}
        for locator in data.get('citation_locators',[]):
            source=next(p for p in origin['paragraphs'] if p['idx']==locator['idx'])
            assert locator['idx']==source['idx'] and locator['title']==source['title']
            assert set(locator)=={'idx','title','reported_by'}
            for sender in locator['reported_by']:
                msg=next(m for m in data['messages'] if m['sender']==sender)
                assert locator['idx'] in msg['output']['support_idxs']
    # Inspect each seven-condition block: only the declared sources/cue/message differences.
    for family in (demos,semantic):
        for tid in {r['task_id'] for r in family}:
            rows={r['condition']:r for r in family if r['task_id']==tid}
            assert set(rows)==set(ARMS)
            baseline=unpack(rows['C00'])
            for arm,row in rows.items():
                data=unpack(row)
                assert data['previous_answer']==baseline['previous_answer']
                if arm in ('N0','N1'):assert data['messages']==[]
                else:assert data['messages']==baseline['messages']
                expected=deepcopy(baseline)
                if arm in ('N0','N1'):expected['messages']=[]
                if arm in ('C10','C11'):expected['citation_locators']=data['citation_locators']
                assert data==expected
                if arm in ('C01','C11','N1'):assert row['payload']['user'].endswith(APPLICATION_CUE)
                if arm=='G':assert row['payload']['user'].endswith(GENERIC_CUE)
    # Accidental gold input fails at the renderer boundary.
    one=deepcopy(first_d[0]);one['answer']='INJECTED_GOLD_FIELD'
    fake=readl(DATA/'demos/HAND_AUTHORED_initial_bundles.jsonl')[0]
    try:load_frozen_bundle(fake,first_d[0],allow_fixture=False)
    except ProtocolError:fixture_rejected=True
    else:raise AssertionError('Fixture allowed in actual path')
    original_bundle=load_frozen_bundle(fake,first_d[0],allow_fixture=True)
    try:render_replay(one,original_bundle,'C00')
    except ProtocolError:gold_rejected=True
    else:raise AssertionError('Gold field accepted')
    histories=read(DATA/'audits/REAL_HISTORY_REPLAY.json')
    assert histories['real_old_json_outputs_read']==77 and histories['raw_old_outputs_rejected_by_new_schema']==77
    scoring=read(DATA/'audits/SCORING_FIXTURE_CHECKS.json')
    assert all(r['status']=='MATCH_UNCHANGED_OFFICIAL_SCORER' for r in scoring['official_parity'])
    assert scoring['paired_formula_fixture']['primary_comparison_enabled'] is False
    assert scoring['missing_export']['n_expected']==6 and scoring['missing_export']['n_valid']==5
    assert scoring['missing_export']['condition_summaries'] is None
    assert scoring['technical_interrupt_export']['status_counts']['TECHNICAL_FAILURE']==1
    lengths=read(DATA/'audits/REFERENCE_LENGTHS.json')
    groups={}
    for family in ('pipeline_fixture','semantic_example','stress'):
        rows=[r for r in lengths['rows'] if r['input_family']==family]
        groups[family]={'rows':len(rows),'min_input_tokens':min(r['reference_input_tokens'] for r in rows),
            'max_input_tokens':max(r['reference_input_tokens'] for r in rows),
            'over_8192_including_512_reserve':sum(r['over_8192_with_candidate_512_output'] for r in rows),
            'over_16384_including_512_reserve':sum(r['over_16384_with_candidate_512_output'] for r in rows)}
    # Existing human forms and H role remain untouched; the preparation code only read C/D inputs.
    old=read(ROOT/'research/expert-annotation-pilot-20261030/PACK_MANIFEST.json')
    import hashlib
    for record in old['reviewer_work_surfaces']:
        assert hashlib.sha256((ROOT/record['path']).read_bytes()).hexdigest()==record['sha256']
    result={'date':'2026-10-30','verdict':'PASS_OFFLINE_INPUT_AND_SCORER_PACKAGE_ONLY',
        'independent_real_task_inputs':352,'waiting_replay_dependencies':56,
        'synthetic_pipeline_examples':56,'hand_authored_semantic_examples':7,
        'old_real_outputs_parsed':77,'adapted_legacy_initial_outputs':4,
        'new_target_schema_replay_coverage':'NOT_YET_AVAILABLE',
        'official_scoring_cases_checked':len(scoring['official_parity']),
        'fixture_refused_in_actual_path':fixture_rejected,'gold_field_refused':gold_rejected,
        'same_question_context_initials_messages_verified':True,'length_groups':groups,
        'model_calls':0,'human_records_filled':0,'H_records_used':0,'execution_verdict':'DO_NOT_RUN',
        'limits':['Actual model/backend and budget not selected.',
                  'No real new-task initial outputs; synthetic/legacy adapters are interface checks only.',
                  'Actual prompts still need provider/chat-schema and output-budget context validation; never silently truncate.',
                  'Semantic adoption and mechanism selectivity require further evidence.']}
    write(HERE/'PREFLIGHT_OFFLINE.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
