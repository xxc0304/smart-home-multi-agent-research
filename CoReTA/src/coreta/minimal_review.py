"""Standalone offline review boundary. No Runner inheritance or model transport."""
import copy
import hashlib
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from jsonschema import Draft202012Validator
from .task_audit import exact_rational
from .schemas import ProtocolError


REVIEW_INSTRUCTIONS = (
    'Review the supplied current candidate independently against the complete public task. '
    'Task interpretations are model assertions, not verified truth. For every issue use only supplied '
    'handles. Recompute each required historical case using its original object, then report a fresh '
    'observation and whether the original observation/objection is supported, refuted or uncertain. '
    'Do not copy old observations as a substitute for calculation. Test current objects separately. '
    'Explain same-object repair, replacement or rebuttal and any remaining dependency. '
    'Return only the output schema, without record IDs, hashes or array cross-reference indexes. '
    'Put new current contradictions in new_findings. If evidence is missing or uncertain, leave unresolved. '
    'Historical failure alone is not failure of a replacement, and preservation alone is not fresh verification.'
)


def clone(value): return copy.deepcopy(value)
def fingerprint(value): return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


@dataclass
class RepairBudget:
    limit: int = 2
    used: int = 0
    def consume(self):
        if self.used>=self.limit:raise ProtocolError('REPAIR_LIMIT','Shared task repair cap reached')
        self.used+=1


def preflight(packet):
    roles=packet['roles']
    if (roles['integrator']!='A0' or {roles['builder'],roles['checker']}!={'A1','A2'}):
        raise ProtocolError('ROLE_ERROR','Builder and checker must be distinct A1/A2')
    if not packet.get('packet_id') or not packet.get('candidate_identity'):
        raise ProtocolError('PACKET_ERROR','Missing program identity')
    targets=packet['current_targets'];sources=packet['task']['sources']
    if not packet['task'].get('text') or not sources:raise ProtocolError('PACKET_ERROR','Missing public material')
    for target in targets.values():
        if not target.get('definition') or target['candidate_version']!=packet['candidate_identity']['version']:
            raise ProtocolError('PACKET_ERROR','Missing or stale current target')
    for key,issue in packet['issues'].items():
        required=issue['required_case_handles']
        if len(set(required))!=len(required) or not issue.get('acceptance_condition'):
            raise ProtocolError('PACKET_ERROR','Case handles must be unique and acceptance condition present')
        if issue['closure_path'] not in {'repair','rebuttal'}:raise ProtocolError('PACKET_ERROR','Unknown closure path')
        if not issue['current_target_handles'] or not set(issue['current_target_handles'])<=targets.keys():
            raise ProtocolError('PACKET_ERROR','Current target content absent')
        for handle in required:
            case=issue['historical_cases'].get(handle,{})
            if any(name not in case for name in ['source_record_id','audited_version','definition','input','quantity','expected_value','old_observed_value']) or not case['definition']:
                raise ProtocolError('PACKET_ERROR','Original case content absent')
            definition=case['definition']
            if isinstance(definition,dict):
                if set(definition)!={'object_handle'}:raise ProtocolError('PACKET_ERROR','Unknown historical object reference shape')
                source=packet.get('historical_objects',{}).get(definition['object_handle'])
                if not source or not source.get('definition') or source['candidate_version']!=case['audited_version']:
                    raise ProtocolError('PACKET_ERROR','Historical object content absent or stale')
        refs=issue.get('required_task_refs',list(sources))
        if not refs or not set(refs)<=sources.keys():raise ProtocolError('PACKET_ERROR','Required public constraints absent')


def dynamic_schema(base,packet):
    schema=clone(base)
    issue_properties={}
    for key,issue in packet['issues'].items():
        review=clone(schema['$defs']['review'])
        original=review['properties']['original_case_reviews']['items']
        original['properties']['case_handle']={'enum':issue['required_case_handles']} if issue['required_case_handles'] else {'not':{}}
        current=clone(schema['$defs']['check'])
        current['properties']['target_handle']={'enum':issue['current_target_handles']}
        current['properties']['task_refs']['items']={'enum':list(packet['task']['sources'])}
        review['properties']['current_checks']['items']=current
        issue_properties[key]=review
    schema['properties']['issue_reviews']={'type':'object','properties':issue_properties,'required':list(issue_properties),'additionalProperties':False}
    schema['$defs']['check']['properties']['target_handle']={'enum':list(packet['current_targets'])}
    schema['$defs']['check']['properties']['task_refs']['items']={'enum':list(packet['task']['sources'])}
    schema['properties']['new_findings']['items']['properties']['related_issue_handle']={'enum':list(packet['issues'])+[None]}
    return schema


