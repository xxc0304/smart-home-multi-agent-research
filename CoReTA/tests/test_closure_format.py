import copy
import json
import unittest
from pathlib import Path
from coreta.closure_format import FormatClosureRunner, FormatClosureClient, inspection_field_guide
from coreta.schemas import ProtocolError
from test_closure_feedback import FeedbackChecks as _Fixtures

ROOT=Path(__file__).resolve().parents[1]

class FormatChecks(unittest.TestCase):
    setup_runner=_Fixtures.setup_runner

    def historical(self, suffix):
        plan=json.loads((ROOT/'engineering/DIFF_REGRESSION_PLAN_20261019.json').read_text(encoding='utf-8'))
        job=next(j for j in plan['jobs'] if j['task_id'].endswith(suffix))
        folder=ROOT/'runs/diff-regression-20261019'/job['job_id']
        reqs=[json.loads(x) for x in (folder/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
        prompt=reqs[-1]['payload']['instructions']
        material=json.JSONDecoder().raw_decode(prompt[prompt.index('\n{"ACTOR"')+1:])[0]['MATERIAL']
        records=[json.loads(x) for x in (folder/'validation.jsonl').read_text(encoding='utf-8').splitlines()]
        r=self.setup_runner(); r.__class__=FormatClosureRunner
        r.current=copy.deepcopy(material['current']); r.version=material['candidate_version']
        r.issues={i['issue_id']:copy.deepcopy(i) for i in material['issues']}
        r.pending=copy.deepcopy(material['pending_closures'])
        return r,material,records

    def test_generated_fields_distinguish_scope(self):
        r,_,_=self.historical('/156')
        guide=inspection_field_guide(r.contracts.schema('ClosureInspection'))
        self.assertIn('scope',guide['checks[]'])
        self.assertNotIn('scope',guide['closure_reviews[]'])
        self.assertNotIn('check_id',guide['checks[]'])
        for name in ('checks','issues','closure_reviews'):
            self.assertEqual(set(guide[name+'[]']),set(r.contracts.schema('ClosureInspection')['properties'][name]['items']['required']))

    def test_real_unknown_fields_still_rejected(self):
        for task in ('/156','/592'):
            r,_,records=self.historical(task)
            raw=next(x['raw'] for x in records if x['code']=='SCHEMA_ERROR')
            with self.assertRaises(ProtocolError) as caught:
                r.contracts.validate('ClosureInspection',json.loads(raw))
            self.assertIn('Additional properties',caught.exception.detail)

    def test_real_syntax_error_gets_position_and_raw_audit(self):
        r,_,records=self.historical('/156'); raw=records[0]['raw']
        def transport(payload,timeout):
            return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':raw}]}]}
        client=FormatClosureClient(r.config,r.log,transport=transport)
        with self.assertRaises(ProtocolError) as caught:
            client.complete({},deadline=r.deadline,logical_seed='fixture')
        self.assertEqual(caught.exception.code,'INVALID_JSON')
        self.assertIn('offset=2677',caught.exception.detail)
        self.assertEqual(json.loads((r.directory/'json_diagnostics.jsonl').read_text())['raw_output'],raw)

    def test_bounded_scripted_repair_preserves_observations(self):
        r,material,records=self.historical('/156')
        good=json.loads(records[1]['raw'])
        # A scripted valid response is a test fixture, not a live model improvement.
        for review in good['closure_reviews']:
            note=review.pop('scope')
            review['observation']+=' '+note
        r.contracts.validate('ClosureInspection',good)
        outputs=[records[0]['raw'],json.dumps(good)]; requests=[]
        def transport(payload,timeout):
            requests.append(copy.deepcopy(payload))
            return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':outputs[len(requests)-1]}]}]}
        r.client=FormatClosureClient(r.config,r.log,transport=transport)
        result=r.call('inspect','A2','ClosureInspection',material,r.validate_inspection)
        self.assertEqual(result,good); self.assertEqual(r.repairs,1)
        self.assertEqual(r.client.attempts,2)
        self.assertIn('exact_field_names',requests[0]['instructions'])
        self.assertIn('offset=2677',requests[1]['instructions'])
        self.assertEqual(result['issues'],json.loads(records[1]['raw'])['issues'])

    def test_second_invalid_response_stops(self):
        r,material,records=self.historical('/156')
        def transport(payload,timeout):
            return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':records[0]['raw']}]}]}
        r.client=FormatClosureClient(r.config,r.log,transport=transport)
        with self.assertRaises(ProtocolError):r.call('inspect','A2','ClosureInspection',material,r.validate_inspection)
        self.assertEqual(r.client.attempts,2);self.assertEqual(r.repairs,1)

if __name__=='__main__':unittest.main()
