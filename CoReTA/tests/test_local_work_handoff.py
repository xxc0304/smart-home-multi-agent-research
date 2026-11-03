"""Atomic work production/consumption invariants; scripted checks, not model effects."""
import copy
import json
import unittest

from coreta.local_work.handoff import HandoffSession
from coreta.local_work.handoff_flow import HandoffFlow


def task():
    return dict(task_id='engineering', question='Combine both partial totals.', members=['A1', 'A2'],
                sources=[dict(id='T1', owner='A1', kind='table', content='2 units at 3 dollars.'),
                         dict(id='T2', owner='A2', kind='table', content='5 units at 4 dollars.')])


def meta(subject='subtotal', unit='USD', period='2019'):
    return dict(subject=subject, unit=unit, period=period)


def receipt(expression, basis, inputs=None, conditions=None, **kw):
    return dict(target='Supported local work', metadata=meta(), expression=expression,
                inputs=inputs or [], basis=basis, conditions=conditions or [], **kw)


def operand(name, ref=None, value=None, metadata=None):
    return dict(name=name, result_id=ref, value=value, metadata=metadata or meta())


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.s = HandoffSession(task())

    def send(self, actor, work, packet=None):
        return self.s.accept_many(actor, work, packet or self.s.packet(actor, 0))

    def producers(self):
        self.send('A1', [receipt('2*3', ['T1'], conditions=['Use for the requested period only.'])])
        self.send('A2', [receipt('5*4', ['T2'])])

    def test_known_formula_is_ready_on_first_submission(self):
        event = self.send('A1', [receipt('2*3', ['T1'])])
        self.assertEqual(event['notices'], [])
        self.assertEqual(self.s.results['W1']['value'], 6)
        self.assertEqual(self.s.binding_rows(), [])

    def test_inline_named_known_values_need_no_separate_nodes(self):
        self.send('A1', [receipt('count*price', ['T1'], inputs=[
            dict(name='count', value=2), dict(name='price', value=3)])])
        self.assertEqual(self.s.results['W1']['value'], 6)
        self.assertEqual(len(self.s.nodes), 1)
        self.assertEqual(self.s.recipes['W1']['expression'], 'count*price')

    def test_explicit_cross_member_selection_executes_atomically(self):
        self.producers()
        event = self.send('A1', [receipt('mine+peer', ['TASK'], inputs=[
            operand('mine', 'W1'), operand('peer', 'W2')])])
        self.assertEqual(event['accepted_work'], ['W3'])
        self.assertEqual(len(event['bindings']), 2)
        self.assertEqual(self.s.results['W3']['value'], 26)
        self.assertEqual(self.s.results['W3']['sources'], ['T1', 'T2', 'TASK'])
        self.assertIn('Use for the requested period only.', self.s.results['W3']['conditions'])

    def test_true_missing_input_stays_waiting(self):
        self.send('A1', [receipt('6+unknown', ['T1'], inputs=[operand('unknown')])])
        self.assertEqual(self.s.results['W1']['status'], 'waiting')
        self.assertIsNone(self.s.results['W1']['value'])

    def test_overlooked_known_input_cannot_be_distinguished_from_true_absence(self):
        # The original source explicitly contains 2 and 3, but host cannot interpret prose for the agent.
        self.send('A1', [receipt('q*p', ['T1'], inputs=[operand('q'), operand('p')])])
        self.assertEqual(self.s.results['W1']['status'], 'waiting')
        self.assertEqual(len(self.s.results['W1']['missing']), 2)

    def test_copied_number_is_not_a_dependency_or_revision_guarantee(self):
        self.producers()
        self.send('A1', [receipt('6+20', ['TASK'])])
        self.send('A1', [receipt('a+b', ['TASK'], inputs=[operand('a', 'W1'), operand('b', 'W2')])])
        self.assertEqual(self.s.results['W3']['value'], self.s.results['W4']['value'])
        self.assertEqual(self.s.results['W3']['sources'], ['TASK'])
        self.assertEqual(self.s.results['W3']['conditions'], [])
        self.assertIn('T2', self.s.results['W4']['sources'])
        self.send('A2', [receipt('5*5', ['T2'], replaces='W2', expected_revision=1)])
        self.assertEqual(self.s.results['W3']['value'], 26)
        self.assertEqual(self.s.results['W4']['value'], 31)

    def test_missing_can_be_replaced_by_explicit_visible_provider(self):
        self.send('A1', [receipt('6+unknown', ['T1'], inputs=[operand('unknown')])])
        self.send('A2', [receipt('5*4', ['T2'])])
        self.send('A1', [receipt('6+unknown', ['T1'], inputs=[operand('unknown', 'W2')],
                                 replaces='W1', expected_revision=1)])
        self.assertEqual(self.s.results['W1']['value'], 26)
        self.assertEqual(self.s.nodes['W1']['revision'], 2)

    def test_wrong_unit_rejects_entire_transaction(self):
        self.producers()
        before = copy.deepcopy((self.s.nodes, self.s.bindings, self.s.results, self.s.disclosed))
        event = self.send('A1', [receipt('a+b', ['TASK'], inputs=[operand('a', 'W1'),
                   operand('b', 'W2', metadata=meta(unit='EUR'))])])
        self.assertEqual(event['accepted_work'], [])
        self.assertIn('unit/period mismatch', event['notices'][0]['reason'])
        self.assertEqual(before, (self.s.nodes, self.s.bindings, self.s.results, self.s.disclosed))

    def test_same_wave_unseen_provider_is_not_admitted(self):
        frozen = self.s.packet('A1', 0)
        self.send('A2', [receipt('5*4', ['T2'])])
        event = self.send('A1', [receipt('x+6', ['T1'], inputs=[operand('x', 'W1')])], frozen)
        self.assertEqual(event['accepted_work'], [])
        self.assertIn('outside saved receipt snapshot', event['notices'][0]['reason'])

    def test_provider_revision_recomputes_consumers_and_conditions(self):
        self.producers()
        self.send('A1', [receipt('a+b', ['TASK'], inputs=[operand('a', 'W1'), operand('b', 'W2')])])
        self.send('A2', [receipt('5*5', ['T2'], conditions=['Corrected price assumption.'],
                                 replaces='W2', expected_revision=1)])
        self.assertEqual(self.s.results['W3']['value'], 31)
        self.assertIn('Corrected price assumption.', self.s.results['W3']['conditions'])
        changed = receipt('5*5', ['T2'], replaces='W2', expected_revision=2)
        changed['metadata']['period'] = '2018'
        self.send('A2', [changed])
        self.assertEqual(self.s.results['W3']['status'], 'waiting')

    def test_revision_to_unknown_does_not_keep_a_stale_binding(self):
        self.producers()
        self.send('A1', [receipt('a+b', ['TASK'], inputs=[operand('a', 'W1'), operand('b', 'W2')])])
        self.send('A1', [receipt('a+b', ['TASK'], inputs=[operand('a', 'W1'), operand('b')],
                                 replaces='W3', expected_revision=1)])
        self.assertEqual(self.s.results['W3']['status'], 'waiting')
        self.assertNotIn(('W3', 'b'), self.s.bindings)

    def test_foreign_revision_and_self_support_rejected(self):
        self.producers()
        event = self.send('A1', [receipt('5', ['TASK'], replaces='W2', expected_revision=1)])
        self.assertEqual(event['accepted_work'], [])
        event = self.send('A1', [receipt('x+1', ['TASK'], inputs=[operand('x', 'W1')],
                                         replaces='W1', expected_revision=1)])
        self.assertIn('cyclic', event['notices'][0]['reason'])
        self.assertEqual(self.s.results['W1']['value'], 6)

    def test_arithmetic_execution_failure_is_not_a_ready_answer(self):
        self.send('A1', [receipt('1/0', ['T1'])])
        self.assertEqual(self.s.results['W1']['status'], 'execution_error')
        self.assertIsNone(self.s.results['W1']['value'])

    def test_invisible_evidence_and_conflicting_operand_forms_rejected(self):
        event = self.send('A1', [receipt('5*4', ['T2'])])
        self.assertEqual(event['accepted_work'], [])
        self.producers()
        event = self.send('A1', [receipt('x+1', ['TASK'], inputs=[operand('x', 'W2', value=20)])])
        self.assertIn('both value and result_id', event['notices'][0]['reason'])


