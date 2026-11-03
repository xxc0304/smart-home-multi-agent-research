import copy
import json
import tempfile
import unittest
from pathlib import Path
from coreta.closure import ClosureClient, ClosureContracts
from coreta.closure_feedback import FeedbackClosureRunner
from coreta.schemas import ProtocolError
from test_revision import TASK

ROOT=Path(__file__).resolve().parents[1]


class FeedbackChecks(unittest.TestCase):
    def setup_runner(self):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        cfg=json.loads((ROOT/'config/deepseek_flash_closure.json').read_text(encoding='utf-8'))
        cfg['generation']['max_input_tokens']=1000000
        prompts=json.loads((ROOT/'design/closure_prompts.json').read_text(encoding='utf-8'))
        return FeedbackClosureRunner(TASK,Path(tmp.name),'feedback-fixture',
            ClosureContracts(ROOT/'design/v0.3/coreta.schema.json'),None,cfg,prompts)

    def historical(self):
        folder=ROOT/'runs/math140-recovery-20261019/postcheck'
        reqs=[json.loads(x) for x in (folder/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
        prompt=reqs[-1]['payload']['instructions']
        material=json.JSONDecoder().raw_decode(prompt[prompt.index('\n{"ACTOR"')+1:])[0]['MATERIAL']
        records=[json.loads(x) for x in (folder/'validation.jsonl').read_text(encoding='utf-8').splitlines()]
        bad=json.loads(records[-1]['raw'])
        r=self.setup_runner(); r.current=copy.deepcopy(material['current'])
        r.version=material['candidate_version']; r.issues={i['issue_id']:copy.deepcopy(i) for i in material['issues']}
        r.pending=copy.deepcopy(material['pending_closures'])
        return r, material, bad

    def test_real_i0004_error_lists_legal_and_illegal_ids(self):
        r,_,bad=self.historical()
        with self.assertRaises(ProtocolError) as caught: r.validate_inspection(bad)
        message=caught.exception.detail
        self.assertIn("['i0001', 'i0002', 'i0003']",message)
        self.assertIn("'i0004': 'open'",message)
        self.assertIn('existing_issue_id',message)
        self.assertEqual(r.issues['i0004']['status'],'open')

    def test_real_repair_preserves_objections_and_bounded_retry(self):
        r,material,bad=self.historical(); good=copy.deepcopy(bad)
        good['closure_reviews']=[x for x in good['closure_reviews'] if x['issue_id']!='i0004']
        responses=[bad,good]; requests=[]
        def transport(payload,timeout):
            requests.append(copy.deepcopy(payload))
            value=responses[len(requests)-1]
            return {'status':'completed','output':[{'type':'message','content':[
                {'type':'output_text','text':json.dumps(value)}]}]}
        r.client=ClosureClient(r.config,r.log,transport=transport)
        result=r.call('inspect','A2','ClosureInspection',material,r.validate_inspection)
        self.assertEqual(result['issues'],bad['issues'])
        self.assertEqual(result['checks'],bad['checks'])
        self.assertEqual(r.repairs,1); self.assertEqual(r.client.attempts,2)
        self.assertIn('closure_review_scope',requests[0]['instructions'])
        self.assertIn("'i0004': 'open'",requests[1]['instructions'])
        r.settle(result,'A2')
        self.assertEqual(r.issues['i0004']['status'],'open')
        self.assertTrue(any(i['status']=='open' for k,i in r.issues.items() if k!='i0004'))

    def test_missing_review_not_silently_accepted(self):
        r,_,bad=self.historical(); bad['closure_reviews']=[]
        with self.assertRaises(ProtocolError) as caught: r.validate_inspection(bad)
        self.assertIn("missing=['i0001', 'i0002', 'i0003']",caught.exception.detail)

    def test_duplicate_review_not_silently_accepted(self):
        r,_,bad=self.historical()
        bad['closure_reviews']=[x for x in bad['closure_reviews'] if x['issue_id']!='i0004']
        bad['closure_reviews'].append(copy.deepcopy(bad['closure_reviews'][0]))
        with self.assertRaises(ProtocolError) as caught: r.validate_inspection(bad)
        self.assertIn("repeated=['i0001']",caught.exception.detail)


if __name__=='__main__': unittest.main()
