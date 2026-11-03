"""v2: exact source binding, locked successful facts, declared-item coverage.

The frozen v1 runner remains unchanged. Binding establishes provenance only;
interpretations and the completeness of extracted check items remain model claims.
"""
from __future__ import annotations

import copy
import json

from .revision import array, choice, obj, text
from .schemas import ProtocolError
from .state import write_json
from .task_audit import AuditClosureRunner, AuditContracts, TASK_FACTS_OUTPUT_TOKENS


VERSION = 'coreta/0.7-source-binding'
VARIANT = 'task_audit_binding_v2'


def source_registry(task):
    registry = {'prompt': {'public_field': '/prompt', 'text': task['prompt']}}
    if task['task_type'] == 'code' and isinstance(task.get('entry_point'), str) and task['entry_point']:
        registry['entry_point'] = {'public_field': '/entry_point', 'text': task['entry_point']}
    return registry


def bind_quote(registry, source_id, quote):
    """No normalization, fuzzy matching, first-match selection or model offsets."""
    source = registry.get(source_id)
    if source is None:
        return {'status': 'unknown_source', 'source_id': source_id, 'match_count': 0, 'candidate_spans': []}
    if not quote:
        return {'status': 'unmatched', 'source_id': source_id, 'match_count': 0, 'candidate_spans': []}
    spans, count = [], 0
    start = source['text'].find(quote)
    while start != -1:
        count += 1
        if len(spans) < 8:
            spans.append({'start': start, 'end': start + len(quote)})
        start = source['text'].find(quote, start + 1)
    result = {'status': 'unique_exact' if count == 1 else 'ambiguous' if count else 'unmatched',
              'source_id': source_id, 'public_field': source['public_field'],
              'coordinate_space': 'source_unicode_codepoints', 'match_count': count, 'candidate_spans': spans}
    if count == 1:
        result.update(spans[0])
    return result


class SourceBindingContracts(AuditContracts):
    def __init__(self, path):
        super().__init__(path)
        defs = self.document['$defs']
        item = obj(item_id=text(80), description=text(1200))
        fact = obj(fact_id=text(40), source_id=choice('prompt', 'entry_point'), quoted_text=text(2000),
                   normalized_fact=text(1000), kind=choice('constraint', 'objective', 'domain', 'ambiguity'),
                   check_items={**array(item, 32), 'minItems': 1})
        defs['TaskFacts'] = obj(facts={**array(fact, 32), 'minItems': 1},
                                coverage_status=choice('partial', 'unknown'))
        patch = obj(fact_id=text(40), source_id=choice('prompt', 'entry_point'), quoted_text=text(2000))
        defs['TaskFactsPatch'] = obj(replacements={**array(patch, 32), 'minItems': 1})
        binding = obj(status={'const': 'unique_exact'}, source_id=choice('prompt', 'entry_point'),
                      public_field=choice('/prompt', '/entry_point'),
                      coordinate_space={'const': 'source_unicode_codepoints'},
                      start={'type': 'integer', 'minimum': 0}, end={'type': 'integer', 'minimum': 1})
        bound_fact = copy.deepcopy(fact)
        bound_fact['properties']['source_binding'] = binding
        bound_fact['required'].append('source_binding')
        bound_fact['properties']['semantic_status'] = {'const': 'model_asserted'}
        bound_fact['required'].append('semantic_status')
        defs['BoundTaskFacts'] = obj(facts={**array(bound_fact, 32), 'minItems': 1},
                                     coverage_status=choice('partial', 'unknown'),
                                     binding_status={'const': 'all_sources_bound'},
                                     semantic_status={'const': 'model_asserted'})
        records = defs['ClosureInspection']['properties']['audit_records']['items']
        records['properties']['check_item_ids'] = {**array(text(80), 128), 'minItems': 1}
        records['required'].append('check_item_ids')
        records['properties']['coverage'] = choice('all_declared_items', 'sampled', 'unable')
        case = records['properties']['cases']['items']
        case['properties']['check_item_id'] = text(80)
        case['required'].append('check_item_id')
        defs['Event']['properties']['schema_version'] = {'const': VERSION}
        defs['Event']['properties']['payload']['anyOf'].append({'$ref': '#/$defs/BoundTaskFacts'})
        self.document['$id'] = 'https://example.invalid/coreta/design/0.7-source-binding/schema.json'
        self.document['title'] = 'CoReTA source-bound facts and declared-item coverage'


