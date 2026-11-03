import json
from pathlib import Path
import unittest
import minimal_final_answer_contract as contract
import local_judgment_frontend as io


class MinimalTerminalTests(unittest.TestCase):
    def setUp(self):
        self.packet=dict(task=dict(choices=[dict(id="O1"),dict(id="O2")]))

    def test_only_two_required_fields_and_no_invented_adoption(self):
        req=contract.request(self.packet)
        self.assertEqual(set(req["schema"]["required"]),{"choice","reasoning"})
        answer=contract.decode('{"choice":"O1","reasoning":"Supported comparison."}',self.packet)
        self.assertEqual(answer["choice"],"O1")
        self.assertNotIn("used_contributions",answer)
        self.assertEqual(answer["extra_annotations"],{})
        self.assertIsNone(contract.decode('{"choice":null,"reasoning":"Unresolved."}',self.packet)["choice"])

    def test_bad_essential_fields_and_duplicate_or_appended_json_rejected(self):
        for value in (dict(reasoning="A"),dict(choice="O1"),dict(choice="other",reasoning="A"),
                      dict(choice="O1",reasoning=" "),dict(choice="O1",reasoning=7)):
            with self.subTest(value=value),self.assertRaises(ValueError):
                contract.decode(json.dumps(value),self.packet)
        for raw in ('{"choice":"O1","choice":"O2","reasoning":"A"}',
                    '{"choice":"O1","reasoning":"A"}{}'):
            with self.assertRaises(ValueError):contract.decode(raw,self.packet)

    def test_extra_annotation_preserved_without_claiming_actual_adoption(self):
        a=contract.decode('{"choice":"O1","reasoning":"A","used_contributions":null}',self.packet)
        self.assertEqual(a["extra_annotations"],dict(used_contributions=None))
        self.assertTrue(a["annotation_issues"])

    def test_actual_quarantined_raw_answer_is_compatible_only_with_future_contract(self):
        root=Path(__file__).resolve().parents[1]
        raw=(root/"runs/evidence-first-live-20261025-r1/063.raw.txt").read_text(encoding="utf-8")
        packet=io.read(root/"runs/evidence-first-prepared-20261025-r1/contexts/hb-local-dev-009/A1.json")
        self.assertEqual(contract.decode(raw,packet)["choice"],"O1")
        # The existing run stays quarantined; compatibility is not retroactive scoring.
        rows=io.read(root/"runs/evidence-first-live-20261025-r1/review.json")["rows"]
        self.assertEqual(rows[62]["status"],"quarantined")
        self.assertIsNone(rows[62]["answer"])


if __name__=="__main__":
    unittest.main()
