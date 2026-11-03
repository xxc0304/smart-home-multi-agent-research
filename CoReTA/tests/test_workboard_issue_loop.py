"""Network-blocked engineering fixtures, not evidence of semantic improvement."""
import copy
import json
import unittest

import test_workboard as baseline
from coreta.handoff.gateway import Journal
from coreta.workboard.gateway import Gateway
from coreta.workboard.issue_loop import (IssueContracts, IssuePrompts, IssueRunner,
                                        VARIANT, CHECK_STAGES, CHOICE_STAGES, settings)


class IssueLoopTests(unittest.TestCase):
    setUp = baseline.WorkboardTests.setUp
    work = baseline.WorkboardTests.work
    change = baseline.WorkboardTests.change

    def respond(self, packet):
        stage = packet['STAGE']
        if stage == 'OBSERVE':
            value = baseline.WorkboardTests.offer(self, packet)
            value['offer']['claims'] = [dict(statement='SCRIPTED claim', premises='SCRIPTED premise', source_refs=['T'])]
            return value
        if stage == 'GROUND':
            return dict(assessments={c['id']: dict(status='unresolved', reason='SCRIPTED limits', evidence_refs=['T'])
                                     for c in packet['CLAIMS']}, limits='SCRIPTED not truth')
        value = baseline.WorkboardTests.respond(self, packet)
        if stage in CHECK_STAGES:
            first = stage == 'CHECK_USE' and packet['BUDGET']['cycle'] == 1
            value.update(finding='issue' if first else 'no_issue_found',
                issues=[dict(concern='SCRIPTED missing constraint', location=packet['AFTER']['id'],
                    kind='reasoning', evidence_refs=['T'], consequence='SCRIPTED invalid comparison')] if first else [],
                rechecks={r['issue_id']: dict(status='persists', reason='SCRIPTED still open', evidence_refs=['T'])
                          for r in packet.get('ISSUES_TO_RECHECK', [])})
            if value['rechecks']:
                value['finding'] = 'issue'
        if stage in CHOICE_STAGES:
            value['issue_dispositions'] = {ref: dict(disposition='accept', reason='SCRIPTED valid concern')
                                          for ref in packet['REQUIRED_ISSUE_IDS']}
        return value

    def engine(self, handler=None):
        packets = copy.deepcopy(self.packets)
        packets.agents = packets.agents[:3]
        for member in packets.members.values():
            member['SELF']['team'] = packets.agents
        journal = Journal(self.folder)
        script = baseline.Script(journal, handler or self.respond)
        config = settings(3, self.legacy)
        config['limits']['max_output_tokens_total'] = 100000
        gateway = Gateway(self.config, config, IssueContracts(self.adapter), IssuePrompts(), journal,
                          transport=script, token_counter=lambda text: len(text)//3)
        return IssueRunner(packets, gateway, journal, self.adapter), script

    def test_full_loop_keeps_call_count_and_open_issue(self):
        runner, script = self.engine()
        result = runner.run()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['http_attempts'], 19)
        self.assertEqual(result['method_variant'], VARIANT)
        self.assertTrue(all(p['METHOD_VARIANT'] == VARIANT for p in script.calls))
        self.assertEqual(result['issue_summary']['selected_version_open_or_uncertain'], 1)
        row = runner.issue_ledger[0]
        self.assertEqual(row['issue_id'], 'R1.I1')
        self.assertEqual(len(row['dispositions']), 3)
        self.assertEqual(len(row['rechecks']), 3)
        later = [p for p in script.calls if p['STAGE'] == 'TRY' and p['BUDGET']['cycle'] == 2][0]
        self.assertEqual(later['ISSUE_LEDGER'][0]['issue_id'], row['issue_id'])
        persisted = json.loads((self.folder/'issue_ledger.json').read_text(encoding='utf-8'))
        self.assertEqual(persisted['issues'], runner.issue_ledger)
        self.assertEqual(result['truth_status'], 'not_certified')

    def test_checker_author_and_application_actor_are_distinct_for_reuse(self):
        def handler(p):
            if p['STAGE'] == 'FINALIZE':
                return self.change(candidate=p['CANDIDATES'][0]['id'], sources=[p['CANDIDATES'][0]['id']])
            return self.respond(p)
        runner, script = self.engine(handler)
        self.assertEqual(runner.run()['status'], 'completed')
        for p in script.calls:
            if p['STAGE'] not in CHECK_STAGES:
                continue
            checker = p['SELF']['agent_id']
            self.assertEqual(p['CHECKER_ACCESS']['agent_id'], checker)
            self.assertEqual(p['SELF_MATERIALS'], runner.packets.member(checker)['SELF_MATERIALS'])
            legal = {r['ref'] for r in p['REFERENCE_INDEX']}
            for ref, access in p['WORK_AUTHOR_ACCESS'].items():
                author = runner.board.get(ref)['author']
                self.assertEqual(access['author'], author)
                expected = {'T', *(m['ref'] for m in runner.packets.member(author)['SELF_MATERIALS'])}
                self.assertEqual(set(access['available_original_refs']), expected)
                self.assertEqual(legal & expected, set(p['SOURCE_ACCESS']['direct_original_refs']) & expected)
            self.assertEqual(p['APPLICATION_ACTOR_ACCESS']['agent_id'], runner.editor)
        final = next(p for p in script.calls if p['STAGE'] == 'FINAL_CHECK_USE')
        self.assertNotEqual(final['WORK_AUTHOR_ACCESS'][final['AFTER']['id']]['author'], runner.editor)

    def test_missing_disposition_stops_without_retry(self):
        def handler(p):
            value = self.respond(p)
            if p['STAGE'] == 'CHOOSE':
                value['issue_dispositions'] = {}
            return value
        runner, script = self.engine(handler)
        result = runner.run()
        self.assertEqual(result['error']['code'], 'SCHEMA_ERROR')
        self.assertEqual(script.calls[-1]['STAGE'], 'CHOOSE')
        self.assertFalse(result['closure_complete'])

    def test_missing_recheck_stops(self):
        def handler(p):
            value = self.respond(p)
            if p['STAGE'] == 'CHECK_USE' and p['BUDGET']['cycle'] == 2:
                value['rechecks'] = {}
            return value
        runner, _ = self.engine(handler)
        self.assertEqual(runner.run()['error']['code'], 'SCHEMA_ERROR')

    def test_empty_issue_finding_is_rejected(self):
        def handler(p):
            value = self.respond(p)
            if p['STAGE'] == 'CHECK_USE':
                value['issues'] = []
            return value
        runner, _ = self.engine(handler)
        self.assertEqual(runner.run()['error']['code'], 'INVALID_ACTION')

    def test_editor_rejection_does_not_delete_issue(self):
        def handler(p):
            value = self.respond(p)
            if p['STAGE'] in CHOICE_STAGES:
                for row in value['issue_dispositions'].values():
                    row['disposition'] = 'reject'
            return value
        runner, script = self.engine(handler)
        result = runner.run()
        final = next(p for p in script.calls if p['STAGE'] == 'FINAL_CHECK_USE')
        self.assertEqual(final['ISSUES_TO_RECHECK'][0]['issue_id'], 'R1.I1')
        self.assertEqual(result['issue_summary']['selected_version_open_or_uncertain'], 1)

    def test_final_review_conflict_is_retained(self):
        def handler(p):
            value = self.respond(p)
            if p['STAGE'] == 'FINAL_CHECK_USE':
                for row in value['rechecks'].values():
                    row['status'] = 'resolved'
                value['finding'] = 'no_issue_found'
            return value
        runner, _ = self.engine(handler)
        result = runner.run()
        self.assertEqual(result['status'], 'completed')
        row = runner.issue_ledger[0]
        self.assertEqual(runner.assessment(row, result['selected_work_id']), 'conflicting_reviews')
        self.assertEqual(result['issue_summary']['selected_version_open_or_uncertain'], 1)

    def test_resolution_is_version_bound_and_requires_no_conflicting_review(self):
        row = dict(rechecks=[dict(work_id='W5', status='resolved')])
        self.assertEqual(IssueRunner.assessment(row, 'W5'), 'model_reported_resolved')
        self.assertEqual(IssueRunner.assessment(row, 'W6'), 'open_or_uncertain')
        row['rechecks'].append(dict(work_id='W5', status='unable'))
        self.assertEqual(IssueRunner.assessment(row, 'W5'), 'open_or_uncertain')

    def test_no_issue_summary_cannot_hide_persisting_recheck(self):
        def handler(p):
            value = self.respond(p)
            if p['STAGE'] == 'CHECK_USE' and p['BUDGET']['cycle'] == 2:
                value['finding'] = 'no_issue_found'
            return value
        runner, _ = self.engine(handler)
        self.assertEqual(runner.run()['error']['code'], 'INVALID_ACTION')

    def test_clean_workflow_supports_empty_objects(self):
        def handler(p):
            value = self.respond(p)
            if p['STAGE'] in CHECK_STAGES:
                value.update(finding='no_issue_found', issues=[])
            return value
        runner, _ = self.engine(handler)
        result = runner.run()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['issue_summary']['raised'], 0)


if __name__ == '__main__':
    unittest.main()
