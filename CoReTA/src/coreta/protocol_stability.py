"""v6: bounded TaskFacts recovery across syntax and exact-source failures."""
import copy
import json

from .inspection_recovery import InspectionRecoveryRunner, RecoveryClient
from .task_audit_binding import FactBindingSession, source_registry
from .task_audit import TASK_FACTS_OUTPUT_TOKENS
from .schemas import ProtocolError
from .audit_delivery import compact

VARIANT = 'task_audit_stability_v6'


class StabilityClient(RecoveryClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        transport = self.transport
        self.last_output = ''
        def capture(payload, timeout):
            response = transport(payload, timeout)
            self.last_output = ''.join(p.get('text', '') for o in response.get('output', [])
                if o.get('type') == 'message' for p in o.get('content', []) if p.get('type') == 'output_text')
            return response
        self.transport = capture

    def complete(self, *args, **kwargs):
        self.last_output = ''
        return super().complete(*args, **kwargs)


class StabilityRunner(InspectionRecoveryRunner):
    def _bound_facts_call(self, actor):
        if self.calls >= self.CAP - 1:
            raise ProtocolError('CALL_LIMIT', 'Fourteen logical stages exhausted')
        self.calls += 1
        registry = source_registry(self.task)
        public = {'task': copy.deepcopy(self.task), 'source_registry': [
            {'source_id': key, 'public_field': row['public_field']} for key, row in registry.items()]}
        feedback = None
        limit = self.config['generation']['max_output_tokens'].get('task_facts', TASK_FACTS_OUTPUT_TOKENS)
        # No independent per-stage one-repair ceiling: the original global cap still applies.
        for attempt in range(self.config['protocol']['max_format_repairs'] + 1):
            repairing = self.fact_binding_session is not None
            name = 'TaskFactsPatch' if repairing else 'TaskFacts'
            schema = self.contracts.schema(name)
            material = copy.deepcopy(public)
            if repairing: material['binding_feedback'] = self.fact_binding_session.feedback()
            if feedback is not None: material['recovery_feedback'] = feedback
            prompt = self.prompts['system'] + '\n' + self.prompts['task_facts_repair' if repairing else 'task_facts']
            prompt += '\n' + compact({'ACTOR': actor, 'MATERIAL': material, 'REFERENCE_INDEX': []})
            payload = self.client.payload(prompt, schema, limit)
            size = self.client.size(payload)
            self.log('task_facts_budget.jsonl', {'attempt': attempt, 'schema': name,
                'estimated_input_count': size, 'remaining_global_repairs': self.config['protocol']['max_format_repairs']-self.repairs})
            if size > self.config['generation']['max_input_tokens']:
                raise ProtocolError('CONTEXT_OVERFLOW', 'TaskFacts recovery input exceeds budget; no evidence removed or request sent')
            raw = ''
            try:
                raw = self.client.complete(payload, deadline=self.deadline,
                    logical_seed=f'{self.seed}|task_facts|{actor}|{self.calls}')
                self.log('audit_responses.jsonl', {'stage': 'task_facts', 'actor': actor, 'raw': raw,
                    'logical_call': self.calls, 'attempt': attempt, 'schema': name})
                try: value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ProtocolError('INVALID_JSON', str(exc)) from exc
                self.contracts.validate(name, value)
                if repairing: self.fact_binding_session.apply_patch(value)
                else: self.fact_binding_session = FactBindingSession(self.task, value)
                self._binding_snapshot(attempt)
                bound = self.fact_binding_session.bound_payload()
                self.contracts.validate('BoundTaskFacts', bound)
                return bound
            except ProtocolError as exc:
                raw = raw or getattr(self.client, 'last_output', '')
                feedback = {'code': exc.code, 'detail': exc.detail, 'previous_output': raw,
                            'response_incomplete': copy.deepcopy(getattr(self.client, 'last_incomplete', None))}
                self.log('validation.jsonl', {'stage': 'task_facts', 'code': exc.code, 'detail': exc.detail,
                                             'raw': raw, 'attempt': attempt, 'schema': name})
                if (exc.code not in {'SCHEMA_ERROR', 'INVALID_JSON', 'REFERENCE_ERROR'} or
                        self.repairs >= self.config['protocol']['max_format_repairs']):
                    raise
                self.repairs += 1
