"""Compute candidate differences without treating model bookkeeping as truth."""
import copy
from .closure_feedback import FeedbackClosureRunner
from .schemas import ProtocolError


def candidate_diff(before, after):
    old = {s['id']: s for s in before['steps']}
    new = {s['id']: s for s in after['steps']}
    return {
        'added_step_ids': sorted(new.keys() - old.keys()),
        'modified_step_ids': sorted(k for k in old.keys() & new.keys() if old[k] != new[k]),
        'removed_step_ids': sorted(old.keys() - new.keys()),
        'artifact_changed': before['artifact'] != after['artifact'],
    }


class DiffClosureRunner(FeedbackClosureRunner):
    def call(self, stage, actor, schema_name, material, validate=None):
        if schema_name == 'ClosureUpdate':
            material = {**material, 'change_tracking_policy':
                'Runtime computes actual differences. changed_step_ids is advisory and retained verbatim. '
                'Every closure proposal requires visible evidence_refs. A difference is not proof of resolution. '
                'For an objection to a discarded draft, explain whether the current candidate depends on it; '
                'request dismissal with evidence if irrelevant, never silently remove the objection.'}
        if schema_name == 'ClosureInspection':
            material = {**material, 'runtime_candidate_diff': candidate_diff(
                material['before']['candidate'], self.current['candidate']),
                'review_policy': 'Verify each closure reason against the applied candidate and cited evidence. '
                'Model changed_step_ids is advisory. Runtime differences do not prove issue resolution. '
                'An objection citing a draft can still affect the current candidate; check dependencies.'}
        return super().call(stage, actor, schema_name, material, validate)

    def validate_proposals(self, value):
        seen = set()
        for proposal in value['closure_proposals']:
            key = proposal['issue_id']
            if key not in self.issues or key in seen:
                raise ProtocolError('REFERENCE_ERROR', 'Unique visible issue required')
            seen.add(key)
            if set(proposal['response_to_objection_ids']) != {
                    o['objection_id'] for o in self.issues[key]['objections']}:
                raise ProtocolError('REFERENCE_ERROR', 'Closure must respond to every recorded objection')
            if not proposal['evidence_refs']:
                raise ProtocolError('REFERENCE_ERROR', 'Closure requires visible evidence_refs; changed steps alone are not evidence')
        if not set(value['next']['issue_ids']).issubset(self.issues):
            raise ProtocolError('REFERENCE_ERROR', 'Next targets must be visible issues')

    def commit_proposals(self, value):
        self.validate_proposals(value)
        audit = {'base_version': self.version,
                 'candidate_diff': candidate_diff(self.current['candidate'], value['candidate']),
                 'model_declarations': [
                     {'issue_id': p['issue_id'], 'changed_step_ids': copy.deepcopy(p['changed_step_ids'])}
                     for p in value['closure_proposals']]}
        super().commit_proposals(value)
        self.log('candidate_diffs.jsonl', {**audit, 'applied_version': self.version,
                                         'event_id': self.current['source_event_id']})
