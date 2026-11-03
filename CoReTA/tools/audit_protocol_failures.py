"""Offline saved-run inventory, not new model evidence."""
import hashlib
import json
from pathlib import Path
from coreta.task_audit_binding import SourceBindingContracts

ROOT=Path(__file__).resolve().parents[1]

def build():
    runs=[]
    names=['task-audit','source-binding','closure-reference','audit-delivery','inspection-recovery']
    for name in names:
        folder=ROOT/f'runs/math140-{name}-20261020/4276ec64c178dafa'
        result=json.loads((folder/'result.json').read_text(encoding='utf-8'))
        errors=[json.loads(x) for x in (folder/'validation.jsonl').read_text(encoding='utf-8').splitlines()] if (folder/'validation.jsonl').exists() else []
        runs.append({'name':name,'status':result['status'],'logical_calls':result['normal_calls'],
                     'http_attempts':result['http_attempts'],'audit_records':result['audit_record_count'],
                     'terminal_errors':result['errors'],
                     'validation':[{'stage':x['stage'],'code':x['code'],'detail':x['detail']} for x in errors]})
    contracts=SourceBindingContracts(ROOT/'design/v0.3/coreta.schema.json')
    fields={}
    def count(value):
        if isinstance(value,dict):return len(value.get('properties',{}))+sum(count(v) for v in value.values())
        if isinstance(value,list):return sum(count(v) for v in value)
        return 0
    for name in ['TaskFacts','TaskFactsPatch','ClosureUpdate','ClosureInspection']:
        s=contracts.schema(name)
        fields[name]={'root_fields':list(s['properties']),'property_declarations_in_transitive_schema':count(s),
                      'schema_chars':len(json.dumps(s,ensure_ascii=False))}
    plans=list((ROOT/'engineering').glob('MATH140_*PLAN_20261020.json'))
    hashes=[]
    for p in plans:
        plan=json.loads(p.read_text(encoding='utf-8'))
        if 'source_hashes' in plan:
            hashes.append({'plan':p.name,'files':len(plan['source_hashes']),
                           'all_match':all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in plan['source_hashes'].items())})
    return {'scope':'Saved development trajectories only; no independence or effectiveness claim',
            'runs':runs,'schema_inventory':fields,'frozen_plans':hashes}

if __name__=='__main__':
    output=ROOT/'engineering/PROTOCOL_FAILURE_MATRIX_20261020.json'
    output.write_text(json.dumps(build(),ensure_ascii=False,indent=2),encoding='utf-8')
    print(str(output))