class FactBindingSession:
    """Append history; repair only unresolved quotes, never delete a declared condition."""
    def __init__(self, task, payload):
        self.registry = source_registry(task)
        facts = payload['facts']
        fact_ids = [f['fact_id'] for f in facts]
        item_ids = [i['item_id'] for f in facts for i in f['check_items']]
        if len(set(fact_ids)) != len(fact_ids) or len(set(item_ids)) != len(item_ids):
            raise ProtocolError('REFERENCE_ERROR', 'Fact IDs and check-item IDs must each be globally unique')
        if len(item_ids) > 128:
            raise ProtocolError('REFERENCE_ERROR', 'At most 128 declared check items are allowed')
        self.original_payload = copy.deepcopy(payload)
        self.current = {f['fact_id']: copy.deepcopy(f) for f in facts}
        self.bindings = {}
        self.history = []
        self._resolve(list(self.current))

    def _resolve(self, ids):
        for key in ids:
            fact = self.current[key]
            self.bindings[key] = bind_quote(self.registry, fact['source_id'], fact['quoted_text'])
        self.history.append(self.snapshot(include_history=False))

    @property
    def pending(self):
        return [key for key, value in self.bindings.items() if value['status'] != 'unique_exact']

    def feedback(self):
        return {'locked_fact_ids': [key for key in self.current if key not in self.pending],
                'unresolved': [{'fact_id': key, 'source_id': self.current[key]['source_id'],
                                'quoted_text': self.current[key]['quoted_text'], **self.bindings[key]}
                               for key in self.pending],
                'repair_rule': 'Replace source_id/quoted_text for every unresolved ID exactly once. '
                               'Do not return locked facts, new facts, offsets, paths, interpretations or check items. '
                               'For ambiguous quotes include more exact context; for unmatched quotes copy exact source text.'}

    def apply_patch(self, patch):
        rows = patch['replacements']
        ids = [row['fact_id'] for row in rows]
        if len(ids) != len(set(ids)) or set(ids) != set(self.pending):
            raise ProtocolError('REFERENCE_ERROR',
                                'Repair must replace exactly all unresolved fact IDs once; locked facts cannot change')
        # Validate all IDs before applying any replacement; accepted meanings/items stay locked.
        for row in rows:
            self.current[row['fact_id']].update(source_id=row['source_id'], quoted_text=row['quoted_text'])
        self._resolve(ids)

    def snapshot(self, include_history=True):
        result = {'original_payload': copy.deepcopy(self.original_payload),
                  'current_facts': copy.deepcopy(list(self.current.values())),
                  'bindings': copy.deepcopy(self.bindings), 'pending_fact_ids': self.pending,
                  'semantic_status': 'model_asserted'}
        if include_history:
            result['history'] = copy.deepcopy(self.history)
        return result

    def bound_payload(self):
        if self.pending:
            raise ProtocolError('REFERENCE_ERROR', 'Unresolved source bindings: ' + ', '.join(self.pending))
        facts = []
        for key, fact in self.current.items():
            binding = self.bindings[key]
            location = {name: binding[name] for name in ('status', 'source_id', 'public_field',
                                                        'coordinate_space', 'start', 'end')}
            facts.append({**copy.deepcopy(fact), 'source_binding': location, 'semantic_status': 'model_asserted'})
        return {'facts': facts, 'coverage_status': self.original_payload['coverage_status'],
                'binding_status': 'all_sources_bound', 'semantic_status': 'model_asserted'}


