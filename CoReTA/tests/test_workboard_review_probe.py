"""Offline experiment integrity checks; scripted outputs are not capability results."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coreta.handoff.__main__ import PROJECT

spec = importlib.util.spec_from_file_location('review_probe_tool', PROJECT / 'tools/workboard_review_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ReviewProbeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='review-probe-offline-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.prepared = self.root / 'prepared'
        self.manifest = probe.prepare(self.prepared)
        guard = patch('urllib.request.urlopen', side_effect=AssertionError('Offline network forbidden'))
        guard.start()
        self.addCleanup(guard.stop)

    def test_original_payload_exact_and_intervention_only_duty(self):
        duties = probe.candidate_duties()
        for item in self.manifest['inputs']:
            rows = [json.loads(x) for x in Path(item['source']).read_text(encoding='utf-8').splitlines()]
            original = next(r['payload'] for r in rows
                            if r['call_context']['logical_call'] == item['historical_logical_call'])
            a = probe.read(self.prepared / (item['id'] + '--A.json'))
            b = probe.read(self.prepared / (item['id'] + '--B.json'))
            self.assertEqual(a, original)
            restored = copy.deepcopy(b)
            prefix, suffix = b['instructions'].split('\nPACKET=', 1)
            self.assertEqual(prefix.count(duties[item['stage']]), 1)
            restored['instructions'] = prefix.replace(duties[item['stage']], probe.STAGES[item['stage']], 1) + '\nPACKET=' + suffix
            self.assertEqual(restored, a)
            self.assertEqual(probe.packet_of(a), probe.packet_of(b))
            p = probe.packet_of(b)
            self.assertEqual(item['member'], p['SELF']['agent_id'])
            self.assertEqual(p['SOURCE_ACCESS']['direct_original_refs'], sorted(['T'] + [m['ref'] for m in p['SELF_MATERIALS']]))

    def test_32_independent_requests_have_no_generated_feedback(self):
        seen = []
        def scripted(payload, timeout):
            seen.append(copy.deepcopy(payload))
            return {'status': 'completed', 'usage': {'input_tokens': 2, 'output_tokens': 3},
                    'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(
                        {'finding': 'unable', 'observation': 'SCRIPTED marker must never enter later input', 'scope': 'fixture'})}]}]}
        result = probe.run(self.prepared, self.root / 'fixture', transport=scripted)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['transport_attempts'], 32)
        self.assertEqual(result['actual_http_attempts'], 0)
        self.assertEqual(result['input_tokens'], 64)
        self.assertEqual(result['output_tokens'], 96)
        for row, payload in zip(self.manifest['calls'], seen):
            self.assertEqual(payload, probe.read(self.prepared / row['payload_file']))
            self.assertNotIn('SCRIPTED marker', payload['instructions'])
        for repeat in (1, 2):
            group = [r for r in result['rows'] if r['repeat'] == repeat]
            self.assertEqual(sum(r['condition'] == 'A' for r in group), 8)
            self.assertEqual(sum(r['condition'] == 'B' for r in group), 8)

    def test_first_incomplete_response_stops_without_retry(self):
        seen = []
        def incomplete(payload, timeout):
            seen.append(payload)
            return {'status': 'incomplete', 'usage': {'input_tokens': 7, 'output_tokens': 3072},
                    'incomplete_details': {'reason': 'max_output_tokens'}, 'output': []}
        result = probe.run(self.prepared, self.root / 'incomplete', transport=incomplete)
        self.assertEqual(len(seen), 1)
        self.assertEqual(result['status'], 'stopped_on_first_error')
        self.assertEqual(result['rows'][0]['error']['code'], 'SCHEMA_ERROR')
        self.assertEqual(sum(r['status'] == 'not_started' for r in result['rows']), 31)
        self.assertEqual(result['output_tokens'], 3072)

    def test_unknown_usage_stops_and_records_attempt(self):
        def unknown(payload, timeout):
            return {'status': 'completed', 'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': '{"finding":"unable","observation":"SCRIPTED","scope":"fixture"}'}]}]}
        result = probe.run(self.prepared, self.root / 'unknown', transport=unknown)
        self.assertEqual(result['rows'][0]['error']['code'], 'USAGE_UNKNOWN')
        self.assertEqual(result['unknown_usage_attempts'], 1)
        self.assertEqual(result['completed'], 0)

    def test_changed_payload_blocked_before_transport(self):
        path = self.prepared / self.manifest['calls'][0]['payload_file']
        payload = probe.read(path)
        payload['max_output_tokens'] = 4096
        path.write_text(json.dumps(payload), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Frozen preparation changed'):
            probe.run(self.prepared, self.root / 'changed', transport=lambda *args: self.fail('Transport called'))
        self.assertFalse((self.root / 'changed').exists())


if __name__ == '__main__':
    unittest.main()
