"""Opt-in v0.5: inspect committed candidates before accepting issue closure."""
import copy
import hashlib
import json

from .revision import RevisionContracts, RevisionRunner, obj, text, array, choice
from .schemas import ProtocolError
from .model_client import DeepSeekClient
from .state import write_json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class ClosureContracts(RevisionContracts):
    def __init__(self, path):
        super().__init__(path)
        defs = self.document['$defs']
        refs = array(text(120))
        issue = obj(description=text(), blocking={'type': 'boolean'}, target_refs=refs,
                    existing_issue_id={'anyOf': [text(30), {'type': 'null'}]}, acceptance_condition=text())
        for name in ('Synthesis', 'Constructive', 'Inspection'):
            defs[name]['properties']['issues'] = array(issue, 6)
        proposal = obj(issue_id=text(30), response_to_objection_ids=array(text(40), 40),
                       disposition=choice('addressed', 'dismissed'), reason=text(),
                       evidence_refs=refs, changed_step_ids=array(text(3), 8))
        defs['ClosureUpdate'] = obj(candidate={'$ref': '#/$defs/Candidate'},
            closure_proposals=array(proposal, 40), issues=array(issue, 6),
            application=text(5000), next={'$ref': '#/$defs/RevisionDecision'})
        review = obj(issue_id=text(30), proposal_event_id=text(120),
            response_to_objection_ids=array(text(40), 40), verdict=choice('resolved', 'unresolved', 'defect'),
            method=text(), observation=text(), evidence_refs=refs)
        defs['ClosureInspection'] = copy.deepcopy(defs['Inspection'])
        defs['ClosureInspection']['properties'].update(
            candidate_version={'type': 'integer'}, candidate_hash=text(64), closure_reviews=array(review, 40))
        defs['ClosureInspection']['required'] += ['candidate_version', 'candidate_hash', 'closure_reviews']
        defs['Event']['properties']['schema_version'] = {'const': 'coreta/0.5-closure'}
        defs['Event']['properties']['payload']['anyOf'] += [
            {'$ref': '#/$defs/ClosureUpdate'}, {'$ref': '#/$defs/ClosureInspection'}]
        defs['Candidate']['properties']['steps']['maxItems'] = 6
        self.document['$id'] = 'https://example.invalid/coreta/design/0.5-closure/schema.json'
        self.document['title'] = 'CoReTA post-application closure review contract'


class ClosureClient(DeepSeekClient):
    """Preserve original responses, expose truncation cause to bounded repair."""
    def __init__(self, config, log, **kwargs):
        self.last_response = None
        def capture(name, value):
            if name == 'responses.jsonl':
                self.last_response = value.get('response')
            log(name, value)
        super().__init__(config, capture, **kwargs)

    def complete(self, *args, **kwargs):
        self.last_response = None
        try:
            return super().complete(*args, **kwargs)
        except ProtocolError as exc:
            if (self.last_response or {}).get('incomplete_details', {}).get('reason') == 'max_output_tokens':
                self.log('failures.jsonl', {'failure_type': 'output_truncated',
                    'response_id': self.last_response.get('id'), 'raw_output': self.last_response.get('output')})
                raise ProtocolError('SCHEMA_ERROR', 'output_truncated: shorten repeated explanation, retain complete artifact and decisive reasoning; original output retained') from exc
            raise


