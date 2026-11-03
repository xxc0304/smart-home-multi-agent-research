"""Opt-in task-grounded audit. Submitted evidence precedes closure decisions."""
from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from fractions import Fraction

from .closure import ClosureContracts, digest
from .closure_diff import candidate_diff
from .closure_format import FormatClosureRunner
from .revision import array, choice, obj, text
from .schemas import ProtocolError, check_refs
from .state import reference_index, write_json


VERSION = 'coreta/0.6-task-audit'
TASK_FACTS_OUTPUT_TOKENS = 4096


class AuditContracts(ClosureContracts):
    def __init__(self, path):
        super().__init__(path)
        defs = self.document['$defs']
        nullable_id = {'anyOf': [text(120), {'type': 'null'}]}
        coverage = choice('complete_for_explicit_list', 'partial', 'unknown')
        locator = obj(kind=choice('prompt_span', 'json_pointer'),
                      start={'type': 'integer', 'minimum': 0},
                      end={'type': 'integer', 'minimum': 0},
                      pointer={'type': 'string', 'maxLength': 300})
        fact = obj(fact_id=text(40), source_locator=locator, quoted_text=text(2000),
                   normalized_fact=text(1000), kind=choice('constraint', 'objective', 'domain', 'ambiguity'),
                   coverage_status=coverage)
        defs['TaskFacts'] = obj(facts=array(fact, 32), coverage_status=coverage)
        case = obj(case_id=text(40), fact_id=text(40), input=text(1000),
                   comparison_kind=choice('exact_equality', 'model_judged'), quantity_key=text(300),
                   expected_value=text(1000), observed_value=text(1000),
                   model_outcome=choice('counterexample', 'match', 'unable'))
        audit = obj(existing_issue_id=nullable_id, target_refs=array(text(120)),
                    task_fact_ids=array(text(40), 32), claim_text=text(1500),
                    attempted_falsification=text(2000), cases={**array(case, 32), 'minItems': 1},
                    coverage=choice('exhaustive_for_listed_facts', 'sampled', 'unable'), scope=text(1000),
                    correctness_critical={'type': 'boolean'},
                    model_verdict=choice('counterexample', 'not_refuted', 'unable'))
        inspection = defs['ClosureInspection']
        inspection['properties']['audit_records'] = {**array(audit, 6), 'minItems': 1}
        inspection['required'].append('audit_records')
        for field, schema in [('closure_path', choice('repair', 'rebuttal')),
                              ('evidence_record_ids', array(text(160), 100))]:
            p = defs['ClosureUpdate']['properties']['closure_proposals']['items']
            p['properties'][field] = schema
            p['required'].append(field)
        review = inspection['properties']['closure_reviews']['items']
        review['properties']['evidence_record_ids'] = array(text(160), 100)
        review['required'].append('evidence_record_ids')
        defs['Event']['properties']['schema_version'] = {'const': VERSION}
        defs['Event']['properties']['stage']['enum'].append('task_facts')
        defs['Event']['properties']['payload']['anyOf'].append({'$ref': '#/$defs/TaskFacts'})
        self.document['$id'] = 'https://example.invalid/coreta/design/0.6-task-audit/schema.json'
        self.document['title'] = 'CoReTA task-grounded audit and evidence retention'


def exact_rational(value):
    """Only canonical exact scalars, never eval(), floats or unit conversion."""
    if len(value) > 160 or not re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?', value):
        return None
    result = Fraction(value)
    return result if str(result) == value else None


def effective_outcome(record):
    if record['model_verdict'] == 'counterexample':
        return 'finding_open'
    unable = record['model_verdict'] == 'unable'
    for case in record['cases']:
        if case['model_outcome'] == 'counterexample':
            return 'finding_open'
        unable |= case['model_outcome'] == 'unable'
        if case['comparison_kind'] == 'exact_equality':
            expected = exact_rational(case['expected_value'])
            observed = exact_rational(case['observed_value'])
            if expected is not None and observed is not None:
                if expected != observed:
                    return 'finding_open'
    if unable and record['correctness_critical']:
        return 'needs_check'
    return 'not_refuted_within_recorded_scope'