class HandoffFlowTests(unittest.TestCase):
    def case(self):
        return dict(case_id='engineering', group='engineering', final_member='A1', task=task())

    def reply(self, receipts=None, **extra):
        return json.dumps(dict(message='Scripted engineering reply, not model generation', receipts=receipts or [], **extra))

    def test_three_wave_cross_member_result_reaches_final(self):
        flow = HandoffFlow(self.case())
        original = flow.pending_requests()
        self.assertNotIn('T2', [s['id'] for s in original['A1']['packet']['sources']])
        flow.submit({'A1': self.reply([receipt('2*3', ['T1'])]),
                     'A2': self.reply([receipt('5*4', ['T2'])])})
        self.assertEqual(flow.session.results['W1']['value'], 6)
        self.assertEqual(flow.session.results['W2']['value'], 20)
        next_requests = flow.pending_requests()
        self.assertIn('receipts', next_requests['A1']['packet'])
        self.assertNotIn('work', next_requests['A1']['packet'])
        flow.submit({'A1': self.reply([receipt('a+b', ['TASK'], inputs=[operand('a', 'W1'), operand('b', 'W2')])]),
                     'A2': self.reply()})
        self.assertEqual(flow.session.results['W3']['value'], 26)
        flow.pending_requests()
        flow.submit({'A1': self.reply(), 'A2': self.reply()})
        flow.pending_requests()
        flow.submit({'A1': json.dumps(dict(answer=None, result_id='W3', scale='', reasoning='Use applicable combined result.'))})
        self.assertEqual(flow.answer['delivered']['answer'], 26)
        self.assertEqual(flow.final_use()['owners'], ['A1', 'A2'])
        self.assertEqual(len(flow.requests), 7)

    def test_failed_atomic_work_is_reported_only_to_submitter(self):
        flow = HandoffFlow(self.case())
        flow.pending_requests()
        flow.submit({'A1': self.reply([receipt('2*3', ['T2'])]), 'A2': self.reply()})
        following = flow.pending_requests()
        self.assertEqual(following['A1']['packet']['tool_feedback']['notices'][0]['kind'], 'rejected_receipt')
        self.assertEqual(following['A2']['packet']['tool_feedback']['notices'], [])
        self.assertEqual(flow.session.nodes, {})

    def test_wrong_but_well_formed_work_is_not_magically_corrected(self):
        flow = HandoffFlow(self.case())
        flow.pending_requests()
        flow.submit({'A1': self.reply([receipt('2*30', ['T1'])]), 'A2': self.reply()})
        self.assertEqual(flow.session.results['W1']['value'], 60)
        self.assertEqual(flow.session.results['W1']['truth_status'], 'model_declared_not_semantically_verified')
        while flow.wave < flow.final_wave:
            flow.submit({actor: self.reply() for actor in flow.pending_requests()})
        flow.pending_requests()
        flow.submit({'A1': json.dumps(dict(answer=6, result_id=None, scale='', reasoning='Reject incorrect price 30.'))})
        self.assertEqual(flow.answer['delivered']['answer'], 6)
        self.assertEqual(flow.final_use()['kind'], 'explicit_answer')

    def test_bad_core_blocks_dependencies_and_old_separate_actions_are_not_silently_converted(self):
        flow = HandoffFlow(self.case())
        flow.pending_requests()
        flow.submit({'A1': self.reply(work=[]), 'A2': self.reply()})
        self.assertEqual(flow.events[0]['notices'][0]['kind'], 'unsupported_separate_work_binding')
        flow.pending_requests()
        flow.submit({'A1': '{"message":', 'A2': self.reply()})
        self.assertEqual(flow.status, 'technical_incomplete')
        self.assertEqual(flow.pending_requests(), {})


if __name__ == '__main__':
    unittest.main()