def check_outcome(check):
    if check['outcome']=='counterexample':return 'current_conflict'
    if check['outcome']=='uncertain':return 'needs_review'
    if check['comparison_kind']=='exact_equality':
        expected,observed=exact_rational(check['expected_value']),exact_rational(check['observed_value'])
        if expected is None or observed is None:return 'needs_review'
        if expected!=observed:return 'current_conflict'
    return 'not_refuted'  # A model observation, never proof.


def project_issue(issue,review,source_handles):
    errors=[]
    observed=review['original_case_reviews'];ids=[x['case_handle'] for x in observed]
    if set(ids)!=set(issue['required_case_handles']) or len(ids)!=len(set(ids)):
        errors.append('Original cases must each have one fresh observation')
    historical=[]
    for row in observed:
        case=issue['historical_cases'].get(row['case_handle'])
        if case is None:errors.append('Unknown original case');continue
        assessment=row['original_assessment']
        fresh,old=exact_rational(row['observed_value']),exact_rational(case['old_observed_value'])
        if assessment=='supported' and fresh is not None and old is not None and fresh!=old:
            errors.append('Supported original conflicts with fresh exact observation')
        if assessment=='uncertain' or not row['reason'].strip() or not row['observed_value'].strip():errors.append('Original recheck incomplete')
        historical.append({'case_handle':row['case_handle'],'old_observed_value':case['old_observed_value'],
            'fresh_observed_value':row['observed_value'],'assessment':assessment,'active_effect':'historical_only'})
    checks=review['current_checks'];outcomes=[check_outcome(c) for c in checks]
    if not checks or any(x!='not_refuted' for x in outcomes):errors.append('Current evidence failed or incomplete')
    refs={ref for c in checks for ref in c['task_refs']}
    if not set(issue.get('required_task_refs',source_handles))<=refs:errors.append('Affected task constraints not covered')
    if any(not c['reason'].strip() or not c['quantity'].strip() or not c['input'].strip() or not c['expected_value'].strip() or not c['observed_value'].strip() for c in checks):errors.append('Current calculation missing')
    if not review['reason'].strip() or review['verdict']!='resolved':errors.append('Closure not independently supported')
    path=issue['closure_path'];resolution=review['resolution'];dependency=review['dependency']
    if path=='repair':
        if resolution not in {'same_object_repaired','replaced'}:errors.append('Repair path mismatch')
        if resolution=='same_object_repaired' and dependency!='not_applicable':errors.append('Revised-object version use must be explained')
        if resolution=='replaced' and dependency!='removed':errors.append('Old dependency remains or is unknown')
        if any(r['original_assessment']!='supported' for r in observed):errors.append('Changed historical finding needs rebuttal or unresolved explanation')
    else:
        if resolution!='rebutted' or dependency!='not_applicable':errors.append('Rebuttal path mismatch')
        if observed and not any(r['original_assessment']=='refuted' for r in observed):errors.append('No original evidence actually rebutted')
    return {'status':('addressed' if path=='repair' else 'dismissed') if not errors else 'open',
        'errors':errors,'historical_observations':historical,'current_outcomes':outcomes,
        'semantic_assessment':'model_asserted; not mechanically verified'}


