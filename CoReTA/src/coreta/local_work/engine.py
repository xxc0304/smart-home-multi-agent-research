"""Continue bounded numeric local work. Executes declared mappings, not semantics."""
from __future__ import annotations

import ast
import copy
import json
import math
import operator
from decimal import Decimal, InvalidOperation

from jsonschema import Draft202012Validator, ValidationError
from coreta.handoff.contracts import HandoffContracts
from coreta.schemas import ProtocolError


class WorkError(ValueError):
    pass


def obj(properties, required=None):
    return dict(type='object', properties=properties, required=list(properties) if required is None else required,
                additionalProperties=False)


TEXT = dict(type='string', minLength=1)
META = obj(dict(subject=TEXT, unit=TEXT, period=TEXT))
INPUT = obj(dict(name=dict(type='string', pattern='^[a-zA-Z][a-zA-Z0-9_]*$'), metadata=META))
WORK_SCHEMA = obj(dict(
    replaces=dict(type=['string', 'null']), expected_revision=dict(type=['integer', 'null'], minimum=1),
    target=TEXT, metadata=META, value=dict(type=['number', 'null']),
    expression=dict(type=['string', 'null']), inputs=dict(type='array', maxItems=6, items=INPUT),
    basis=dict(type='array', minItems=1, uniqueItems=True, items=TEXT),
    conditions=dict(type='array', uniqueItems=True, items=TEXT)))
BINDING_SCHEMA = obj(dict(work_id=TEXT, expected_revision=dict(type='integer', minimum=1),
                          input=TEXT, result_id=dict(type=['string', 'null'])))
CORE_SCHEMA = obj(dict(message=TEXT, work=dict(type='array', maxItems=2)), required=['message', 'work'])
RESPONSE_SCHEMA = copy.deepcopy(CORE_SCHEMA)
RESPONSE_SCHEMA['properties']['work']['items'] = WORK_SCHEMA
RESPONSE_SCHEMA['properties']['bindings'] = dict(type='array', maxItems=6, items=BINDING_SCHEMA)


def numeric(value):
    if type(value) not in (int, float):
        raise WorkError('value must be a finite number, not bool or null')
    result = Decimal(str(value))
    if not result.is_finite():
        raise WorkError('value must be a finite number')
    return result


def expression_names(expression):
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 512:
        raise WorkError('expression must be nonblank, at most 512 characters')
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError as exc:
        raise WorkError('invalid arithmetic expression') from exc
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Name, ast.Load, ast.Constant,
               ast.Add, ast.Sub, ast.Mult, ast.Div, ast.UAdd, ast.USub)
    nodes = list(ast.walk(tree))
    if len(nodes) > 80 or any(not isinstance(n, allowed) for n in nodes):
        raise WorkError('only bounded arithmetic + - * / is supported')
    for node in nodes:
        if isinstance(node, ast.Constant):
            numeric(node.value)
    return tree, {n.id for n in nodes if isinstance(n, ast.Name)}


def calculate(expression, values):
    tree, names = expression_names(expression)
    if names != set(values):
        raise WorkError('expression names and inputs do not match')
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}

    def visit(node):
        if isinstance(node, ast.Constant):
            return numeric(node.value)
        if isinstance(node, ast.Name):
            return numeric(values[node.id])
        if isinstance(node, ast.UnaryOp):
            return -visit(node.operand) if isinstance(node.op, ast.USub) else visit(node.operand)
        if isinstance(node, ast.BinOp):
            return operations[type(node.op)](visit(node.left), visit(node.right))
        raise WorkError('unsupported arithmetic node')
    try:
        value = float(visit(tree.body))
    except (ArithmeticError, InvalidOperation, OverflowError) as exc:
        raise WorkError('arithmetic execution failed: ' + type(exc).__name__) from exc
    if not math.isfinite(value):
        raise WorkError('non-finite arithmetic result')
    return value


