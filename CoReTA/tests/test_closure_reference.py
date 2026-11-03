import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from coreta.closure_reference import (ReferenceAuditRunner, closure_reference_contract, reference_conflicts)
from coreta.task_audit_binding import SourceBoundAuditRunner
from coreta.schemas import ProtocolError

ROOT = Path(__file__).resolve().parents[1]

class ClosureReferenceChecks(unittest.TestCase):
    def test_empty_explicit(self):
        self.assertEqual(closure_reference_contract({'i1': {}})['issues'][0]['expected_evidence_record_ids'], [])
        self.assertEqual(reference_conflicts({'closure_proposals': [{'issue_id': 'i1', 'evidence_record_ids': []}]}, {'i1': {}}), [])

    def test_missing_unexpected_and_duplicate(self):
        value = {'closure_proposals': [{'issue_id': 'i1', 'evidence_record_ids': ['event', 'event']}]}
        row = reference_conflicts(value, {'i1': {'evidence_records': [{'record_id': 'audit1'}]}})[0]
        self.assertEqual(row['missing'], ['audit1'])
        self.assertEqual(row['unexpected'], ['event'])
        self.assertEqual(row['duplicate_ids'], ['event'])

    def test_matching_still_invokes_parent_validation(self):
        runner = object.__new__(ReferenceAuditRunner)
        runner.issues = {'i1': {'evidence_records': [{'record_id': 'audit1'}]}}
        value = {'closure_proposals': [{'issue_id': 'i1', 'evidence_record_ids': ['audit1']}]}
        with patch.object(SourceBoundAuditRunner, 'validate_proposals', side_effect=ProtocolError('INVALID_ACTION', 'repair required')) as parent:
            with self.assertRaises(ProtocolError): runner.validate_proposals(value)
            parent.assert_called_once_with(value)

    def test_apply_guidance_is_input_only(self):
        runner = object.__new__(ReferenceAuditRunner)
        runner.issues = {'i1': {}}
        material = {'candidate': 'unchanged'}
        with patch.object(SourceBoundAuditRunner, 'call', return_value='ok') as parent:
            self.assertEqual(runner.call('apply', 'A0', 'ClosureUpdate', material), 'ok')
            self.assertEqual(parent.call_args.args[3]['closure_reference_contract']['issues'][0]['expected_evidence_record_ids'], [])
        self.assertEqual(material, {'candidate': 'unchanged'})

    def test_real_failures_are_retained_and_diagnosed(self):
        path = ROOT/'runs/math140-source-binding-20261020/4276ec64c178dafa/validation.jsonl'
        rows = [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]
        applies = [json.loads(x['raw']) for x in rows if x['stage']=='apply']
        self.assertEqual(len(applies), 2)
        for value in applies:
            original = copy.deepcopy(value)
            issues = {p['issue_id']: {} for p in value['closure_proposals']}
            conflicts = reference_conflicts(value, issues)
            self.assertEqual(len(conflicts), 4)
            self.assertTrue(all(x['expected_evidence_record_ids']==[] and x['unexpected'] for x in conflicts))
            runner = object.__new__(ReferenceAuditRunner); runner.issues = issues
            with self.assertRaises(ProtocolError) as error: runner.validate_proposals(value)
            self.assertIn('AUDIT_REFERENCE_CONFLICT=', error.exception.detail)
            self.assertEqual(value, original)
            # Explicit synthetic correction tests the gate only, never replaces a real response.
            corrected = copy.deepcopy(value)
            for p in corrected['closure_proposals']: p['evidence_record_ids'] = []
            self.assertEqual(reference_conflicts(corrected, issues), [])

if __name__ == '__main__': unittest.main()
