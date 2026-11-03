"""Static component-review gates; no model calls or hidden answers."""
import copy
from .audit_delivery import audit_reference_index
from .schemas import ProtocolError


def prepare_review(data):
    data=copy.deepcopy(data)
    material=data['MATERIAL'];actor=data['ACTOR'];builder=material['subject']['sent_from']
    if actor not in {'A1','A2'} or builder not in {'A1','A2'} or actor==builder:
        raise ProtocolError('REVIEW_ROLE_ERROR','Checker must be A1/A2 and differ from builder and A0')
    issues={x['issue_id']:x for x in material['issues']}
    required=[]
    for key,p in material['pending_closures'].items():
        if key not in issues:raise ProtocolError('REVIEW_INPUT_ERROR','Pending issue absent')
        issue=issues[key]
        if set(p['response_to_objection_ids'])!={x['objection_id'] for x in issue['objections']}:
            raise ProtocolError('REVIEW_INPUT_ERROR','Pending proposal omits objections')
        records=issue.get('evidence_records',[])
        if set(p['evidence_record_ids'])!={x['record_id'] for x in records}:
            raise ProtocolError('REVIEW_INPUT_ERROR','Pending proposal and original records differ')
        for record in records:
            for case in record['payload']['cases']:
                required.append({'issue_id':key,'record_id':record['record_id'],
                    'case':copy.deepcopy(case),'original_claim':record['payload']['claim_text']})
    visible=set(audit_reference_index(material));missing=set()
    def walk(value):
        if isinstance(value,dict):
            for key,child in value.items():
                if key in {'basis_refs','evidence_refs','target_refs'}:
                    missing.update(x for x in child if x not in visible)
                else:walk(child)
        elif isinstance(value,list):
            for child in value:walk(child)
    walk(material)
    if missing:raise ProtocolError('REVIEW_INPUT_ERROR','Referenced content absent: '+str(sorted(missing)))
    material['original_case_review_contract']={
        'cases_to_recheck':required,
        'rules':'For each pending issue, recheck every original record and check_item_id/input pair with exactly the stored identifiers. '
                'Keep historical counterexamples distinct from tests of replacement objects. Explain whether the candidate depends on the refuted object. '
                'Never rename an old-object input to claim it tests a new object. Report observed values faithfully; do not erase a historical contradiction. '
                'If the required evidence does not justify closure, leave the issue unresolved and explain the missing connection.'}
    return data,{'role_valid':True,'actor':actor,'builder':builder,'pending_count':len(material['pending_closures']),
                 'original_cases':len(required),'missing_reference_ids':[]}
