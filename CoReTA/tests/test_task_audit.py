"""Offline state-machine fixtures. Scripted success is not model capability evidence."""
import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from coreta.closure import ClosureContracts, digest
from coreta.closure_format import FormatClosureClient, FormatClosureRunner
from coreta.schemas import ProtocolError
from coreta.task_audit import AuditClosureRunner, AuditContracts, effective_outcome, exact_rational
from test_revision import TASK, candidate, decision


ROOT = Path(__file__).resolve().parents[1]


def facts(task=TASK):
    return {'facts': [{'fact_id': 'f1',
             'source_locator': {'kind': 'prompt_span', 'start': 0, 'end': len(task['prompt']), 'pointer': ''},
             'quoted_text': task['prompt'], 'normalized_fact': 'Public task objective',
             'kind': 'objective', 'coverage_status': 'unknown'}], 'coverage_status': 'unknown'}


def audit(version=0, existing=None, observed='0', relation='exact_equality'):
    return {'existing_issue_id': existing, 'target_refs': [f'v{version}:s1'], 'task_fact_ids': ['f1'],
            'claim_text': 'Fixture candidate satisfies the public constraint',
            'attempted_falsification': 'Manually substitute a public input',
            'cases': [{'case_id': 'c1', 'fact_id': 'f1', 'input': '(1,-1)',
                       'comparison_kind': relation, 'quantity_key': 'generator value at public input',
                       'expected_value': '0', 'observed_value': observed, 'model_outcome': 'match'}],
            'coverage': 'exhaustive_for_listed_facts', 'scope': 'Only the listed public fact',
            'correctness_critical': True, 'model_verdict': 'not_refuted'}


class AuditScript:
    """Produces controlled protocol outputs, deliberately including false verdicts."""
    def __init__(self, mismatch=False):
        self.mismatch = mismatch
        self.seen = []

    def __call__(self, payload, timeout):
        prompt = payload['instructions']
        context = json.JSONDecoder().raw_decode(prompt[prompt.index('\n{"ACTOR"')+1:])[0]
        self.seen.append(copy.deepcopy(context))
        material = context['MATERIAL']
        props = payload['text']['format']['schema']['properties']
        if 'facts' in props:
            value = facts(material['task'])
        elif 'steps' in props:
            value = candidate()
        elif 'closure_proposals' in props:
            value = {'candidate': candidate(), 'closure_proposals': [], 'issues': [],
                     'application': 'Fixture rebuttal for scripted objection', 'next': decision()}
            for issue in material['issues']:
                if issue['status'] in {'addressed', 'dismissed'}:
                    continue
                value['closure_proposals'].append({
                    'issue_id': issue['issue_id'], 'response_to_objection_ids': [o['objection_id'] for o in issue['objections']],
                    'closure_path': 'rebuttal', 'disposition': 'dismissed',
                    'evidence_record_ids': [r['record_id'] for r in issue.get('evidence_records', [])],
                    'reason': 'The scripted objection is invalid', 'evidence_refs': [context['REFERENCE_INDEX'][0]],
                    'changed_step_ids': []})
        elif 'candidate_hash' in props:
            existing = material['issues'][0]['issue_id'] if material['issues'] else None
            value = {'candidate_version': material['candidate_version'], 'candidate_hash': material['candidate_hash'],
                     'checks': [{'target_refs': [f'v{material["candidate_version"]}:s1'], 'method': 'manual',
                                 'observation': 'Fixture only', 'conclusion': 'supported', 'scope': 'public input'}],
                     'audit_records': [audit(material['candidate_version'], existing, '-3' if self.mismatch else '0')],
                     'issues': [], 'closure_reviews': []}
            for key, proposal in material['pending_closures'].items():
                value['closure_reviews'].append({
                    'issue_id': key, 'proposal_event_id': proposal['proposal_event_id'],
                    'response_to_objection_ids': proposal['response_to_objection_ids'],
                    'evidence_record_ids': proposal['evidence_record_ids'], 'verdict': 'resolved',
                    'method': 'Manual recheck of original case', 'observation': 'Fixture verdict',
                    'evidence_refs': [context['REFERENCE_INDEX'][0]]})
        elif 'candidate' in props:
            value = {'candidate': candidate(), 'issues': []}
        else:
            value = {'status': 'provided', 'body': 'Independent fixture construction', 'basis_refs': [],
                     'attempted_issue_ids': [i['issue_id'] for i in material['issues']], 'issues': []}
        return {'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': json.dumps(value)}]}], 'usage': {'input_tokens': 1, 'output_tokens': 1}}


class TaskAuditChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.contracts = AuditContracts(ROOT / 'design/v0.3/coreta.schema.json')
        self.config = json.loads((ROOT / 'config/deepseek_flash_closure.json').read_text(encoding='utf-8'))
        self.config['generation']['max_input_tokens'] = 1000000
        self.prompts = json.loads((ROOT / 'design/task_audit_prompts.json').read_text(encoding='utf-8'))

    def runner(self, script=None, directory=None, bank=None):
        path = directory or self.path
        path.mkdir(parents=True, exist_ok=True)
        runner = AuditClosureRunner(TASK, path, 'audit-fixture', self.contracts, None,
                                    copy.deepcopy(self.config), self.prompts, draft_bank=bank)
        runner.client = FormatClosureClient(runner.config, runner.log, transport=script or AuditScript())
        return runner

    def prepared(self):
        runner = self.runner()
        runner.version = 0
        runner.current = {'version': 0, 'source_event_id': 'audit-fixture:source', 'candidate': candidate()}
        runner.task_facts = runner.emit('task_facts', 'A2', facts())
        runner._last_builder = 'A1'
        return runner

    def inspection(self, runner, observed='0', existing=None):
        value = {'candidate_version': runner.version, 'candidate_hash': digest(runner.current['candidate']),
                 'checks': [{'target_refs': [f'v{runner.version}:s1'], 'method': 'manual',
                             'observation': 'Fixture trace', 'conclusion': 'supported', 'scope': 'fixture'}],
                 'audit_records': [audit(runner.version, existing, observed)], 'issues': [], 'closure_reviews': []}
        for key, proposal in runner.pending.items():
            value['closure_reviews'].append({
                'issue_id': key, 'proposal_event_id': proposal['proposal_event_id'],
                'response_to_objection_ids': proposal['response_to_objection_ids'],
                'evidence_record_ids': proposal['evidence_record_ids'], 'verdict': 'resolved',
                'method': 'Recompute original public input', 'observation': 'Fixture recheck',
                'evidence_refs': [runner.current['source_event_id']]})
        return value

    def open_finding(self, runner):
        runner.settle(self.inspection(runner, '-3'), 'A2')
        return next(i for i in runner.issues.values() if i.get('evidence_records'))

    def update(self, runner, issue, path='rebuttal'):
        revised = candidate()
        if path == 'repair':
            revised['artifact'] = r'\boxed{2}\quad\text{with corrected derivation}'
            revised['steps'][0]['text'] = 'Repaired derivation for the fixture'
        return {'candidate': revised, 'issues': [], 'application': 'Fixture handling', 'next': decision(),
                'closure_proposals': [{
                    'issue_id': issue['issue_id'], 'response_to_objection_ids': [o['objection_id'] for o in issue['objections']],
                    'closure_path': path, 'disposition': 'addressed' if path == 'repair' else 'dismissed',
                    'reason': 'Explicit handling of original cases',
                    'evidence_refs': [issue['source_event_id']], 'changed_step_ids': [],
                    'evidence_record_ids': [r['record_id'] for r in issue.get('evidence_records', [])]}]}

    def test_schema_and_prompts_preserve_draft_compatibility(self):
        Draft202012Validator.check_schema(self.contracts.document)
        old = json.loads((ROOT / 'design/closure_prompts.json').read_text(encoding='utf-8'))
        self.assertEqual(self.prompts['system'], old['system'])
        self.assertEqual(self.prompts['draft'], old['draft'])
        legacy = ClosureContracts(ROOT / 'design/v0.3/coreta.schema.json')
        self.assertEqual(self.contracts.schema('Candidate'), legacy.schema('Candidate'))

    def test_facts_quote_unicode_and_public_code_field(self):
        runner = self.prepared()
        runner.task = {**TASK, 'prompt': '甲😀乙', 'entry_point': 'public_function'}
        value = facts(runner.task)
        fact = value['facts'][0]
        fact['source_locator'].update(start=1, end=2)
        fact['quoted_text'] = '😀'
        runner.validate_task_facts(value)
        fact['source_locator'] = {'kind': 'json_pointer', 'start': 0, 'end': 0, 'pointer': '/entry_point'}
        fact['quoted_text'] = 'public_function'
        runner.validate_task_facts(value)
        fact['quoted_text'] = 'invented_function'
        with self.assertRaises(ProtocolError):
            runner.validate_task_facts(value)

    def test_facts_reject_duplicate_ids_empty_and_bad_spans(self):
        runner = self.prepared()
        for transform in (lambda v: v['facts'].append(copy.deepcopy(v['facts'][0])),
                          lambda v: v['facts'].clear(),
                          lambda v: v['facts'][0]['source_locator'].update(end=9999)):
            value = facts()
            transform(value)
            with self.assertRaises(ProtocolError):
                runner.validate_task_facts(value)

    def test_exact_gate_only_declared_canonical_equality(self):
        self.assertEqual(effective_outcome(audit(observed='-3')), 'finding_open')
        self.assertEqual(effective_outcome(audit(observed='-3', relation='model_judged')), 'not_refuted_within_recorded_scope')
        self.assertEqual(effective_outcome(audit(observed='about -3')), 'not_refuted_within_recorded_scope')
        for invalid in ('1/0', '0.1', '2/4', '-0', '__import__("os")', '3 m', '1e3'):
            self.assertIsNone(exact_rational(invalid))
        self.assertEqual(str(exact_rational('-5/19')), '-5/19')

    def test_unable_critical_opens_but_not_refuted_does_not_close(self):
        runner = self.prepared()
        value = self.inspection(runner)
        value['audit_records'][0]['cases'][0]['model_outcome'] = 'unable'
        runner.settle(value, 'A2')
        self.assertTrue(runner.blockers())
        issue = next(iter(runner.issues.values()))
        runner.settle(self.inspection(runner, existing=issue['issue_id']), 'A2')
        self.assertEqual(issue['status'], 'open')

    def test_conflicting_resolved_keeps_original_and_uses_one_request(self):
        runner = self.prepared()
        issue = self.open_finding(runner)
        original = copy.deepcopy(issue['evidence_records'][0])
        runner.commit_proposals(self.update(runner, issue))
        value = self.inspection(runner, '-3', issue['issue_id'])
        def transport(payload, timeout):
            return {'status': 'completed', 'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': json.dumps(value)}]}]}
        runner.client = FormatClosureClient(runner.config, runner.log, transport=transport)
        result = runner.call('inspect', 'A2', 'ClosureInspection',
                             {**runner.view(), 'pending_closures': runner.pending}, runner.validate_inspection)
        runner.settle(result, 'A2')
        self.assertEqual(runner.client.attempts, 1)
        self.assertEqual(runner.repairs, 0)
        self.assertEqual(runner.issues[issue['issue_id']]['status'], 'open')
        self.assertEqual(runner.issues[issue['issue_id']]['evidence_records'][0], original)
        self.assertEqual(len(runner.audit_ledger), 2)
        self.assertEqual(result['closure_reviews'][0]['verdict'], 'resolved')
        self.assertEqual(issue['status'], 'open')
        event_rows = [json.loads(x) for x in (runner.directory / 'events.jsonl').read_text().splitlines()]
        self.assertEqual(sum(e['stage'] == 'inspect' for e in event_rows), 2)

    def test_valid_repair_and_rebuttal_are_separate_close_paths(self):
        for path, expected in (('repair', 'addressed'), ('rebuttal', 'dismissed')):
            with self.subTest(path=path):
                runner = self.prepared()
                issue = self.open_finding(runner)
                before = digest(runner.current['candidate'])
                runner.commit_proposals(self.update(runner, issue, path))
                self.assertEqual(issue['status'], 'open')  # commit uses a copy of the registry
                self.assertEqual(runner.issues[issue['issue_id']]['status'], 'pending_check')
                self.assertEqual(before == digest(runner.current['candidate']), path == 'rebuttal')
                runner.settle(self.inspection(runner, existing=issue['issue_id']), 'A2')
                self.assertEqual(runner.issues[issue['issue_id']]['status'], expected)

    def test_repair_metadata_only_or_missing_original_evidence_rejected(self):
        runner = self.prepared()
        issue = self.open_finding(runner)
        update = self.update(runner, issue, 'repair')
        update['candidate'] = candidate()
        update['candidate']['summary'] = 'Changed metadata only'
        with self.assertRaises(ProtocolError):
            runner.commit_proposals(update)
        update = self.update(runner, issue)
        update['closure_proposals'][0]['evidence_record_ids'] = []
        with self.assertRaises(ProtocolError):
            runner.commit_proposals(update)

    def test_changed_candidate_reopens_closed_issue_without_erasing_evidence(self):
        runner = self.prepared()
        issue = self.open_finding(runner)
        originals = copy.deepcopy(issue['evidence_records'])
        runner.commit_proposals(self.update(runner, issue))
        runner.settle(self.inspection(runner, existing=issue['issue_id']), 'A2')
        self.assertEqual(runner.issues[issue['issue_id']]['status'], 'dismissed')
        value = self.update(runner, runner.issues[issue['issue_id']], 'repair')
        value['closure_proposals'] = []
        runner.commit_proposals(value)
        self.assertEqual(runner.issues[issue['issue_id']]['status'], 'needs_revalidation')
        self.assertEqual(runner.issues[issue['issue_id']]['evidence_records'], originals)

    def test_bad_role_hash_refs_or_missing_recheck_retain_response_without_retry(self):
        for problem in ('role', 'hash', 'refs', 'fact', 'coverage', 'recheck'):
            with self.subTest(problem=problem):
                runner = self.prepared()
                issue = self.open_finding(runner)
                runner.commit_proposals(self.update(runner, issue))
                value = self.inspection(runner, existing=issue['issue_id'])
                actor = 'A1' if problem == 'role' else 'A2'
                if problem == 'hash': value['candidate_hash'] = 'stale'
                if problem == 'refs': value['audit_records'][0]['target_refs'] = ['invisible:source']
                if problem == 'fact': value['audit_records'][0]['task_fact_ids'] = ['missing']
                if problem == 'coverage': value['audit_records'][0]['task_fact_ids'].append('f2')
                if problem == 'recheck': value['audit_records'][0]['cases'][0]['input'] = 'a different input'
                runner.settle(value, actor)
                self.assertEqual(runner.issues[issue['issue_id']]['status'], 'open')
                self.assertIsNone(runner.last_reviewed)
                self.assertEqual(len(runner.audit_ledger), 2)
                self.assertTrue(runner.audit_ledger[-1]['validation_errors'])

    def test_erroneous_fact_reference_can_be_rebutted_without_repeating_it(self):
        runner = self.prepared()
        value = self.inspection(runner, '-3')
        value['audit_records'][0]['task_fact_ids'] = ['invalid-fact']
        value['audit_records'][0]['cases'][0]['fact_id'] = 'invalid-fact'
        runner.settle(value, 'A2')
        issue = next(i for i in runner.issues.values() if i.get('evidence_records'))
        original = copy.deepcopy(issue['evidence_records'])
        runner.commit_proposals(self.update(runner, issue))
        recheck = self.inspection(runner, existing=issue['issue_id'])
        runner.settle(recheck, 'A2')
        self.assertEqual(runner.issues[issue['issue_id']]['status'], 'dismissed')
        self.assertEqual(runner.issues[issue['issue_id']]['evidence_records'], original)
        self.assertFalse(runner.audit_ledger[-1]['validation_errors'])

    def test_structural_retry_retains_malformed_response(self):
        runner = self.prepared()
        good = self.inspection(runner)
        outputs = ['{"checks":', json.dumps(good)]
        def transport(payload, timeout):
            return {'status': 'completed', 'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': outputs.pop(0)}]}]}
        runner.client = FormatClosureClient(runner.config, runner.log, transport=transport)
        value = runner.call('inspect', 'A2', 'ClosureInspection', {**runner.view(), 'pending_closures': {}})
        runner.settle(value, 'A2')
        self.assertEqual(runner.client.attempts, 2)
        self.assertEqual(runner.repairs, 1)
        self.assertEqual(len(runner.audit_ledger), 1)
        self.assertIn('{\\"checks\\":', (runner.directory / 'responses.jsonl').read_text())

    def test_short_path_visibility_and_no_final(self):
        script = AuditScript()
        runner = self.runner(script)
        result = runner.run()
        self.assertEqual(result['normal_calls'], 8)
        self.assertEqual(result['stop_reason'], 'complete')
        self.assertEqual([e['stage'] for e in runner.events],
                         ['draft'] * 3 + ['task_facts', 'synthesize', 'build', 'apply', 'inspect'])
        self.assertEqual(set(script.seen[3]['MATERIAL']), {'task'})
        self.assertNotIn('drafts', script.seen[-1]['MATERIAL'])
        self.assertEqual(result['artifact'], runner.current['candidate']['artifact'])
        self.assertFalse(result['finalizer_changed'])

    def test_worst_path_14_and_final_finding_preserved(self):
        runner = self.runner(AuditScript(mismatch=True))
        result = runner.run()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['normal_calls'], 14)
        self.assertEqual(result['http_attempts'], 14)
        self.assertEqual(result['stop_reason'], 'budget_exhausted')
        self.assertEqual(result['audit_record_count'], 3)
        self.assertEqual(runner.issues['i0001']['status'], 'open')
        self.assertEqual(len(runner.issues['i0001']['evidence_records']), 3)
        self.assertEqual(runner.events[-1]['stage'], 'inspect')
        with self.assertRaises(ProtocolError):
            runner.call('inspect', 'A2', 'ClosureInspection', runner.view())

    def test_shared_legacy_draft_bank_reuses_exact_initials(self):
        bank = self.path / 'bank'
        old_dir = self.path / 'old'
        old_dir.mkdir()
        old_prompts = json.loads((ROOT / 'design/closure_prompts.json').read_text(encoding='utf-8'))
        old = FormatClosureRunner(TASK, old_dir, 'old-fixture',
                                  ClosureContracts(ROOT / 'design/v0.3/coreta.schema.json'), None,
                                  copy.deepcopy(self.config), old_prompts, draft_bank=bank)
        old.client = FormatClosureClient(old.config, old.log, transport=AuditScript())
        self.assertEqual(old.run_drafts()['draft_count'], 3)
        runner = self.runner(directory=self.path / 'new', bank=bank)
        result = runner.run()
        self.assertEqual(result['normal_calls'], 8)
        self.assertEqual(result['http_attempts'], 5)
        self.assertEqual([e['payload'] for e in old.drafts], [e['payload'] for e in runner.drafts])

    def test_real_140_text_is_only_source_for_constructed_fixture(self):
        folder = ROOT / 'runs/math140-format-20261019/4276ec64c178dafa'
        public = json.loads((folder / 'public_task.json').read_text(encoding='utf-8'))
        events = [json.loads(x) for x in (folder / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
        inspection = next(e for e in events if e['stage'] == 'inspect')
        self.assertIn('-3', json.dumps(inspection['payload']))
        runner = self.prepared()
        runner.task = public
        matches = list(re.finditer(r'p\(\s*-?\s*\d+\s*,\s*-?\s*\d+\s*\)', public['prompt']))
        self.assertEqual(len(matches), 8)
        extracted = {'facts': [], 'coverage_status': 'partial'}
        for number, match in enumerate(matches, 1):
            extracted['facts'].append({
                'fact_id': f'f{number}', 'source_locator': {'kind': 'prompt_span', 'start': match.start(),
                                                         'end': match.end(), 'pointer': ''},
                'quoted_text': match.group(), 'normalized_fact': 'Listed vanishing constraint: ' + match.group(),
                'kind': 'constraint', 'coverage_status': 'partial'})
        runner.validate_task_facts(extracted)
        runner.task_facts = runner.emit('task_facts', 'A2', extracted)
        applied = next(e for e in reversed(events) if e['stage'] == 'apply')
        runner.version = inspection['payload']['candidate_version']
        runner.current = {'version': runner.version, 'source_event_id': applied['event_id'],
                          'candidate': copy.deepcopy(applied['payload']['candidate'])}
        value = self.inspection(runner, '-3')
        record = value['audit_records'][0]
        record['task_fact_ids'] = ['f7']
        record['cases'][0]['fact_id'] = 'f7'
        record['cases'][0]['quantity_key'] = 'g1(1,-1)'
        record['claim_text'] = 'Applied generator g1 vanishes at the original listed point (1,-1)'
        runner.settle(value, 'A2')
        self.assertEqual(runner.audit_ledger[-1]['effective_outcome'], 'finding_open')
        self.assertFalse(runner.audit_ledger[-1]['validation_errors'])


if __name__ == '__main__':
    unittest.main()
