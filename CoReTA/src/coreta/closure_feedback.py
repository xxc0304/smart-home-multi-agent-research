"""Narrow v0.5 feedback variant; preserve all objections and closure rules."""
from collections import Counter
from .closure import ClosureRunner
from .schemas import ProtocolError


class FeedbackClosureRunner(ClosureRunner):
    def call(self, stage, actor, schema_name, material, validate=None):
        if schema_name == 'ClosureInspection':
            material = {**material, 'closure_review_scope': {
                'allowed_pending_issue_ids': sorted(self.pending),
                'open_without_closure_proposal_ids': sorted(k for k, i in self.issues.items()
                    if k not in self.pending and i['status'] not in {'addressed', 'dismissed'}),
                'routing_rule': 'closure_reviews is exactly for pending_closures. Put objections to other open issues in issues with existing_issue_id, or in checks; never fabricate a proposal to review.'}}
        return super().call(stage, actor, schema_name, material, validate)

    def validate_inspection(self, value):
        keys = [r['issue_id'] for r in value['closure_reviews']]
        invalid = sorted(set(keys) - set(self.pending))
        missing = sorted(set(self.pending) - set(keys))
        repeated = sorted(k for k, n in Counter(keys).items() if n > 1)
        if invalid or missing or repeated:
            statuses = {k: self.issues.get(k, {}).get('status', 'not_visible') for k in invalid}
            raise ProtocolError('REFERENCE_ERROR',
                f'closure_reviews must cover exactly pending issue IDs {sorted(self.pending)}, once each. '
                f'Invalid IDs/statuses={statuses}; missing={missing}; repeated={repeated}. '
                'Keep every substantive objection: move observations about open issues without proposals '
                'to issues using their existing_issue_id, or checks with visible target_refs. '
                'Do not invent proposal_event_id for them. Do not delete objections merely to pass validation.')
        return super().validate_inspection(value)