class WorkSession:
    def __init__(self, task):
        self.task = copy.deepcopy(task)
        self.members = list(task['members'])
        if len(set(self.members)) != len(self.members) or not self.members:
            raise WorkError('invalid members')
        self.sources = {s['id']: copy.deepcopy(s) for s in task['sources']}
        if len(self.sources) != len(task['sources']) or 'TASK' in self.sources:
            raise WorkError('source IDs must be unique, TASK reserved')
        if any(s['owner'] not in self.members + ['public'] for s in self.sources.values()):
            raise WorkError('unknown source owner')
        self.sources['TASK'] = dict(id='TASK', owner='public', kind='task', content=task['question'])
        self.disclosed = {sid for sid, s in self.sources.items() if s['owner'] == 'public'}
        self.nodes = {}
        self.bindings = {}
        self.events = []
        self.results = {}

    def packet(self, member, wave):
        if member not in self.members:
            raise WorkError('unknown member')
        visible = [copy.deepcopy(s) for sid, s in self.sources.items()
                   if sid in self.disclosed or s['owner'] == member]
        return dict(task=dict(task_id=self.task['task_id'], question=self.task['question']),
                    member=member, wave=wave, sources=visible,
                    work=copy.deepcopy(list(self.nodes.values())),
                    results=copy.deepcopy(self.results), bindings=copy.deepcopy(self.binding_rows()))

    def binding_rows(self):
        return [dict(work_id=w, input=i, **copy.deepcopy(value)) for (w, i), value in self.bindings.items()]

    def apply(self, member, raw, packet):
        """Admit a reply against its saved request snapshot; retain every rejection."""
        event = dict(member=member, raw=raw, accepted_work=[], notices=[], bindings=[])
        try:
            value = HandoffContracts.decode(raw, dict(type='object'))
            core = {k: value[k] for k in ('message', 'work') if k in value}
            HandoffContracts.decode(json.dumps(core, allow_nan=False), CORE_SCHEMA)
            if not core['message'].strip():
                raise WorkError('blank message')
        except (ProtocolError, ValueError, TypeError, AttributeError, OverflowError) as exc:
            event.update(status='unreadable_core', error=str(exc))
            self.events.append(event)
            return event
        if packet.get('member') != member or packet.get('task') != dict(task_id=self.task['task_id'], question=self.task['question']):
            raise WorkError('reply packet targets wrong member/task')
        allowed_sources = {s['id'] for s in packet['sources']}
        snapshot_work = {w['id']: w for w in packet['work']}
        visible_work = set(snapshot_work)
        event.update(status='readable', message=core['message'])
        for item in core['work']:
            try:
                key = self.add(member, item, allowed_sources, visible_work)
                event['accepted_work'].append(key)
            except (WorkError, ValidationError, TypeError) as exc:
                event['notices'].append(dict(kind='rejected_work', reason=str(exc), raw=item))
        proposals = value.get('bindings', [])
        if not isinstance(proposals, list) or len(proposals) > 6:
            event['notices'].append(dict(kind='invalid_optional_bindings', raw=proposals))
            proposals = []
        for proposal in proposals:
            try:
                Draft202012Validator(BINDING_SCHEMA).validate(proposal)
                if proposal['work_id'] not in visible_work or (proposal['result_id'] is not None and proposal['result_id'] not in visible_work):
                    raise WorkError('binding refers outside saved work snapshot')
                provider = proposal['result_id']
                if provider is not None and self.nodes[provider]['metadata'] != snapshot_work[provider]['metadata']:
                    raise WorkError('provider metadata changed since saved consumer snapshot')
                self.bind(member, **proposal)
                event['bindings'].append(dict(status='accepted', **proposal))
            except (WorkError, ValidationError, TypeError) as exc:
                event['notices'].append(dict(kind='rejected_binding', reason=str(exc), raw=proposal))
        extras = sorted(set(value) - {'message', 'work', 'bindings'})
        if extras:
            event['notices'].append(dict(kind='extra_annotations_retained_in_raw', fields=extras))
        self.recompute()
        self.events.append(event)
        return event

    def add(self, member, item, allowed_sources, visible_work):
        Draft202012Validator(WORK_SCHEMA).validate(item)
        if not set(item['basis']) <= allowed_sources:
            raise WorkError('source outside saved visibility')
        names = [i['name'] for i in item['inputs']]
        if len(names) != len(set(names)):
            raise WorkError('duplicate input name')
        if item['expression'] is None:
            numeric(item['value'])
            if names:
                raise WorkError('literal cannot have inputs')
        else:
            if item['value'] is not None:
                raise WorkError('operation cannot also assert a value')
            _, expected = expression_names(item['expression'])
            if expected != set(names):
                raise WorkError('expression variables must match declared inputs')
        old = item['replaces']
        previous_inputs = {}
        if old is not None:
            if old not in visible_work or old not in self.nodes:
                raise WorkError('unknown replacement work')
            previous = self.nodes[old]
            if previous['owner'] != member or item['expected_revision'] != previous['revision']:
                raise WorkError('replacement owner/revision mismatch')
            key, revision = old, previous['revision'] + 1
            previous_inputs = {i['name']: i['metadata'] for i in previous['inputs']}
        else:
            if item['expected_revision'] is not None:
                raise WorkError('new work must have null expected_revision')
            key, revision = f'W{len(self.nodes)+1}', 1
        node = {k: copy.deepcopy(v) for k, v in item.items() if k not in ('replaces', 'expected_revision')}
        self.nodes[key] = dict(id=key, owner=member, revision=revision, **node)
        # A local formula/condition correction preserves unchanged input meanings.
        current_inputs = {i['name']: i['metadata'] for i in item['inputs']}
        for pair in list(self.bindings):
            if pair[0] == key and (pair[1] not in current_inputs or
                                   current_inputs[pair[1]] != previous_inputs.get(pair[1])):
                del self.bindings[pair]
        self.disclosed.update(item['basis'])
        return key

    def bind(self, member, work_id, expected_revision, input, result_id):
        node = self.nodes[work_id]
        if node['owner'] != member or node['revision'] != expected_revision:
            raise WorkError('binding owner/revision mismatch')
        slots = {i['name']: i for i in node['inputs']}
        if input not in slots:
            raise WorkError('unknown input slot')
        if result_id is None:
            self.bindings.pop((work_id, input), None)
            return
        if result_id not in self.nodes:
            raise WorkError('unknown result work')
        provided = self.nodes[result_id]['metadata']
        if any(slots[input]['metadata'][field] != provided[field] for field in ('unit', 'period')):
            raise WorkError('declared unit/period mismatch')
        # Check cycles before publishing the edge.
        def reaches(start, goal, seen):
            if start == goal:
                return True
            if start in seen:
                return False
            seen.add(start)
            return any(reaches(b['result_id'], goal, seen) for (w, _), b in self.bindings.items() if w == start)
        if reaches(result_id, work_id, set()):
            raise WorkError('cyclic self-support')
        self.bindings[(work_id, input)] = dict(result_id=result_id, metadata=copy.deepcopy(provided))

    def recompute(self):
        result = {}

        def evaluate(key):
            if key in result:
                return result[key]
            node = self.nodes[key]
            conditions = set(node['conditions'])
            sources = set(node['basis'])
            waiting, values = [], {}
            for slot in node['inputs']:
                name = slot['name']
                binding = self.bindings.get((key, name))
                if binding is None:
                    waiting.append(dict(input=name, reason='missing_binding'))
                    continue
                provider = self.nodes[binding['result_id']]
                if provider['metadata'] != binding['metadata'] or any(
                        provider['metadata'][field] != slot['metadata'][field] for field in ('unit', 'period')):
                    waiting.append(dict(input=name, reason='changed_metadata'))
                    continue
                upstream = evaluate(binding['result_id'])
                if upstream['status'] != 'ready':
                    waiting.append(dict(input=name, reason='upstream_not_ready'))
                    continue
                values[name] = upstream['value']
                conditions.update(upstream['conditions'])
                sources.update(upstream['sources'])
            if waiting:
                row = dict(status='waiting', value=None, missing=waiting)
            else:
                try:
                    value = node['value'] if node['expression'] is None else calculate(node['expression'], values)
                    row = dict(status='ready', value=value, missing=[])
                except WorkError as exc:
                    row = dict(status='execution_error', value=None, error=str(exc), missing=[])
            result[key] = dict(**row, revision=node['revision'], metadata=copy.deepcopy(node['metadata']),
                               conditions=sorted(conditions), sources=sorted(sources),
                               truth_status='model_declared_not_semantically_verified')
            return result[key]
        for key in self.nodes:
            evaluate(key)
        self.results = result
        return copy.deepcopy(result)

    def deliver(self, raw, packet):
        schema = obj(dict(answer=dict(type=['number', 'string', 'null']),
                          result_id=dict(type=['string', 'null']), scale=dict(type='string'), reasoning=TEXT))
        value = HandoffContracts.decode(raw, schema)
        if not value['reasoning'].strip():
            raise WorkError('blank final reasoning')
        supplied = value['answer']
        if supplied is not None and (type(supplied) is not str):
            numeric(supplied)
        output = dict(model_answer=copy.deepcopy(value), delivered=copy.deepcopy(value),
                      delivery_mode='best_effort', conditions=[], notices=[])
        key = value['result_id']
        if key is not None:
            frozen = packet['results'].get(key)
            if not frozen or frozen['status'] != 'ready':
                output['notices'].append('unavailable_result_reference; explicit answer retained')
            else:
                output['delivered']['answer'] = frozen['value']
                output['conditions'] = list(frozen['conditions'])
                output['delivery_mode'] = 'explicit_result_reference'
        if output['delivered']['answer'] is None:
            output['notices'].append('model_nonanswer_not_host_override')
        return output
