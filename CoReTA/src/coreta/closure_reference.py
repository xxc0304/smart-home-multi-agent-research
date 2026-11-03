"""Explicit audit-ID contract; immutable v2 implementation is inherited."""
import copy
import json

from .schemas import ProtocolError
from .task_audit_binding import SourceBoundAuditRunner

VARIANT = 'task_audit_reference_v3'


def closure_reference_contract(issues):
    return {
        'rules': 'evidence_record_ids contains ONLY record_id values from this issue evidence_records. '
                 'Copy the exact expected set, including [] when there has been no audit for this issue. '
                 'Event IDs, step references and objection IDs are different namespaces; put supporting '
                 'visible event/step references in evidence_refs. Never invent audit IDs. '
                 'Empty audit IDs do not waive objections, repair requirements or subsequent inspection.',
        'issues': [{'issue_id': key,
                    'expected_evidence_record_ids': sorted({r['record_id'] for r in issue.get('evidence_records', [])})}
                   for key, issue in sorted(issues.items())]}


def reference_conflicts(value, issues):
    conflicts = []
    for proposal in value['closure_proposals']:
        key = proposal['issue_id']
        if key not in issues:
            continue  # Existing parent validator diagnoses unknown issue IDs.
        expected = {r['record_id'] for r in issues[key].get('evidence_records', [])}
        submitted = proposal['evidence_record_ids']
        actual = set(submitted)
        if actual != expected or len(submitted) != len(actual):
            conflicts.append({'issue_id': key, 'expected_evidence_record_ids': sorted(expected),
                              'submitted_evidence_record_ids': submitted,
                              'missing': sorted(expected-actual), 'unexpected': sorted(actual-expected),
                              'duplicate_ids': sorted({x for x in submitted if submitted.count(x)>1})})
    return conflicts


class ReferenceAuditRunner(SourceBoundAuditRunner):
    def call(self, stage, actor, schema_name, material, validate=None):
        if stage == 'apply':
            material = {**copy.deepcopy(material),
                        'closure_reference_contract': closure_reference_contract(self.issues)}
        return super().call(stage, actor, schema_name, material, validate)

    def validate_proposals(self, value):
        conflicts = reference_conflicts(value, self.issues)
        if conflicts:
            raise ProtocolError('REFERENCE_ERROR', 'AUDIT_REFERENCE_CONFLICT=' +
                                json.dumps(conflicts, ensure_ascii=False, sort_keys=True) +
                                '; Use ordinary supporting citations in evidence_refs. '
                                'Return a complete update; do not delete substantive objections or repairs.')
        return super().validate_proposals(value)
