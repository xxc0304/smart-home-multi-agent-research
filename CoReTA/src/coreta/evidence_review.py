"""Evidence review boundary with proposal path supplied by the program."""
import json
import uuid
from pathlib import Path
from jsonschema import Draft202012Validator
from .minimal_review import RepairBudget,clone,check_outcome
from .aligned_review import align_packet,preflight,dynamic_schema
from .task_audit import exact_rational
from .schemas import ProtocolError

REVIEW_INSTRUCTIONS = (
    'Review the current candidate independently. Use the complete public task, supplied targets, '
    'original cases and each issue acceptance_condition. The integrator closure_path is a PROPOSAL '
    'to be verified, not truth. It is supplied as input; do not output resolution or dependency labels. '
    'Answer in reason: (1) does fresh calculation confirm the original observation, '
    '(2) how does the current candidate repair or replace the affected premise and is that bridge valid, '
    '(3) does evidence actually satisfy this closure proposal? If the path is inappropriate, evidence '
    'is missing, old error is still relied on or the connection is uncertain, return unresolved/defect. '
    'original_assessment evaluates ONLY the recorded observation: supported confirms old_observed_value; '
    'refuted means that observation is wrong, not merely that an old candidate was refuted. '
    'For exact_equality return ONLY canonical integers or reduced rational scalars in expected_value '
    'and observed_value. Put calculations in reason. Use model_judged for nonzero, integrality, pairs '
    'or qualitative assertions. Numerical agreement is not a proof that the reasoning is valid. '
    'current_checks tests claims the CURRENT target needs to satisfy; counterexample means a conflict '
    'with the CURRENT target, never merely a rejection of a discarded answer. Keep reason, observed '
    'value and outcome consistent; a calculation contradicting the claim must not be marked match. '
    'Recompute every required original case, and cover affected task refs. With reviewer_selected '
    'coverage choose relevant supplied refs and check the acceptance condition; no exhaustiveness '
    'follows from a citation. Keep history distinct from new observations and current checks. '
    'Use only supplied handles. Return only the specified output fields; no generated IDs or array '
    'cross-reference indexes. Put new current contradictions in new_findings; preserve uncertainty.'
)


def project_issue(issue,review,source_handles):
    errors=[];historical=[]
    rows=review['original_case_reviews'];ids=[r['case_handle'] for r in rows]
    if set(ids)!=set(issue['required_case_handles']) or len(ids)!=len(set(ids)):
        errors.append('Original cases must each have one fresh observation')
    for row in rows:
        case=issue['historical_cases'].get(row['case_handle'])
        if case is None:errors.append('Unknown original case');continue
        old,fresh=exact_rational(case['old_observed_value']),exact_rational(row['observed_value'])
        assessment=row['original_assessment']
        if old is not None and fresh is not None:
            if assessment=='supported' and old!=fresh:errors.append('Supported original conflicts with fresh scalar')
            if assessment=='refuted' and old==fresh:errors.append('Refuted original conflicts with unchanged scalar')
        if assessment=='uncertain' or not row['reason'].strip() or not row['observed_value'].strip():
            errors.append('Original recheck incomplete')
        historical.append({'case_handle':row['case_handle'],'old_observed_value':case['old_observed_value'],
            'fresh_observed_value':row['observed_value'],'assessment':assessment,'active_effect':'historical_only'})
    checks=review['current_checks'];outcomes=[check_outcome(c) for c in checks]
    if not checks or any(o!='not_refuted' for o in outcomes):errors.append('Current evidence failed or incomplete')
    refs={ref for c in checks for ref in c['task_refs']}
    if issue.get('task_coverage_mode')!='reviewer_selected' and not set(issue.get('required_task_refs',source_handles))<=refs:
        errors.append('Affected task constraints not covered')
    if any(not c[name].strip() for c in checks for name in ['reason','input','quantity','expected_value','observed_value']):
        errors.append('Current calculation missing')
    if not review['reason'].strip() or review['verdict']!='resolved':errors.append('Closure not independently supported')
    if issue['closure_path']=='repair' and any(r['original_assessment']!='supported' for r in rows):
        errors.append('Original finding disputed; repair proposal needs clarification or rebuttal')
    # Rebuttal can challenge a premise/applicability even if the recorded observation is correct.
    return {'status':('addressed' if issue['closure_path']=='repair' else 'dismissed') if not errors else 'open',
        'errors':errors,'historical_observations':historical,'current_outcomes':outcomes,
        'task_coverage_mode':issue.get('task_coverage_mode','explicit_constraints'),
        'task_exhaustiveness_proven':False,'semantic_assessment':'model_asserted; not mechanically verified'}


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
