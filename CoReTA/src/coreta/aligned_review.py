"""Aligned flat review boundary. Frozen previous prototype is unchanged."""
import copy
import json
import uuid
from pathlib import Path
from jsonschema import Draft202012Validator
from .minimal_review import RepairBudget,clone,check_outcome
from .minimal_review import preflight as original_preflight, dynamic_schema as original_schema, project_issue as original_project
from .task_audit import exact_rational
from .schemas import ProtocolError

REVIEW_INSTRUCTIONS = (
    'Review the current candidate independently using the public task and supplied evidence. '
    'original_assessment assesses ONLY the original recorded OBSERVATION: supported means your fresh '
    'calculation confirms old_observed_value; refuted means the old recorded value is wrong. '
    'If old g fails as originally reported, the audit observation is SUPPORTED even though g is refuted. '
    'For exact_equality expected_value and observed_value MUST be ONLY canonical integers or reduced '
    'rational scalars (0, -1, 5/19). Put all equations and derivations in reason. '
    'Use model_judged for nonzero, integrality, ordered pairs and other qualitative comparisons. '
    'current_checks must test claims that need to hold for the CURRENT target to be correct. '
    'A counterexample to a discarded answer belongs in the historical recheck or explanation, '
    'not as a counterexample to the current candidate. '
    'Cover required original cases and affected task refs when supplied. For reviewer_selected coverage '
    'choose relevant supplied task refs and actually check the acceptance condition; no full-task '
    'exhaustiveness is inferred from citing a source. '
    'Explain same-object repair, replacement or rebuttal. A rebuttal can challenge an original value '
    'or its expected premise/applicability; preserve original observations and show your fresh work. '
    'Use only supplied handles, no generated IDs or array cross-reference indexes. '
    'Return the complete output schema. Uncertainty stays unresolved; new current contradictions go '
    'to new_findings. Never suppress a real mathematical conflict to satisfy formatting.'
)


def align_packet(packet):
    packet=clone(packet)
    for issue in packet['issues'].values():
        if issue['required_case_handles']:
            issue['task_coverage_mode']='original_case_constraints'
        else:
            issue['task_coverage_mode']='reviewer_selected'
            issue['required_task_refs']=[]
    return packet


def preflight(packet):
    probe=clone(packet)
    for issue in probe['issues'].values():
        if issue.get('task_coverage_mode')=='reviewer_selected':
            if issue['required_case_handles']:raise ProtocolError('PACKET_ERROR','Original case constraints cannot be waived')
            issue['required_task_refs']=list(probe['task']['sources'])
    return original_preflight(probe)


def dynamic_schema(base,packet):
    schema=original_schema(base,packet)
    pattern=r'^-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?$'
    for key,issue in packet['issues'].items():
        item=schema['properties']['issue_reviews']['properties'][key]['properties']['original_case_reviews']['items']
        conditions=[]
        for handle,case in issue['historical_cases'].items():
            if exact_rational(case['old_observed_value']) is not None:
                conditions.append({'if':{'properties':{'case_handle':{'const':handle}},'required':['case_handle']},
                    'then':{'properties':{'observed_value':{'pattern':pattern}}}})
        if conditions:item['allOf']=conditions
    return schema


def project_issue(issue,review,source_handles):
    projected_issue=clone(issue)
    if issue.get('task_coverage_mode')=='reviewer_selected':
        # At least one actual current check with valid task refs is still required.
        projected_issue['required_task_refs']=[]
    decision=original_project(projected_issue,review,source_handles)
    for row in review['original_case_reviews']:
        case=issue['historical_cases'].get(row['case_handle'])
        if case is None:continue
        old=exact_rational(case['old_observed_value']);fresh=exact_rational(row['observed_value'])
        if row['original_assessment']=='refuted' and old is not None and fresh is not None and old==fresh:
            decision['errors'].append('Original scalar observation is unchanged, so refuted contradicts the submitted evidence')
    # Observation correctness is distinct from applicability of the old objection.
    if (issue['closure_path']=='rebuttal' and review['resolution']=='rebutted' and review['dependency']=='not_applicable'
            and review['reason'].strip()):
        decision['errors']=[e for e in decision['errors'] if e!='No original evidence actually rebutted']
        decision['rebuttal_basis']='Independent model reasoning; applicability not mechanically proven'
    decision['task_coverage_mode']=issue.get('task_coverage_mode','explicit_constraints')
    decision['task_exhaustiveness_proven']=False
    if decision['errors']:decision['status']='open'
    elif review['verdict']=='resolved':decision['status']='dismissed' if issue['closure_path']=='rebuttal' else 'addressed'
    return decision


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
        packet=align_packet(packet);preflight(packet);schema=dynamic_schema(self.base,packet)
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
