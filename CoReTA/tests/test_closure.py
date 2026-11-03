"""v0.5 engineering regressions; scripted outputs are not capability evidence."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from coreta.closure import ClosureClient, ClosureContracts, ClosureRunner, digest
from coreta.schemas import ProtocolError
from test_revision import TASK, candidate, decision

ROOT = Path(__file__).resolve().parents[1]


def proposal(key='i0001'):
    return {'description': 'Wrong algorithm, independent of trace typo', 'blocking': True,
        'target_refs': [], 'existing_issue_id': key, 'acceptance_condition': 'Reconstruct the invariant'}


class ClosureScript:
    def __init__(self, reject=False):
        self.seen = []
        self.reject = reject

    def __call__(self, payload, timeout):
        prompt = payload['instructions']
        context = json.JSONDecoder().raw_decode(prompt[prompt.index('\n{"ACTOR"')+1:])[0]
        m = context['MATERIAL']
        props = payload['text']['format']['schema']['properties']
        self.seen.append(copy.deepcopy(context))
        if 'steps' in props:
            value = candidate()
        elif 'closure_proposals' in props:
            value = {'candidate': candidate(), 'closure_proposals': [], 'issues': [],
                'application': 'Independently recomputed the invariant', 'next': decision()}
            for i in m['issues']:
                value['closure_proposals'].append({'issue_id': i['issue_id'],
                    'response_to_objection_ids': [o['objection_id'] for o in i['objections']],
                    'disposition': 'addressed', 'reason': 'Reconstruction',
                    'evidence_refs': [context['REFERENCE_INDEX'][0]], 'changed_step_ids': []})
        elif 'candidate_hash' in props:
            value = {'candidate_version': m['candidate_version'], 'candidate_hash': m['candidate_hash'],
                'checks': [{'target_refs': [context['REFERENCE_INDEX'][0]], 'method': 'manual',
                    'observation': 'One plus one is two', 'conclusion': 'supported', 'scope': 'addition'}],
                'issues': [], 'closure_reviews': []}
            for key, p in m['pending_closures'].items():
                value['closure_reviews'].append({'issue_id': key, 'proposal_event_id': p['proposal_event_id'],
                    'response_to_objection_ids': p['response_to_objection_ids'],
                    'verdict': 'unresolved' if self.reject else 'resolved',
                    'method': 'manual', 'observation': 'Insufficient proof' if self.reject else 'Reconstructed',
                    'evidence_refs': [context['REFERENCE_INDEX'][0]]})
        elif 'candidate' in props:
            value = {'candidate': candidate(), 'issues': [proposal(None)]}
        else:
            value = {'status': 'provided', 'body': 'Recomputed addition', 'basis_refs': [],
                'attempted_issue_ids': [i['issue_id'] for i in m['issues']], 'issues': []}
        return {'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': json.dumps(value)}]}], 'usage': {'input_tokens': 1, 'output_tokens': 1}}


class ClosureChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.contracts = ClosureContracts(ROOT/'design/v0.3/coreta.schema.json')
        self.cfg = json.loads((ROOT/'config/deepseek_flash_closure.json').read_text(encoding='utf-8'))
        self.cfg['generation']['max_input_tokens'] = 1000000
        self.prompts = json.loads((ROOT/'design/closure_prompts.json').read_text(encoding='utf-8'))

    def runner(self, script=None, system='coreta_revision'):
        r = ClosureRunner(TASK, self.path, 'fixture', self.contracts, None, self.cfg, self.prompts, system=system)
        r.client = ClosureClient(self.cfg, r.log, transport=script or ClosureScript())
        return r

    def setup_issue(self):
        r = self.runner()
        r.version = 0
        r.current = {'version': 0, 'source_event_id': 'fixture:e0', 'candidate': candidate()}
        r.proposed_issues([proposal(None)], 'fixture:e0', r.issues)
        return r

    def update(self, r):
        return {'candidate': candidate(), 'closure_proposals': [{'issue_id': 'i0001',
            'response_to_objection_ids': ['i0001:o1'], 'disposition': 'addressed', 'reason': 'Claim repaired',
            'evidence_refs': ['fixture:e0'], 'changed_step_ids': []}], 'issues': [],
            'application': 'Proposed repair', 'next': decision()}

    def inspection(self, r, verdict='resolved'):
        return {'candidate_version': r.version, 'candidate_hash': digest(r.current['candidate']),
            'checks': [{'target_refs': ['fixture:e0'], 'method': 'manual', 'observation': 'Trace',
                'conclusion': 'supported', 'scope': 'fixture'}], 'issues': [],
            'closure_reviews': [{'issue_id': 'i0001', 'proposal_event_id': r.pending['i0001']['proposal_event_id'],
                'response_to_objection_ids': ['i0001:o1'], 'verdict': verdict, 'method': 'manual',
                'observation': 'Trace', 'evidence_refs': ['fixture:e0']}]}

    def test_schema_valid(self):
        Draft202012Validator.check_schema(self.contracts.document)

    def test_apply_cannot_close_without_review(self):
        r = self.setup_issue(); r.commit_proposals(self.update(r))
        self.assertEqual(r.issues['i0001']['status'], 'pending_check')
        self.assertTrue(r.blockers())

    def test_editing_explanation_does_not_automatically_close(self):
        r = self.setup_issue(); u = self.update(r)
        u['candidate']['summary'] = 'Trace fixed, algorithm unchanged'
        r.commit_proposals(u); r.settle(self.inspection(r, 'unresolved'), 'A2')
        self.assertEqual(r.issues['i0001']['status'], 'open')

    def test_valid_rebuttal_can_dismiss(self):
        r = self.setup_issue(); u = self.update(r); u['closure_proposals'][0]['disposition'] = 'dismissed'
        r.commit_proposals(u); r.settle(self.inspection(r), 'A2')
        self.assertEqual(r.issues['i0001']['status'], 'dismissed')

    def test_stale_candidate_hash_rejected(self):
        r = self.setup_issue(); r.commit_proposals(self.update(r)); v = self.inspection(r)
        v['candidate_hash'] = 'stale'
        with self.assertRaises(ProtocolError): r.validate_inspection(v)

    def test_omitted_objection_rejected(self):
        r = self.setup_issue(); u = self.update(r)
        u['closure_proposals'][0]['response_to_objection_ids'] = []
        with self.assertRaises(ProtocolError): r.validate_proposals(u)

    def test_resolved_and_new_objection_rejected(self):
        r = self.setup_issue(); r.commit_proposals(self.update(r)); v = self.inspection(r)
        v['issues'] = [proposal()]
        with self.assertRaises(ProtocolError): r.validate_inspection(v)

    def test_blocking_promoted(self):
        r = self.setup_issue(); r.issues['i0001']['blocking'] = False
        r.proposed_issues([proposal()], 'fixture:e1', r.issues)
        self.assertTrue(r.issues['i0001']['blocking'])

    def test_changed_candidate_invalidates_closed_issue(self):
        r = self.setup_issue(); r.commit_proposals(self.update(r)); r.settle(self.inspection(r), 'A2')
        u = self.update(r); u['closure_proposals'] = []; u['candidate']['summary'] = 'New assumption'
        r.commit_proposals(u)
        self.assertEqual(r.issues['i0001']['status'], 'needs_revalidation')

    def test_worst_path_13_calls_no_final_rewrite(self):
        r = self.runner(ClosureScript(reject=True)); result = r.run()
        self.assertEqual(result['normal_calls'], 13)
        self.assertEqual(result['stop_reason'], 'budget_exhausted')
        self.assertFalse(any(e['stage'] == 'final' for e in r.events))
        self.assertEqual(result['artifact'], r.current['candidate']['artifact'])

    def test_success_after_post_application_review(self):
        r = self.runner(); result = r.run()
        self.assertEqual(result['normal_calls'], 7)
        self.assertEqual(result['stop_reason'], 'complete')
        self.assertEqual([e['stage'] for e in r.events][-3:], ['build', 'apply', 'inspect'])

    def test_all_baselines_keep_synthesis(self):
        for system, count in [('independent_aggregate', 4), ('static_debate', 10), ('independent_refine', 10)]:
            script = ClosureScript(); r = self.runner(script, system); result = r.run()
            self.assertEqual(result['normal_calls'], count)
            self.assertIn('final_candidates', script.seen[-1]['MATERIAL'])
            self.assertEqual(result['review_status'], 'unreviewed')

    def test_truncation_preserved_and_bounded(self):
        def truncated(payload, timeout):
            return {'status': 'incomplete', 'incomplete_details': {'reason': 'max_output_tokens'},
                'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'partial'}]}]}
        r = self.runner(); r.client = ClosureClient(self.cfg, r.log, transport=truncated)
        result = r.run()
        self.assertEqual(result['format_repairs'], 1)
        self.assertEqual(result['http_attempts'], 2)
        logs = [json.loads(x) for x in (self.path/'failures.jsonl').read_text().splitlines()]
        self.assertEqual(logs[0]['failure_type'], 'output_truncated')
        self.assertIn('partial', json.dumps(logs[0]['raw_output']))

    def test_inspection_failure_delivers_unreviewed_candidate(self):
        class FailureScript(ClosureScript):
            def __call__(self, payload, timeout):
                if 'closure_reviews' in payload['text']['format']['schema']['properties']:
                    raise ProtocolError('MODEL_UNAVAILABLE', 'fixture outage')
                return super().__call__(payload, timeout)
        r = self.runner(FailureScript()); result = r.run()
        self.assertEqual(result['status'], 'degraded')
        self.assertEqual(result['review_status'], 'unreviewed')
        self.assertEqual(result['artifact'], r.current['candidate']['artifact'])

    def test_null_incomplete_details_keeps_protocol_failure(self):
        def empty_response(payload, timeout):
            return {'status': 'completed', 'incomplete_details': None, 'output': []}
        r = self.runner(); r.client = ClosureClient(self.cfg, r.log, transport=empty_response)
        result = r.run()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['errors'][0]['code'], 'SCHEMA_ERROR')
        self.assertEqual(result['http_attempts'], 2)

    def test_failed_response_with_null_details_degrades(self):
        def failed_response(payload, timeout):
            return {'status': 'failed', 'incomplete_details': None, 'output': []}
        r = self.runner(); r.client = ClosureClient(self.cfg, r.log, transport=failed_response)
        result = r.run()
        self.assertEqual(result['errors'][0]['code'], 'SCHEMA_ERROR')
        self.assertEqual(result['http_attempts'], 2)


if __name__ == '__main__': unittest.main()
