"""One frozen full-flow engineering regression on seen MATH140."""
import argparse,hashlib,json,os
from pathlib import Path
from tokenizers import Tokenizer
from coreta.closure import digest
from coreta.converged_flow import ConvergedFlow
from coreta.protocol_stability import StabilityClient,StabilityRunner
from coreta.task_audit_binding import SourceBindingContracts
from coreta.state import write_json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/converged-flow-20261020'
PLAN=ROOT/'engineering/CONVERGED_FLOW_PLAN_20261020.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def setup(directory,bank):
    cfg=read(ROOT/'config/deepseek_flash_inspection.json')
    task=read(ROOT/'data/math-expanded-screen-20261019/public/4276ec64c178dafa.json')
    prompts=read(ROOT/'design/source_binding_prompts.json')
    contracts=SourceBindingContracts(ROOT/'design/v0.3/coreta.schema.json');contracts.validate('PublicTask',task)
    tok=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
    count=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
    b=StabilityRunner(task,directory,'converged-flow-20261020',contracts,None,cfg,prompts,17,draft_bank=bank)
    b.client=StabilityClient(cfg,b.log,token_counter=count)
    return b,ConvergedFlow(b,ROOT/'design/convergence/evidence_review.schema.json',count)
def build():
    if OUT.exists() or PLAN.exists():raise ValueError('Refuse overwrite')
    OUT.mkdir();bank=OUT/'draft-bank';bank.mkdir();b,flow=setup(OUT/'preflight',bank)
    prior=read(ROOT/'runs/math140-inspection-recovery-20261020/draft_migration.json');receipts=[]
    for actor,row in zip(('A0','A1','A2'),prior):
        source=Path(row['original']);saved=read(source);candidate=saved['candidate']
        if sha(source)!=row['original_sha256'] or digest(candidate)!=row['candidate_hash_unchanged']:raise ValueError('Original draft changed')
        material={'task':b.task,'actor':actor,'seed':17,'config':b.config,'system_prompt':b.prompts['system'],
                  'draft_prompt':b.prompts['draft'],'schema':b.contracts.schema('Candidate')}
        fingerprint=hashlib.sha256(json.dumps(material,sort_keys=True).encode()).hexdigest()
        dest=bank/(fingerprint+'.json');write_json(dest,{'fingerprint':fingerprint,'candidate':candidate})
        receipts.append({'actor':actor,'original':str(source),'original_sha256':sha(source),'destination':str(dest),
            'candidate_hash':digest(candidate),'reason':'Exact original cached draft replay under current config fingerprint; no regeneration'})
    write_json(OUT/'draft_receipts.json',receipts);write_json(OUT/'public_task.json',b.task)
    files=list((ROOT/'src/coreta').glob('*.py'))+list((ROOT/'design').glob('*.json'))+[ROOT/'design/v0.3/coreta.schema.json',ROOT/'design/convergence/evidence_review.schema.json',ROOT/'config/deepseek_flash_inspection.json',ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json',Path(__file__),OUT/'draft_receipts.json',OUT/'public_task.json']+list(bank.glob('*.json'))+[Path(r['original']) for r in receipts]
    plan={'scope':'One seen all-initial-fail engineering regression, not new-task efficacy','initial_scores':[0,0,0],
        'single_invocation':True,'normal_call_cap':14,'cached_draft_calls':3,'new_logical_stage_cap':11,
        'format_repair_cap':2,'http_attempt_upper_bound':39,'task_timeout_seconds':1800,
        'input_limit':32768,'inspect_output_limit':8192,'other_output_limit':4096,
        'runtime_excludes':'Gold, old diagnostics, prior repaired candidates and prior review responses',
        'failure_policy':'Retain failure; no rerun or source edits after launch',
        'score_policy':'Score final delivered artifact only, immutable Linux Math-Verify image',
        'scoring_image':'sha256:841f8763c03c5cc688a811a90e13e82541d3350cdaccf3bba64aefb627be5cf6',
        'source_hashes':{str(p):sha(p) for p in files}}
    write_json(PLAN,plan);print(json.dumps({'plan':str(PLAN),'draft_hashes':[r['candidate_hash'] for r in receipts]}))
def run():
    plan=read(PLAN)
    for name,h in plan['source_hashes'].items():
        if sha(Path(name))!=h:raise ValueError('Frozen source changed: '+name)
    if (OUT/'launch.json').exists():raise ValueError('Single invocation already launched')
    if not os.environ.get('DEEPSEEK_API_KEY'):raise ValueError('Configured API credential unavailable')
    directory=OUT/'trajectory';directory.mkdir();b,flow=setup(directory,OUT/'draft-bank')
    if b.config['model']!='deepseek-flash' or b.config['base_url']!='https://api.deepseek.com':raise ValueError('Unexpected endpoint')
    write_json(OUT/'launch.json',{'single_invocation':True,'run_id':b.run_id})
    try:result=flow.run()
    except Exception as exc:
        write_json(OUT/'implementation_error.json',{'type':type(exc).__name__,'message':str(exc)});raise
    result['frozen_hashes_match']=all(sha(Path(name))==h for name,h in plan['source_hashes'].items())
    write_json(OUT/'result.json',result);write_json(ROOT/'engineering/CONVERGED_FLOW_RESULT_20261020.json',result)
    print(json.dumps({k:result[k] for k in ['status','stop_reason','normal_calls','http_attempts','format_repairs','review_count','review_status','native_evidence_count','errors','frozen_hashes_match']}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','run']);p.add_argument('--live',action='store_true');a=p.parse_args()
    if a.mode=='run' and not a.live:p.error('--live required')
    {'build':build,'run':run}[a.mode]()
