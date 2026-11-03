"""Compose existing solving stages with evidence-review packets; no Runner subclass."""
import copy
import time
import uuid
from pathlib import Path
from .closure import digest
from .minimal_review import RepairBudget
from .evidence_review import ReviewAdapter
from .minimal_review_transport import execute_review
from .schemas import ProtocolError
from .state import write_json

VARIANT='coreta_converged_flow'

class ConvergedFlow:
    def __init__(self,backend,schema_path,token_counter=None):
        self.b=backend;self.schema_path=Path(schema_path);self.counter=token_counter
        self.budget=RepairBudget(backend.config['protocol']['max_format_repairs'],backend.repairs)
        self.snapshots={};self.native_ledger=[];self.review_trace=[];self.last_valid_review=None
    def remember(self):
        if self.b.current:
            self.snapshots[(self.b.version,digest(self.b.current['candidate']))]=copy.deepcopy(self.b.current)
    def packet(self,built,checker):
        b=self.b
        sources={'T1':b.task['prompt']}
        for fact in b.task_facts['payload']['facts']:
            for item in fact['check_items']:
                sources['T'+str(len(sources)+1)]={'quoted_text':fact['quoted_text'],'check_item':item['description'],'interpretation_status':'model_asserted'}
        p={'packet_id':b.run_id+'-review-'+str(len(self.review_trace)),
            'candidate_identity':{'version':b.version,'hash':digest(b.current['candidate'])},
            'roles':{'integrator':'A0','builder':built['sent_from'],'checker':checker},
            'task':{'text':b.task['prompt'],'sources':sources},
            'current_targets':{'C1':{'definition':b.current['candidate']['artifact'],'candidate_version':b.version}},
            'historical_objects':{},'issues':{},'contribution':copy.deepcopy(built),
            'supporting_history':[]}
        for event in b.drafts:
            p['supporting_history'].append({'event_id':event['event_id'],'excerpt_notice':'Exact original draft steps','payload':{'steps':copy.deepcopy(event['payload']['steps'])}})
        mapping={};n=0;objects={}
        active={k:i for k,i in b.issues.items() if k in b.pending or i['status'] not in {'addressed','dismissed'}}
        for key,issue in active.items():
            n+=1;handle='I'+str(n);mapping[handle]=key;proposal=b.pending.get(key)
            row={'closure_path':proposal['closure_path'] if proposal else 'repair',
                'closure_requested':proposal is not None,'acceptance_condition':issue['acceptance_condition'],
                'description':issue['description'],'active_objections':copy.deepcopy(issue['objections']),
                'proposed_resolution_reason':proposal['reason'] if proposal else 'Inspection only: no closure has been proposed.',
                'required_case_handles':[],'historical_cases':{},'current_target_handles':['C1'],'required_task_refs':[]}
            for record in issue.get('evidence_records',[]):
                if record.get('format')!='minimal_review_current_check/v1':
                    raise ProtocolError('PACKET_ERROR','Legacy evidence requires explicit migration, not silent coercion')
                identity=(record['candidate_version'],record['candidate_hash'])
                if identity not in self.snapshots:raise ProtocolError('PACKET_ERROR','Original candidate snapshot unavailable')
                if identity not in objects:
                    obj='O'+str(len(objects)+1);objects[identity]=obj
                    p['historical_objects'][obj]={'candidate_version':identity[0],'candidate_hash':identity[1],
                        'definition':self.snapshots[identity]['candidate']['artifact']}
                c=record['check'];case='H'+str(sum(len(x['historical_cases']) for x in p['issues'].values())+len(row['historical_cases'])+1)
                for task_ref in c['task_refs']:
                    if sources.get(task_ref)!=record['task_sources'].get(task_ref):
                        raise ProtocolError('PACKET_ERROR','Original public constraint identity changed')
                    if task_ref not in row['required_task_refs']:row['required_task_refs'].append(task_ref)
                row['required_case_handles'].append(case)
                row['historical_cases'][case]={'source_record_id':record['record_id'],'audited_version':identity[0],
                    'definition':{'object_handle':objects[identity]},'input':c['input'],'quantity':c['quantity'],
                    'expected_value':c['expected_value'],'old_observed_value':c['observed_value'],'task_refs':c['task_refs']}
            if not row['required_task_refs']:row['required_task_refs']=['T1']
            p['issues'][handle]=row
        if not p['issues']:
            mapping['Q0']=None
            p['issues']['Q0']={'closure_path':'repair','closure_requested':False,'routine_inspection_ticket':True,
                'acceptance_condition':'Actually verify a decisive dependency of the current candidate against the public task; report any concrete defect.',
                'required_case_handles':[],'historical_cases':{},'current_target_handles':['C1'],'required_task_refs':['T1']}
        return p,mapping
    def add_finding(self,event,check,packet,key=None):
        b=self.b
        proposal={'description':'Current check: '+check['quantity']+'; observed '+check['observed_value']+'; '+check['reason'],
            'blocking':True,'target_refs':[b.current['source_event_id']],'existing_issue_id':key,
            'acceptance_condition':'Recompute the stored original case, repair the current claim or rebut the observation, and verify affected public constraints.'}
        if key is None:key='i'+str(len(b.issues)+1).zfill(4)
        b.proposed_issues([proposal],event['event_id'],b.issues)
        record={'record_id':uuid.uuid4().hex,'format':'minimal_review_current_check/v1','event_id':event['event_id'],
            'auditor':event['sent_from'],'candidate_version':b.version,'candidate_hash':digest(b.current['candidate']),
            'check':copy.deepcopy(check),'task_sources':{ref:copy.deepcopy(packet['task']['sources'][ref]) for ref in check['task_refs']}}
        b.issues[key].setdefault('evidence_records',[]).append(copy.deepcopy(record))
        self.native_ledger.append(record);b.log('native_evidence.jsonl',record)
        return key
    def review(self,built,checker,turn):
        b=self.b
        if b.calls>=14:raise ProtocolError('CALL_LIMIT','Fourteen logical stages exhausted')
        packet,mapping=self.packet(built,checker);self.budget.used=b.repairs
        adapter=ReviewAdapter(b.directory/f'review-{turn}',self.schema_path,token_counter=self.counter,shared_budget=self.budget,
            max_input_tokens=b.config['generation']['max_input_tokens'])
        b.calls+=1
        http_before=b.client.attempts
        result=execute_review(adapter,b.client,packet,timeout_seconds=max(0,b.deadline-time.monotonic()))
        b.repairs=self.budget.used
        result['stage_http_attempts']=b.client.attempts-http_before
        trace={'turn':turn,'packet':packet,'mapping':mapping,'execution':result};self.review_trace.append(trace)
        b.log('minimal_reviews.jsonl',trace)
        projection=result['final_projection']
        if result['terminal_error'] or not projection or projection['global_errors']:
            error=result['terminal_error'] or {'code':'REVIEW_ERROR','detail':str(projection['global_errors'] if projection else 'No review response')}
            raise ProtocolError(error['code'],error['detail'])
        # Adapter logs preserve the actual provider output; this event references the projection.
        event={'event_id':f'{b.run_id}:e{len(b.events):04d}','schema_version':'coreta/converged-review',
            'sent_from':checker,'base_version':b.version,'stage':'inspect','task_id':b.task['task_id'],
            'payload':{'projection':copy.deepcopy(projection),'review_packet_id':packet['packet_id']}}
        b.log('events.jsonl',event);b.events.append(event)
        contested=set();native=[]
        # Reconstruct only current observations from stored adapter rows; never promote historical failures.
        path=adapter.directory/'current_checks.jsonl'
        if path.exists():
            import json
            for line in path.read_text(encoding='utf-8').splitlines():
                row=json.loads(line)
                if row['request_id']!=projection['request_id']:continue
                native.append(row)
        for row in native:
            handle=row['issue_handle'];decision=projection['issues'].get(handle,{})
            # Re-evaluate explicit current check values; a business error cannot erase submitted evidence.
            from .minimal_review import check_outcome
            if check_outcome(row['check']) in {'current_conflict','needs_review'}:
                contested.add(self.add_finding(event,row['check'],packet,mapping[handle]))
        for finding in projection['new_findings']:
            if finding['errors']:continue
            if finding['outcome'] in {'current_conflict','needs_review'}:
                h=finding['raw']['related_issue_handle'];key=mapping.get(h) if h is not None else None
                contested.add(self.add_finding(event,finding['raw']['check'],packet,key))
        complete=projection['all_issues_resolved'] and not contested
        invalid_findings=[f for f in projection['new_findings'] if f['errors']]
        if invalid_findings:
            b.proposed_issues([{'description':'New review finding could not be validated: '+str([f['errors'] for f in invalid_findings]),
                'blocking':True,'target_refs':[b.current['source_event_id']],'existing_issue_id':None,
                'acceptance_condition':'Recheck and submit the finding with valid public constraints and current target.'}],event['event_id'],b.issues)
        for handle,decision in projection['issues'].items():
            key=mapping[handle]
            if decision['status']=='open':complete=False
            if key is None:
                if decision['status']=='open' and not contested:
                    proposal={'description':'Independent current-candidate review incomplete: '+str(decision['errors']),
                        'blocking':True,'target_refs':[b.current['source_event_id']],'existing_issue_id':None,
                        'acceptance_condition':'Provide a complete independent check of the current decisive dependency.'}
                    b.proposed_issues([proposal],event['event_id'],b.issues)
                continue
            if key in b.pending:
                issue=b.issues[key]
                issue['status']=decision['status'] if key not in contested else 'open'
                issue['handling_events'].append({'review_event':event['event_id'],'version':b.version,
                    'proposal':copy.deepcopy(b.pending[key]),'decision':copy.deepcopy(decision)})
        b.pending={}
        self.last_valid_review=copy.deepcopy(b.current) if complete else None
        b.last_reviewed=copy.deepcopy(self.last_valid_review)
        return result
    def collaborate(self):
        b=self.b
        facts=b.call('task_facts','A2','TaskFacts',{'task':copy.deepcopy(b.task)})
        b.task_facts=b.emit('task_facts','A2',facts)
        value=b.call('synthesize','A0','Synthesis',b.view());registry={}
        b.proposed_issues(value['issues'],f'{b.run_id}:e{len(b.events):04d}',registry)
        b.candidate_commit('synthesize',value,registry);self.remember()
        actor='A1';requested={'goal':'Repair active objections or reconstruct a decisive dependency','issue_ids':[]}
        for turn in range(3):
            checker='A2' if actor=='A1' else 'A1'
            built_value=b.call('build' if turn==0 else 'work',actor,'Constructive',
                {**b.view(),'request':{**requested,'active_blocking_issue_ids':[i['issue_id'] for i in b.blockers()]}},b.validate_work)
            built=b.record('build' if turn==0 else 'work',actor,built_value)
            b.attempts.append({'event_id':built['event_id'],'issue_ids':built_value['attempted_issue_ids']})
            value=b.call('apply','A0','ClosureUpdate',{**b.view(),'evidence':[built],'remaining_work_turns':2-turn},b.validate_proposals)
            b.commit_proposals(value);self.remember()
            review=self.review(built,checker,turn)
            if not b.blockers() and self.last_valid_review and value['next']['action'].startswith('FINISH'):
                return 'complete'
            if b.blockers() and built_value['status']=='cannot_help' and value['next']['action']=='FINISH_STALLED':
                attempted={key for a in b.attempts for key in a['issue_ids']}
                if all(i['issue_id'] in attempted for i in b.blockers()):return 'stalled'
            requested=copy.deepcopy(value['next']);requested['post_application_review']=review['final_projection']
            actor=value['next']['recipient'] if value['next']['recipient'] in {'A1','A2'} else checker
        return 'budget_exhausted'
    def run(self):
        b=self.b;errors=[];status='completed';stop='not_started'
        try:
            b.initial_drafts();self.remember();stop=self.collaborate()
        except ProtocolError as exc:
            status='degraded';stop='runtime_error';errors.append({'code':exc.code,'detail':exc.detail})
        result={'protocol_variant':VARIANT,'status':status if b.current else 'failed','stop_reason':stop,'task_id':b.task['task_id'],
            'artifact':b.current['candidate']['artifact'] if b.current else '',
            'delivery_candidate':copy.deepcopy(b.current),'normal_calls':b.calls,'http_attempts':b.client.attempts,
            'format_repairs':b.repairs,'issues':b.issues,'errors':errors,'review_count':len(self.review_trace),
            'review_status':'reviewed' if b.current==self.last_valid_review and b.current else 'unreviewed',
            'native_evidence_count':len(self.native_ledger),'finalizer_changed':False,'semantic_correctness_proven':False}
        write_json(b.directory/'result.json',result)
        return result
