"""v4 apply boundary: visible audit citations and lossless compact repair requests."""
import copy
import json

from .closure_reference import ReferenceAuditRunner, closure_reference_contract
from .schemas import ProtocolError
from .state import reference_index
from .revision import check_refs

VARIANT = 'task_audit_delivery_v4'


def audit_reference_index(material):
    refs = set(reference_index(material))
    def walk(value):
        if isinstance(value, dict):
            # A complete stored record grants visibility; an ID string alone does not.
            required = {'record_id', 'event_id', 'auditor', 'candidate_version', 'candidate_hash',
                        'payload', 'effective_outcome', 'validation_errors'}
            if required <= value.keys() and isinstance(value['payload'], dict):
                refs.add(value['record_id'])
            for key, child in value.items():
                if key not in {'basis_refs', 'evidence_refs', 'target_refs', 'evidence_record_ids'}:
                    walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(material)
    return sorted(refs)


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def apply_prompt(system, instruction, actor, material, visible, previous=None, error=None):
    context = {'ACTOR': actor, 'MATERIAL': material, 'REFERENCE_INDEX': visible}
    if previous is not None:
        try: previous = json.loads(previous)
        except json.JSONDecodeError: pass
        context.update(PREVIOUS_OUTPUT=previous, STRUCTURAL_ERROR=error,
                       repair_rule='Return a complete corrected output. Preserve substantive reasoning, objections and original audit cases.')
    # Schema is supplied once in the API structured-output contract, not duplicated here.
    return system + '\n' + instruction + '\n' + compact(context)


class DeliveryAuditRunner(ReferenceAuditRunner):
    def call(self, stage, actor, schema_name, material, validate=None):
        if stage != 'apply':
            return super().call(stage, actor, schema_name, material, validate)
        if self.calls >= self.CAP - 1:
            raise ProtocolError('CALL_LIMIT', 'Fourteen logical stages exhausted')
        self.calls += 1
        material = {**copy.deepcopy(material), 'closure_reference_contract': closure_reference_contract(self.issues),
                    'change_tracking_policy': 'Runtime computes actual differences. changed_step_ids is advisory; differences do not prove resolution.'}
        visible = audit_reference_index(material)
        schema = self.contracts.schema(schema_name)
        limit = self.config['generation']['max_output_tokens'][stage]
        raw, error = None, None
        for attempt in range(2):
            prompt = apply_prompt(self.prompts['system'], self.prompts[stage], actor, material, visible, raw, error)
            payload = self.client.payload(prompt, schema, limit)
            size = self.client.size(payload)
            self.log('apply_budget.jsonl', {'attempt': attempt, 'estimated_input_count': size,
                     'configured_limit': self.config['generation']['max_input_tokens'],
                     'lossless_material': True, 'previous_output_included': raw is not None,
                     'repair_reserve_tokens': limit if attempt == 0 else 0})
            if size + (limit if attempt == 0 else 0) > self.config['generation']['max_input_tokens']:
                raise ProtocolError('CONTEXT_OVERFLOW', 'Lossless apply request exceeds configured input budget; no evidence removed, no request sent')
            raw = ''
            try:
                raw = self.client.complete(payload, deadline=self.deadline,
                                           logical_seed=f'{self.seed}|apply|{actor}|{self.calls}')
                self.log('apply_responses.jsonl', {'attempt': attempt, 'raw': raw})
                try: value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ProtocolError('INVALID_JSON', 'Output must be one JSON object') from exc
                self.contracts.validate(schema_name, value)
                check_refs(value, set(visible))
                self.check_targets(value, set(visible))
                for proposal in value.get('issues', []):
                    if proposal['existing_issue_id'] is not None and proposal['existing_issue_id'] not in self.issues:
                        raise ProtocolError('REFERENCE_ERROR', 'existing_issue_id must reference a visible issue')
                self.contracts.validate('Candidate', value['candidate'])
                if validate: validate(value)
                return value
            except ProtocolError as exc:
                self.log('validation.jsonl', {'stage': stage, 'code': exc.code, 'detail': exc.detail,
                                              'raw': raw, 'attempt': attempt})
                if (exc.code not in {'SCHEMA_ERROR', 'INVALID_JSON', 'REFERENCE_ERROR', 'INVALID_ACTION'}
                        or attempt or self.repairs >= self.config['protocol']['max_format_repairs']):
                    raise
                self.repairs += 1
                error = exc.detail
