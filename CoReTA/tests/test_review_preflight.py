import copy
import json
import unittest
from pathlib import Path
from coreta.review_preflight import prepare_review
from coreta.schemas import ProtocolError
ROOT=Path(__file__).resolve().parents[1]

class ReviewPreflightChecks(unittest.TestCase):
    def data(self):
        return json.loads((ROOT/'runs/math140-correct-repair-review-v2-20261020/public_component_input.json').read_text(encoding='utf-8'))
    def test_original_role_mistake_blocked(self):
        with self.assertRaises(ProtocolError): prepare_review(self.data())
    def test_correct_role_preserves_candidate_and_original_cases(self):
        data=self.data();data['ACTOR']='A2';before=copy.deepcopy(data)
        out,receipt=prepare_review(data)
        self.assertEqual(out['MATERIAL']['current'],before['MATERIAL']['current'])
        self.assertEqual(data,before);self.assertEqual(receipt['pending_count'],4)
        self.assertGreater(receipt['original_cases'],0)
    def test_absent_objection_blocked(self):
        data=self.data();data['ACTOR']='A2';next(iter(data['MATERIAL']['pending_closures'].values()))['response_to_objection_ids']=[]
        with self.assertRaises(ProtocolError): prepare_review(data)
    def test_missing_original_record_blocked(self):
        data=self.data();data['ACTOR']='A2'
        issue=next(x for x in data['MATERIAL']['issues'] if x.get('evidence_records'))
        issue['evidence_records']=[]
        with self.assertRaises(ProtocolError): prepare_review(data)
    def test_missing_reference_content_blocked(self):
        data=self.data();data['ACTOR']='A2';data['MATERIAL']['current']['candidate']['steps'][0]['basis_refs']=['not-visible']
        with self.assertRaises(ProtocolError): prepare_review(data)

if __name__=='__main__':unittest.main()
