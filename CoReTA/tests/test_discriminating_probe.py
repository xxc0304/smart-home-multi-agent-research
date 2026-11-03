"""Diagnostic integrity checks; scripted outputs are not efficacy evidence."""
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from coreta.handoff.__main__ import PROJECT
from coreta.schemas import ProtocolError

sys.path.insert(0, str(PROJECT / 'tools'))
import workboard_discriminating_probe as probe


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prepared = self.root / 'prepared'
        probe.prepare(self.prepared)
        guard = patch('urllib.request.urlopen', side_effect=AssertionError('No offline network'))
        guard.start()
        self.addCleanup(guard.stop)

    def response(self, raw):
        return {'status': 'completed', 'usage': {'input_tokens': 10, 'output_tokens': 20},
                'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': raw}]}]}

    def test_inputs_and_fixed_budget(self):
        manifest = probe.validate(self.prepared)
        self.assertEqual(len(manifest['calls']), 16)
        self.assertEqual(manifest['max_output_tokens'], 49152)
        for item in manifest['inputs']:
            first, second = [probe.read(self.prepared / f"{item['id']}--{arm}.json")
                             for arm in ('F', 'D')]
            self.assertEqual(probe.packet_of(first), probe.packet_of(second))
            self.assertEqual({k: v for k, v in first.items() if k != 'instructions'},
                             {k: v for k, v in second.items() if k != 'instructions'})
            if item['id'].startswith('hb-'):
                source = probe.SOURCE / f"{item['id']}--d0_continuation--CHECK_EFFECT--S.json"
                self.assertEqual(probe.packet_of(first), probe.packet_of(probe.read(source)))
        self.assertNotRegex(probe.DUTIES['D'], r'\b(?:Pine|son|bridge|Oak|dangerous)\b')

    def test_full_run_no_feedback_injected(self):
        seen = []
        raw = json.dumps({'investigation': [], 'verdict': 'unresolved',
                          'assessment': 'FIXTURE_ONLY_MARKER', 'limits': 'offline'})
        def transport(payload, timeout):
            seen.append(payload)
            return self.response(raw)
        result = probe.run(self.prepared, self.root / 'fixture', transport)
        self.assertEqual((result['status'], result['completed'], result['actual_http_attempts']),
                         ('completed', 16, 0))
        self.assertEqual(result['output_tokens'], 320)
        manifest = probe.read(self.prepared / 'manifest.json')
        for row, value in zip(manifest['calls'], seen):
            self.assertEqual(value, probe.read(self.prepared / row['payload_file']))
            self.assertNotIn('FIXTURE_ONLY_MARKER', value['instructions'])

    def test_malformed_stops_no_retry(self):
        calls = []
        def transport(payload, timeout):
            calls.append(payload)
            return self.response('{}\n{}')
        result = probe.run(self.prepared, self.root / 'malformed', transport)
        self.assertEqual(len(calls), 1)
        self.assertEqual((result['status'], result['completed']), ('stopped_on_first_error', 0))

    def test_frozen_tamper_rejected_before_transport(self):
        manifest = probe.read(self.prepared / 'manifest.json')
        path = self.prepared / manifest['calls'][0]['payload_file']
        path.write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError):
            probe.run(self.prepared, self.root / 'tamper', lambda *a: self.fail('Transport called'))

    def test_required_limits_failure_continuation_never_repeats_failed_call(self):
        raw = json.dumps({'investigation': [], 'verdict': 'unresolved', 'assessment': 'fixture'})
        failed = self.root / 'first'
        result = probe.run(self.prepared, failed, lambda *a: self.response(raw))
        self.assertEqual(result['completed'], 0)
        # Fixture used one simulated transport, not HTTP; make an explicit continuation fixture.
        progress = probe.read(failed / 'progress.json')
        progress['actual_http_attempts'] = 1
        probe.write_json(failed / 'progress.json', progress)
        next_prepared = self.root / 'remaining'
        manifest = probe.prepare(next_prepared, failed)
        probe.validate(next_prepared)
        self.assertEqual(manifest['max_http_attempts'], 15)
        self.assertNotIn(manifest['continuation']['skipped_call'], manifest['calls'])
        self.assertEqual(len(manifest['calls']), 15)


if __name__ == '__main__':
    unittest.main()
