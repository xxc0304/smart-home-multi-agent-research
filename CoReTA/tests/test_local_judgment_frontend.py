import copy
import json
from pathlib import Path
import tempfile
import unittest

from jsonschema.exceptions import ValidationError
import local_judgment_frontend as module


class LocalJudgmentInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.packet = module.first_packet(module.DEFAULT_PREPARED, 'unit-01', 'A2')
        self.first = dict(status='proceed', text='How does the reported restoration time affect the relocation window?',
                          evidence=[dict(source='S02', quote=self.packet['own_sources'][0]['content'])], target=None)
        self.second = dict(status='conditional', conclusion='The report gives a bounded restoration time.',
                           evidence=copy.deepcopy(self.first['evidence']),
                           scope='Restroom timing only; not whole-venue certification.',
                           missing=['Whether the reported work completes on time.'])

    def test_matched_first_context_and_shared_second_prompt_schema(self):
        a = module.request('first', 'ordinary', self.packet)
        b = module.request('first', 'local_question', self.packet)
        self.assertEqual(a['schema'], b['schema'])
        self.assertEqual(a['max_output_tokens'], b['max_output_tokens'])
        self.assertNotEqual(a['instructions'], b['instructions'])
        self.assertEqual(a['instructions'].split('PACKET=', 1)[1], b['instructions'].split('PACKET=', 1)[1])
        following = module.second_packet(self.packet, self.first)
        self.assertEqual(module.request('second', 'ordinary', following), module.request('second', 'local_question', following))

    def test_context_isolation_and_no_label_or_manual_fields(self):
        following = module.second_packet(self.packet, self.first)
        self.assertEqual(set(following), {'task', 'member', 'public_sources', 'own_sources', 'earlier_work'})
        self.assertEqual(following['own_sources'], self.packet['own_sources'])
        self.assertEqual({s['ref'] for s in following['own_sources']}, {'S02'})
        self.assertNotIn('target', following)
        self.assertNotIn('historical_work', following)
        self.assertNotIn('field_meanings', self.packet)
        self.assertNotIn('offline_labels', json.dumps(following))
        # Inherited bias in model-generated text is allowed and is not claimed to be sanitized.
        first = dict(self.first, text='Is the Library really preferable?')
        self.assertIn('Library', module.second_packet(self.packet, first)['earlier_work'])

    def test_pass_and_empty_citations_are_valid_without_new_work(self):
        first = dict(self.first, status='pass', text='No supported contribution identified.', evidence=[])
        self.assertIsNone(module.second_packet(self.packet, first))
        following = module.second_packet(self.packet, self.first)
        value = dict(self.second, status='abstain', evidence=[], missing=[])
        self.assertEqual(module.decode(json.dumps(value), 'second', following)[0], value)

    def test_schema_boundaries(self):
        for key in self.first:
            bad = copy.deepcopy(self.first); del bad[key]
            with self.assertRaises(ValidationError): module.decode(json.dumps(bad), 'first', self.packet)
        for bad in [dict(self.first, extra=True), dict(self.first, text=None), dict(self.first, evidence=None),
                    dict(self.first, status='answer'), dict(self.first, text=''), dict(self.first, target=False)]:
            with self.assertRaises(ValidationError): module.decode(json.dumps(bad), 'first', self.packet)
        with self.assertRaises(module.InterfaceError):
            module.decode(json.dumps(dict(self.first, text='  ')), 'first', self.packet)
        following = module.second_packet(self.packet, self.first)
        for bad in [dict(self.second, conclusion=None), dict(self.second, missing=[False]),
                    dict(self.second, scope=''), dict(self.second, missing=None)]:
            with self.assertRaises(ValidationError): module.decode(json.dumps(bad), 'second', following)
        with self.assertRaises(module.InterfaceError):
            module.decode(json.dumps(dict(self.second, missing=['  '])), 'second', following)

    def test_strict_json_duplicate_nested_nonfinite_and_truncation(self):
        for raw in ['{"x":1,"x":2}', '{"outer":{"x":1,"x":2}}', '{"x":NaN}',
                    '{"x":Infinity}', '{"x":-Infinity}', '{', '```json\n{}\n```']:
            with self.assertRaises(ValueError): module.strict_json(raw)

    def test_visible_exact_citation_rebinding_only(self):
        bad = copy.deepcopy(self.first); bad['evidence'][0]['source'] = 'PUBLIC.1'
        value, events = module.decode(json.dumps(bad), 'first', self.packet)
        self.assertEqual(value['evidence'][0]['source'], 'S02')
        self.assertEqual(len(events), 1)
        self.assertEqual(bad['evidence'][0]['source'], 'PUBLIC.1')
        for cite in [dict(source='S01', quote=self.first['evidence'][0]['quote']),
                     dict(source='S02', quote='A fabricated claim.'), dict(source='S02', quote=' ')]:
            bad = dict(self.first, evidence=[cite])
            with self.assertRaises((ValidationError, module.InterfaceError)):
                module.decode(json.dumps(bad), 'first', self.packet)

    def test_ambiguous_quote_and_wrong_target_rejected(self):
        packet = copy.deepcopy(self.packet)
        packet['public_sources'].extend([dict(ref='EX1', content='Exact shared sentence.'),
                                         dict(ref='EX2', content='Exact shared sentence.')])
        bad = dict(self.first, evidence=[dict(source='S02', quote='Exact shared sentence.')])
        with self.assertRaises(module.InterfaceError): module.decode(json.dumps(bad), 'first', packet)
        with self.assertRaises(module.InterfaceError):
            module.decode(json.dumps(dict(self.first, target='invented target')), 'first', self.packet)
        good = dict(self.first, target=self.packet['historical_work']['reason'][:80])
        self.assertEqual(module.decode(json.dumps(good), 'first', self.packet)[0], good)

    def test_semantic_errors_are_not_mislabeled_technical(self):
        wrong = dict(self.second, conclusion='This proves the entire venue is safe for the full day.')
        following = module.second_packet(self.packet, self.first)
        self.assertEqual(module.decode(json.dumps(wrong), 'second', following)[0], wrong)

    def test_complete_historical_replay_and_no_live_entrypoint(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'replay'
            report = module.replay(out)
            self.assertEqual(report['legacy_total'], 48)
            self.assertEqual(report['legacy_admitted'] +
                sum(r['status']=='rejected' for r in module.read(out/'REPLAY.json')['legacy_rows']), 48)
            self.assertEqual(report['network_calls'], 0)
            self.assertEqual(module.read(out/'REPLAY.json')['real_new_schema_provider_outputs'], 0)
            with self.assertRaises(module.InterfaceError): module.replay(out)
        self.assertFalse(hasattr(module, 'run'))

    def test_offline_prepare_does_not_read_labels_and_hashes_packets(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'prepared'
            report = module.prepare(out)
            self.assertEqual(report['contexts'], 16)
            self.assertEqual(report['first_requests'], 32)
            self.assertFalse(module.read(out/'contract.json')['network_enabled'])
            manifest = module.read(out/'manifest.json')
            for name, expected in manifest['files'].items():
                self.assertEqual(module.digest(out/name), expected)
            self.assertFalse(any('label' in name.lower() for name in manifest['files']))
            with self.assertRaises(module.InterfaceError): module.prepare(out)


if __name__ == '__main__':
    unittest.main()
