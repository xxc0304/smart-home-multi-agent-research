import json
from pathlib import Path
import tempfile
import unittest
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import run_rule_resource_calibration as runner


class RuleResourceRunnerTests(unittest.TestCase):
    @staticmethod
    def mock(payload,timeout):
        packet=io.strict_json(payload['instructions'].split('PACKET=',1)[1])
        source=(packet['own_sources'] or packet['public_sources'])[0]['ref']
        answer=dict(conclusion='Technical fixture.',source_ids=[source],status='conditional',scope='Not a task result.',missing=[])
        return dict(status='completed',usage=dict(input_tokens=10,output_tokens=10),
                    output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(answer))])])

    def test_twelve_requests_budget_packets_and_no_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'p';o=Path(temp)/'o';runner.freeze(p);m,plan,c=runner.verify(p)
            self.assertEqual(len(plan['schedule']),12);self.assertEqual(m['max_total_output_tokens'],18432)
            state=runner.run(p,o,transport=self.mock,local_validation=True)
            self.assertEqual(state['attempts'],12);self.assertEqual(state['max_requests'],12)
            self.assertEqual(state['output_budget_reserved'],18432)
            self.assertEqual(len(state['completed']),12)
            with self.assertRaisesRegex(ValueError,'no resume'):runner.run(p,o,transport=self.mock,local_validation=True)

    def test_isolated_json_error_continues_transport_stops_and_complete_roster(self):
        for mode in ['json','transport','usage']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                p=Path(temp)/'p';o=Path(temp)/'o';runner.freeze(p);calls=0
                def mock(payload,timeout):
                    nonlocal calls
                    calls+=1
                    if calls==4 and mode=='transport':raise TimeoutError('fixture')
                    r=self.mock(payload,timeout)
                    if calls==4 and mode=='json':r['output'][0]['content'][0]['text']='{'
                    if calls==4 and mode=='usage':r.pop('usage')
                    return r
                if mode=='json':
                    s=runner.run(p,o,transport=mock,local_validation=True)
                    self.assertEqual(s['status'],'completed_with_quarantine');self.assertEqual(calls,12)
                else:
                    with self.assertRaises((ValueError,ProtocolError)):runner.run(p,o,transport=mock,local_validation=True)
                    self.assertEqual(calls,4)
                self.assertEqual(len(io.read(o/'review.json')['rows']),12)

    def test_auth_gate_and_input_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'p';runner.freeze(p)
            with self.assertRaises(FileNotFoundError):runner.gates(p)
            manifest=io.read(p/'manifest.json');manifest['max_requests']=13;io.write(p/'manifest.json',manifest)
            with self.assertRaisesRegex(ValueError,'budget'):runner.verify(p)

    def test_full_load_mock_explicitly_not_provider_output(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'p';runner.freeze(p);r=runner.preflight(p)
            self.assertEqual(r['mock_attempts'],12)
            self.assertEqual(r['real_new_task_provider_outputs'],0)
            self.assertEqual(r['complete_historical_common_replay']['admitted'],48)
            self.assertLess(r['maximum_adapted_output_tokens'],1536)


if __name__=='__main__':unittest.main()