class ClosureRunner(RevisionRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending = {}
        self.last_reviewed = None

    def emit(self, stage, actor, payload):
        event = {'event_id': f'{self.run_id}:e{len(self.events):04d}', 'schema_version': 'coreta/0.5-closure',
            'sent_from': actor, 'base_version': self.version, 'stage': stage,
            'task_id': self.task['task_id'], 'payload': copy.deepcopy(payload)}
        self.contracts.validate('Event', event)
        self.log('events.jsonl', event)
        self.events.append(event)
        return event

    def view(self):
        # Never truncate active objections to fit a history window.
        return {'task': self.task, 'drafts': self.drafts, 'current': self.current,
            'issues': copy.deepcopy(list(self.issues.values())), 'attempts': self.attempts,
            'candidate_version': self.version,
            'candidate_hash': digest(self.current['candidate']) if self.current else None}

    def proposed_issues(self, proposals, event_id, registry):
        for n, proposal in enumerate(proposals):
            key = proposal['existing_issue_id']
            if key is None:
                key = f'i{len(registry)+1:04d}'
                registry[key] = {**copy.deepcopy(proposal), 'issue_id': key, 'status': 'open',
                    'source_event_id': event_id, 'version': self.version,
                    'handling_events': [], 'objections': []}
            issue = registry[key]
            issue['blocking'] = issue['blocking'] or proposal['blocking']
            issue['status'] = 'open'
            issue['objections'].append({'objection_id': f'{key}:o{len(issue["objections"])+1}',
                'event_id': event_id, 'text': proposal['description'], 'target_refs': proposal['target_refs'],
                'acceptance_condition': proposal['acceptance_condition']})

    def validate_proposals(self, value):
        steps = {s['id']: s for s in value['candidate']['steps']}
        before = {s['id']: s for s in self.current['candidate']['steps']}
        seen = set()
        for p in value['closure_proposals']:
            key = p['issue_id']
            if key not in self.issues or key in seen:
                raise ProtocolError('REFERENCE_ERROR', 'Unique visible issue required')
            seen.add(key)
            issue = self.issues[key]
            if set(p['response_to_objection_ids']) != {o['objection_id'] for o in issue['objections']}:
                raise ProtocolError('REFERENCE_ERROR', 'Closure must respond to every recorded objection')
            if any(s not in steps or steps[s] == before.get(s) for s in p['changed_step_ids']):
                raise ProtocolError('REFERENCE_ERROR', 'Closure changed steps must actually change')
            if not p['evidence_refs'] and not p['changed_step_ids']:
                raise ProtocolError('REFERENCE_ERROR', 'Closure requires evidence or changed steps')
        if not set(value['next']['issue_ids']).issubset(self.issues):
            raise ProtocolError('REFERENCE_ERROR', 'Next targets must be visible issues')

    def commit_proposals(self, value):
        self.validate_proposals(value)
        registry = copy.deepcopy(self.issues)
        changed = digest(value['candidate']) != digest(self.current['candidate'])
        for issue in registry.values():
            if changed and issue['blocking'] and issue['status'] in {'addressed', 'dismissed'}:
                issue['status'] = 'needs_revalidation'
        event_id = f'{self.run_id}:e{len(self.events):04d}'
        self.proposed_issues(value['issues'], event_id, registry)
        self.pending = {}
        for p in value['closure_proposals']:
            key = p['issue_id']
            # A fresh objection introduced in this same update needs a subsequent response.
            if set(p['response_to_objection_ids']) != {o['objection_id'] for o in registry[key]['objections']}:
                continue
            registry[key]['status'] = 'pending_check'
            self.pending[key] = {**copy.deepcopy(p), 'proposal_event_id': event_id}
        self.candidate_commit('apply', value, registry)

    def validate_inspection(self, value):
        if value['candidate_version'] != self.version or value['candidate_hash'] != digest(self.current['candidate']):
            raise ProtocolError('REFERENCE_ERROR', 'Inspection must match current candidate version/hash')
        seen = set()
        newly_contested = {p['existing_issue_id'] for p in value['issues'] if p['existing_issue_id']}
        for r in value['closure_reviews']:
            key = r['issue_id']
            if key not in self.pending or key in seen:
                raise ProtocolError('REFERENCE_ERROR', 'Review must identify unique pending proposal')
            seen.add(key)
            p = self.pending[key]
            if r['proposal_event_id'] != p['proposal_event_id'] or set(r['response_to_objection_ids']) != set(p['response_to_objection_ids']):
                raise ProtocolError('REFERENCE_ERROR', 'Review must cover exact proposal and objections')
            if r['verdict'] == 'resolved' and key in newly_contested:
                raise ProtocolError('INVALID_ACTION', 'Cannot resolve issue while adding an unresolved objection to it')
        if seen != set(self.pending):
            raise ProtocolError('REFERENCE_ERROR', 'Review every pending closure proposal')
        if not value['checks'] or any(not c['target_refs'] for c in value['checks']):
            raise ProtocolError('REFERENCE_ERROR', 'Candidate inspection requires visible targets')

    def settle(self, value, actor):
        self.validate_inspection(value)
        event = self.record('inspect', actor, value)
        for r in value['closure_reviews']:
            issue = self.issues[r['issue_id']]
            issue['status'] = self.pending[r['issue_id']]['disposition'] if r['verdict'] == 'resolved' else 'open'
            issue['handling_events'].append({'version': self.version, 'review_event': event['event_id'], **r})
        self.last_reviewed = copy.deepcopy(self.current)
        self.log('reviews.jsonl', {'version': self.version, 'candidate_hash': digest(self.current['candidate']),
            'review_event': event['event_id'], 'issues': self.issues})
        self.pending = {}

    def blockers(self):
        return [i for i in self.issues.values() if i['blocking'] and i['status'] not in {'addressed', 'dismissed'}]

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
            before = copy.deepcopy(self.current)
            value = self.call('apply', 'A0', 'ClosureUpdate', {**self.view(), 'evidence': [built],
                'remaining_work_turns': 2-turn}, self.validate_proposals)
            self.commit_proposals(value)
            checked = self.call('inspect', checker, 'ClosureInspection', {**self.view(), 'subject': built,
                'before': before, 'pending_closures': self.pending}, self.validate_inspection)
            self.settle(checked, checker)
            blockers = self.blockers()
            required = not value['next']['action'].startswith('FINISH')
            if not blockers and not required:
                return 'complete'
            attempted = {k for a in self.attempts for k in a['issue_ids']}
            if (blockers and contribution['status'] == 'cannot_help'
                    and value['next']['action'] == 'FINISH_STALLED'
                    and all(i['issue_id'] in attempted for i in blockers)):
                return 'stalled'
            requested = copy.deepcopy(value['next'])
            requested['post_application_objections'] = copy.deepcopy(checked['issues'])
            requested['closure_reviews'] = copy.deepcopy(checked['closure_reviews'])
            actor = value['next']['recipient'] if value['next']['recipient'] in {'A1', 'A2'} else checker
        return 'budget_exhausted'

    def run(self):
        errors, status, stop = [], 'completed', 'not_started'
        try:
            self.initial_drafts()
            if self.system == 'coreta_revision':
                stop = self.collaborate()
            else:
                stop = self.baseline()
                value = self.call('final', 'A0', 'Candidate', {**self.view(), 'final_candidates': self.final_candidates})
                self.version += 1
                event = self.emit('final', 'A0', value)
                self.current = {'version': self.version, 'source_event_id': event['event_id'], 'candidate': value}
        except ProtocolError as exc:
            status, stop = 'degraded', 'runtime_error'
            errors.append({'code': exc.code, 'detail': exc.detail})
        artifact = self.current['candidate']['artifact'] if self.current else ''
        reviewed = bool(self.last_reviewed and self.current == self.last_reviewed)
        result = {'task_id': self.task['task_id'], 'run_id': self.run_id, 'system': self.system,
            'status': status if self.current else 'failed', 'stop_reason': stop, 'artifact': artifact,
            'prefinal_artifact': artifact, 'finalizer_changed': False, 'delivery_candidate': self.current,
            'review_status': 'reviewed' if reviewed else 'unreviewed', 'last_reviewed_candidate': self.last_reviewed,
            'normal_calls': self.calls, 'http_attempts': self.client.attempts, 'format_repairs': self.repairs,
            'issues': self.issues, 'errors': errors, 'seed': self.seed}
        write_json(self.directory/'result.json', result)
        return result
