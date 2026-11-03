"""v5: bounded inspection output and retained partial-response recovery."""
import copy
import json

from .audit_delivery import DeliveryAuditRunner, audit_reference_index, compact
from .closure_diff import candidate_diff
from .closure_format import FormatClosureClient
from .schemas import ProtocolError

VARIANT = 'task_audit_inspection_v5'
GUIDANCE = (
    'Prioritize decisive checks of the CURRENT candidate against original public constraints. '
    'Give each decisive calculation fully once in an audit_record; other fields may identify that '
    'record by its response-local ordinal for explanation only, not invent a stored record_id. '
    'Return every required closure_review and preserve every substantive objection and original '
    'case recheck. Do not duplicate the same derivation in checks, issues and closure_reviews. '
    'Old draft claims need checking only when they support the current candidate or an active objection. '
    'A concise response must still include complete evidence, cases, bindings and all schema fields. '
    'Do not suppress findings to save space; use the full available output budget when needed.'
)


class RecoveryClient(FormatClosureClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        transport = self.transport
        self.last_incomplete = None
        def capture(payload, timeout):
            response = transport(payload, timeout)
            if response.get('status') == 'incomplete':
                text = ''.join(p.get('text', '') for o in response.get('output', [])
                               if o.get('type') == 'message' for p in o.get('content', [])
                               if p.get('type') == 'output_text')
                self.last_incomplete = {'status': 'incomplete', 'details': response.get('incomplete_details'),
                                        'partial_output': text}
            return response
        self.transport = capture

    def complete(self, *args, **kwargs):
        self.last_incomplete = None
        return super().complete(*args, **kwargs)


def inspection_prompt(system, instruction, actor, material, visible, feedback=None):
    context = {'ACTOR': actor, 'MATERIAL': material, 'REFERENCE_INDEX': visible,
               'inspection_writing_policy': GUIDANCE}
    if feedback is not None:
        context['recovery_feedback'] = feedback
        context['recovery_rule'] = ('Previous output was not accepted. Return ONE complete schema-conforming JSON '
                                    'object, not a continuation. Preserve all substantive objections and decisive '
                                    'calculations from partial_output; remove repeated wording, never evidence.')
    return system + '\n' + instruction + '\n' + compact(context)


class InspectionRecoveryRunner(DeliveryAuditRunner):
    def call(self, stage, actor, schema_name, material, validate=None):
        if stage != 'inspect':
            return super().call(stage, actor, schema_name, material, validate)
        if self.calls >= self.CAP - 1:
            raise ProtocolError('CALL_LIMIT', 'Fourteen logical stages exhausted')
        self.calls += 1
        material = copy.deepcopy(material)
        material.pop('drafts', None)  # Same inspection visibility as frozen v1-v4.
        material['runtime_candidate_diff'] = candidate_diff(material['before']['candidate'], self.current['candidate'])
        material['closure_review_scope'] = {'allowed_pending_issue_ids': sorted(self.pending),
            'rule': 'closure_reviews covers exactly pending_closures; other objections belong in issues.'}
        schema = self.contracts.schema(schema_name)
        visible = audit_reference_index(material)
        limit = self.config['generation']['max_output_tokens']['inspect']
        feedback = None
        for attempt in range(2):
            prompt = inspection_prompt(self.prompts['system'], self.prompts['inspect'], actor, material, visible, feedback)
            payload = self.client.payload(prompt, schema, limit)
            size = self.client.size(payload)
            self.log('inspection_budget.jsonl', {'attempt': attempt, 'estimated_input_count': size,
                'configured_limit': self.config['generation']['max_input_tokens'], 'max_output_tokens': limit,
                'recovery_includes_previous': feedback is not None})
            if size > self.config['generation']['max_input_tokens']:
                raise ProtocolError('CONTEXT_OVERFLOW', 'Complete inspection/recovery input exceeds configured budget; no evidence dropped or request sent')
            raw = ''
            try:
                raw = self.client.complete(payload, deadline=self.deadline,
                                           logical_seed=f'{self.seed}|inspect|{actor}|{self.calls}')
                self.log('audit_responses.jsonl', {'stage': stage, 'actor': actor, 'raw': raw,
                                                  'logical_call': self.calls, 'attempt': attempt})
                try: value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ProtocolError('INVALID_JSON', 'Return one complete JSON object') from exc
                self.contracts.validate(schema_name, value)
                self.accept_inspection(value, actor, set(visible))
                return value
            except ProtocolError as exc:
                incomplete = getattr(self.client, 'last_incomplete', None)
                partial = incomplete['partial_output'] if incomplete else raw
                feedback = {'code': exc.code, 'detail': exc.detail, 'partial_output': partial,
                            'response_status': incomplete['status'] if incomplete else 'invalid_output',
                            'incomplete_details': incomplete['details'] if incomplete else None}
                self.log('inspection_recovery.jsonl', {'attempt': attempt, **feedback})
                self.log('validation.jsonl', {'stage': stage, 'code': exc.code, 'detail': exc.detail,
                                             'raw': partial, 'attempt': attempt})
                if (exc.code not in {'SCHEMA_ERROR', 'INVALID_JSON'} or attempt or
                        self.repairs >= self.config['protocol']['max_format_repairs']):
                    raise
                self.repairs += 1
