"""Offline exact replay of the original uncommitted v3 apply response."""
import copy
import hashlib
import json
from pathlib import Path
from fractions import Fraction as Q
from coreta.protocol_stability import StabilityRunner
from coreta.task_audit_binding import SourceBindingContracts
from coreta.audit_delivery import audit_reference_index
from coreta.revision import check_refs
from coreta.state import write_json
from coreta.closure import digest
from coreta.schemas import ProtocolError

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'runs/math140-closure-reference-20261020/4276ec64c178dafa'
OUT=ROOT/'runs/math140-correct-repair-offline-20261020'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
    if OUT.exists():raise ValueError('Refuse overwrite')
    request=rows(SOURCE/'requests.jsonl')[-1]
    assert '|apply|' in request['logical_seed']
    text=request['payload']['instructions'];ctx=json.JSONDecoder().raw_decode(text[text.index('\n{"ACTOR"')+1:])[0]
    material=ctx['MATERIAL']
    original=next(x['raw'] for x in rows(SOURCE/'validation.jsonl') if x['stage']=='apply' and x['code']=='REFERENCE_ERROR')
    value=json.loads(original)
    OUT.mkdir();write_json(OUT/'original_apply.json',value)
    directory=OUT/'trajectory';directory.mkdir()
    r=StabilityRunner(material['task'],directory,'offline-correct-repair',SourceBindingContracts(ROOT/'design/v0.3/coreta.schema.json'),None,
        read(ROOT/'config/deepseek_flash_inspection.json'),read(ROOT/'design/source_binding_prompts.json'))
    r.current=copy.deepcopy(material['current']);r.version=r.current['version']
    r.issues={i['issue_id']:copy.deepcopy(i) for i in material['issues']};r.task_facts=copy.deepcopy(material['task_facts'])
    before=digest(r.current['candidate']);error=None
    try:
        r.contracts.validate('ClosureUpdate',value)
        check_refs(value,set(audit_reference_index(material)))
        r.check_targets(value,set(audit_reference_index(material)))
        for issue in value['issues']:
            if issue['existing_issue_id'] is not None and issue['existing_issue_id'] not in r.issues:
                raise ProtocolError('REFERENCE_ERROR','Unknown issue')
        r.contracts.validate('Candidate',value['candidate'])
        r.validate_proposals(value)
        r.commit_proposals(value)
    except ProtocolError as exc:error={'code':exc.code,'detail':exc.detail}
    write_json(OUT/'state_after.json',{'current':r.current,'issues':r.issues,'pending':r.pending})
    # Independent exact checks, never part of replayed model material.
    points=[(0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(2,2)]
    p1=lambda x,y:x**3-y**3-x+y
    p2=lambda x,y:2*x-2*x**3-3*x*y+3*x*x*y
    point=(Q(5,19),Q(16,19))
    result={'scope':'Offline interface replay; no new model output or completed end-to-end recovery',
        'error':error,'original_output_modified':False,'original_candidate_hash':digest(value['candidate']),
        'candidate_changed':digest(r.current['candidate'])!=before,
        'committed_equals_original_apply_candidate':r.current['candidate']==value['candidate'],
        'pending_closure_issue_ids':sorted(r.pending),'post_commit_inspection_performed':False,
        'all_proposals_closed':False,'external_api_requests':0,
        'offline_arithmetic':{'basis_zero_at_all_eight_points':all(p1(x,y)==0 and p2(x,y)==0 for x,y in points),
            'basis_zero_at_correct_point':p1(*point)==0 and p2(*point)==0,
            'swapped_point_p2':str(p2(point[1],point[0]))},
        'source_hashes':{str(p):sha(p) for p in [SOURCE/'requests.jsonl',SOURCE/'validation.jsonl']}}
    write_json(OUT/'result.json',result)
    write_json(ROOT/'engineering/CORRECT_REPAIR_REPLAY_20261020.json',result)
    print(json.dumps(result))
if __name__=='__main__':run()
