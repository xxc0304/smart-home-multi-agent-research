"""Explicit historical/current attribution; old evidence is never rewritten."""
import copy
from datetime import datetime, timezone
from .protocol_stability import StabilityRunner
from .task_audit_binding import SourceBindingContracts
from .task_audit import effective_outcome
from .revision import obj,text,array,choice
from .closure import digest
from .audit_delivery import audit_reference_index
from .state import write_json

VARIANT='task_audit_attribution_v7'

class AttributionContracts(SourceBindingContracts):
    def __init__(self,path):
        super().__init__(path)
        record=self.document['$defs']['ClosureInspection']['properties']['audit_records']['items']
        record['properties'].update(evidence_scope=choice('current','historical'),
            audited_version={'type':'integer','minimum':0},
            source_record_id={'anyOf':[text(160),{'type':'null'}]})
        record['required']+=['evidence_scope','audited_version','source_record_id']
        review=self.document['$defs']['ClosureInspection']['properties']['closure_reviews']['items']
        bridge=obj(dependency_status=choice('removed','still_used','unknown'),
            original_record_ids=array(text(160),100),current_record_indexes=array({'type':'integer','minimum':0},6),
            explanation=text(3000),evidence_refs=array(text(120)))
        review['properties']['replacement_bridge']={'anyOf':[bridge,{'type':'null'}]}
        review['required'].append('replacement_bridge')


def attribution_gate(value,issues,pending,version,current_refs):
    errors=[];eligible=set();historical={}
    records=value['audit_records']
    for index,record in enumerate(records):
        key=record['existing_issue_id']
        if record['evidence_scope']=='current':
            if record['source_record_id'] is not None or record['audited_version']!=version:
                errors.append('Current audit must bind current version without historical source')
            if not set(record['target_refs']) & set(current_refs):
                errors.append('Current audit requires a current candidate target')
        else:
            original=next((r for r in issues.get(key,{}).get('evidence_records',[]) if r['record_id']==record['source_record_id']),None)
            if original is None:
                errors.append('Historical source must belong to the same issue');continue
            if any(record.get(k)!=v for k,v in original['payload'].items() if k!='existing_issue_id'):
                errors.append('Historical audit payload must remain unchanged apart from explicit issue attribution')
            if record['audited_version']!=original['candidate_version'] or record['claim_text']!=original['payload']['claim_text']:
                errors.append('Historical version and original claim must remain unchanged')
            # Preserve cases as values, including IDs, expected values and observations.
            if record['cases']!=original['payload']['cases']:
                errors.append('Historical cases must preserve original exact payload; mixed records are invalid')
            if record['task_fact_ids']!=original['payload']['task_fact_ids'] or record['check_item_ids']!=original['payload']['check_item_ids']:
                errors.append('Historical constraint bindings must remain unchanged')
            historical.setdefault(key,[]).append((index,original['record_id']))
    for review in value['closure_reviews']:
        key=review['issue_id'];proposal=pending.get(key)
        if not proposal or proposal['closure_path']!='repair':continue
        originals={r['record_id'] for r in issues.get(key,{}).get('evidence_records',[])}
        if not originals:continue
        bridge=review['replacement_bridge']
        if not bridge:
            errors.append('Repair with original audit evidence requires replacement bridge');continue
        listed=bridge['current_record_indexes']
        if (bridge['dependency_status']!='removed' or set(bridge['original_record_ids'])!=originals or
                {r for _,r in historical.get(key,[])}!=originals or not listed or len(set(listed))!=len(listed) or
                not bridge['explanation'].strip() or not set(bridge['evidence_refs']) & set(current_refs)):
            errors.append('Replacement bridge lacks removal, original rechecks or current evidence');continue
        valid=True
        for index in listed:
            if index>=len(records):valid=False;continue
            row=records[index]
            if (row['existing_issue_id']!=key or row['evidence_scope']!='current' or
                    effective_outcome(row)!='not_refuted_within_recorded_scope'):
                valid=False
        # Any current finding on this issue vetoes closure, including unlisted ones.
        if any(r['existing_issue_id']==key and r['evidence_scope']=='current' and
               effective_outcome(r)!='not_refuted_within_recorded_scope' for r in records):valid=False
        required_items={(c['fact_id'],c['check_item_id']) for r in issues[key].get('evidence_records',[]) for c in r['payload']['cases']}
        current_items={(c['fact_id'],c['check_item_id']) for i in listed if i<len(records) for c in records[i]['cases']}
        if not required_items<=current_items:valid=False
        if not valid:errors.append('Replacement candidate has failed, missing or unrelated current audit');continue
        if review['verdict']=='resolved':eligible.update(i for i,_ in historical.get(key,[]))
    return list(dict.fromkeys(errors)),eligible


