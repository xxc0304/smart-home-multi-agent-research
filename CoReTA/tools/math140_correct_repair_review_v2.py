"""One frozen inspection-only replay; never counted as task success."""
import argparse
import hashlib
import json
from pathlib import Path
from coreta.protocol_stability import StabilityRunner, StabilityClient
from coreta.task_audit_binding import SourceBindingContracts
from coreta.state import write_json
from coreta.schemas import ProtocolError
from tokenizers import Tokenizer

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/math140-correct-repair-review-v2-20261020'
PLAN=ROOT/'engineering/MATH140_CORRECT_REPAIR_REVIEW_V2_PLAN_20261020.json'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
    if OUT.exists() or PLAN.exists(): raise ValueError('Refuse overwrite')
    source=ROOT/'runs/math140-closure-reference-20261020/4276ec64c178dafa/requests.jsonl'
    requests=[json.loads(x) for x in source.read_text(encoding='utf-8').splitlines()]
    selected=requests[-1]
    prompt=selected['payload']['instructions'];ctx=json.JSONDecoder().raw_decode(prompt[prompt.index('\n{"ACTOR"')+1:])[0]
    state=read(ROOT/'runs/math140-correct-repair-offline-20261020/state_after.json')
    original_material=ctx['MATERIAL']
    original_events=[json.loads(x) for x in (source.parent/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    original_events=[{'event_id':e['event_id'],'excerpt_notice':'Exact original step excerpts; not the complete event.', 'payload':{'steps':e['payload']['steps']}} for e in original_events if e['stage']=='draft']
    replay_events=[json.loads(x) for x in (ROOT/'runs/math140-correct-repair-offline-20261020/trajectory/events.jsonl').read_text(encoding='utf-8').splitlines()]
    snapshots=[]
    for line in (source.parent/'commits.jsonl').read_text(encoding='utf-8').splitlines():
        commit=json.loads(line)
        snapshots.extend({'version':x['version'],'source_event_id':x['source_event_id'],'excerpt_notice':'Exact original candidate steps only', 'candidate':{'steps':x['candidate']['steps']}} for x in (commit.get('before'),commit.get('after')) if x and x['version']<2)
    ctx={'ACTOR':'A1','MATERIAL':{'task':original_material['task'],
        'current':state['current'],'issues':list(state['issues'].values()),
        'task_facts':original_material['task_facts'],'pending_closures':state['pending'],
        'before':original_material['current'],'subject':original_material['evidence'][-1],
        'review_source_events':original_events,'review_candidate_snapshots':snapshots}}
    OUT.mkdir();input_path=OUT/'public_component_input.json'
    write_json(input_path,{'ACTOR':ctx['ACTOR'],'MATERIAL':ctx['MATERIAL']})
    files=[input_path,source,source.parent/'events.jsonl',source.parent/'commits.jsonl',ROOT/'runs/math140-correct-repair-offline-20261020/state_after.json',ROOT/'runs/math140-correct-repair-offline-20261020/trajectory/events.jsonl',Path(__file__),ROOT/'config/deepseek_flash_inspection.json',ROOT/'design/source_binding_prompts.json',ROOT/'design/v0.3/coreta.schema.json',ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json']
    files += list((ROOT/'src/coreta').glob('*.py'))
    write_json(PLAN,{'scope':'Independent review of offline-committed original correct repair; engineering continuation, not original end-to-end success',
        'source_request_log':str(source),'source_logical_seed':selected['logical_seed'],
        'input_path':str(input_path),'output':str(OUT),'max_logical_calls':1,'max_requests':2,
        'inspection_output_cap':8192,'failure_policy':'One invocation; retain all failures; no rerun',
        'runtime_excludes':'gold answers and offline diagnoses; original prior audit is supplied as evidence that must be rechecked',
        'source_hashes':{str(p):sha(p) for p in files}})
    print('Frozen inspection component input and plan')

def run():
    plan=read(PLAN)
    for f,h in plan['source_hashes'].items():
        if sha(Path(f))!=h: raise ValueError('Frozen source changed')
    if (OUT/'launch.json').exists(): raise ValueError('Single invocation only')
    data=read(Path(plan['input_path']));material=data['MATERIAL']
    cfg=read(ROOT/'config/deepseek_flash_inspection.json');prompts=read(ROOT/'design/source_binding_prompts.json')
    directory=OUT/'trajectory';directory.mkdir()
    r=StabilityRunner(material['task'],directory,'correct-repair-review',SourceBindingContracts(ROOT/'design/v0.3/coreta.schema.json'),None,cfg,prompts)
    r.current=material['current'];r.version=r.current['version'];r.task_facts=material['task_facts']
    r.issues={x['issue_id']:x for x in material['issues']};r.pending=material['pending_closures']
    r._last_builder=material['subject']['sent_from']
    tokenizer=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
    r.client=StabilityClient(cfg,r.log,token_counter=lambda s:len(tokenizer.encode(s,add_special_tokens=False).ids))
    write_json(OUT/'launch.json',{'single_invocation':True,'actor':data['ACTOR']})
    error=None;value=None
    try: value=r.call('inspect',data['ACTOR'],'ClosureInspection',material,r.validate_inspection)
    except ProtocolError as exc: error={'code':exc.code,'detail':exc.detail}
    if value is not None:
        write_json(OUT/'inspection.json',value)
        r.settle(value,data['ACTOR'])
    write_json(OUT/'state_after_review.json',{'current':r.current,'issues':r.issues,'pending':r.pending})
    hashes=all(sha(Path(f))==h for f,h in plan['source_hashes'].items())
    result={'scope':plan['scope'],'error':error,'complete_output_received':value is not None,
        'logical_calls':r.calls,'http_attempts':r.client.attempts,'format_repairs':r.repairs,
        'audit_records':len(r.audit_ledger),'valid_audit_records':sum(not x['validation_errors'] for x in r.audit_ledger),
        'audit_outcomes':[{'record_id':x['record_id'],'outcome':x['effective_outcome'],'validation_errors':x['validation_errors']} for x in r.audit_ledger],
        'frozen_hashes_match':hashes,'task_success_evaluated':False, 'issue_statuses':{k:x['status'] for k,x in r.issues.items()}}
    write_json(OUT/'result.json',result);write_json(ROOT/'engineering/MATH140_CORRECT_REPAIR_REVIEW_V2_RESULT_20261020.json',result)
    print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','run']);p.add_argument('--live',action='store_true');a=p.parse_args()
    if a.mode=='run' and not a.live:p.error('Explicit --live required')
    {'build':build,'run':run}[a.mode]()
