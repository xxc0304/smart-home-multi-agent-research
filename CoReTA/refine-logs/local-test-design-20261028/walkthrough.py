"""Analyst-assisted replay of existing formulas, NOT automatic test generation."""
from decimal import Decimal as D
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
FLOW = ROOT / 'runs/local-work-handoff-confirm-live-20261027-v1/flows/dependent-02-local_work-r1'
SOURCE = FLOW / 'requests/03-A2.json'
packet = json.loads(SOURCE.read_text(encoding='utf-8'))['packet']
nodes = {node['id']: node for node in packet['receipts']}
source_cells = {}
# The analyst selected row14/header1 by reading this historical example.
# This only authenticates that explicit selection; it is not automatic row discovery.
for source in packet['sources']:
    if source['id'] not in ('T1', 'T2'):
        continue
    table = json.loads(source['content'])
    assert table[14][0] == 'Total equity'
    for column in range(1, len(table[1])):
        year = table[1][column]
        source_cells[year] = {'source_id': source['id'], 'row': 14, 'column': column,
                              'year_header_row': 1, 'original_value': table[14][column],
                              'numeric_value': str(D(table[14][column].replace(',', '')))}
bindings = {}
for key in ('W1', 'W2'):
    for slot in nodes[key]['inputs']:
        match = re.fullmatch(r'e(20\d{2})', slot['name'])
        assert match is not None
        year = match.group(1)
        cell = source_cells[year]
        assert D(str(slot['value'])) == D(cell['numeric_value'])
        bindings[(key, slot['name'])] = dict(year=year, **cell)
ops = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
       ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b}


