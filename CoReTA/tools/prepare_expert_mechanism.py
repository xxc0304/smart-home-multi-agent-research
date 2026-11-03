"""Prepare API-neutral inputs and honestly labeled offline checks; no model client."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import argparse
import importlib.util
import json
import sys

from expert_mechanism_protocol import (ACTORS, FOCAL, ARMS, OUTPUT_SCHEMA, INITIAL_SYSTEM,
    REPLAY_SYSTEM, APPLICATION_CUE, GENERIC_CUE, ProtocolError, render_initial,
    render_replay, load_frozen_bundle, parse_output, assess_context)
from score_expert_mechanism import score_one, score_batch, paired_effects, transitions

ROOT=Path(__file__).resolve().parent.parent
HERE=ROOT/'implement-stage/expert-mechanism-inputs-20261030'
DATA=ROOT/'data/expert-mechanism-inputs-20261030-v0.2'
MUSIQUE=ROOT/'data/external/musique-v1.0-20261030'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def readl(path):return [json.loads(s) for s in Path(path).read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def writel(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')


def request_meta(tid,actor,stage,condition=None,fixture=False):
    return {'request_id':f'{tid}|{stage}|{actor}|{condition or "base"}', 'task_id':tid,
            'actor':actor,'stage':stage,'condition':condition or stage,
            'evidence_kind':'PIPELINE_FIXTURE_NOT_MODEL_OUTPUTS' if fixture else 'REAL_TASK_INPUT_NO_MODEL_OUTPUT',
            'backend':None,'execution_allowed':False,'candidate_max_output_tokens':512}


def synthetic_bundle(task,all_sources=False):
    pars=task['paragraphs'];ids=[p['idx'] for p in pars]
    assignments={'M1':ids if all_sources else [ids[0]], 'M2':[ids[1]],
                 'M3':[ids[0],ids[2]],'M4':[]}
    rows=[]
    for i,actor in enumerate(ACTORS):
        p=pars[min(i,len(pars)-1)]
        output={'answer':f'PIPELINE_FIXTURE_ANSWER_{actor}', 'support_idxs':assignments[actor],
                'reasoning':'Hand-authored pipeline fixture, not a model answer. Visible paragraph text: '+p['paragraph_text']}
        rows.append({'actor':actor,'raw_output':json.dumps(output,ensure_ascii=False)})
    return {'kind':'HAND_AUTHORED_PIPELINE_FIXTURE','task_id':task['id'],
            'note':'Answers are placeholders, source text comes only from sanitized visible input; no gold answer used.',
            'records':rows}


def make_replays(task,bundle,allow_fixture=False):
    outputs=load_frozen_bundle(bundle,task,allow_fixture=allow_fixture,source_root=ROOT)
    fixture=bundle['kind']!='FROZEN_MODEL_OUTPUTS'
    rows=[]
    for arm in ARMS:
        rendered=render_replay(task,outputs,arm)
        rows.append({**request_meta(task['id'],FOCAL,'receiver_replay',arm,fixture),
            'initial_bundle_kind':bundle['kind'],**rendered})
    return rows


def semantic_worked_example(task):
    """Hand-authored on a visible D task; never used as generated participant data."""
    assert task['id']=='2hop__123383_21417'
    visible={p['idx']:p['paragraph_text'] for p in task['paragraphs']}
    assert 'Yale Law School (1843)' in visible[15]
    assert 'professor of law at the Yale Law School' in visible[17]
    outputs={
        'M1':{'answer':'1843','support_idxs':[17,15],
            'reasoning':"Paragraph 17 identifies Sturges's employer as Yale Law School. Paragraph 15 dates Yale Law School to 1843. The 1887 renaming concerns Yale College/Yale University, not the creation of the law school."},
        'M2':{'answer':'1887','support_idxs':[15],
            'reasoning':'Paragraph 15 says Yale College was renamed Yale University in 1887, so I currently use 1887 for the institutional employer.'},
        'M3':{'answer':'1887','support_idxs':[15,17],
            'reasoning':'Sturges worked at Yale. The paragraph about Yale states that Yale College was renamed Yale University in 1887. I treat this as the relevant creation date.'},
        'M4':{'answer':None,'support_idxs':[17],
            'reasoning':'The biography names Yale Law School and a later Miami deanship. The particular institutional employer must be matched to its own date rather than to a similarly named institution.'},
    }
    bundle={'kind':'HAND_AUTHORED_PIPELINE_FIXTURE','subtype':'SEMANTIC_WORKED_EXAMPLE_NOT_MODEL_BEHAVIOR',
            'task_id':task['id'],'note':'Manually constructed from visible P15/P17, not generated model answers and not a scientific treatment outcome.',
            'records':[{'actor':a,'raw_output':json.dumps(outputs[a],ensure_ascii=False)} for a in ACTORS]}
    return bundle,{'reviewer':'assistant','basis':'visible paragraph text, not gold-driven citation selection',
        'observations':['M1 combines employer identification and the law school date.',
                        'M2/M3 use the 1887 renaming as the wrong relation; their cited paragraph IDs are legal.',
                        'M4 contributes a relevant entity-matching caution while offering no final answer.'],
        'scope':'Shows what the prompts and semantic checks mean; not empirical evidence that a model has this behavior.'}


def legacy_replay():
    """Real old responses; permission/contract adaptation is explicitly not a reproduction."""
    seed=read(ROOT/'research/expert-team-assets-20261029/CASE_SEED_8.json')
    c=next(c for c in seed['cases'] if c['id']=='C03')
    records=[r for r in c['records'] if r['row']['method']=='shared']
    paragraphs=[]; ref_map={}
    for record in records:
        for source in record['packet']['information_available']:
            if source['ref'] not in ref_map:
                ref_map[source['ref']]=len(paragraphs)
                paragraphs.append({'idx':len(paragraphs),'title':source['ref'],'paragraph_text':source['content']})
            else:
                assert paragraphs[ref_map[source['ref']]]['paragraph_text']==source['content']
    task={'id':'LEGACY_C03_INTERFACE_ONLY','question':records[0]['packet']['task']['scenario'], 'paragraphs':paragraphs}
    choices={r['id']:r['text'] for r in records[0]['packet']['task']['choices']}
    bundle={'kind':'LEGACY_CONTRACT_ADAPTER','task_id':task['id'],'records':[],
            'scope':'Common interface replay only; full union visibility is an adapter, not original experimental permissions.'}
    audit=[]
    for actor,record in zip(ACTORS,records):
        raw=(ROOT/record['raw_path']).read_text(encoding='utf-8');value=json.loads(raw)
        assert raw==record['raw_text']
        output={'answer':choices[value['choice']] if value['choice'] is not None else None,
                'reasoning':value['reasoning'],'support_idxs':[]}
        bundle['records'].append({'actor':actor,'raw_output':json.dumps(output,ensure_ascii=False),
             'original_raw_path':record['raw_path'],'original_raw_output':raw,
             'citation_status':'Not recorded as numerical source IDs in the original schema; left empty, not guessed.'})
        audit.append({'actor':actor,'original_raw_path':record['raw_path'],'original_contract':'choice/reasoning',
                      'mapped_choice_to_original_display_name':True,'original_reasoning_unchanged':True,
                      'new_numerical_citation_schema_covered':False})
    return task,bundle,audit


def controlled_scoring(target):
    """Gold is used ONLY here on the scoring side, never to prepare peer messages."""
    supports=[p['idx'] for p in target['paragraphs'] if p['is_supporting']]
    wrong=next(p['idx'] for p in target['paragraphs'] if not p['is_supporting'])
    exact={'answer':target['answer'],'support_idxs':supports,'reasoning':'HAND_AUTHORED_SCORING_FIXTURE'}
    alias=deepcopy(exact);alias['answer']=(target['answer_aliases'] or [target['answer'].upper()])[0]
    wrong_answer=deepcopy(exact);wrong_answer['answer']='zzzz_fixture_nonanswer_zzzz'
    wrong_support=deepcopy(exact);wrong_support['support_idxs']=[wrong]
    partial=deepcopy(exact);partial['support_idxs']=supports[:1]
    abstain={'answer':None,'support_idxs':[],'reasoning':'Hand-authored intentional abstention fixture.'}
    values={'exact':exact,'alias_or_normalized_variant':alias,'wrong_answer':wrong_answer,
            'wrong_support':wrong_support,'partial_support':partial,'abstention':abstain}
    requests=[];responses=[];checks=[]
    # Separate unchanged upstream aggregate entry point for one-case parity.
    official_path=ROOT/'research/musique-data-preparation-20261030/official_scorer/evaluate_v1.0.py'
    spec=importlib.util.spec_from_file_location('upstream_eval_fixture',official_path)
    official=importlib.util.module_from_spec(spec);spec.loader.exec_module(official)
    import tempfile
    with tempfile.TemporaryDirectory(prefix='expert-score-fixture-') as temp:
        temp=Path(temp);gold=temp/'gold.jsonl';writel(gold,[target])
        for name,output in values.items():
            item=request_meta(target['id'],FOCAL,'score_fixture',name,True)
            requests.append(item)
            responses.append({'request_id':item['request_id'],'status':'ok',
                'source_kind':'HAND_AUTHORED_SCORING_FIXTURE','raw_output':json.dumps(output,ensure_ascii=False)})
            score=score_one(output,target)
            pred=temp/'pred.jsonl';writel(pred,[{'id':target['id'],'predicted_answer':output['answer'] or '',
                'predicted_support_idxs':output['support_idxs'],'predicted_answerable':True}])
            upstream=official.evaluate(str(pred),str(gold))
            assert {k:round(score[k],3) for k in upstream}==upstream
            checks.append({'case':name,'status':'MATCH_UNCHANGED_OFFICIAL_SCORER','metrics':score})
    batch=score_batch(requests,responses,{target['id']:target},fixture=True)
    assert not batch['primary_comparison_enabled']
    missing=score_batch(requests,responses[:-1],{target['id']:target},fixture=True)
    assert missing['status']=='INCOMPLETE_NO_PRIMARY_SUMMARY' and missing['condition_summaries'] is None
    broken=deepcopy(responses);broken[0]={'request_id':requests[0]['request_id'],'status':'truncated','raw_output':'{"answer":'}
    interrupted=score_batch(requests,broken,{target['id']:target},fixture=True)
    assert interrupted['status_counts']['TECHNICAL_FAILURE']==1 and not interrupted['primary_comparison_enabled']
    # Controlled matrix checks the paired formula; all numbers are fixtures.
    matrix_requests=[];matrix_responses=[]
    for arm in ARMS:
        req=request_meta(target['id'],FOCAL,'controlled_matrix',arm,True);matrix_requests.append(req)
        output=exact if arm in ('C10','C01','C11','N1') else wrong_answer
        matrix_responses.append({'request_id':req['request_id'],'status':'ok',
            'source_kind':'HAND_AUTHORED_SCORING_FIXTURE','raw_output':json.dumps(output,ensure_ascii=False)})
    matrix=score_batch(matrix_requests,matrix_responses,{target['id']:target},fixture=True)
    matrix['paired_effects']=paired_effects(matrix)
    em=next(r for r in matrix['paired_effects']['effects'] if r['metric']=='answer_em')
    assert em['source_average_effect']==.5 and em['application_average_effect']==.5
    assert em['interaction']==-1 and em['message_application_minus_no_message_application']==0
    return requests,responses,{'evidence_type':'CONTROLLED_FIXTURES_NOT_MODEL_RESULTS','official_parity':checks,
        'missing_export':missing,'technical_interrupt_export':interrupted,'paired_formula_fixture':matrix,
        'transition_fixtures':{'harm':transitions(exact,wrong_answer,target),
                               'correction':transitions(wrong_answer,exact,target)}}


def prepare():
    if (DATA/'actual_responses').exists() and any((DATA/'actual_responses').rglob('*.json*')):
        raise RuntimeError('Actual responses present; preserve this package and prepare a new version')
    c=readl(MUSIQUE/'inputs/C_calibration.jsonl')
    d=readl(MUSIQUE/'inputs/D_development.jsonl')
    selected=d[:8]
    assert len(c)==160 and len(d)==80 and len(selected)==8
    independent=[];pending=[];demos=[];bundles=[]
    for split,tasks,actors in [('C',c,ACTORS[:2]),('D',selected,ACTORS)]:
        for task in tasks:
            for actor in actors:
                independent.append({**request_meta(task['id'],actor,'independent_'+split),
                    'payload':render_initial(task)})
    for task in selected:
        bundle=synthetic_bundle(task);bundles.append(bundle)
        demos+=make_replays(task,bundle,allow_fixture=True)
        for arm in ARMS:
            pending.append({**request_meta(task['id'],FOCAL,'receiver_replay',arm),
                'status':'WAITING_FOR_ACTUAL_FROZEN_INITIAL_OUTPUTS',
                'depends_on':[request_meta(task['id'],actor,'independent_D')['request_id'] for actor in ACTORS],
                'payload':None})
    writel(DATA/'independent_inputs.jsonl',independent)
    writel(DATA/'independent_C160_inputs.jsonl',[r for r in independent if r['stage']=='independent_C'])
    writel(DATA/'independent_D8_inputs.jsonl',[r for r in independent if r['stage']=='independent_D'])
    writel(DATA/'pending_replay_dependencies.jsonl',pending)
    writel(DATA/'demos/HAND_AUTHORED_initial_bundles.jsonl',bundles)
    writel(DATA/'demos/HAND_AUTHORED_replay_inputs.jsonl',demos)
    task,legacy,audit=legacy_replay()
    write(DATA/'demos/LEGACY_interface_task.json',task);write(DATA/'demos/LEGACY_initial_bundle.json',legacy)
    legacy_requests=make_replays(task,legacy,allow_fixture=True)
    assert all(not r['operation_checks']['source_locator_applied'] for r in legacy_requests)
    writel(DATA/'demos/LEGACY_replay_inputs.jsonl',legacy_requests)
    # Raw outputs from the old task have a different schema. Check and record, do not silently call it full coverage.
    seed=read(ROOT/'research/expert-team-assets-20261029/CASE_SEED_8.json')
    rejected=parsed=0
    for case in seed['cases']:
        for record in case.get('records',[]):
            json.loads(record['raw_text']);parsed+=1
            try:parse_output(record['raw_text'],range(20))
            except ProtocolError:rejected+=1
    write(DATA/'audits/REAL_HISTORY_REPLAY.json',{'real_old_json_outputs_read':parsed,
        'raw_old_outputs_rejected_by_new_schema':rejected,'adapted_initial_records':audit,
        'scope':'Common input/parser/response replay only; not real MuSiQue output, not old-condition reproduction.',
        'new_task_real_response_coverage':'MISSING_BEFORE_FIRST_TECHNICAL_MODEL_CHECK',
        'source_locator_real_response_branch':'Not covered; old numerical citations absent, correctly not fabricated.'})
    semantic_bundle,semantic_review=semantic_worked_example(selected[0])
    semantic_requests=make_replays(selected[0],semantic_bundle,allow_fixture=True)
    write(DATA/'demos/HAND_AUTHORED_semantic_bundle.json',semantic_bundle)
    writel(DATA/'demos/HAND_AUTHORED_semantic_replay_inputs.jsonl',semantic_requests)
    write(DATA/'audits/SEMANTIC_WORKED_EXAMPLE_REVIEW.json',semantic_review)
    # Only after prompt preparation: isolated scoring-side targets and controlled gold fixtures.
    ct=readl(MUSIQUE/'scoring/C_calibration.jsonl');dt=readl(MUSIQUE/'scoring/D_development.jsonl')
    selected_ids={t['id'] for t in selected};dt=[t for t in dt if t['id'] in selected_ids]
    writel(DATA/'private_scoring/C160_targets.jsonl',ct);writel(DATA/'private_scoring/D8_targets.jsonl',dt)
    writel(DATA/'private_scoring/selected_targets.jsonl',ct+dt)
    requests,responses,checks=controlled_scoring(dt[0])
    writel(DATA/'fixtures/HAND_AUTHORED_score_requests.jsonl',requests)
    writel(DATA/'fixtures/HAND_AUTHORED_score_responses.jsonl',responses)
    write(DATA/'audits/SCORING_FIXTURE_CHECKS.json',checks)
    # CPU length checking, including an actual longest-D input and all-citation stress fixture.
    from tokenizers import Tokenizer
    tokenizer=Tokenizer.from_file(str(ROOT/'data/external/qwen3-4b-tokenizer-20261030/tokenizer.json'))
    tokenizer.no_truncation();tokenizer.no_padding()
    def count(row):return len(tokenizer.encode(row['payload']['system']+'\n'+row['payload']['user'],add_special_tokens=False).ids)
    longest=max(d,key=lambda t:len(tokenizer.encode(json.dumps(t,ensure_ascii=False),add_special_tokens=False).ids))
    stress=make_replays(longest,synthetic_bundle(longest,all_sources=True),allow_fixture=True)
    writel(DATA/'demos/LONG_D_ALL_CITATIONS_STRESS_FIXTURE.jsonl',stress)
    length_rows=[{'request_id':r['request_id'],'condition':r['condition'],
        'reference_input_tokens':count(r),'over_8192_with_candidate_512_output':count(r)+512>8192,
        'over_16384_with_candidate_512_output':count(r)+512>16384,
        'live_context_assessment':assess_context(count(r)),
        'input_family':'stress' if r in stress else 'semantic_example' if r in semantic_requests else 'pipeline_fixture'}
        for r in demos+semantic_requests+stress]
    write(DATA/'audits/REFERENCE_LENGTHS.json',{'scope':'System+user task text only; reference tokenizer, not provider/chat-template or hidden reasoning count.',
        'truncation':False,'candidate_output_reserve':512,'rows':length_rows,
        'max_input_tokens':max(r['reference_input_tokens'] for r in length_rows),
        'all_citation_stress_task_id':longest['id']})
    write(DATA/'OUTPUT_SCHEMA.json',OUTPUT_SCHEMA)
    write(DATA/'ACTOR_ASSIGNMENT_PENDING.json',{'status':'MODEL_CONFIGURATIONS_UNSELECTED',
        'M1':{'candidate_configuration':'E','calibrated_expert':False},
        'M2':{'candidate_configuration':'B','focal_receiver':True},
        'M3':{'candidate_configuration':'B'},'M4':{'candidate_configuration':'B'},
        'note':'Host metadata only. Do not put configuration names or assumed expertise into model prompts.'})
    write(DATA/'INITIAL_BUNDLE_EXAMPLE.json',{'kind':'FROZEN_MODEL_OUTPUTS','task_id':selected[0]['id'],
        'records':[{'actor':actor,'raw_response_path':'PATH_TO_ACTUAL_RAW_JSON_OUTPUT',
                    'raw_output':'ACTUAL_JSON_OUTPUT_TEXT_REQUIRED'} for actor in ACTORS],
        'note':'This is an interface specification, not an executable response bundle.'})
    protocol='# 逐字模型提示\n\n数据块由渲染器追加；模型看不到结构性任务ID、角色能力或gold。\n\n'
    for name,value in [('独立作答系统',INITIAL_SYSTEM),('协作系统',REPLAY_SYSTEM),('后果核对A',APPLICATION_CUE),('通用核对G',GENERIC_CUE)]:
        protocol+=f'## {name}\n\n```text\n{value}\n```\n\n'
    (HERE/'PROMPTS.md').write_text(protocol,encoding='utf-8')
    report={'date':'2026-10-30','status':'OFFLINE_PACKAGE_PREPARED_NOT_LIVE_PREFLIGHT',
        'independent_inputs':len(independent),'C160_two_configs':320,'D8_four_members':32,
        'pending_replays':len(pending),'synthetic_replay_examples':len(demos),
        'semantic_worked_replay_examples':len(semantic_requests),
        'legacy_interface_replay_examples':len(legacy_requests),'source_schema':OUTPUT_SCHEMA,
        'max_reference_stress_input_tokens':max(r['reference_input_tokens'] for r in length_rows),
        'model_calls':0,'training_runs':0,'H_records_used':0,
        'remaining':['Model/backend and actual generation settings not selected.',
            'Real MuSiQue initial responses and successful citation-locator replay not yet available.',
            'Source-locator/G-A instruction lengths and hidden reasoning costs not exactly matched.',
            'Semantic contribution validity and causal adoption cannot be certified by structural checks.']}
    write(HERE/'PACKAGE_CHECKS.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='source_schema'},ensure_ascii=False,indent=2))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--initials');parser.add_argument('--task-inputs')
    parser.add_argument('--output');args=parser.parse_args()
    if args.initials:
        if not args.task_inputs or not args.output:parser.error('--initials needs --task-inputs and --output')
        bundle=read(args.initials);tasks={t['id']:t for t in readl(args.task_inputs)}
        rows=make_replays(tasks[bundle['task_id']],bundle,allow_fixture=False)
        writel(Path(args.output),rows)
        print('Prepared seven conditions from declared actual raw responses; backend execution still disabled.')
    else:prepare()


if __name__=='__main__':main()
