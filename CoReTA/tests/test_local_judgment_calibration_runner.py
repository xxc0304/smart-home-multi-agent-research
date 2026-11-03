import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jsonschema.exceptions import ValidationError
from coreta.schemas import ProtocolError
import local_judgment_frontend as interface
import run_local_judgment_calibration as runner


class CalibrationRunnerTests(unittest.TestCase):
    @staticmethod
    def mock(payload, timeout):
        packet = interface.strict_json(payload['instructions'].split('PACKET=', 1)[1])
        source = (packet['own_sources'] or packet['public_sources'])[0]
        answer = dict(status='conditional', conclusion='Technical fixture only.',
                      evidence=[dict(source=source['ref'], quote=source['content'])],
                      scope='Synthetic payload; no claim of task correctness.', missing=[])
        return dict(status='completed', usage=dict(input_tokens=10, output_tokens=10),
                    output=[dict(type='message', content=[dict(type='output_text', text=json.dumps(answer))])])

    def test_complete_24_mock_calls_and_runtime_never_reads_rubric(self):
        with tempfile.TemporaryDirectory() as folder:
            prepared, output = Path(folder)/'prepared', Path(folder)/'output'
            runner.freeze(prepared)
            original_read = interface.read
            def guard(path):
                self.assertNotIn('rubric', str(path).lower())
                self.assertNotIn('evaluation.json', str(path).lower())
                self.assertNotIn('offline_labels', str(path).lower())
                return original_read(path)
            with patch.object(interface, 'read', guard):
                state = runner.run(prepared, output, transport=self.mock, local_validation=True)
            self.assertEqual(state['attempts'], 24)
            self.assertEqual(state['status'], 'completed')
            self.assertEqual(len(list(output.glob('*.raw.txt'))), 24)
            self.assertEqual(state['input_tokens'], 240)
            self.assertEqual(state['output_tokens'], 240)
            self.assertEqual(state['output_budget_reserved'], 36864)
            self.assertEqual(len(interface.read(output/'review.json')['rows']), 24)
            self.assertFalse(state['unknown_usage'])
            with self.assertRaisesRegex(ValueError, 'no resume'):
                runner.run(prepared, output, transport=self.mock, local_validation=True)

    def test_first_failure_stops_and_preserves_failed_and_unrun_slots(self):
        for kind, offset in [('json', 1), ('duplicate', 12), ('incomplete', 24), ('transport', 3),
                             ('missing_usage', 9), ('citation', 2), ('no_text', 4), ('schema', 7), ('overcap', 6)]:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                prepared, output = Path(folder)/'prepared', Path(folder)/'output'
                runner.freeze(prepared)
                calls = 0
                def failing(payload, timeout):
                    nonlocal calls
                    calls += 1
                    if calls == offset and kind == 'transport':
                        raise TimeoutError('synthetic timeout')
                    result = self.mock(payload, timeout)
                    if calls != offset:
                        return result
                    text = result['output'][0]['content'][0]
                    if kind == 'json': text['text'] = '{'
                    elif kind == 'duplicate': text['text'] = '{"status":"answer","status":"answer"}'
                    elif kind == 'incomplete': result['status'] = 'incomplete'
                    elif kind == 'missing_usage': result.pop('usage')
                    elif kind == 'no_text': result['output'] = []
                    elif kind == 'overcap': result['usage']['output_tokens'] = 1537
                    elif kind == 'citation':
                        value=json.loads(text['text']);value['evidence'][0]['quote']='Never supplied.';text['text']=json.dumps(value)
                    elif kind == 'schema':
                        value=json.loads(text['text']);del value['scope'];text['text']=json.dumps(value)
                    return result
                with self.assertRaises((ValueError, ProtocolError, ValidationError)):
                    runner.run(prepared, output, transport=failing, local_validation=True)
                state = interface.read(output/'progress.json')
                self.assertEqual(calls, offset)
                self.assertEqual(state['attempts'], offset)
                self.assertEqual(state['status'], 'stopped')
                self.assertEqual(len(state['completed']), offset-1)
                review = interface.read(output/'review.json')['rows']
                self.assertEqual(len(review), 24)
                self.assertEqual(review[offset-1]['status'], 'failed')
                self.assertTrue(all(r['status']=='not_run' for r in review[offset:]))
                self.assertTrue(all(r['semantic_score'] is None for r in review))
                self.assertEqual(len((output/'responses.jsonl').read_text(encoding='utf-8').splitlines()), offset)
                if kind not in ('transport', 'no_text'):
                    self.assertTrue((output/f'{offset:02d}.raw.txt').exists())
                self.assertEqual(state['unknown_usage'], kind in ('transport','missing_usage'))

    def test_mock_cannot_fall_back_to_network(self):
        with tempfile.TemporaryDirectory() as folder:
            prepared=Path(folder)/'prepared';runner.freeze(prepared)
            with self.assertRaisesRegex(ValueError,'mock transport'):
                runner.run(prepared, Path(folder)/'out', local_validation=True)

    def test_live_requires_fresh_dual_review_and_specific_authorization(self):
        with tempfile.TemporaryDirectory() as folder:
            prepared=Path(folder)/'prepared';runner.freeze(prepared)
            sha=interface.digest(prepared/'manifest.json')
            with self.assertRaises(FileNotFoundError): runner.gates(prepared)
            interface.write(prepared/'PREFLIGHT.json', dict(status='passed',manifest_sha256=sha))
            interface.write(prepared/'EXPERIMENT_REVIEW.json', dict(science='PASS',readiness='BLOCKED',technical_launch='RUN_ALLOWED',manifest_sha256=sha))
            with self.assertRaisesRegex(ValueError,'dual review'): runner.gates(prepared)
            interface.write(prepared/'EXPERIMENT_REVIEW.json', dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED',manifest_sha256=sha))
            with self.assertRaises(FileNotFoundError): runner.gates(prepared)
            auth=dict(authorized=True,manifest_sha256='stale',max_requests=24,destination='https://api.deepseek.com/responses',user_authorization_text='SYNTHETIC TEST ONLY')
            interface.write(prepared/'AUTHORIZATION.json',auth)
            with self.assertRaisesRegex(ValueError,'authorization'):runner.gates(prepared)
            auth['manifest_sha256']=sha;interface.write(prepared/'AUTHORIZATION.json',auth)
            runner.gates(prepared)  # No call to run or HTTP in this gate test.
            interface.write(prepared/'PREFLIGHT.json',dict(status='passed',manifest_sha256='stale'))
            with self.assertRaisesRegex(ValueError,'preflight'):runner.gates(prepared)

    def test_tampered_input_code_budget_and_path_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            prepared=Path(folder)/'prepared';runner.freeze(prepared)
            manifest=interface.read(prepared/'manifest.json')
            bad=copy.deepcopy(manifest);bad['max_requests']=25;interface.write(prepared/'manifest.json',bad)
            with self.assertRaisesRegex(ValueError,'budget'):runner.verify(prepared)
            bad=copy.deepcopy(manifest);bad['code_sha256']['src/coreta/model_client.py']='wrong';interface.write(prepared/'manifest.json',bad)
            with self.assertRaisesRegex(ValueError,'changed'):runner.verify(prepared)
            interface.write(prepared/'manifest.json',manifest)
            (prepared/'config.json').write_text('{}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'changed'):runner.verify(prepared)
            with self.assertRaisesRegex(ValueError,'leaves root'):runner.child(prepared,'../escape')

    def test_input_overflow_stops_before_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            prepared=Path(folder)/'prepared';runner.freeze(prepared)
            config=interface.read(prepared/'config.json');config['generation']['max_input_tokens']=1
            interface.write(prepared/'config.json',config)
            manifest=interface.read(prepared/'manifest.json');manifest['files']['config.json']=interface.digest(prepared/'config.json')
            interface.write(prepared/'manifest.json',manifest)
            calls=0
            def transport(payload, timeout):
                nonlocal calls
                calls+=1
                return self.mock(payload, timeout)
            with self.assertRaises(ProtocolError):runner.run(prepared,Path(folder)/'out',transport=transport,local_validation=True)
            self.assertEqual(calls,0)
            self.assertEqual(interface.read(Path(folder)/'out/progress.json')['attempts'],0)

    def test_complete_preflight_adapted_load_explicitly_not_provider_results(self):
        with tempfile.TemporaryDirectory() as folder:
            prepared=Path(folder)/'prepared';runner.freeze(prepared)
            report=runner.preflight(prepared)
            self.assertEqual(report['status'],'passed')
            self.assertEqual(report['mock_attempts'],24)
            self.assertEqual(report['real_new_task_provider_outputs'],0)
            self.assertEqual(report['complete_historical_common_replay'],dict(total=48,admitted=48))
            self.assertLessEqual(report['maximum_adapted_output_tokens'],1536)
            self.assertLess(report['maximum_mock_input_estimate'],8192)
            with self.assertRaisesRegex(ValueError,'do not resume'):runner.preflight(prepared)


if __name__=='__main__':unittest.main()
