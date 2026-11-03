import json
from pathlib import Path
import tempfile
import unittest
from prepare_local_condition_pilot import prepare
from run_local_condition_pilot import run


class PilotTests(unittest.TestCase):
    def response(self, payload, timeout):
        choice = payload['text']['format']['schema']['properties']['choice']['enum'][0]
        value = dict(choice=choice, reason='Mock transport only.', withdrawn_conditions=[])
        return dict(status='completed', usage=dict(input_tokens=100, output_tokens=25),
            output=[dict(type='message', content=[dict(type='output_text', text=json.dumps(value))])])

    def test_mock_full_batch_without_label_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared = prepare(root/'prepared')
            (prepared/'offline_labels.json').unlink()
            result = run(prepared, root/'run', transport=self.response)
            self.assertEqual(result['attempts'], 24)
            self.assertEqual(result['output_tokens'], 600)
            self.assertEqual(result['status'], 'completed')
            rows = result['completed']
            self.assertEqual(len({(r['case'], r['repeat']) for r in rows}), 12)

    def test_format_failure_stops_first_attempt(self):
        def malformed(payload, timeout):
            response = self.response(payload, timeout)
            response['output'][0]['content'][0]['text'] = '{'
            return response
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared = prepare(root/'prepared')
            with self.assertRaises(json.JSONDecodeError):
                run(prepared, root/'run', transport=malformed)
            state = json.loads((root/'run/progress.json').read_text())
            self.assertEqual(state['attempts'], 1)
            self.assertEqual(state['status'], 'stopped')
            self.assertEqual(len(state['completed']), 0)

    def test_manifest_mutation_rejected_before_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared = prepare(root/'prepared')
            config = prepared/'config.json'
            config.write_text('{}')
            with self.assertRaises(ValueError):
                run(prepared, root/'run', transport=self.response)
            self.assertFalse((root/'run').exists())


if __name__ == '__main__':
    unittest.main()
