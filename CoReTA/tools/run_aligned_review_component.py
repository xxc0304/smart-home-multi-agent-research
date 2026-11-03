"""Frozen, single-invocation minimal-protocol component check."""
import argparse
import hashlib
import json
from pathlib import Path
from tokenizers import Tokenizer
from coreta.aligned_review import ReviewAdapter
from coreta.minimal_review import RepairBudget
from coreta.protocol_stability import StabilityClient
from coreta.minimal_review_transport import execute_review,provider_payload
from coreta.state import write_json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/aligned-review-component-20261020'
PLAN=ROOT/'engineering/ALIGNED_REVIEW_COMPONENT_PLAN_20261020.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def counter():
    tok=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
    return lambda s:len(tok.encode(s,add_special_tokens=False).ids)
def build():
    if OUT.exists() or PLAN.exists():raise ValueError('Refuse overwrite')
    source=ROOT/'runs/minimal-real-packet-20261020/packet.json';mapping=ROOT/'runs/minimal-real-packet-20261020/mapping.json'
    packet=read(source);cfg=read(ROOT/'config/deepseek_flash_inspection.json')
    OUT.mkdir();write_json(OUT/'packet.json',packet);write_json(OUT/'mapping.json',read(mapping))
    a=ReviewAdapter(OUT/'preflight',ROOT/'design/convergence/aligned_review.schema.json',token_counter=counter())
    c=StabilityClient(cfg,a.log,token_counter=counter());request=a.request(packet)
    size=c.size(provider_payload(c,request,8192))
    if size>32768:raise ValueError('Provider input exceeds limit')
    files=[source,mapping,OUT/'packet.json',OUT/'mapping.json',Path(__file__),ROOT/'design/convergence/aligned_review.schema.json',ROOT/'config/deepseek_flash_inspection.json',ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json']+list((ROOT/'src/coreta').glob('*.py'))
    plan={'scope':'Independent minimal-review component of a fixed seen candidate; not full-task success',
        'one_invocation':True,'logical_checks':1,'format_repairs_max':2,'http_attempt_upper_bound':9,
        'input_limit':32768,'output_limit':8192,'actual_provider_input_estimate':size,
        'packet_path':str(OUT/'packet.json'),'output':str(OUT),
        'runtime_excludes':'gold, offline diagnosis, prior review responses; supplied prior candidate and original evidence only',
        'source_hashes':{str(p):sha(p) for p in files}}
    write_json(PLAN,plan);print(json.dumps({'plan':str(PLAN),'provider_input_estimate':size}))
def run():
    plan=read(PLAN)
    for f,h in plan['source_hashes'].items():
        if sha(Path(f))!=h:raise ValueError('Frozen source changed: '+f)
    if (OUT/'launch.json').exists():raise ValueError('Single invocation only')
    cfg=read(ROOT/'config/deepseek_flash_inspection.json');packet=read(Path(plan['packet_path']))
    adapter=ReviewAdapter(OUT/'live',ROOT/'design/convergence/aligned_review.schema.json',token_counter=counter(),shared_budget=RepairBudget(2,0))
    client=StabilityClient(cfg,adapter.log,token_counter=counter())
    write_json(OUT/'launch.json',{'single_invocation':True,'component_budget_only':True})
    result=execute_review(adapter,client,packet)
    result['frozen_hashes_match']=all(sha(Path(f))==h for f,h in plan['source_hashes'].items())
    write_json(OUT/'result.json',result);write_json(ROOT/'engineering/ALIGNED_REVIEW_COMPONENT_RESULT_20261020.json',result)
    projection=result['final_projection'] or {}
    print(json.dumps({'http_attempts':result['http_attempts'],'repairs_used':result['repairs_used'],'terminal_error':result['terminal_error'],
        'global_errors':projection.get('global_errors'),'issues':{k:v['status'] for k,v in projection.get('issues',{}).items()},
        'all_issues_resolved':projection.get('all_issues_resolved'),'frozen_hashes_match':result['frozen_hashes_match']}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','run']);p.add_argument('--live',action='store_true');a=p.parse_args()
    if a.mode=='run' and not a.live:p.error('Explicit --live required')
    {'build':build,'run':run}[a.mode]()
