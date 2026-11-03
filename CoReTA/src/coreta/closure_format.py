"""Exact inspection field guidance and positional JSON repair diagnostics."""
import json
from .closure import ClosureClient
from .closure_diff import DiffClosureRunner
from .schemas import ProtocolError


def inspection_field_guide(schema):
    guide = {'root': list(schema['properties'])}
    for name in ('checks', 'issues', 'closure_reviews'):
        row = schema['properties'][name]['items']
        guide[name + '[]'] = list(row['properties'])
    return guide


class FormatClosureRunner(DiffClosureRunner):
    def call(self, stage, actor, schema_name, material, validate=None):
        if schema_name == 'ClosureInspection':
            material = {**material, 'inspection_output_contract': {
                'exact_field_names': inspection_field_guide(self.contracts.schema(schema_name)),
                'rules': 'Return one complete JSON object without code fences or trailing text. '
                'Use exactly the fields for each record type. checks requires scope; closure_reviews has no scope. '
                'Neither record type allows check_id. Put all substantive reasoning in method/observation '
                'and objections in issues; do not omit objections to satisfy formatting. '
                'Use proper JSON commas, quotes and escaped backslashes. This field guide is input only.'}}
        return super().call(stage, actor, schema_name, material, validate)


class FormatClosureClient(ClosureClient):
    def complete(self, *args, **kwargs):
        raw = super().complete(*args, **kwargs)
        try:
            json.loads(raw)
        except json.JSONDecodeError as exc:
            self.log('json_diagnostics.jsonl', {'message': exc.msg, 'line': exc.lineno,
                'column': exc.colno, 'offset': exc.pos, 'raw_output': raw})
            raise ProtocolError('INVALID_JSON',
                f'JSON syntax: {exc.msg}; line={exc.lineno}, column={exc.colno}, offset={exc.pos}. '
                'Repair the syntax and recheck the complete object against OUTPUT_SCHEMA. '
                'Keep all substantive observations and objections; do not add fields from another record type.') from exc
        return raw
