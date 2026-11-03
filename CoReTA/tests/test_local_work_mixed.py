"""Mixed-sampling, common-tool fairness and failure invariants; not model scores."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from coreta.local_work.data import read
from coreta.local_work.mixed_data import select, EXCLUDED_CONTEXTS
from coreta.local_work.comparison import ComparisonFlow, replay_files, ARMS
from coreta.handoff.contracts import HandoffContracts
from local_work_comparison_smoke import smoke_case
from score_local_work_mixed import score
from coreta.local_work.evaluation import summarize

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/source/tatqa-20261027/tatqa_dataset_train.json'
CASE = ROOT / 'runs/local-work-mixed-prepared-20261027-v1/tasks/main-01/runtime.json'


class MixedTests(unittest.TestCase):
    def setUp(self):
        self.case = read(CASE)

    def finish_until_final(self, flow):
        while flow.wave < flow.final_wave:
            pending = flow.pending_requests()
            flow.submit({a: json.dumps(dict(message='Scripted interface check')) for a in pending})
        return flow.pending_requests()

    def test_uniform_main_sample_preserved(self):
        plan = select(SOURCE)
        self.assertEqual(plan['main_count'], 12)
        self.assertEqual(plan['eligible_questions'], 5526)
        self.assertEqual(plan['main_annotations'], {'table': 10, 'table-text': 2})
        self.assertEqual(plan['main_distinct_contexts'], 12)
        self.assertEqual(plan, select(SOURCE))
        main = [r for r in plan['rows'] if r['group'] == 'main']
        supplement = [r for r in plan['rows'] if r['group'] == 'diagnostic']
        self.assertFalse({r['context_index'] for r in main} & EXCLUDED_CONTEXTS)
        self.assertFalse({r['context_index'] for r in main} & {r['context_index'] for r in supplement})
        self.assertEqual(len(supplement), 2)

    def test_common_tools_and_source_access_equal_in_multi_agent_arms(self):
        a = ComparisonFlow(self.case, 'ordinary').pending_requests()
        b = ComparisonFlow(self.case, 'local_work').pending_requests()
        for actor in a:
            self.assertEqual(a[actor]['packet'], b[actor]['packet'])
            self.assertEqual(a[actor]['schema'], b[actor]['schema'])
            self.assertEqual(a[actor]['max_output_tokens'], b[actor]['max_output_tokens'])
            self.assertNotEqual(a[actor]['instructions'], b[actor]['instructions'])

    def test_equal_call_caps_and_full_context_single_agent(self):
        for arm in ARMS:
            flow = ComparisonFlow(self.case, arm)
            self.assertEqual(len(flow.schedule()), 7)
            self.assertEqual(sum(c for _, c in flow.schedule()), 13824)
        single = ComparisonFlow(self.case, 'single').pending_requests()['A1']
        self.assertEqual(len(single['packet']['sources']), len(self.case['task']['sources']) + 1)

    def test_main_final_roles_balanced_and_pairwise_fixed(self):
        plan = select(SOURCE)
        roles = [r['final_member'] for r in plan['rows'] if r['group'] == 'main']
        self.assertEqual(roles.count('A1'), 6)
        self.assertEqual(roles.count('A2'), 6)
        for arm in ('ordinary', 'local_work'):
            self.assertEqual(ComparisonFlow(self.case, arm).final_member, self.case['final_member'])

    def test_publication_is_next_wave_and_full_original(self):
        flow = ComparisonFlow(self.case, 'ordinary')
        snapshot = flow.pending_requests()
        self.assertNotIn('P1', [s['id'] for s in snapshot['A1']['packet']['sources']])
        flow.submit({'A1': json.dumps(dict(message='Read the table', source_ids=['T1'])),
                     'A2': json.dumps(dict(message='Read the paragraphs', source_ids=['P1']))})
        following = flow.pending_requests()['A1']['packet']
        original = next(s['content'] for s in self.case['task']['sources'] if s['id'] == 'P1')
        self.assertEqual(next(s['content'] for s in following['sources'] if s['id'] == 'P1'), original)
        self.assertEqual(len(following['messages']), 2)

    def test_ordinary_agent_can_use_local_work_option(self):
        from local_work_offline_trace import work
        flow = ComparisonFlow(self.case, 'ordinary')
        pending = flow.pending_requests()
        flow.submit({'A1': json.dumps(dict(message='Optional work is allowed', work=[work('x', ['T1'], value=3)])),
                     'A2': json.dumps(dict(message='No change'))})
        self.assertEqual(flow.session.results['W1']['value'], 3)

    def test_invalid_optional_component_does_not_drop_message(self):
        flow = ComparisonFlow(self.case, 'ordinary')
        flow.pending_requests()
        flow.submit({'A1': json.dumps(dict(message='Valid core', work='bad', calculations=[dict(expression='1/0', values={})])),
                     'A2': json.dumps(dict(message='Valid sibling'))})
        self.assertEqual(flow.status, 'pending')
        self.assertEqual(len(flow.messages), 2)
        self.assertEqual(len(flow.events[0]['notices']), 2)

    def test_core_failure_saves_sibling_and_stops_dependencies(self):
        flow = ComparisonFlow(self.case, 'ordinary')
        flow.pending_requests()
        flow.submit({'A1': '{"message":', 'A2': json.dumps(dict(message='Valid sibling'))})
        self.assertEqual(flow.status, 'technical_incomplete')
        self.assertEqual(len(flow.messages), 1)
        self.assertEqual(flow.pending_requests(), {})
        self.assertEqual(len(flow.requests), 2)

    def test_missing_file_replay_exports_partial_state(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / 'responses').mkdir()
            (path / 'responses/00-A2.raw.txt').write_text('{"message":"valid"}', encoding='utf8')
            result = replay_files(self.case, 'ordinary', path / 'responses', path / 'out')
            self.assertEqual(result['status'], 'technical_incomplete')
            self.assertEqual(result['received_responses'], 1)
            self.assertTrue((path / 'out/EVENTS.json').exists())
            self.assertFalse((path / 'out/requests/01-A1.json').exists())

    def test_undecodable_file_preserves_full_wave_raw_bytes_and_sibling(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / 'responses').mkdir()
            original = '{"message":"UTF16 example"}'.encode('utf-16')
            (path / 'responses/00-A1.raw.txt').write_bytes(original)
            (path / 'responses/00-A2.raw.txt').write_text('{"message":"valid sibling"}', encoding='utf8')
            result = replay_files(self.case, 'ordinary', path / 'responses', path / 'out',
                                  provenance='encoding regression fixture')
            self.assertEqual(result['status'], 'technical_incomplete')
            self.assertEqual(result['provenance'], 'encoding regression fixture')
            self.assertEqual((path / 'out/raw_bytes/00-A1.raw.bytes').read_bytes(), original)
            self.assertTrue((path / 'out/requests/00-A2.json').exists())
            events = read(path / 'out/EVENTS.json')
            self.assertEqual(events[0]['status'], 'unreadable_file')
            self.assertEqual(events[1]['status'], 'readable')
            self.assertFalse((path / 'out/requests/01-A1.json').exists())

    def test_caller_provenance_label_is_recorded_but_not_certified(self):
        flow = ComparisonFlow(self.case, 'ordinary', provenance='scripted test')
        self.assertEqual(flow.summary()['provenance'], 'scripted test')
        self.assertEqual(flow.summary()['provenance_status'], 'caller_declared_not_certified')
        self.assertIsNone(flow.summary()['method_accuracy'])

    def test_final_extra_annotations_and_optional_reference_do_not_discard_answer(self):
        flow = ComparisonFlow(self.case, 'single')
        self.finish_until_final(flow)
        flow.submit({'A1': json.dumps(dict(answer=0, scale='', reasoning='Zero is an answer',
                                          result_id=['invalid'], extra='kept in raw'))})
        self.assertEqual(flow.status, 'completed')
        self.assertEqual(flow.answer['delivered']['answer'], 0)
        self.assertEqual(len(flow.answer['notices']), 2)

    def test_calculator_result_rendering_available_to_all_arms(self):
        old = read(ROOT / 'runs/local-work-offline-20261027-v1/tasks/task-05/runtime.json')
        for arm in ARMS:
            record = smoke_case(old, arm)
            self.assertEqual(record['summary']['status'], 'completed')
            self.assertEqual(record['summary']['final']['delivered']['answer'], 206.7)
            self.assertEqual(record['summary']['prepared_requests'], 7)
            self.assertEqual(record['summary']['network_calls'], 0)

    def test_no_reference_fields_in_model_packets(self):
        for arm in ARMS:
            for req in ComparisonFlow(self.case, arm).pending_requests().values():
                task = req['packet']['task']
                self.assertEqual(set(task), {'task_id', 'question'})
                self.assertEqual(json.loads(req['instructions'].split('PACKET=', 1)[1]), req['packet'])
                HandoffContracts.decode('{"message":"valid"}', req['schema'])

    def test_official_evaluator_zero_scale_and_wrong_answer(self):
        reference = dict(answer=0, answer_type='arithmetic', scale='')
        self.assertEqual(score(reference, dict(answer=0, scale=''))['exact_match'], 1)
        reference = dict(answer=1, answer_type='arithmetic', scale='million')
        self.assertEqual(score(reference, dict(answer=1, scale='billion'))['exact_match'], 0)
        self.assertEqual(score(reference, dict(answer=2, scale='million'))['exact_match'], 0)
        self.assertEqual(score(reference, dict(answer=None, scale='million'))['nonanswer'], True)
        self.assertEqual(score(reference, dict(answer='  ', scale='million'))['nonanswer'], True)

    def test_main_and_supplement_not_pooled_and_no_phantom_scores(self):
        cases = [dict(case_id='m', group='main'), dict(case_id='d', group='diagnostic')]
        empty = summarize(cases, [])
        self.assertEqual(empty['status'], 'not_run')
        self.assertIsNone(empty['groups']['main']['arms']['ordinary']['official_em_completed'])
        rows = [dict(case_id='m', group='main', arm='ordinary', status='completed', exact_match=1),
                dict(case_id='m', group='main', arm='local_work', status='completed', exact_match=0),
                dict(case_id='d', group='diagnostic', arm='local_work', status='completed', exact_match=1)]
        result = summarize(cases, rows)
        self.assertEqual(result['groups']['main']['paired']['ordinary_only'], 1)
        self.assertEqual(result['groups']['diagnostic']['paired']['incomplete_or_missing'], ['d'])
        self.assertEqual(result['groups']['main']['arms']['local_work']['official_em_completed'], 0)
        self.assertEqual(result['groups']['diagnostic']['arms']['local_work']['official_em_completed'], 1)

    def test_incomplete_rows_are_not_silently_removed_from_operational_denominator(self):
        cases = [dict(case_id='a', group='main'), dict(case_id='b', group='main')]
        rows = [dict(case_id='a', group='main', arm='ordinary', status='completed', exact_match=1),
                dict(case_id='b', group='main', arm='ordinary', status='technical_incomplete')]
        result = summarize(cases, rows)['groups']['main']['arms']['ordinary']
        self.assertEqual(result['official_em_completed'], 1)
        self.assertEqual(result['end_to_end_success_all_planned'], 0.5)
        self.assertEqual(result['incomplete_or_missing'], ['b'])


if __name__ == '__main__':
    unittest.main()
