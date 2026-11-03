import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema.exceptions import ValidationError

import local_judgment_frontend as interface
import prepare_local_judgment_calibration as calibration


class CalibrationPreparationTests(unittest.TestCase):
    def test_only_resources_change_and_gold_never_loaded(self):
        original_read = interface.read
        def guarded(path):
            self.assertNotIn('offline', str(path).lower())
            self.assertNotIn('evaluator', str(path).lower())
            return original_read(path)
        with patch.object(interface, 'read', guarded):
            for item in original_read(calibration.ITEMS)['items']:
                left = calibration.build_packet(item, 'with_resources')
                right = calibration.build_packet(item, 'without_resources')
                self.assertEqual(len(left['own_sources']), 5)
                self.assertEqual(len(right['own_sources']), 0)
                left.pop('own_sources'); right.pop('own_sources')
                self.assertEqual(left, right)

    def test_roster_hashes_and_no_live_entrypoint(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'prepared'
            summary = calibration.prepare(out)
            self.assertEqual(summary['proposed_attempts'], 24)
            plan = interface.read(out / 'CALIBRATION_PLAN.json')
            self.assertEqual(len(plan['schedule']), 24)
            self.assertEqual(plan['unique_parent_scenarios'], 1)
            manifest = interface.read(out / 'manifest.json')
            for name, value in manifest['files'].items():
                self.assertEqual(interface.digest(out / name), value)
            self.assertFalse(any('gold' in name or 'label' in name for name in manifest['files']))
            for item in plan['schedule']:
                request = interface.read(out / item['request'])
                self.assertEqual(request['max_output_tokens'], 1536)
            with self.assertRaises(interface.InterfaceError): calibration.prepare(out)
        self.assertFalse(hasattr(calibration, 'run'))

    def test_no_resources_cannot_cite_private_materials(self):
        item = interface.read(calibration.ITEMS)['items'][0]
        without = calibration.build_packet(item, 'without_resources')
        value = dict(status='abstain', conclusion='Not established here.', evidence=[], scope='Local question.', missing=[])
        self.assertEqual(interface.decode(json.dumps(value), 'second', without)[0], value)
        value['evidence'] = [dict(source=item['source'], quote='Anything')]
        with self.assertRaises(ValidationError): interface.decode(json.dumps(value), 'second', without)

    def test_scope_error_remains_semantic_not_parse_failure(self):
        item = interface.read(calibration.ITEMS)['items'][0]
        packet = calibration.build_packet(item, 'with_resources')
        value = dict(status='answer', conclusion='The raft guarantees return to the mother ship.',
                     evidence=[dict(source=item['source'], quote=next(s['content'] for s in packet['own_sources'] if s['ref']==item['source']))],
                     scope='All conditions.', missing=[])
        self.assertEqual(interface.decode(json.dumps(value), 'second', packet)[0], value)


if __name__ == '__main__':
    unittest.main()
