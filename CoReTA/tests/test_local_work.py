"""Engineering invariants, not evidence of autonomous coordination or accuracy."""
import copy
import json
import os
import unittest
from pathlib import Path

from coreta.local_work.data import read, member_packet, swapped
from coreta.local_work.engine import WorkSession, RESPONSE_SCHEMA
from coreta.local_work.prompts import request, final_request
from coreta.handoff.contracts import HandoffContracts
from coreta.schemas import ProtocolError
from local_work_offline_trace import work, metadata, response, binding, trace


ROOT = Path(__file__).resolve().parents[1]
TASK = Path(os.environ.get('CORETA_LOCAL_WORK_TASK', ROOT / 'runs/local-work-offline-20261027-v1/tasks/task-05/runtime.json'))


class LocalWorkTests(unittest.TestCase):
    def setUp(self):
        self.task = read(TASK)
        self.s = WorkSession(self.task)

    def apply(self, actor, items=None, edges=None):
        packet = self.s.packet(actor, 0)
        return self.s.apply(actor, response(work=items, bindings=edges), packet)

    def setup_difference(self, conditions=None):
        self.apply('A2', [work('committed_credit', ['P4'], value=1137.4, conditions=conditions),
                          work('uncommitted_credit', ['TASK'], expression='total - committed', inputs=[
                              dict(name='total', metadata=metadata('total_available_credit')),
                              dict(name='committed', metadata=metadata('committed_credit'))])])
        self.apply('A1', [work('total_available_credit', ['T1'], value=1344.1)])
        self.apply('A2', edges=[binding('W2', 'total', 'W3'), binding('W2', 'committed', 'W1')])

    def test_real_source_continuation(self):
        record = trace(self.task)
        self.assertEqual(record['final']['delivered']['answer'], 206.7)
        self.assertEqual(record['snapshots'][0]['results']['W2']['status'], 'waiting')
        self.assertEqual(record['snapshots'][1]['results']['W2']['sources'], ['P4', 'T1', 'TASK'])
        self.assertEqual(record['autonomous_generations'], 0)

    def test_missing_input_never_becomes_zero(self):
        self.apply('A1', [work('out', ['TASK'], expression='x + 1', inputs=[dict(name='x', metadata=metadata('x'))])])
        self.assertEqual(self.s.results['W1']['status'], 'waiting')
        self.assertIsNone(self.s.results['W1']['value'])

    def test_wrong_unit_and_period_are_explicit_rejections(self):
        self.setup_difference()
        item = work('total_available_credit', ['T1'], value=1344.1)
        item['metadata']['period'] = '2018-12-31'
        item['metadata']['unit'] = 'USD'
        self.apply('A1', [item])
        event = self.apply('A2', edges=[binding('W2', 'total', 'W4')])
        self.assertEqual(event['notices'][0]['kind'], 'rejected_binding')
        self.assertEqual(self.s.results['W2']['value'], 206.7)  # prior valid edge preserved

    def test_consumer_can_explicitly_map_different_subject_labels(self):
        self.setup_difference()
        item = work('total credit shown in the table', ['T1'], value=1344.1)
        self.apply('A1', [item])
        event = self.apply('A2', edges=[binding('W2', 'total', 'W4')])
        self.assertEqual(event['notices'], [])
        self.assertEqual(self.s.results['W2']['value'], 206.7)

    def test_condition_inheritance_is_not_silently_cleared(self):
        self.setup_difference(['forecast, not confirmed actual'])
        self.assertEqual(self.s.results['W2']['conditions'], ['forecast, not confirmed actual'])
        delivery = self.s.deliver(json.dumps(dict(answer=None, result_id='W2', scale='million', reasoning='use result')),
                                  self.s.packet('A1', 'final'))
        self.assertEqual(delivery['conditions'], ['forecast, not confirmed actual'])

    def test_literal_revision_recomputes_descendant(self):
        self.setup_difference()
        self.apply('A1', [work('total_available_credit', ['T1'], value=1400, replaces='W3', expected_revision=1)])
        self.assertEqual(self.s.results['W2']['value'], 262.6)
        self.assertEqual(self.s.nodes['W3']['revision'], 2)

    def test_changed_metadata_blocks_stale_edge_and_leaves_other_work(self):
        self.setup_difference()
        item = work('total_available_credit', ['T1'], value=1400, replaces='W3', expected_revision=1)
        item['metadata']['period'] = '2018-12-31'
        self.apply('A1', [item])
        self.assertEqual(self.s.results['W2']['missing'][0]['reason'], 'changed_metadata')
        self.assertEqual(self.s.results['W1']['value'], 1137.4)

    def test_operation_revision_reuses_unchanged_input_bindings(self):
        self.setup_difference()
        item = copy.deepcopy(self.s.nodes['W2'])
        item = {k: v for k, v in item.items() if k not in ('id', 'owner', 'revision')}
        item.update(replaces='W2', expected_revision=1, expression='total + committed')
        self.apply('A2', [item])
        self.assertEqual(self.s.results['W2']['value'], 2481.5)
        self.assertEqual(self.s.results['W1']['status'], 'ready')

    def test_conditions_only_revision_keeps_inputs_and_updates_conditions(self):
        self.setup_difference()
        item = {k: copy.deepcopy(v) for k, v in self.s.nodes['W2'].items()
                if k not in ('id', 'owner', 'revision')}
        item.update(replaces='W2', expected_revision=1, conditions=['newly identified condition'])
        self.apply('A2', [item])
        self.assertEqual(self.s.results['W2']['value'], 206.7)
        self.assertEqual(self.s.results['W2']['conditions'], ['newly identified condition'])

    def test_changed_input_definition_only_drops_affected_binding(self):
        self.setup_difference()
        item = {k: copy.deepcopy(v) for k, v in self.s.nodes['W2'].items()
                if k not in ('id', 'owner', 'revision')}
        item.update(replaces='W2', expected_revision=1)
        item['inputs'][0]['metadata']['period'] = '2018-12-31'
        self.apply('A2', [item])
        self.assertEqual(self.s.results['W2']['missing'], [dict(input='total', reason='missing_binding')])
        self.assertIn(('W2', 'committed'), self.s.bindings)

    def test_saved_snapshot_cannot_authorize_unseen_provider_metadata(self):
        self.setup_difference()
        frozen = self.s.packet('A2', 2)
        item = work('unrelated_quantity', ['T1'], value=99, replaces='W3', expected_revision=1)
        self.apply('A1', [item])
        event = self.s.apply('A2', response(bindings=[binding('W2', 'total', 'W3')]), frozen)
        self.assertEqual(event['notices'][0]['kind'], 'rejected_binding')
        self.assertEqual(self.s.results['W2']['status'], 'waiting')

    def test_stale_revision_and_foreign_owner_do_not_change_state(self):
        self.setup_difference()
        event = self.apply('A1', edges=[binding('W2', 'total', 'W3')])
        self.assertEqual(event['notices'][0]['kind'], 'rejected_binding')
        event = self.apply('A2', edges=[binding('W2', 'total', 'W3', revision=9)])
        self.assertEqual(event['notices'][0]['kind'], 'rejected_binding')
        self.assertEqual(self.s.results['W2']['value'], 206.7)

    def test_cycles_cannot_become_support(self):
        self.apply('A1', [work('same', ['TASK'], expression='x + 1', inputs=[dict(name='x', metadata=metadata('same'))]),
                          work('same', ['TASK'], expression='x + 1', inputs=[dict(name='x', metadata=metadata('same'))])])
        self.apply('A1', edges=[binding('W1', 'x', 'W2')])
        event = self.apply('A1', edges=[binding('W2', 'x', 'W1')])
        self.assertIn('cyclic', event['notices'][0]['reason'])
        self.assertEqual(self.s.results['W1']['status'], 'waiting')

    def test_same_wave_cannot_use_later_disclosure(self):
        a1 = self.s.packet('A1', 0)
        self.apply('A2', [work('committed_credit', ['P4'], value=1137.4)])
        event = self.s.apply('A1', response(work=[work('x', ['P4'], value=1)]), a1)
        self.assertEqual(event['notices'][0]['kind'], 'rejected_work')
        self.assertEqual(len(self.s.nodes), 1)

    def test_bad_optional_edge_does_not_discard_valid_sibling(self):
        self.setup_difference()
        event = self.apply('A2', edges=[{'unexpected': 'bad'}, binding('W2', 'total', 'W3')])
        self.assertEqual(event['status'], 'readable')
        self.assertEqual(len(event['notices']), 1)
        self.assertEqual(len(event['bindings']), 1)

    def test_bad_work_does_not_discard_valid_work(self):
        event = self.apply('A1', [{'wrong': 'fields'}, work('x', ['T1'], value=0)])
        self.assertEqual(event['status'], 'readable')
        self.assertEqual(len(event['accepted_work']), 1)
        self.assertEqual(self.s.results['W1']['value'], 0)

    def test_unreadable_core_keeps_raw_and_does_not_mutate(self):
        for raw in ('{"message":"x","work":[', '{"message":"x","message":"y","work":[]}',
                    '{"message":"x","work":[NaN]}', '{"message":"x"}', '[]'):
            event = self.s.apply('A1', raw, self.s.packet('A1', 0))
            self.assertEqual(event['status'], 'unreadable_core')
            self.assertEqual(event['raw'], raw)
        self.assertEqual(self.s.nodes, {})

    def test_nonfinite_bool_and_code_are_not_executed(self):
        for item in (work('x', ['T1'], value=True), work('x', ['T1'], expression='__import__("os")'),
                     work('x', ['T1'], expression='1e999')):
            event = self.apply('A1', [item])
            self.assertEqual(event['notices'][0]['kind'], 'rejected_work')
        self.assertEqual(self.s.nodes, {})

    def test_division_failure_is_not_a_format_failure(self):
        event = self.apply('A1', [work('x', ['TASK'], expression='1 / 0')])
        self.assertEqual(event['status'], 'readable')
        self.assertEqual(self.s.results['W1']['status'], 'execution_error')

    def test_unresolved_work_does_not_override_best_effort_answer(self):
        self.apply('A1', [work('out', ['TASK'], expression='x', inputs=[dict(name='x', metadata=metadata('x'))])])
        delivered = self.s.deliver(json.dumps(dict(answer=7, result_id=None, scale='', reasoning='best effort')),
                                   self.s.packet('A1', 'final'))
        self.assertEqual(delivered['delivered']['answer'], 7)

    def test_formula_valid_does_not_certify_source_semantics(self):
        # Deliberately incorrect source interpretation: host cannot know the number is wrong.
        self.apply('A1', [work('total_available_credit', ['T1'], value=42)])
        self.assertEqual(self.s.results['W1']['truth_status'], 'model_declared_not_semantically_verified')

    def test_source_isolation_swaps_and_roundtrip_prompt_contract(self):
        first = member_packet(self.task, 'A1')
        other = member_packet(swapped(self.task), 'A2')
        self.assertEqual([s['content'] for s in first['sources']], [s['content'] for s in other['sources']])
        self.assertFalse(any(s['id'].startswith('P') for s in first['sources']))
        req = request(self.s, 'A1', 0)
        HandoffContracts.decode(response(), req['schema'])
        packet = json.loads(req['instructions'].split('\nPACKET=', 1)[1])
        self.assertEqual(packet, req['packet'])
        self.assertNotIn('answer', packet['task'])
        self.assertNotIn('derivation', packet['task'])


if __name__ == '__main__':
    unittest.main()
