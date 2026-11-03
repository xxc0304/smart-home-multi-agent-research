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
OUT=ROOT/'runs/math140-inspection-component-20261020'
PLAN=ROOT/'engineering/MATH140_INSPECTION_COMPONENT_PLAN_20261020.json'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
    if OUT.exists() or PLAN.exists(): raise ValueError('Refuse overwrite')
    source=ROOT/'runs/math140-audit-delivery-20261020/4276ec64c178dafa/requests.jsonl'
    requests=[json.loads(x) for x in source.read_text(encoding='utf-8').splitlines()]
    selected=next(x for x in requests if '|inspect|' in x['logical_seed'])
    prompt=selected['payload']['instructions'];ctx=json.JSONDecoder().raw_decode(prompt[prompt.index('\n{"ACTOR"')+1:])[0]
    OUT.mkdir();input_path=OUT/'public_component_input.json'
    write_json(input_path,{'ACTOR':ctx['ACTOR'],'MATERIAL':ctx['MATERIAL']})
    files=[input_path,source,Path(__file__),ROOT/'config/deepseek_flash_inspection.json',ROOT/'design/source_binding_prompts.json',ROOT/'design/v0.3/coreta.schema.json',ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json']
    files += list((ROOT/'src/coreta').glob('*.py'))
    write_json(PLAN,{'scope':'Inspection component replay only; fixed seen public candidate, not end-to-end task success',
        'source_request_log':str(source),'source_logical_seed':selected['logical_seed'],
        'input_path':str(input_path),'output':str(OUT),'max_logical_calls':1,'max_requests':2,
        'inspection_output_cap':8192,'failure_policy':'One invocation; retain all failures; no rerun',
        'runtime_excludes':'gold answers, diagnoses, old inspection outputs and later trajectories',
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
    r=StabilityRunner(material['task'],directory,'inspection-component',SourceBindingContracts(ROOT/'design/v0.3/coreta.schema.json'),None,cfg,prompts)
    r.current=material['current'];r.version=r.current['version'];r.task_facts=material['task_facts']
    r.issues={x['issue_id']:x for x in material['issues']};r.pending=material['pending_closures']
    r._last_builder=material['subject']['sent_from']
    tokenizer=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
    r.client=StabilityClient(cfg,r.log,token_counter=lambda s:len(tokenizer.encode(s,add_special_tokens=False).ids))
    write_json(OUT/'launch.json',{'single_invocation':True,'actor':data['ACTOR']})
    error=None;value=None
    try: value=r.call('inspect',data['ACTOR'],'ClosureInspection',material,r.validate_inspection)
    except ProtocolError as exc: error={'code':exc.code,'detail':exc.detail}
    if value is not None: write_json(OUT/'inspection.json',value)
    hashes=all(sha(Path(f))==h for f,h in plan['source_hashes'].items())
    result={'scope':plan['scope'],'error':error,'complete_output_received':value is not None,
        'logical_calls':r.calls,'http_attempts':r.client.attempts,'format_repairs':r.repairs,
        'audit_records':len(r.audit_ledger),'valid_audit_records':sum(not x['validation_errors'] for x in r.audit_ledger),
        'audit_outcomes':[{'record_id':x['record_id'],'outcome':x['effective_outcome'],'validation_errors':x['validation_errors']} for x in r.audit_ledger],
        'frozen_hashes_match':hashes,'task_success_evaluated':False}
    write_json(OUT/'result.json',result);write_json(ROOT/'engineering/MATH140_INSPECTION_COMPONENT_RESULT_20261020.json',result)
    print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','run']);p.add_argument('--live',action='store_true');a=p.parse_args()
    if a.mode=='run' and not a.live:p.error('Explicit --live required')
    {'build':build,'run':run}[a.mode]()