class ReviewAdapter:
    def __init__(self,directory,schema_path,max_input_tokens=32768,max_repairs=2,token_counter=None,shared_budget=None):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.base=json.loads(Path(schema_path).read_text(encoding='utf-8'))
        self.max_input=max_input_tokens;self.max_repairs=max_repairs;self.budget=shared_budget if shared_budget is not None else RepairBudget(max_repairs)
        self.counter=token_counter or (lambda text:len(text.encode('utf-8')))
        self.requests={}
    @property
    def repairs(self):return self.budget.used
    def log(self,name,value):
        with (self.directory/(name+'.jsonl')).open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(value,ensure_ascii=False)+'\n')
    def request(self,packet,feedback=None):
        packet=clone(packet);preflight(packet);schema=dynamic_schema(self.base,packet)
        serialized=json.dumps({'instructions':REVIEW_INSTRUCTIONS,'packet':packet,'schema':schema,'feedback':feedback},ensure_ascii=False,separators=(',',':'))
        size=self.counter(serialized)+256
        if size>self.max_input:raise ProtocolError('CONTEXT_OVERFLOW','Complete review packet exceeds input budget')
        request_id=uuid.uuid4().hex
        self.requests[request_id]={'packet':packet,'schema':schema,'consumed':False}
        self.log('requests',{'request_id':request_id,'instructions':REVIEW_INSTRUCTIONS,'packet':packet,'schema':schema,'feedback':feedback,'input_estimate':size})
        return {'request_id':request_id,'instructions':REVIEW_INSTRUCTIONS,'packet':clone(packet),'schema':clone(schema),'feedback':clone(feedback)}
    def repair(self,request_id,raw,error):
        self.budget.consume()
        return self.request(self.requests[request_id]['packet'],{'error':error,'previous_output':raw})
    def consume(self,request_id,raw,current_identity,response_status='completed'):
        self.log('responses',{'request_id':request_id,'raw':raw,'response_status':response_status})
        request=self.requests.get(request_id)
        global_errors=[]
        if request is None or request['consumed']:global_errors.append('Unknown or already consumed request binding')
        if request is not None:
            request['consumed']=True
            if request['packet']['candidate_identity']!=current_identity:global_errors.append('Stale candidate packet')
        if response_status!='completed':global_errors.append('Incomplete response retained; not accepted')
        try:value=json.loads(raw)
        except json.JSONDecodeError:value=None;global_errors.append('Invalid JSON')
        if global_errors:return self._result(request_id,global_errors,{},[])
        packet=request['packet'];schema=request['schema']
        if (not isinstance(value,dict) or set(value)!={'issue_reviews','new_findings'} or
            not isinstance(value['issue_reviews'],dict) or not isinstance(value['new_findings'],list)):
            return self._result(request_id,['Invalid response envelope'],{},[])
        if set(value['issue_reviews'])-packet['issues'].keys():
            return self._result(request_id,['Unknown issue handle'],{},[])
        # New contradictions are applied before any issue closure.
        findings=[];blocked=set();unlinked=False
        for item in value['new_findings']:
            validator=Draft202012Validator({'$defs':schema['$defs'],**schema['properties']['new_findings']['items']})
            err=[e.message for e in validator.iter_errors(item)]
            outcome=check_outcome(item['check']) if not err else 'needs_review'
            row={'record_id':uuid.uuid4().hex,'raw':clone(item),'errors':err,'outcome':outcome}
            findings.append(row);self.log('new_findings',row)
            if err:
                related=item.get('related_issue_handle') if isinstance(item,dict) else None
                if related in packet['issues']:blocked.add(related)
                else:unlinked=True
            elif outcome!='not_refuted':
                if item['related_issue_handle'] is None:unlinked=True
                else:blocked.add(item['related_issue_handle'])
        decisions={}
        for key,issue in packet['issues'].items():
            review=value['issue_reviews'].get(key)
            if review is None:decisions[key]={'status':'open','errors':['Missing issue review']};continue
            validator=Draft202012Validator({'$defs':schema['$defs'],**schema['properties']['issue_reviews']['properties'][key]})
            errors=[e.message for e in validator.iter_errors(review)]
            if errors:decisions[key]={'status':'open','errors':errors};continue
            decision=project_issue(issue,review,list(packet['task']['sources']))
            for row in decision['historical_observations']:
                self.log('observations',{'record_id':uuid.uuid4().hex,'request_id':request_id,'issue_handle':key,**row})
            for row in review['current_checks']:
                self.log('current_checks',{'record_id':uuid.uuid4().hex,'request_id':request_id,'issue_handle':key,'check':clone(row)})
            if key in blocked:decision['status']='open';decision['errors'].append('New current contradiction on this issue')
            decisions[key]=decision
        result=self._result(request_id,[],decisions,findings)
        result['all_issues_resolved']=not unlinked and all(d['status'] in {'addressed','dismissed'} for d in decisions.values())
        self.log('projection',result)
        return result
    def _result(self,request_id,errors,issues,findings):
        result={'request_id':request_id,'global_errors':errors,'issues':issues,'new_findings':findings,
                'all_issues_resolved':False,'task_correctness_proven':False}
        self.log('validation',result)
        return result
