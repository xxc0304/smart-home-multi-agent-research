"""Bounded executor faults with a scripted transport; no external calls."""
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from prepare_issue_loop_comparison import prepare, verify
from run_issue_loop_comparison import run
from audit_issue_loop_load import response
from export_issue_loop_review import export


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        blocker = patch('urllib.request.urlopen', side_effect=AssertionError('No network'))
        blocker.start()
        self.addCleanup(blocker.stop)
        self.prepared = self.root/'prepared'
        prepare(self.prepared, counter=lambda text: len(text)//3)
        self.calls = []

    def factory(self, bad=None):
        def factory(pair, method):
            def transport(payload, timeout):
                self.calls.append((pair, method))
                if bad == 'transport':
                    raise urllib.error.URLError('SCRIPTED offline failure')
                packet = json.loads(payload['instructions'].split('\nPACKET=', 1)[1].split('\nOUTPUT_SCHEMA=', 1)[0])
                value = response(packet, method, issues_per_check=2)
                text = 'BROKEN JSON' if bad == 'format' else json.dumps(value)
                result = dict(status='completed', usage=dict(input_tokens=10, output_tokens=10),
                    output=[dict(type='message', content=[dict(type='output_text', text=text)])])
                if bad == 'usage':
                    result.pop('usage')
                if bad == 'excess_output':
                    result['usage']['output_tokens'] = 1000000
                return result
            return transport
        return factory

    def execute(self, bad=None, counter=None):
        return run(self.prepared, self.root/'live', transport_factory=self.factory(bad),
                   counter=counter or (lambda text: len(text)//3))

    def test_complete_82_with_feedback_and_export(self):
        result = self.execute()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['http_attempts'], 82)
        self.assertEqual(len(self.calls), 82)
        self.assertEqual(len(result['units']), 4)
        self.assertFalse(result['unknown_usage'])
        rows = export(self.root/'live', self.root/'review')
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row['artifact_exact_match'] in (0, 1) for row in rows))
        self.assertTrue(all(row['meaningful_corrections'] is None for row in rows))
        self.assertTrue(all(row['status'] == 'completed' for row in rows))

    def test_format_stops_after_one_no_retry(self):
        with self.assertRaises(Exception):
            self.execute('format')
        progress = json.loads((self.root/'live/progress.json').read_text())
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(progress['status'], 'stopped_on_first_technical_error')
        self.assertEqual(progress['http_attempts'], 1)
        self.assertFalse(progress['unknown_usage'])
        rows = export(self.root/'live', self.root/'partial-review')
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row['artifact_exact_match'] is None for row in rows))
        self.assertEqual(sum(row['status'] == 'not_run' for row in rows), 3)

    def test_missing_usage_is_not_counted_as_zero(self):
        with self.assertRaises(Exception):
            self.execute('usage')
        progress = json.loads((self.root/'live/progress.json').read_text())
        self.assertEqual(progress['unknown_usage_attempts'], 1)
        self.assertTrue(progress['unknown_usage'])
        self.assertEqual(len(self.calls), 1)

    def test_transport_uncertainty_stops(self):
        with self.assertRaises(Exception):
            self.execute('transport')
        progress = json.loads((self.root/'live/progress.json').read_text())
        self.assertTrue(progress['unknown_usage'])
        self.assertEqual(progress['http_attempts'], 1)

    def test_excess_usage_stops_before_next_call(self):
        with self.assertRaises(Exception):
            self.execute('excess_output')
        self.assertEqual(len(self.calls), 1)

    def test_no_implicit_resume(self):
        (self.root/'live').mkdir()
        with self.assertRaises(ValueError):
            self.execute()
        self.assertFalse(self.calls)

    def test_changed_schedule_is_rejected_before_transport(self):
        path = self.prepared/'manifest.json'
        value = json.loads(path.read_text())
        value['pairs'][0]['methods'].reverse()
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            self.execute()
        self.assertFalse(self.calls)
        self.assertFalse((self.root/'live').exists())

    def test_missing_source_hash_is_rejected(self):
        path = self.prepared/'manifest.json'
        value = json.loads(path.read_text())
        value['source_hashes'].pop(next(iter(value['source_hashes'])))
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            verify(self.prepared)

    def test_missing_prepared_hash_is_rejected(self):
        path = self.prepared/'manifest.json'
        value = json.loads(path.read_text())
        value['prepared_hashes'].pop(next(iter(value['prepared_hashes'])))
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            verify(self.prepared)

    def test_context_overflow_never_sends_request(self):
        with self.assertRaises(Exception):
            self.execute(counter=lambda text: 10000000)
        self.assertFalse(self.calls)


if __name__ == '__main__':
    unittest.main()