class SourceBoundAuditRunner(AuditClosureRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fact_binding_session = None
        self._coverage_logged = set()

    def emit(self, stage, actor, payload):
        event = {'event_id': f'{self.run_id}:e{len(self.events):04d}', 'schema_version': VERSION,
                 'sent_from': actor, 'base_version': self.version, 'stage': stage,
                 'task_id': self.task['task_id'], 'payload': copy.deepcopy(payload)}
        self.contracts.validate('Event', event)
        self.log('events.jsonl', event)
        self.events.append(event)
        return event

    def call(self, stage, actor, schema_name, material, validate=None):
        if stage == 'task_facts':
            return self._bound_facts_call(actor)
        return super().call(stage, actor, schema_name, material, validate)

    def _binding_snapshot(self, attempt):
        snapshot = {'attempt': attempt, **self.fact_binding_session.snapshot()}
        self.log('source_bindings.jsonl', snapshot)
        write_json(self.directory / 'source_binding_state.json', snapshot)

    def _bound_facts_call(self, actor):
        if self.calls >= self.CAP - 1:
            raise ProtocolError('CALL_LIMIT', 'Fourteen logical stages exhausted')
        self.calls += 1
        registry = source_registry(self.task)
        public = {'task': copy.deepcopy(self.task), 'source_registry': [
            {'source_id': key, 'public_field': row['public_field']} for key, row in registry.items()]}
        feedback = None
        previous_raw = ''
        limit = self.config['generation']['max_output_tokens'].get('task_facts', TASK_FACTS_OUTPUT_TOKENS)
        for attempt in range(2):
            repairing = self.fact_binding_session is not None
            schema_name = 'TaskFactsPatch' if repairing else 'TaskFacts'
            schema = self.contracts.schema(schema_name)
            material = {**public}
            if repairing:
                material['binding_feedback'] = self.fact_binding_session.feedback()
            elif feedback:
                material.update(structural_error=feedback, previous_output=previous_raw)
            prompt = self.prompts['system'] + '\n' + self.prompts['task_facts_repair' if repairing else 'task_facts']
            prompt += '\n' + json.dumps({'ACTOR': actor, 'MATERIAL': material, 'REFERENCE_INDEX': [],
                                         'OUTPUT_SCHEMA': schema}, ensure_ascii=False)
            raw = ''
            try:
                raw = self.client.complete(self.client.payload(prompt, schema, limit), deadline=self.deadline,
                                           logical_seed=f'{self.seed}|task_facts|{actor}|{self.calls}')
                self.log('audit_responses.jsonl', {'stage': 'task_facts', 'actor': actor, 'raw': raw,
                                                   'logical_call': self.calls, 'attempt': attempt, 'schema': schema_name})
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ProtocolError('INVALID_JSON', 'Return one complete JSON object') from exc
                self.contracts.validate(schema_name, value)
                if repairing:
                    self.fact_binding_session.apply_patch(value)
                else:
                    self.fact_binding_session = FactBindingSession(self.task, value)
                self._binding_snapshot(attempt)
                bound = self.fact_binding_session.bound_payload()
                self.contracts.validate('BoundTaskFacts', bound)
                return bound
            except ProtocolError as exc:
                self.log('validation.jsonl', {'stage': 'task_facts', 'code': exc.code, 'detail': exc.detail,
                                              'raw': raw, 'attempt': attempt, 'schema': schema_name})
                if (exc.code not in {'SCHEMA_ERROR', 'INVALID_JSON', 'REFERENCE_ERROR'} or attempt or
                        self.repairs >= self.config['protocol']['max_format_repairs']):
                    raise
                self.repairs += 1
                feedback, previous_raw = exc.detail, raw

    def _items(self):
        facts = self.task_facts['payload']['facts'] if self.task_facts else []
        return {item['item_id']: fact['fact_id'] for fact in facts for item in fact['check_items']}

    def _inspection_errors(self, value, actor, visible):
        errors = super()._inspection_errors(value, actor, visible)
        items = self._items()
        for record in value['audit_records']:
            declared = record['check_item_ids']
            tested = {c['check_item_id'] for c in record['cases']}
            available = {key for key, fact_id in items.items() if fact_id in record['task_fact_ids']}
            if len(declared) != len(set(declared)) or not set(declared) <= available:
                errors.append('Audit check-item IDs must be unique and belong to its declared facts')
            if tested != set(declared):
                errors.append('Every declared check item requires an explicit case; one case cannot cover sibling items')
            if any(items.get(c['check_item_id']) != c['fact_id'] for c in record['cases']):
                errors.append('Audit case check-item/fact association is invalid')
            if record['coverage'] == 'all_declared_items' and (set(declared) != available or tested != available):
                errors.append('all_declared_items requires cases for every declared item inside the referenced facts')
        for review in value['closure_reviews']:
            if review['verdict'] != 'resolved' or review['issue_id'] not in self.pending:
                continue
            originals = self.issues[review['issue_id']].get('evidence_records', [])
            required = {(c['check_item_id'], c['input']) for row in originals for c in row['payload']['cases']
                        if c['check_item_id'] in items}
            actual = {(c['check_item_id'], c['input']) for row in value['audit_records']
                      if row['existing_issue_id'] == review['issue_id'] for c in row['cases']}
            if not required <= actual:
                errors.append('Closure must recheck the original check-item/input pairs')
        return list(dict.fromkeys(errors))

    def accept_inspection(self, value, actor, visible=None):
        accepted = super().accept_inspection(value, actor, visible)
        event_id = accepted['event']['event_id']
        if event_id not in self._coverage_logged:
            items = self._items()
            for number, record in enumerate(value['audit_records'], 1):
                available = {key for key, fact in items.items() if fact in record['task_fact_ids']}
                tested = {case['check_item_id'] for case in record['cases']}
                self.log('item_coverage.jsonl', {
                    'record_id': f'{event_id}:a{number:02d}', 'model_coverage': record['coverage'],
                    'available_declared_item_ids': sorted(available), 'case_item_ids': sorted(tested),
                    'all_declared_items_mentioned': tested == available,
                    'task_exhaustiveness_proven': False, 'semantic_status': 'model_asserted',
                    'validation_errors': accepted['errors']})
            self._coverage_logged.add(event_id)
        return accepted

    def run(self):
        result = super().run()
        inspected = any(e['stage'] == 'inspect' for e in self.events)
        result.update(protocol_variant=VARIANT,
                      source_bindings_complete=bool(self.task_facts),
                      declared_check_item_count=len(self._items()),
                      pipeline_completed=result['status'] == 'completed' and inspected,
                      mechanism_evaluable=any(not row['validation_errors'] for row in self.audit_ledger))
        write_json(self.directory / 'result.json', result)
        return result