def calculate(expression, variables):
    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return D(str(node.value))
        if isinstance(node, ast.Name):
            return variables[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -visit(node.operand)
        raise ValueError('Unsupported expression')
    return visit(ast.parse(expression, mode='eval'))


def work(key, changed_year=None, amount=D(0)):
    node = nodes[key]
    values = {}
    for slot in node['inputs']:
        if 'result_id' in slot:
            values[slot['name']] = work(slot['result_id'], changed_year, amount)
        else:
            value = D(str(slot['value']))
            # Mutate all occurrences tied to the SAME actual source cell, not a
            # metadata string. The mapping above remains analyst-assisted.
            binding = bindings[(key, slot['name'])]
            if binding['year'] == changed_year:
                value += amount
            values[slot['name']] = value
    return calculate(node['expression'], values) if node['expression'] else D(str(node['value']))


baseline = {key: work(key) for key in ('W2', 'W3')}
assert baseline == {'W2': D('659439.4'), 'W3': D('690221.04')}
trials = []
for year in ('2015', '2016', '2017', '2018', '2019'):
    deltas = {key: work(key, year, D(100)) - baseline[key] for key in baseline}
    trials.append({'changed_year': year, 'increase': 100,
                   'observed_deltas': {key: str(value) for key, value in deltas.items()},
                   'manually_grounded_five_year_mean_expected_delta': '20',
                   'violates_this_property': {key: value != D(20) for key, value in deltas.items()}})
assert {key: D(value) for key, value in trials[-1]['observed_deltas'].items()} == {'W2': D(20), 'W3': D(32)}
assert {key: D(value) for key, value in trials[0]['observed_deltas'].items()} == {'W2': D(20), 'W3': D(12)}

# A bad property copied from the wrong dependency reverses selection.
bad_expected = D(32)
bad_property = {key: work(key, '2019', D(100)) - baseline[key] == bad_expected
                for key in baseline}
assert bad_property == {'W2': False, 'W3': True}


def mean_property(candidate, target_years):
    outcomes = []
    for year in source_cells:
        actual = candidate(year) - candidate(None)
        expected = D(100) / len(target_years) if year in target_years else D(0)
        outcomes.append({'year': year, 'actual_delta': str(actual),
                         'expected_delta': str(expected), 'violated': actual != expected})
    return {'all_scans_pass': not any(row['violated'] for row in outcomes), 'scans': outcomes}


def candidate(key):
    return lambda year: work(key, year, D(100) if year is not None else D(0))


def equivalent_rewrite(year):
    # Analyst-created correct control, NOT a model-generated alternative.
    values = {y: D(cell['numeric_value']) + (D(100) if y == year else 0)
              for y, cell in source_cells.items()}
    return ((values['2019'] + values['2018']) +
            (values['2017'] + values['2016'] + values['2015'])) / 5


def frozen_switch(current_key, alternative_key, results):
    # Hypothetical precommitted LOCAL rule; does not change historical final output.
    if not results[current_key]['all_scans_pass'] and results[alternative_key]['all_scans_pass']:
        return {'action': 'select_local_alternative', 'selected': alternative_key}
    return {'action': 'retain_current', 'selected': current_key}


five_years = set(source_cells)
valid_results = {key: mean_property(candidate(key), five_years) for key in ('W2', 'W3')}
valid_switch = frozen_switch('W3', 'W2', valid_results)
assert valid_switch['selected'] == 'W2'
equivalent_results = {'W2': valid_results['W2'], 'rewrite': mean_property(equivalent_rewrite, five_years)}
assert all(row['all_scans_pass'] for row in equivalent_results.values())
assert frozen_switch('W2', 'rewrite', equivalent_results)['selected'] == 'W2'
def wrong_offset(year):
    return candidate('W2')(year) + D(1000)


wrong_offset_property = mean_property(wrong_offset, five_years)
assert wrong_offset_property['all_scans_pass'] and wrong_offset(None) != baseline['W2']
wrong_target_results = {key: mean_property(candidate(key), {'2018', '2019'})
                        for key in ('W1', 'W2')}
wrong_target_switch = frozen_switch('W2', 'W1', wrong_target_results)
assert wrong_target_switch['selected'] == 'W1'
direct_recompute = sum(D(cell['numeric_value']) for cell in source_cells.values()) / len(source_cells)
assert direct_recompute == baseline['W2']
wrong_scope_direct = sum(D(source_cells[y]['numeric_value']) for y in ('2018', '2019')) / 2
assert wrong_scope_direct == work('W1')
summary = json.loads((FLOW / 'SUMMARY.json').read_text(encoding='utf-8'))
assert summary['final']['delivered']['answer'] == float(baseline['W2'])
result = {
    'status': 'analyst_assisted_engineering_walkthrough_only', 'new_api_calls': 0,
    'actual_source_path': SOURCE.relative_to(ROOT).as_posix(),
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'formulas': {key: nodes[key] for key in ('W1', 'W2', 'W3')},
    'analyst_assisted_verified_source_bindings': [dict(work_id=key, input_name=name, **value)
                                                 for (key, name), value in bindings.items()],
    'baseline_values': {key: str(value) for key, value in baseline.items()},
    'trials': trials,
    'invalid_property_control': {
        'description': 'Assume increasing FY2019 by100 should increase result by32; this is the WRONG expected relation for the task',
        'passes': bad_property,
        'consequence': 'Blindly using a generated test can reject the correct existing W2 and retain erroneous W3'},
    'v2_fixed_template_valid_scope': {'results': valid_results, 'hypothetical_local_switch': valid_switch},
    'equivalent_correct_control': {'results': equivalent_results,
                                   'hypothetical_local_switch': frozen_switch('W2', 'rewrite', equivalent_results)},
    'wrong_offset_undetected_control': {
        'description': 'A five-year mean plus1000 is wrong but has identical sensitivity under every chosen source-record perturbation',
        'value': str(wrong_offset(None)), 'test_result': wrong_offset_property,
        'consequence': 'Passing every sensitivity check is only a necessary property, weaker than direct computation of the already accepted mean specification.'},
    'v2_wrong_target_control': {
        'description': 'Wrongly claim that original five-year task asks for only2018/2019. The fixed mean template is mathematically valid but task-inapplicable.',
        'results': wrong_target_results, 'hypothetical_local_switch': wrong_target_switch,
        'selected_numeric_answer': str(work('W1')),
        'consequence': 'Correct existing W2 would be replaced by wrong-for-task W1. Template validity does not validate chosen target scope.'},
    'simplification_control': {
        'same_accepted_target_set_direct_mean': str(direct_recompute),
        'matches_existing_correct_W2': direct_recompute == baseline['W2'],
        'requires_alternative_candidate_or_perturbation': False,
        'same_wrong_scope_direct_mean': str(wrong_scope_direct),
        'interpretation': 'With the correct full target set and values already required by this template, direct recomputation solves the local task. Behavioral testing has not shown extra solving value over this simpler control; neither removes target-scope ambiguity.'},
    'nondiscriminating_control': {'property': 'Re-executing unchanged candidate yields same value',
                                 'passes': {'W2': True, 'W3': True},
                                 'consequence': 'Self-consistency alone does not select a correct interpretation'},
    'actual_final_answer': summary['final']['delivered']['answer'],
    'added_correct_task_answers_demonstrated': 0,
    'analyst_inputs': ['historical error focus W3', 'existing W2 as alternative',
                      'five-year mean interpretation of question',
                      'raw-source/year to input mapping', 'sensitivity-test template and expected delta'],
    'not_demonstrated': ['automatic focus selection', 'automatic alternative generation',
                        'automatic valid-test generation/admission', 'autonomous source-grounded rebinding',
                        'model adoption/repair', 'multi-agent quality gain'],
}
(HERE / 'WALKTHROUGH.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'mechanical_replay': 'passed', 'five_year_mean_vs_erroneous_deltas': trials[-1]['observed_deltas'],
                  'bad_property_passes': bad_property, 'added_correct_task_answers_demonstrated': 0,
                  'new_api_calls': 0}, ensure_ascii=False))
