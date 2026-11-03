"""Atomic submission of numeric local work; semantic selection stays with the model."""
import ast
import copy

from jsonschema import Draft202012Validator, ValidationError
from .engine import WorkSession, WorkError, obj, TEXT, META, numeric, expression_names


OPERAND = obj(dict(name=dict(type='string', pattern='^[a-zA-Z][a-zA-Z0-9_]*$'),
                   metadata=META, value=dict(type=['number', 'null']), result_id=dict(type=['string', 'null'])),
              required=['name'])
RECEIPT = obj(dict(target=TEXT, metadata=META, expression=TEXT,
                   inputs=dict(type='array', maxItems=6, items=OPERAND),
                   basis=dict(type='array', minItems=1, uniqueItems=True, items=TEXT),
                   conditions=dict(type='array', uniqueItems=True, items=TEXT),
                   replaces=dict(type=['string', 'null']),
                   expected_revision=dict(type=['integer', 'null'], minimum=1)),
              required=['target', 'metadata', 'expression', 'basis', 'conditions'])


class HandoffSession(WorkSession):
    def __init__(self, task):
        super().__init__(task)
        self.recipes = {}

    def packet(self, member, wave):
        packet = super().packet(member, wave)
        packet['receipts'] = [dict(id=key, owner=self.nodes[key]['owner'], revision=self.nodes[key]['revision'],
                                   **copy.deepcopy(recipe)) for key, recipe in self.recipes.items()]
        del packet['work']
        del packet['bindings']
        return packet

    def accept(self, member, receipt, packet):
        """One transaction: compile known numbers, register work and connect explicit references."""
        if packet.get('member') != member or packet.get('task') != dict(task_id=self.task['task_id'], question=self.task['question']):
            raise WorkError('receipt packet targets wrong member/task')
        Draft202012Validator(RECEIPT).validate(receipt)
        visible = {node['id']: node for node in packet['receipts']}
        allowed_sources = {source['id'] for source in packet['sources']}
        tree, names = expression_names(receipt['expression'])
        operands = receipt.get('inputs', [])
        declared = {operand['name']: operand for operand in operands}
        if len(declared) != len(operands) or set(declared) != names:
            raise WorkError('expression variables must match declared inputs exactly')
        constants, remaining, references = {}, [], {}
        for name, operand in declared.items():
            value, ref = operand.get('value'), operand.get('result_id')
            if value is not None and ref is not None:
                raise WorkError('operand cannot specify both value and result_id')
            if value is not None:
                numeric(value)
                constants[name] = value
                continue
            if 'metadata' not in operand:
                raise WorkError('unknown or referenced operand requires expected metadata')
            remaining.append(dict(name=name, metadata=copy.deepcopy(operand['metadata'])))
            if ref is not None:
                if ref not in visible:
                    raise WorkError('result reference outside saved receipt snapshot')
                if ref not in self.nodes or self.nodes[ref]['metadata'] != visible[ref]['metadata']:
                    raise WorkError('provider metadata changed since saved consumer snapshot')
                references[name] = ref

        class Substitute(ast.NodeTransformer):
            def visit_Name(self, node):
                return ast.copy_location(ast.Constant(value=constants[node.id]), node) if node.id in constants else node

        compiled = ast.unparse(ast.fix_missing_locations(Substitute().visit(tree)))
        item = dict(replaces=receipt.get('replaces'), expected_revision=receipt.get('expected_revision'),
                    target=receipt['target'], metadata=copy.deepcopy(receipt['metadata']), value=None,
                    expression=compiled, inputs=remaining, basis=copy.deepcopy(receipt['basis']),
                    conditions=copy.deepcopy(receipt['conditions']))
        trial = copy.deepcopy(self)
        key = trial.add(member, item, allowed_sources, set(visible))
        # A replacement is a complete operand declaration, not an implicit reuse of prior choices.
        for pair in list(trial.bindings):
            if pair[0] == key:
                del trial.bindings[pair]
        accepted_bindings = []
        for name, ref in references.items():
            trial.bind(member, key, trial.nodes[key]['revision'], name, ref)
            accepted_bindings.append(dict(status='accepted', work_id=key,
                                          expected_revision=trial.nodes[key]['revision'], input=name, result_id=ref))
        trial.recipes[key] = {name: copy.deepcopy(value) for name, value in receipt.items()
                              if name not in ('replaces', 'expected_revision')}
        trial.recompute()
        self.nodes, self.bindings, self.results = trial.nodes, trial.bindings, trial.results
        self.disclosed, self.recipes = trial.disclosed, trial.recipes
        return key, accepted_bindings

    def accept_many(self, member, receipts, packet):
        event = dict(accepted_work=[], bindings=[], notices=[])
        if not isinstance(receipts, list) or len(receipts) > 2:
            event['notices'].append(dict(kind='invalid_optional_receipts', raw=receipts))
            return event
        for receipt in receipts:
            try:
                key, bindings = self.accept(member, receipt, packet)
                event['accepted_work'].append(key)
                event['bindings'].extend(bindings)
            except (WorkError, ValidationError, TypeError) as exc:
                event['notices'].append(dict(kind='rejected_receipt', reason=str(exc), raw=receipt))
        return event
