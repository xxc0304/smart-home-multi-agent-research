import copy
import json
import tempfile
import unittest
from pathlib import Path
from coreta.evidence_attribution import AttributionContracts, AttributionRunner, attribution_gate
from coreta.audit_delivery import audit_reference_index
from coreta.schemas import ProtocolError
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/math140-correct-repair-review-v3-20261020'

class AttributionChecks(unittest.TestCase):
    def prepared(self):
        data=json.loads((RUN/'public_component_input.json').read_text(encoding='utf-8'))
        self.material=data['MATERIAL'];self.issues={x['issue_id']:x for x in self.material['issues']}
        self.pending=self.material['pending_closures'];self.version=self.material['current']['version']
        self.refs={self.material['current']['source_event_id']}|{self.material['current']['source_event_id']+'#'+s['id'] for s in self.material['current']['candidate']['steps']}
        value=json.loads((RUN/'inspection.json').read_text(encoding='utf-8'));new=[]
        for issue,original_index in [('i0001',0),('i0004',1)]:
            source=self.issues[issue]['evidence_records'][0]
            history=copy.deepcopy(source['payload']);history.update(evidence_scope='historical',audited_version=source['candidate_version'],source_record_id=source['record_id'])
            new.append(history)
            current=copy.deepcopy(value['audit_records'][original_index])
            current['cases']=current['cases'][4:] if issue=='i0001' else current['cases'][2:]
            current.update(evidence_scope='current',audited_version=self.version,source_record_id=None,model_verdict='not_refuted')
            new.append(current)
        value['audit_records']=new
        for review in value['closure_reviews']:
            issue=review['issue_id'];review['replacement_bridge']=None
            if issue in ['i0001','i0004']:
                index=1 if issue=='i0001' else 3
                review['replacement_bridge']={'dependency_status':'removed','original_record_ids':[r['record_id'] for r in self.issues[issue]['evidence_records']],
                    'current_record_indexes':[index],'explanation':'SYNTHETIC FIXTURE: old objects discarded; explicit replacement basis tests support the repaired dependency.',
                    'evidence_refs':[self.material['current']['source_event_id']]}
        return value
    def gate(self,value):return attribution_gate(value,self.issues,self.pending,self.version,self.refs)
    def test_original_mixed_output_not_automatically_migrated(self):
        self.prepared();original=json.loads((RUN/'inspection.json').read_text(encoding='utf-8'))
        with self.assertRaises(ProtocolError):AttributionContracts(ROOT/'design/v0.3/coreta.schema.json').validate('ClosureInspection',original)
    def test_explicit_synthetic_split_passes(self):
        value=self.prepared();AttributionContracts(ROOT/'design/v0.3/coreta.schema.json').validate('ClosureInspection',value)
        self.assertEqual(self.gate(value),([],{0,2}))
    def test_still_used_and_unknown_block(self):
        for state in ['still_used','unknown']:
            value=self.prepared();value['closure_reviews'][0]['replacement_bridge']['dependency_status']=state
            self.assertTrue(self.gate(value)[0])
    def test_failed_replacement_blocks_even_if_unlisted(self):
        value=self.prepared();value['audit_records'][1]['cases'][0]['observed_value']='1'
        self.assertTrue(self.gate(value)[0])
        extra=copy.deepcopy(value['audit_records'][1]);value=self.prepared();value['audit_records'].append(extra)
        self.assertTrue(self.gate(value)[0])
    def test_original_observation_cannot_be_erased(self):
        value=self.prepared();value['audit_records'][0]['cases'][0]['observed_value']='0'
        self.assertTrue(self.gate(value)[0])
    def test_wrong_version_or_source_blocks(self):
        for field,val in [('audited_version',999),('source_record_id','invented')]:
            value=self.prepared();value['audit_records'][0][field]=val
            self.assertTrue(self.gate(value)[0])
    def test_missing_current_constraint_blocks(self):
        value=self.prepared();value['audit_records'][1]['cases']=value['audit_records'][1]['cases'][:1]
        self.assertTrue(self.gate(value)[0])
    def test_real_schema_state_machine_preserves_history_and_closes_fixture(self):
        value=self.prepared();before=copy.deepcopy(value)
        with tempfile.TemporaryDirectory() as tmp:
            r=AttributionRunner(self.material['task'],Path(tmp),'attribution-fixture',AttributionContracts(ROOT/'design/v0.3/coreta.schema.json'),None,
                json.loads((ROOT/'config/deepseek_flash_inspection.json').read_text()),json.loads((ROOT/'design/source_binding_prompts.json').read_text()))
            r.current=copy.deepcopy(self.material['current']);r.version=self.version;r.issues=copy.deepcopy(self.issues)
            r.pending=copy.deepcopy(self.pending);r.task_facts=self.material['task_facts'];r._last_builder='A1'
            accepted=r.accept_inspection(value,'A2',set(audit_reference_index(self.material)))
            self.assertEqual(accepted['errors'],[])
            r.settle(value,'A2')
            self.assertEqual(r.issues['i0001']['status'],'addressed')
            self.assertEqual(r.audit_ledger[0]['effective_outcome'],'finding_open')
            self.assertEqual(r.audit_ledger[0]['active_effect'],'historical_retained')
            self.assertEqual(r.issues['i0001']['evidence_records'][0],self.issues['i0001']['evidence_records'][0])
            self.assertEqual(value,before)

if __name__=='__main__':unittest.main()