def public_value(task, locator):
    if locator['kind'] == 'prompt_span':
        prompt = task['prompt']
        start, end = locator['start'], locator['end']
        if not 0 <= start < end <= len(prompt) or locator['pointer']:
            raise ValueError('Invalid prompt span')
        return prompt[start:end]
    if locator['start'] or locator['end']:
        raise ValueError('JSON Pointer locators use start=end=0')
    pointer = locator['pointer']
    if not pointer.startswith('/'):
        raise ValueError('JSON Pointer must identify a public field')
    current = task
    for token in pointer[1:].split('/'):
        key = token.replace('~1', '/').replace('~0', '~')
        current = current[int(key)] if isinstance(current, list) else current[key]
    return current if isinstance(current, str) else json.dumps(current, ensure_ascii=False, sort_keys=True)


class AuditClosureRunner(FormatClosureRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.system != 'coreta_revision':
            raise ValueError('task_audit_v1 is an explicit CoReTA-only runner')
        self.CAP = 15  # inherited call() reserves an unused final slot; 14 actual logical stages
        self.task_facts = None
        self.audit_ledger = []
        self._accepted = {}
        self._last_builder = None

    def emit(self, stage, actor, payload):
        event = {'event_id': f'{self.run_id}:e{len(self.events):04d}', 'schema_version': VERSION,
                 'sent_from': actor, 'base_version': self.version, 'stage': stage,
                 'task_id': self.task['task_id'], 'payload': copy.deepcopy(payload)}
        self.contracts.validate('Event', event)
        self.log('events.jsonl', event)
        self.events.append(event)
        return event

    def view(self):
        return {**super().view(), 'task_facts': copy.deepcopy(self.task_facts)}

    def record(self, stage, actor, value):
        if stage in {'build', 'work'}:
            self._last_builder = actor
        return super().record(stage, actor, value)

    def validate_task_facts(self, value):
        seen = set()
        for fact in value['facts']:
            if fact['fact_id'] in seen:
                raise ProtocolError('REFERENCE_ERROR', 'TaskFact ids must be unique')
            seen.add(fact['fact_id'])
            try:
                quoted = public_value(self.task, fact['source_locator'])
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                raise ProtocolError('REFERENCE_ERROR', f'Invalid source_locator for {fact["fact_id"]}') from exc
            if quoted != fact['quoted_text']:
                raise ProtocolError('REFERENCE_ERROR', f'TaskFact {fact["fact_id"]} quote does not match public task')
        if not seen:
            raise ProtocolError('REFERENCE_ERROR', 'At least one public task fact is required')

    def call(self, stage, actor, schema_name, material, validate=None):
        if stage not in {'task_facts', 'inspect'}:
            return super().call(stage, actor, schema_name, material, validate)
        if self.calls >= self.CAP - 1:
            raise ProtocolError('CALL_LIMIT', 'Fourteen logical stages exhausted')
        self.calls += 1
        # C evaluates the applied candidate, public facts and supplied contribution.
        # It does not need all independent drafts; omitted draft citations are not visible.
        material = copy.deepcopy(material)
        if stage == 'inspect':
            material.pop('drafts', None)
        schema = self.contracts.schema(schema_name)
        if stage == 'inspect':
            material['audit_output_contract'] = {
                'root_fields': list(schema['properties']),
                'audit_record_fields': list(schema['properties']['audit_records']['items']['properties']),
                'audit_case_fields': list(schema['properties']['audit_records']['items']['properties']['cases']['items']['properties']),
                'closure_review_fields': list(schema['properties']['closure_reviews']['items']['properties'])}
        visible = set(reference_index(material))
        prompt = self.prompts['system'] + '\n' + self.prompts[stage]
        prompt += '\n' + json.dumps({'ACTOR': actor, 'MATERIAL': material,
                                     'REFERENCE_INDEX': sorted(visible), 'OUTPUT_SCHEMA': schema}, ensure_ascii=False)
        limit = self.config['generation']['max_output_tokens'].get(stage, TASK_FACTS_OUTPUT_TOKENS)
        payload = self.client.payload(prompt, schema, limit)
        for attempt in range(2):
            raw = ''
            try:
                raw = self.client.complete(payload, deadline=self.deadline,
                                           logical_seed=f'{self.seed}|{stage}|{actor}|{self.calls}')
                self.log('audit_responses.jsonl', {'stage': stage, 'actor': actor, 'raw': raw,
                                                   'logical_call': self.calls, 'attempt': attempt})
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ProtocolError('INVALID_JSON', 'Return one complete JSON object') from exc
                self.contracts.validate(schema_name, value)
                if stage == 'task_facts':
                    self.validate_task_facts(value)
                else:
                    # All business/reference conflicts become retained diagnostics, not retries.
                    self.accept_inspection(value, actor, visible)
                return value
            except ProtocolError as exc:
                self.log('validation.jsonl', {'stage': stage, 'code': exc.code, 'detail': exc.detail,
                                              'raw': raw, 'attempt': attempt})
                retryable = {'SCHEMA_ERROR', 'INVALID_JSON'}
                if stage == 'task_facts':
                    retryable.add('REFERENCE_ERROR')
                if exc.code not in retryable or attempt or self.repairs >= self.config['protocol']['max_format_repairs']:
                    raise
                self.repairs += 1
                payload = self.client.payload(prompt + '\nSTRUCTURAL_ERROR=' + exc.detail +
                                              '\nPREVIOUS_OUTPUT=' + raw +
                                              '\nRepair syntax/structure without deleting substantive evidence.', schema, limit)

    def collaborate(self):
        value = self.call('task_facts', 'A2', 'TaskFacts', {'task': copy.deepcopy(self.task)})
        self.task_facts = self.emit('task_facts', 'A2', value)
        return super().collaborate()

    @staticmethod
    def evidence_ids(issue):
        return {row['record_id'] for row in issue.get('evidence_records', [])}

    def validate_proposals(self, value):
        super().validate_proposals(value)
        differences = candidate_diff(self.current['candidate'], value['candidate'])
        for proposal in value['closure_proposals']:
            issue = self.issues[proposal['issue_id']]
            if set(proposal['evidence_record_ids']) != self.evidence_ids(issue):
                raise ProtocolError('REFERENCE_ERROR', 'Closure must respond to every original audit record ID')
            if proposal['closure_path'] == 'repair':
                if proposal['disposition'] != 'addressed':
                    raise ProtocolError('INVALID_ACTION', 'Repair requires addressed disposition')
                targets = {ref.rsplit(':', 1)[-1].rsplit('#', 1)[-1] for ref in issue['target_refs']}
                changed = set(differences['added_step_ids'] + differences['modified_step_ids'] + differences['removed_step_ids'])
                if not differences['artifact_changed'] and not (changed & targets):
                    raise ProtocolError('INVALID_ACTION', 'Repair requires artifact or targeted-step changes; metadata is insufficient')
            elif proposal['disposition'] != 'dismissed':
                raise ProtocolError('INVALID_ACTION', 'Rebuttal requires dismissed disposition')

    def commit_proposals(self, value):
        before_hash = digest(self.current['candidate'])
        super().commit_proposals(value)
        for proposal in self.pending.values():
            proposal.update(base_candidate_hash=before_hash,
                            applied_candidate_hash=digest(self.current['candidate']), applied_by='A0')

    def _inspection_errors(self, value, actor, visible):
        errors = []
        if actor == 'A0' or actor == self._last_builder or self._last_builder not in {'A1', 'A2'}:
            errors.append('Inspector must differ from builder and integrator')
        if value['candidate_version'] != self.version or value['candidate_hash'] != digest(self.current['candidate']):
            errors.append('Inspection candidate version/hash is stale')
        try:
            check_refs(value, visible)
            self.check_targets(value, visible)
        except ProtocolError as exc:
            errors.append(exc.detail)
        if any(not c['target_refs'] for c in value['checks']):
            errors.append('Checks need visible targets')
        known = {f['fact_id'] for f in self.task_facts['payload']['facts']} if self.task_facts else set()
        for record in value['audit_records']:
            fact_ids = set(record['task_fact_ids'])
            case_ids = [c['case_id'] for c in record['cases']]
            used = {c['fact_id'] for c in record['cases']}
            if not record['target_refs'] or not fact_ids or not fact_ids <= known or not used <= fact_ids:
                errors.append('Audit targets/fact IDs must be visible and cases must bind declared facts')
            if len(case_ids) != len(set(case_ids)):
                errors.append('Audit case IDs must be unique within a record')
            if record['coverage'] == 'exhaustive_for_listed_facts' and used != fact_ids:
                errors.append('Exhaustive audit omitted a declared fact')
            if record['existing_issue_id'] is not None and record['existing_issue_id'] not in self.issues:
                errors.append('Audit existing_issue_id is not visible')
        keys = [r['issue_id'] for r in value['closure_reviews']]
        if set(keys) != set(self.pending) or len(keys) != len(set(keys)):
            errors.append('Closure reviews must cover exactly the pending proposals once')
        for review in value['closure_reviews']:
            proposal = self.pending.get(review['issue_id'])
            if proposal is None:
                continue
            if (review['proposal_event_id'] != proposal['proposal_event_id'] or
                    set(review['response_to_objection_ids']) != set(proposal['response_to_objection_ids']) or
                    set(review['evidence_record_ids']) != set(proposal['evidence_record_ids'])):
                errors.append('Review does not bind the exact proposal, objections and original records')
            if not review['evidence_refs']:
                errors.append('Closure review requires visible evidence')
            if review['verdict'] == 'resolved':
                originals = self.issues[review['issue_id']].get('evidence_records', [])
                # A bad fact ID can itself be rebutted; do not require generating the
                # same invalid reference forever. The original record IDs still bind
                # the rebuttal, and a fresh valid audit of this issue remains required.
                required = {(c['fact_id'], c['input']) for row in originals for c in row['payload']['cases']
                            if c['fact_id'] in known}
                linked = [row for row in value['audit_records'] if row['existing_issue_id'] == review['issue_id']]
                rechecked = {(c['fact_id'], c['input']) for row in value['audit_records']
                             if row['existing_issue_id'] == review['issue_id'] for c in row['cases']}
                if (originals and not linked) or not required <= rechecked:
                    errors.append('Resolved requires an audit recheck of every original fact/input case')
        for issue in value['issues']:
            if issue['existing_issue_id'] is not None and issue['existing_issue_id'] not in self.issues:
                errors.append('Inspection issue references an invisible issue ID')
        return list(dict.fromkeys(errors))

    def _finding(self, record, event, outcome, original_issue_ids):
        key = record['payload']['existing_issue_id']
        if key not in original_issue_ids:
            key = None
        proposal = {'description': f'{outcome}: {record["payload"]["claim_text"]}', 'blocking': True,
                    'target_refs': copy.deepcopy(record['payload']['target_refs']), 'existing_issue_id': key,
                    'acceptance_condition': 'Repair or independently rebut the original audit cases and recheck the affected constraints.'}
        if key is None:
            key = f'i{len(self.issues)+1:04d}'
        self.proposed_issues([proposal], event['event_id'], self.issues)
        self.issues[key].setdefault('evidence_records', []).append(copy.deepcopy(record))
        self.issues[key]['status'] = 'open'
        return key

    def accept_inspection(self, value, actor, visible=None):
        self.contracts.validate('ClosureInspection', value)
        fingerprint = (self.version, actor, digest(value))
        if fingerprint in self._accepted:
            return self._accepted[fingerprint]
        # This append happens before business/reference validation or issue closure.
        event = self.emit('inspect', actor, value)
        visible = set(reference_index(self.view())) if visible is None else visible
        errors = self._inspection_errors(value, actor, visible)
        original_issue_ids = set(self.issues)
        contested = set()
        for n, payload in enumerate(value['audit_records'], 1):
            outcome = effective_outcome(payload)
            row = {'record_id': f'{event["event_id"]}:a{n:02d}', 'event_id': event['event_id'],
                   'auditor': actor, 'submitted_at': datetime.now(timezone.utc).isoformat(),
                   'candidate_version': value['candidate_version'], 'candidate_hash': value['candidate_hash'],
                   'payload': copy.deepcopy(payload), 'effective_outcome': outcome,
                   'validation_errors': copy.deepcopy(errors)}
            self.log('audit_ledger.jsonl', row)
            self.audit_ledger.append(copy.deepcopy(row))
            if outcome in {'finding_open', 'needs_check'}:
                contested.add(self._finding(row, event, outcome, original_issue_ids))
        for proposal in value['issues']:
            key = proposal['existing_issue_id']
            if key is not None and key not in original_issue_ids:
                continue
            if key is None:
                key = f'i{len(self.issues)+1:04d}'
            self.proposed_issues([proposal], event['event_id'], self.issues)
            contested.add(key)
        if errors:
            # Invalid references/roles remain visible as unresolved work, never a retry.
            self.proposed_issues([{'description': 'Audit validation: ' + '; '.join(errors), 'blocking': True,
                                  'target_refs': [self.current['source_event_id']], 'existing_issue_id': None,
                                  'acceptance_condition': 'Repeat an independent, correctly bound audit of the current candidate.'}],
                                 event['event_id'], self.issues)
        accepted = {'event': event, 'errors': errors, 'contested': contested}
        self._accepted[fingerprint] = accepted
        return accepted

    def validate_inspection(self, value):
        # Semantic conflicts are handled only after persistence in accept_inspection().
        self.contracts.validate('ClosureInspection', value)

    def settle(self, value, actor):
        accepted = self.accept_inspection(value, actor)
        event, errors, contested = accepted['event'], accepted['errors'], accepted['contested']
        reviews = {r['issue_id']: r for r in value['closure_reviews']}
        for key, proposal in self.pending.items():
            review = reviews.get(key)
            resolved = bool(review and review['verdict'] == 'resolved' and not errors and key not in contested)
            issue = self.issues[key]
            issue['status'] = proposal['disposition'] if resolved else 'open'
            issue['handling_events'].append({'version': self.version, 'review_event': event['event_id'],
                                            'proposal': copy.deepcopy(proposal), 'review': copy.deepcopy(review),
                                            'effective_verdict': 'resolved' if resolved else 'unresolved'})
        self.last_reviewed = None if errors else copy.deepcopy(self.current)
        self.log('reviews.jsonl', {'version': self.version, 'candidate_hash': digest(self.current['candidate']),
                                  'review_event': event['event_id'], 'validation_errors': errors,
                                  'contested_issue_ids': sorted(contested), 'issues': self.issues})
        self.pending = {}

    def run(self):
        result = super().run()
        result.update(protocol_variant='task_audit_v1', normal_call_cap=14, scheduler_cap=self.CAP,
                      task_facts=self.task_facts, audit_record_count=len(self.audit_ledger),
                      audit_open_issue_ids=[i['issue_id'] for i in self.blockers() if i.get('evidence_records')])
        write_json(self.directory / 'result.json', result)
        return result
