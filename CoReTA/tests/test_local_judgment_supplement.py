import json
from pathlib import Path
import tempfile
import unittest

from coreta.schemas import ProtocolError
import local_judgment_frontend as interface
import prepare_local_judgment_supplement as preparation
import run_local_judgment_supplement as runner


class SupplementTests(unittest.TestCase):
    @staticmethod
    def mock(payload, timeout):
        packet=interface.strict_json(payload['instructions'].split('PACKET=',1)[1])
        source=(packet['own_sources'] or packet['public_sources'])[0]['ref']
        answer=dict(conclusion='Supplement technical fixture.',source_ids=[source],status='conditional',scope='Fixture only.',missing=[])
        return dict(status='completed',usage=dict(input_tokens=10,output_tokens=10),
                    output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(answer))])])

    def test_only_unattempted_ten_and_exact_original_packets(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'p';runner.freeze(p)
            m,plan,c=runner.verify(p)
            self.assertEqual(m['max_requests'],10)
            self.assertEqual(m['max_total_output_tokens'],15360)
            self.assertEqual([r['original_slot'] for r in plan['schedule']],list(range(15,25)))
            for r in plan['schedule']:
                packet_name=r['item']+'-'+r['condition']+'.json'
                self.assertEqual(interface.read(p/'packets'/packet_name),interface.read(preparation.PARENT_PREPARED/'packets'/packet_name))
                self.assertNotEqual(r['original_slot'],14)
            self.assertEqual({r['item'] for r in plan['schedule']},{'moon-local-04','moon-local-05','moon-local-06'})

    def test_complete_ten_never_calls_original_slots_or_exceeds_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'p';o=Path(folder)/'out';runner.freeze(p)
            state=runner.run(p,o,transport=self.mock,local_validation=True)
            self.assertEqual(state['attempts'],10)
            self.assertEqual(state['output_budget_reserved'],15360)
            self.assertEqual(len(state['completed']),10)
            self.assertEqual(state['max_requests'],10)
            self.assertEqual([r['original_slot'] for r in state['completed']],list(range(15,25)))
            with self.assertRaisesRegex(ValueError,'no resume'):runner.run(p,o,transport=self.mock,local_validation=True)

    def test_single_bad_independent_reply_quarantined_and_transport_stops(self):
        for mode in ['json','transport']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                p=Path(folder)/'p';o=Path(folder)/'out';runner.freeze(p);calls=0
                def transport(payload,timeout):
                    nonlocal calls
                    calls+=1
                    if calls==3 and mode=='transport':raise TimeoutError('fixture')
                    r=self.mock(payload,timeout)
                    if calls==3:r['output'][0]['content'][0]['text']='{'
                    return r
                if mode=='transport':
                    with self.assertRaises(ProtocolError):runner.run(p,o,transport=transport,local_validation=True)
                    self.assertEqual(calls,3)
                else:
                    state=runner.run(p,o,transport=transport,local_validation=True)
                    self.assertEqual(calls,10);self.assertEqual(len(state['completed']),9)
                    self.assertEqual(len(state['quarantined']),1)
                self.assertEqual(len(interface.read(o/'review.json')['rows']),10)

    def test_parent_batch_and_24_request_authorization_not_accepted(self):
        with self.assertRaisesRegex(ValueError,'own10-slot batch'):
            runner.verify(interface.ROOT/'runs/local-judgment-moon-calibration-prepared-20261025-r3')
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'p';runner.freeze(p);sha=interface.digest(p/'manifest.json')
            interface.write(p/'PREFLIGHT.json',dict(status='passed',manifest_sha256=sha))
            interface.write(p/'EXPERIMENT_REVIEW.json',dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED',manifest_sha256=sha))
            interface.write(p/'AUTHORIZATION.json',dict(authorized=True,max_requests=24,manifest_sha256=sha,
                destination='https://api.deepseek.com/responses',user_authorization_text='TEST ONLY'))
            with self.assertRaisesRegex(ValueError,'authorization'):runner.gates(p)

    def test_complete_supplement_preflight_is_only_mock(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'p';runner.freeze(p);result=runner.preflight(p)
            self.assertEqual(result['mock_attempts'],10)
            self.assertEqual(result['model_requests'],0)
            self.assertEqual(result['real_new_task_provider_outputs'],0)
            self.assertLess(result['maximum_adapted_output_tokens'],1536)


if __name__=='__main__':unittest.main()
