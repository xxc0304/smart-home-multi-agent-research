"""Offline checks for scientific data boundaries and sequential message delivery."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from expert_mechanism_protocol import ACTORS, ProtocolError
from expert_discussion import DiscussionSession, SoloSession, VOTE_RULE
from expert_discussion_scoring import aggregate_votes, compare_session
from prepare_expert_training import dependency_groups, select_validation, sft_record


def task():
    return dict(id='HOST_ONLY_ID', question='When was X established?', paragraphs=[
        dict(idx=0, title='X', paragraph_text='X was established in 1900.'),
        dict(idx=1, title='Y', paragraph_text='Y was established in 1950.')])


def output(answer='1900', reason='Hand-authored fixture.'):
    return dict(answer=answer, support_idxs=[0], reasoning=reason)


def target():
    return dict(id=task()['id'], answer='1900', answer_aliases=['nineteen hundred'],
                answerable=True, paragraphs=[dict(idx=0, is_supporting=True), dict(idx=1, is_supporting=False)])


def make_session(disclosure='known_expert', fixture=True):
    return DiscussionSession(task(), expert_actor='M1', disclosure=disclosure,
                             seed=13, vote_rule=VOTE_RULE, fixture=fixture)


def data(request):
    return json.loads(request['payload']['user'].split('\n', 1)[1])


def finish(session):
    while (req := session.next_request()) is not None:
        text = (f"PUBLIC_SENTINEL_{len(session.records)}" if req['stage'] in ('discussion', 'reflection')
                else json.dumps(output(reason=f"PRIVATE_{req['actor']}_{req['stage']}")))
        session.submit(req['request_id'], raw_output=text)
    return session


class MessageFlowChecks(unittest.TestCase):
    def test_initials_independent_and_disclosure_after_initials(self):
        session = make_session()
        for actor in ACTORS:
            req = session.next_request()
            self.assertEqual(req['actor'], actor)
            self.assertEqual(data(req)['history'], [])
            self.assertNotIn('team_information', data(req))
            self.assertNotIn(task()['id'], req['payload']['user'])
            session.submit(req['request_id'], raw_output=json.dumps(output()))
        self.assertEqual(len(data(session.next_request())['history']), 4)
        self.assertIn('team_information', data(session.next_request()))

    def test_immediate_broadcast_and_full_four_round_schedule(self):
        session = finish(make_session())
        messages = [r for r in session.records if r['stage'] == 'discussion']
        self.assertEqual(len(messages), 16)
        self.assertEqual(len(session.records), 24)
        for i, req in enumerate(messages):
            history = data(req)['history']
            self.assertEqual(len(history), 4 + i)
            self.assertEqual([h['text'] for h in history[4:]], [r['raw_output'] for r in messages[:i]])
        for r in range(1, 5):
            self.assertEqual({m['actor'] for m in messages if m['round'] == r}, set(ACTORS))
        self.assertIsNone(session.next_request())

    def test_finals_never_receive_other_private_finals(self):
        session = finish(make_session())
        finals = [r for r in session.records if r['stage'] == 'final']
        self.assertEqual(len(finals), 4)
        for req in finals:
            history = data(req)['history']
            self.assertEqual(len(history), 20)
            self.assertTrue(all(h['phase'] != 'final' for h in history))
            for actor in ACTORS:
                self.assertNotIn(f'PRIVATE_{actor}_final', req['payload']['user'])

    def test_solo_has_only_own_initial_and_own_reflections(self):
        team = finish(make_session())
        solo = finish(SoloSession.from_team(team))
        self.assertEqual(len(solo.records), 5)
        self.assertEqual(solo.reused_initial, team.records[0])
        for i, req in enumerate(solo.records):
            history = data(req)['history']
            self.assertEqual(len(history), i + 1)
            self.assertTrue(all(h['sender'] == 'M1' for h in history))
            self.assertNotIn('team_information', data(req))
            for actor in ('M2', 'M3', 'M4'):
                self.assertNotIn(f'PRIVATE_{actor}_', req['payload']['user'])
        self.assertEqual(compare_session(team, target(), solo)['status'], 'COMPLETE_PAIRED')

    def test_explicit_disclosure_and_reproducible_order(self):
        a, b = finish(make_session('hidden')), finish(make_session('hidden'))
        self.assertEqual(a.trace(), b.trace())
        self.assertTrue(all('team_information' not in data(r) for r in a.records))
        with self.assertRaises(ProtocolError):
            DiscussionSession(task(), expert_actor='M1', disclosure=None, seed=1, vote_rule=VOTE_RULE)

    def test_failure_stops_chain_preserves_raw_and_no_summary(self):
        for status, raw, expected in [('timeout', None, 'TECHNICAL_FAILURE'),
                                      ('ok', '{invalid', 'PROTOCOL_INVALID')]:
            session = make_session()
            req = session.next_request()
            session.submit(req['request_id'], raw_output=raw, status=status)
            self.assertTrue(session.failed)
            self.assertIsNone(session.next_request())
            self.assertEqual(session.records[0]['status'], expected)
            self.assertEqual(session.records[0]['raw_output'], raw)
            self.assertIsNone(compare_session(session, target())['comparisons'])

    def test_request_ids_and_snapshots_are_not_mutable_from_caller(self):
        session = make_session()
        req = session.next_request()
        req['payload']['user'] = 'mutated'
        self.assertNotEqual(session.next_request()['payload']['user'], 'mutated')
        with self.assertRaises(ProtocolError):
            session.submit('wrong-id', raw_output=json.dumps(output()))
        session.submit(req['request_id'], raw_output=json.dumps(output()))
        trace = session.trace()
        trace['records'].clear()
        self.assertEqual(len(session.records), 1)

    def test_real_response_requires_matching_raw_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'raw.txt'
            raw = json.dumps(output())
            path.write_text(raw, encoding='utf-8')
            session = make_session(fixture=False)
            req = session.next_request()
            self.assertEqual(session.submit(req['request_id'], raw_output=raw,
                                           raw_response_path=path)['status'], 'VALID')
            req = session.next_request()
            self.assertEqual(session.submit(req['request_id'], raw_output=raw + ' ',
                                           raw_response_path=path)['status'], 'PROTOCOL_INVALID')

    def test_fixture_cannot_be_primary_and_incomplete_solo_blocks_pair(self):
        team = finish(make_session())
        report = compare_session(team, target())
        self.assertFalse(report['primary_comparison_enabled'])
        self.assertEqual(report['comparisons']['expert_initial']['answer_em'], 1)
        report = compare_session(team, target(), SoloSession.from_team(team))
        self.assertIsNone(report['comparisons'])
        self.assertEqual(report['status'], 'INCOMPLETE_SOLO_NO_PRIMARY_SUMMARY')

    def test_omitting_solo_cannot_enable_primary_even_with_raw_file_declarations(self):
        # Hand-authored temporary files exercise qualification flags only.
        # They are NOT evidence of an actual model, and are never exported as results.
        with tempfile.TemporaryDirectory() as folder:
            team = make_session(fixture=False)
            while (req := team.next_request()) is not None:
                raw = ('Temporary test text.' if req['stage'] == 'discussion' else json.dumps(output()))
                path = Path(folder) / f'{len(team.records)}.txt'
                path.write_text(raw, encoding='utf-8')
                team.submit(req['request_id'], raw_output=raw, raw_response_path=path)
            report = compare_session(team, target())
            self.assertEqual(report['status'], 'COMPLETE_TEAM_DESCRIPTIVE')
            self.assertFalse(report['primary_comparison_enabled'])
            self.assertIsNotNone(report['comparisons'])


class VoteChecks(unittest.TestCase):
    def test_normalization_plurality_and_abstentions(self):
        outputs = dict(zip(ACTORS, [output('The X!'), output('x'), output('Y'), output(None)]))
        vote = aggregate_votes(outputs, seed=1)
        self.assertEqual(vote['vote_counts'], {'x': 2, 'y': 1})
        self.assertEqual(vote['winning_actors'], ['M1', 'M2'])
        self.assertFalse(vote['tie'])
        self.assertEqual(vote['abstained'], ['M4'])

    def test_gold_aliases_not_used_for_voting(self):
        outputs = dict(zip(ACTORS, [output('1900'), output('nineteen hundred'), output('1950'), output('1950')]))
        vote = aggregate_votes(outputs, seed=1)
        self.assertEqual(vote['answer'], '1950')
        self.assertEqual(len(vote['vote_counts']), 3)

    def test_ties_and_all_abstentions(self):
        outputs = dict(zip(ACTORS, [output('1900'), output('1900'), output('1950'), output('1950')]))
        self.assertEqual(aggregate_votes(outputs, seed=2), aggregate_votes(outputs, seed=2))
        selected = CounterVotes(outputs)
        self.assertEqual(selected, {'1900', '1950'})
        vote = aggregate_votes({a: output(None) for a in ACTORS}, seed=0)
        self.assertIsNone(vote['answer'])
        self.assertEqual(vote['winning_actors'], [])

    def test_vote_expected_scores_keep_random_representative_separate(self):
        team = finish(make_session())
        team.finals = dict(zip(ACTORS, [output('1900'), output('1900'), output('1950'), output('1950')]))
        report = compare_session(team, target())
        self.assertEqual(report['final_vote_expected']['answer_em'], .5)
        self.assertIn(report['comparisons']['team_final_vote']['answer_em'], (0, 1))


def CounterVotes(outputs):
    return {aggregate_votes(outputs, seed=i)['answer'] for i in range(30)}


def index_row(i, *, component=None, support=None, context=None):
    return dict(id=str(i), question_hash=f'q{i}', component_ids=[component or f'c{i}'],
        standalone_component_question_hashes=[f'u{i}'], support_hashes=[support or f'p{i}'],
        context_hashes=context or [support or f'p{i}'])


class TrainingChecks(unittest.TestCase):
    def test_transitive_subproblem_and_support_in_distractor_grouping(self):
        rows = [index_row(1, component='same'), index_row(2, component='same', support='fact'),
                index_row(3, context=['fact', 'p3']), index_row(4)]
        self.assertEqual(dependency_groups(rows), [['1', '2', '3'], ['4']])

    def test_grouped_validation_preserves_groups_and_is_repeatable(self):
        groups = [['a', 'b', 'c'], ['d', 'e'], ['f'], ['g']]
        selected = select_validation(groups, target=3, seed=2)
        self.assertEqual(len(selected), 3)
        self.assertEqual(selected, select_validation(groups, target=3, seed=2))
        for group in groups:
            self.assertIn(len(set(group) & selected), (0, len(group)))
        with self.assertRaises(ProtocolError):
            select_validation([['a', 'b']], target=1)

    def test_sft_supervision_only_in_assistant_and_no_synthetic_reasoning(self):
        gold = target()
        gold['answer'] = 'GOLD_SENTINEL'
        gold['question_decomposition'] = [{'question': 'SECRET_DECOMPOSITION'}]
        record = sft_record(task(), gold)
        self.assertEqual(record['id'], task()['id'])
        inp = record['messages'][:2]
        self.assertNotIn('GOLD_SENTINEL', json.dumps(inp))
        self.assertNotIn('SECRET_DECOMPOSITION', json.dumps(record))
        self.assertNotIn(task()['id'], json.dumps(inp))
        self.assertEqual(set(json.loads(record['messages'][2]['content'])), {'answer', 'support_idxs'})
        gold['id'] = 'wrong'
        with self.assertRaises(ProtocolError):
            sft_record(task(), gold)

    def test_real_export_complete_and_group_isolated(self):
        folder = ROOT / 'data/expert-training-20261030-v1'
        report = json.loads((folder / 'SPLIT_REPORT.json').read_text(encoding='utf-8'))
        assignments = [json.loads(s) for s in (folder / 'assignments.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(assignments), 2000)
        self.assertFalse(any(report['overlap_checks'].values()))
        roles = {}
        for row in assignments:
            roles.setdefault(row['group'], set()).add(row['role'])
        self.assertTrue(all(len(v) == 1 for v in roles.values()))
        for role, n in [('train', report['n_train']), ('validation', report['n_validation'])]:
            inputs = [json.loads(s) for s in (folder / f'{role}.inputs.jsonl').read_text(encoding='utf-8').splitlines()]
            targets = [json.loads(s) for s in (folder / f'{role}.targets.jsonl').read_text(encoding='utf-8').splitlines()]
            messages = [json.loads(s) for s in (folder / f'{role}.messages.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual(len(inputs), n)
            self.assertEqual({r['id'] for r in inputs}, {r['id'] for r in targets})
            self.assertEqual(len(messages), n)
            for inp, gold, msg in zip(inputs, targets, messages):
                self.assertEqual(msg, sft_record(inp, gold))


if __name__ == '__main__':
    unittest.main()
