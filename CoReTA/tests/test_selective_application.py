"""Frozen diagnostic transport and output integrity, without network requests."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from coreta.handoff.__main__ import PROJECT
from coreta.handoff.gateway import write_json

sys.path.insert(0, str(PROJECT / 'tools'))
import run_selective_application as probe


class SelectiveTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        guard = patch('urllib.request.urlopen', side_effect=AssertionError('Offline network forbidden'))
        guard.start()
        self.addCleanup(guard.stop)

    def response(self, value):
        return {'status': 'completed', 'usage': {'input_tokens': 11, 'output_tokens': 7},
                'output': [{'type': 'message', 'content': [{'type': 'output_text',
                 'text': value if isinstance(value, str) else json.dumps(value)}]}]}

    def test_fixed24_no_feedback_or_gold_injection(self):
        manifest = probe.validate(probe.PREPARED)
        seen = []
        def transport(payload, timeout):
            seen.append(payload)
            schema = probe.output_schema(payload)
            return self.response({'artifact': schema['properties']['artifact']['enum'][0],
                                  'work_text': 'FIXTURE_ONLY_NO_EFFICACY'})
        report = probe.run(probe.PREPARED, self.root / 'valid', transport)
        self.assertEqual((report['status'], report['completed'], report['actual_http_attempts']),
                         ('completed', 24, 0))
        self.assertEqual(report['output_tokens'], 168)
        for row, payload in zip(manifest['calls'], seen):
            self.assertEqual(payload, probe.read(probe.PREPARED / row['payload_file']))
            self.assertNotIn('FIXTURE_ONLY_NO_EFFICACY', payload['instructions'])

    def test_bad_json_missing_field_illegal_answer_stop_without_repair(self):
        for index, raw in enumerate(['{}\n{}', '{"artifact":"invalid","work_text":"x"}',
                                     '{"work_text":"missing artifact"}']):
            seen = []
            def transport(payload, timeout):
                seen.append(payload)
                return self.response(raw)
            report = probe.run(probe.PREPARED, self.root / str(index), transport)
            self.assertEqual(len(seen), 1)
            self.assertEqual((report['completed'], report['status']), (0, 'stopped_on_first_error'))
            self.assertEqual(sum(row['status'] == 'not_started' for row in report['rows']), 23)

    def test_missing_usage_is_not_zero_cost(self):
        def transport(payload, timeout):
            value = {'artifact': probe.output_schema(payload)['properties']['artifact']['enum'][0],
                     'work_text': 'fixture'}
            response = self.response(value)
            response.pop('usage')
            return response
        report = probe.run(probe.PREPARED, self.root / 'usage', transport)
        self.assertEqual(report['unknown_usage_attempts'], 1)
        self.assertEqual(report['rows'][0]['error']['code'], 'USAGE_UNKNOWN')

    def test_payload_tamper_rejected_before_transport(self):
        import shutil
        local = self.root / 'prepared'
        shutil.copytree(probe.PREPARED, local)
        manifest = probe.read(local / 'manifest.json')
        target = local / manifest['calls'][0]['payload_file']
        # Hash keys point at original frozen absolute paths; move payload hash keys to this fixture copy.
        manifest['payload_hashes'] = {str(local / Path(path).name): digest
                                      for path, digest in manifest['payload_hashes'].items()}
        write_json(local / 'manifest.json', manifest)
        target.write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError):
            probe.run(local, self.root / 'tamper', lambda *args: self.fail('Transport called'))


if __name__ == '__main__':
    unittest.main()
