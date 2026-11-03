"""Offline comparator checks on three- and four-member real task packet shapes."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_workboard as baseline
from test_workboard_issue_loop import IssueLoopTests
from prepare_issue_loop_comparison import DATA, ARCHIVE, METHODS, budget, engine, read, prepare, verify
from coreta.handoff.__main__ import PROJECT, DESIGN, configure
from coreta.workboard.choice_inputs import ChoicePackets
from coreta.workboard.issue_loop import CHECK_STAGES, CHOICE_STAGES


class ComparisonTests(unittest.TestCase):
    def test_preparation_verify_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as folder, patch('urllib.request.urlopen', side_effect=AssertionError('No network')):
            output = Path(folder)/'prepared'
            manifest = prepare(output, counter=lambda text: len(text)//3)
            self.assertEqual(verify(output), manifest)
            self.assertEqual(len(manifest['pairs']), 2)
            first = output/manifest['pairs'][0]['initial_cache']
            first.write_text(first.read_text(encoding='utf-8')+' ', encoding='utf-8')
            with self.assertRaises(ValueError):
                verify(output)

    def test_both_arms_on_three_and_four_members(self):
        config, legacy = configure(PROJECT/'config/deepseek_flash_inspection.json', DESIGN/'runtime.defaults.json')
        for task, ordinal in (('hb-dev-005', 1), ('hb-dev-006', 2)):
            packets = ChoicePackets(DATA/task, 'distributed')
            cache = read(ARCHIVE/(task+'-r1')/'initial/cache.json')
            snapshot = copy.deepcopy(cache)
            for method in METHODS:
                with self.subTest(task=task, method=method), tempfile.TemporaryDirectory() as folder:
                    fixture = IssueLoopTests()
                    def handler(p):
                        stage = p['STAGE']
                        if stage == 'OBSERVE':
                            return dict(action='offer', offer=dict(target=p['CURRENT_WORK']['id'],
                                knowledge='SCRIPTED fact', support=[dict(ref='T', excerpt='SCRIPTED excerpt')],
                                proposed_use='SCRIPTED revision', claims=[dict(statement='SCRIPTED claim',
                                    premises='SCRIPTED premises', source_refs=['T'])]))
                        if stage == 'GROUND':
                            return dict(assessments={c['id']: dict(status='unresolved', reason='SCRIPTED', evidence_refs=['T'])
                                for c in p['CLAIMS']}, limits='SCRIPTED')
                        if stage in {'TRY', 'FINALIZE'}:
                            return fixture.change('new', work=dict(artifact='option_2', work_text='SCRIPTED revision', open_points=[]), sources=['T'])
                        if stage in CHECK_STAGES:
                            issue = method == METHODS[1]
                            value = dict(finding='no_issue_found', observation='SCRIPTED', scope='SCRIPTED')
                            if issue:
                                value.update(issues=[], rechecks={})
                            return value
                        if stage in CHOICE_STAGES:
                            value = dict(candidate_id=p['CHOICES'][-1], reason='SCRIPTED')
                            if method == METHODS[1]:
                                value['issue_dispositions'] = {}
                            return value
                        raise AssertionError(stage)
                    with patch('urllib.request.urlopen', side_effect=AssertionError('No network')):
                        runner = engine(Path(folder), packets, config, legacy, method, ordinal,
                                        cache, lambda text: len(text)//3,
                                        transport=lambda payload, timeout: script(payload, timeout))
                        script = baseline.Script(runner.journal, handler)
                        result = runner.run()
                    self.assertEqual(result['status'], 'completed', result.get('error'))
                    self.assertEqual(result['http_attempts'], (len(packets.agents)+1)**2)
                    self.assertNotIn('INITIAL', [p['STAGE'] for p in script.calls])
                    self.assertTrue(all(p['METHOD_VARIANT'] == method for p in script.calls))
                    for packet in script.calls:
                        canonical = {w['id']: w for w in packet.get('CANDIDATES', [])}
                        for key in ('CURRENT_WORK', 'BEFORE', 'AFTER', 'FINAL_PROPOSAL', 'FALLBACK'):
                            view = packet.get(key)
                            if view and view.get('content_in') == 'CANDIDATES':
                                original = runner.board.get(view['id'])
                                self.assertEqual(canonical[view['id']], original)
                        if packet['STAGE'] in CHECK_STAGES:
                            self.assertIn('WORK_AUTHOR_ACCESS', packet)
                            self.assertEqual('ISSUE_LEDGER' in packet, method == METHODS[1])
                    self.assertEqual(cache, snapshot)

    def test_budget_caps_match(self):
        _, legacy = configure(PROJECT/'config/deepseek_flash_inspection.json', DESIGN/'runtime.defaults.json')
        self.assertEqual(budget(4, legacy)['limits']['max_output_tokens_total'], 67584)
        self.assertEqual(budget(3, legacy)['limits']['max_output_tokens_total'], 45056)


if __name__ == '__main__':
    unittest.main()
