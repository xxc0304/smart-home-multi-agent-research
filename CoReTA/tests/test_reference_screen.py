"""Reference isolation/repair regressions and independent screening boundaries."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from coreta.model_client import DeepSeekClient
from coreta.revision import RevisionContracts, RevisionRunner
from coreta.schemas import ProtocolError, check_refs
from coreta.state import reference_index
from test_revision import Script, TASK, candidate

ROOT = Path(__file__).resolve().parents[1]


class ReferenceScreenChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def runner(self, script, directory=None, bank=None):
        cfg = json.loads((ROOT / 'config/deepseek_flash.json').read_text(encoding='utf-8'))
        cfg['generation']['max_input_tokens'] = 1000000
        cfg['generation']['max_output_tokens'].update(synthesize=3072, build=2048, inspect=2048, apply=4096)
        prompts = json.loads((ROOT / 'design/revision_prompts.json').read_text(encoding='utf-8'))
        d = directory or self.directory
        d.mkdir(exist_ok=True)
        r = RevisionRunner(TASK, d, 'fixture', RevisionContracts(ROOT / 'design/v0.3/coreta.schema.json'),
                           None, cfg, prompts, draft_bank=bank)
        r.client = DeepSeekClient(cfg, r.log, transport=script)
        return r

    def test_current_exposes_both_aliases(self):
        visible = set(reference_index({'current': {'version': 2, 'source_event_id': 'e2', 'candidate': candidate()}}))
        self.assertTrue({'e2', 'e2#s1', 'v2:s1'} <= visible)

    def test_citation_does_not_expose_hidden_source(self):
        c = candidate()
        c['steps'][0]['basis_refs'] = ['hidden#s1']
        visible = set(reference_index({'current': {'version': 2, 'source_event_id': 'e2', 'candidate': c}}))
        self.assertNotIn('hidden#s1', visible)
        with self.assertRaises(ProtocolError):
            check_refs({'basis_refs': ['hidden#s1']}, visible)

    def test_old_version_not_visible_without_old_material(self):
        visible = set(reference_index({'current': {'version': 2, 'source_event_id': 'e2', 'candidate': candidate()}}))
        for ref in ['v1:s1', 'e1#s1']:
            with self.assertRaises(ProtocolError):
                check_refs({'basis_refs': [ref]}, visible)

    def test_visible_versions_keep_distinct_sources(self):
        material = [{'version': n, 'source_event_id': f'e{n}', 'candidate': candidate()} for n in (1, 2)]
        self.assertTrue({'e1#s1', 'e2#s1', 'v1:s1', 'v2:s1'} <= set(reference_index(material)))

    def test_repair_suggestions_do_not_cross_event(self):
        with self.assertRaises(ProtocolError) as caught:
            check_refs({'basis_refs': ['e1#s99']}, {'e1#s1', 'e2#s99', 'v2:s99'})
        self.assertIn('e1#s1', caught.exception.detail)
        self.assertNotIn('e2#s99', caught.exception.detail)
        self.assertNotIn('v2:s99', caught.exception.detail)

    def test_actual_call_repairs_bad_reference_then_commits(self):
        script, repair_prompts = Script(), []
        corrupted = False
        def transport(payload, timeout):
            nonlocal corrupted
            response = script(payload, timeout)
            if 'body' in payload['text']['format']['schema']['properties']:
                value = json.loads(response['output'][0]['content'][0]['text'])
                if not corrupted:
                    value['basis_refs'] = ['fixture:e0003#s99']
                    corrupted = True
                else:
                    repair_prompts.append(payload['instructions'])
                    value['basis_refs'] = ['fixture:e0003#s1']
                response['output'][0]['content'][0]['text'] = json.dumps(value)
            return response
        r = self.runner(transport)
        result = r.run()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['format_repairs'], 1)
        self.assertIn('fixture:e0003#s99', repair_prompts[0])
        self.assertIn('same source', repair_prompts[0])
        self.assertEqual(next(e for e in r.events if e['stage']=='build')['payload']['basis_refs'], ['fixture:e0003#s1'])

    def test_screen_calls_only_three_independent_drafts(self):
        script = Script()
        r = self.runner(script)
        result = r.run_drafts()
        self.assertEqual(result['draft_count'], 3)
        self.assertEqual(result['normal_calls'], 3)
        self.assertEqual([s for s, _, _ in script.seen], ['draft'] * 3)
        self.assertTrue(all(set(material) == {'task'} for _, _, material in script.seen))
        self.assertFalse((self.directory / 'result.json').exists())

    def test_screen_bank_is_reusable_for_collaboration(self):
        bank = self.directory / 'bank'
        first = self.runner(Script(), self.directory / 'screen', bank)
        first.run_drafts()
        second = self.runner(Script(), self.directory / 'comparison', bank)
        result = second.run()
        self.assertEqual([e['payload'] for e in first.drafts], [e['payload'] for e in second.drafts])
        self.assertEqual(result['http_attempts'], 5)


if __name__ == '__main__':
    unittest.main()
