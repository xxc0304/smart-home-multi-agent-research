"""Matched B/C/U control: review contribution, then let A0 commit closures."""
import copy
from .closure import ClosureRunner


class PrecheckRunner(ClosureRunner):
    def commit_proposals(self, value):
        super().commit_proposals(value)
        for key, p in self.pending.items():
            self.issues[key]['status'] = p['disposition']
            self.issues[key]['handling_events'].append({'version': self.version,
                'mode': 'lead_commit_without_post_review', **copy.deepcopy(p)})
        self.log('lead_closures.jsonl', {'version': self.version, 'issues': self.issues})
        self.pending = {}

    def collaborate(self):
        value = self.call('synthesize', 'A0', 'Synthesis', self.view())
        registry = {}
        self.proposed_issues(value['issues'], f'{self.run_id}:e{len(self.events):04d}', registry)
        self.candidate_commit('synthesize', value, registry)
        actor = 'A1'
        requested = {'goal': 'Repair active objections or reconstruct a decisive dependency', 'issue_ids': []}
        for turn in range(3):
            checker = 'A2' if actor == 'A1' else 'A1'
            material = {**self.view(), 'request': {**requested,
                'active_blocking_issue_ids': [i['issue_id'] for i in self.blockers()]}}
            contribution = self.call('build' if turn == 0 else 'work', actor, 'Constructive', material, self.validate_work)
            built = self.record('build' if turn == 0 else 'work', actor, contribution)
            self.attempts.append({'event_id': built['event_id'], 'issue_ids': contribution['attempted_issue_ids']})
            checked = self.call('inspect', checker, 'Inspection', {**self.view(), 'subject': built})
            inspected = self.record('inspect', checker, checked)
            value = self.call('apply', 'A0', 'ClosureUpdate', {**self.view(), 'evidence': [built, inspected],
                'remaining_work_turns': 2-turn}, self.validate_proposals)
            self.commit_proposals(value)
            blockers = self.blockers()
            if not blockers and value['next']['action'].startswith('FINISH'):
                return 'complete'
            attempted = {k for a in self.attempts for k in a['issue_ids']}
            if (blockers and contribution['status'] == 'cannot_help'
                    and value['next']['action'] == 'FINISH_STALLED'
                    and all(i['issue_id'] in attempted for i in blockers)):
                return 'stalled'
            requested = copy.deepcopy(value['next'])
            requested['pre_application_objections'] = copy.deepcopy(checked['issues'])
            actor = value['next']['recipient'] if value['next']['recipient'] in {'A1', 'A2'} else checker
        return 'budget_exhausted'