class AttributionRunner(StabilityRunner):
    def call(self,stage,actor,schema_name,material,validate=None):
        if stage=='inspect':
            material={**copy.deepcopy(material),'evidence_attribution_contract':
                'Each audit record is current or historical, never mixed. Historical uses exact original claim, '
                'version, source_record_id and complete unchanged cases. Current uses current version, '
                'source_record_id=null and current candidate targets. For repair with prior evidence, '
                'replacement_bridge must bind original IDs and zero-based indexes of successful current audits, '
                'explain removal of the refuted dependency and cite current evidence. If dependency remains '
                'or is unknown, do not resolve. Preserve all original counterexamples. This is a model-checked '
                'dependency explanation, not mechanically proven removal.'}
        return super().call(stage,actor,schema_name,material,validate)

    def accept_inspection(self,value,actor,visible=None):
        self.contracts.validate('ClosureInspection',value)
        fingerprint=(self.version,actor,digest(value))
        if fingerprint in self._accepted:return self._accepted[fingerprint]
        event=self.emit('inspect',actor,value)
        visible=set(audit_reference_index(self.view())) if visible is None else visible
        errors=self._inspection_errors(value,actor,visible)
        current_refs={self.current['source_event_id']}|{f"{self.current['source_event_id']}#{s['id']}" for s in self.current['candidate']['steps']}|{f"v{self.version}:{s['id']}" for s in self.current['candidate']['steps']}
        extra,eligible=attribution_gate(value,self.issues,self.pending,self.version,current_refs)
        errors=list(dict.fromkeys(errors+extra));original_issue_ids=set(self.issues);contested=set()
        for index,payload in enumerate(value['audit_records']):
            outcome=effective_outcome(payload)
            historical_ok=not errors and index in eligible
            row={'record_id':f"{event['event_id']}:a{index+1:02d}",'event_id':event['event_id'],
                'auditor':actor,'submitted_at':datetime.now(timezone.utc).isoformat(),
                'candidate_version':value['candidate_version'],'candidate_hash':value['candidate_hash'],
                'payload':copy.deepcopy(payload),'effective_outcome':outcome,
                'validation_errors':copy.deepcopy(errors),'active_effect':'historical_retained' if historical_ok else outcome}
            self.log('audit_ledger.jsonl',row);self.audit_ledger.append(copy.deepcopy(row))
            items=self._items()
            available={k for k,f in items.items() if f in payload['task_fact_ids']}
            tested={c['check_item_id'] for c in payload['cases']}
            self.log('item_coverage.jsonl',{'record_id':row['record_id'],'model_coverage':payload['coverage'],
                'available_declared_item_ids':sorted(available),'case_item_ids':sorted(tested),
                'all_declared_items_mentioned':tested==available,'task_exhaustiveness_proven':False,
                'semantic_status':'model_asserted','validation_errors':copy.deepcopy(errors)})
            if not historical_ok and outcome in {'finding_open','needs_check'}:
                contested.add(self._finding(row,event,outcome,original_issue_ids))
        for proposal in value['issues']:
            key=proposal['existing_issue_id']
            if key is not None and key not in original_issue_ids:continue
            if key is None:key=f'i{len(self.issues)+1:04d}'
            self.proposed_issues([proposal],event['event_id'],self.issues);contested.add(key)
        if errors:
            self.proposed_issues([{'description':'Attribution audit validation: '+'; '.join(errors),'blocking':True,
                'target_refs':[self.current['source_event_id']],'existing_issue_id':None,
                'acceptance_condition':'Repeat an independent correctly attributed audit.'}],event['event_id'],self.issues)
        accepted={'event':event,'errors':errors,'contested':contested}
        self._accepted[fingerprint]=accepted
        return accepted

    def run(self):
        result=super().run()
        result['protocol_variant']=VARIANT
        write_json(self.directory/'result.json',result)
        return result
