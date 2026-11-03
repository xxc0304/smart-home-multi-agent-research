"""Observed live interface failures, feedback isolation and actual work-result use."""
import copy
import json
import unittest

from coreta.local_work.comparison_v2 import ComparisonFlowV2, SCALES, make_flow
from coreta.handoff.contracts import HandoffContracts
from local_work_offline_trace import work, metadata, binding


def case():
    return dict(case_id='engineering', group='engineering', final_member='A1',
                task=dict(task_id='engineering', question='Combine supported quantities.', members=['A1', 'A2'],
                          sources=[dict(id='T1', owner='A1', kind='table', content='Quantity x = 3.'),
                                   dict(id='P1', owner='A2', kind='paragraph', content='Add 2 to supplied x.')]))


def reply(**kw):
    return json.dumps(dict(message='Scripted interface verification, not model output', **kw))


class InterfaceTests(unittest.TestCase):
    def test_initial_guidance_and_schema_equal_across_multiagent_arms(self):
        left = ComparisonFlowV2(case(), 'ordinary').pending_requests()
        right = ComparisonFlowV2(case(), 'local_work').pending_requests()
        for actor in left:
            self.assertEqual(left[actor]['packet'], right[actor]['packet'])
            self.assertEqual(left[actor]['schema'], right[actor]['schema'])
            self.assertIn('TOOL INTERFACE', left[actor]['instructions'])
            self.assertIsNone(left[actor]['packet']['tool_feedback'])

    def test_feedback_is_own_only_next_wave_and_saved_identically(self):
        flow = ComparisonFlowV2(case(), 'ordinary')
        initial = flow.pending_requests()
        invalid = work('bad', ['T1'], value=3, expression='3')
        flow.submit({'A1': reply(work=[invalid]), 'A2': reply()})
        following = flow.pending_requests()
        self.assertIsNone(initial['A1']['packet']['tool_feedback'])
        own = following['A1']['packet']['tool_feedback']
        self.assertEqual(own['notices'][0]['reason'], 'operation cannot also assert a value')
        self.assertEqual(following['A2']['packet']['tool_feedback']['notices'], [])
        self.assertEqual(flow.requests[-2:], list(following.values()))
        self.assertEqual(following, flow.pending_requests())
        for request in following.values():
            self.assertEqual(json.loads(request['instructions'].split('\nPACKET=', 1)[1]), request['packet'])

    def test_rejected_calculation_not_auto_repaired_and_can_be_corrected(self):
        flow = ComparisonFlowV2(case(), 'ordinary')
        flow.pending_requests()
        flow.submit({'A1': reply(calculations=[dict(expression='3+2', values={'x': 3})]), 'A2': reply()})
        self.assertEqual(flow.calculations, [])
        feedback = flow.pending_requests()['A1']['packet']['tool_feedback']
        self.assertEqual(feedback['notices'][0]['kind'], 'rejected_calculation')
        flow.submit({'A1': reply(calculations=[dict(expression='3+2', values={})]), 'A2': reply()})
        following = flow.pending_requests()
        self.assertEqual(following['A1']['packet']['tool_feedback']['accepted_calculations'][0]['value'], 5)
        self.assertEqual(following['A2']['packet']['tool_feedback']['accepted_calculations'], [])
        self.assertEqual(following['A1']['packet']['tool_feedback']['notices'], [])

    def test_no_extra_calls_and_no_forced_work_reference(self):
        for arm in ('ordinary', 'local_work', 'single'):
            flow = ComparisonFlowV2(case(), arm)
            self.assertEqual(len(flow.schedule()), 7)
            self.assertEqual(sum(cap for _, cap in flow.schedule()), 13824)
            while flow.wave < flow.final_wave:
                flow.submit({actor: reply() for actor in flow.pending_requests()})
            request = flow.pending_requests()['A1']
            self.assertEqual(request['schema']['properties']['scale']['enum'], SCALES)
            flow.submit({'A1': json.dumps(dict(answer=0, result_id=None, scale='', reasoning='Explicit zero.'))})
            self.assertEqual(flow.answer['delivered']['answer'], 0)
            self.assertEqual(flow.final_use()['kind'], 'explicit_answer')

    def test_literal_operation_guidance_keeps_runtime_mutual_exclusion(self):
        flow = ComparisonFlowV2(case(), 'ordinary')
        request = flow.pending_requests()['A1']
        good = work('x', ['T1'], value=3)
        HandoffContracts.decode(reply(work=[good]), request['schema'])
        invalid = copy.deepcopy(good)
        invalid['expression'] = '3'
        self.assertNotIn('oneOf', request['schema']['properties']['work']['items'])
        flow.submit({'A1': reply(work=[invalid]), 'A2': reply()})
        self.assertEqual(flow.events[0]['engine_event']['notices'][0]['kind'], 'rejected_work')
        self.assertEqual(flow.status, 'pending')

    def test_cross_member_graph_can_reach_final_and_retains_conditions(self):
        flow = ComparisonFlowV2(case(), 'local_work')
        flow.pending_requests()
        provider = work('x', ['T1'], value=3, conditions=['Input must refer to the requested period.'])
        consumer = work('total', ['P1'], expression='x+2',
                        inputs=[dict(name='x', metadata=metadata('x'))])
        flow.submit({'A1': reply(work=[provider]), 'A2': reply(work=[consumer])})
        flow.pending_requests()
        flow.submit({'A1': reply(), 'A2': reply(bindings=[binding('W2', 'x', 'W1')])})
        flow.pending_requests()
        flow.submit({'A1': reply(), 'A2': reply()})
        flow.pending_requests()
        flow.submit({'A1': json.dumps(dict(answer=5, scale='', reasoning='Use the combined work.', result_id='W2'))})
        trace = flow.final_use()
        self.assertEqual(trace['owners'], ['A1', 'A2'])
        self.assertEqual(trace['work_ids'], ['W1', 'W2'])
        self.assertEqual(flow.answer['delivered']['answer'], 5)
        self.assertIn(provider['conditions'][0], flow.answer['conditions'])

    def test_calculator_is_not_counted_as_explicit_work_chain(self):
        flow = ComparisonFlowV2(case(), 'single')
        flow.pending_requests()
        flow.submit({'A1': reply(calculations=[dict(expression='3+2', values={})])})
        while flow.wave < flow.final_wave:
            flow.submit({'A1': reply()})
        flow.pending_requests()
        flow.submit({'A1': json.dumps(dict(answer=5, scale='', reasoning='Calculator result.', result_id='C1'))})
        self.assertEqual(flow.final_use()['kind'], 'calculator_reference')
        self.assertEqual(flow.final_use()['owners'], [])

    def test_core_failure_still_blocks_dependencies(self):
        flow = ComparisonFlowV2(case(), 'local_work')
        flow.pending_requests()
        flow.submit({'A1': '{"message":', 'A2': reply()})
        self.assertEqual(flow.status, 'technical_incomplete')
        self.assertEqual(flow.pending_requests(), {})

    def test_discussion_control_has_calculator_but_no_work_capability(self):
        flow = make_flow(case(), 'discussion')
        initial = flow.pending_requests()
        self.assertNotIn('work', initial['A1']['schema']['properties'])
        self.assertNotIn('work', initial['A1']['packet'])
        self.assertEqual(len(flow.schedule()), 7)
        flow.submit({'A1': reply(work=[work('x', ['T1'], value=3)],
                                 calculations=[dict(expression='3+2', values={})]), 'A2': reply()})
        following = flow.pending_requests()
        self.assertEqual(flow.session.nodes, {})
        self.assertEqual(following['A1']['packet']['calculator_results'][0]['value'], 5)
        self.assertEqual(following['A1']['packet']['tool_feedback']['notices'][0]['kind'], 'unsupported_work_component')
        self.assertEqual(flow.summary()['arm'], 'discussion')

    def test_v2_scoring_retains_unstarted_and_keeps_strata_separate(self):
        from score_local_work_v2 import aggregate
        rows = []
        for group in ('ordinary_regression', 'controlled_dependency'):
            for arm in ('discussion', 'ordinary', 'local_work'):
                for number in (1, 2):
                    rows.append(dict(case_id=f'{group}-{number}', group=group, arm=arm,
                                     status='completed' if number == 1 else 'not_started',
                                     exact_match=1 if number == 1 else None))
        result = aggregate(rows)
        for group in result['groups'].values():
            for values in group['arms'].values():
                self.assertEqual(values['planned'], 2)
                self.assertEqual(values['official_em_completed'], 1)
                self.assertEqual(values['all_planned_success'], .5)

    def test_unavailable_work_or_calculator_reference_gets_no_graph_credit(self):
        for ref in ('W1', 'C99'):
            flow = ComparisonFlowV2(case(), 'single')
            flow.pending_requests()
            waiting = work('waiting', ['T1'], expression='missing+2',
                           inputs=[dict(name='missing', metadata=metadata('missing'))])
            flow.submit({'A1': reply(work=[waiting])})
            while flow.wave < flow.final_wave:
                flow.submit({'A1': reply()})
            flow.pending_requests()
            flow.submit({'A1': json.dumps(dict(answer=9, scale='', reasoning='Explicit fallback.', result_id=ref))})
            self.assertEqual(flow.answer['delivered']['answer'], 9)
            self.assertEqual(flow.final_use()['kind'], 'explicit_answer')
            self.assertEqual(flow.final_use()['owners'], [])


if __name__ == '__main__':
    unittest.main()
