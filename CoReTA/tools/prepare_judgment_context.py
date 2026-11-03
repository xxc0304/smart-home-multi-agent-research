"""Prepare local diagnostic inputs only; no client, credentials, or network."""
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / 'refine-logs/judgment-context-design-20261023'
OLD = PROJECT / 'runs/selective-application-prepared-20261023-r2'

def historical(name, correct):
    path = OLD / f'application-{name}--F.json'
    payload = json.loads(path.read_text(encoding='utf-8'))
    packet = json.loads(payload['instructions'].split('\nPACKET=', 1)[1].split('\nOUTPUT_SCHEMA=', 1)[0])
    return {'id': name, 'origin': 'reused_development_task_with_authored_advice',
            'source_file': str(path), 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'evidence': {k: packet[k] for k in ('TASK', 'SELF', 'SELF_MATERIALS', 'PUBLIC_REPORTS')},
            'before': packet['BEFORE'], 'good': correct, 'bad': packet['CONTRIBUTION']['text']}

cases = [
    historical('004', 'The guilty driver was in a car, which excludes the motorcyclist Z. '
               'Combine the car, age and sex constraints across the available reports. '
               'The task does not explicitly identify the son as a passenger.'),
    historical('034', 'Cedar has the recalled landline, generator and emergency radio from P-S03. '
               'S01 explicitly reports that Pine is dangerous. Preserve that attribution; '
               'independent confirmation of the report and Cedar safety are separate questions.'),
    {'id': 'report-control', 'origin': 'new_authored_control_not_holdout',
     'evidence': {'TASK': {'text': 'Choose an available clinic for a routine appointment. '
                    'The current notices cover all candidates. Explain your choice.', 'choices': ['East', 'West']},
         'SELF': {'agent_id': 'A1'},
         'SELF_MATERIALS': [{'ref': 'S01', 'content': 'The municipal notice explicitly states that East clinic is closed today because of a water leak.'}],
         'PUBLIC_REPORTS': [{'ref': 'P-S02', 'author': 'A2', 'source_ref': 'S02',
             'reported_excerpt': 'West clinic is open today and has routine appointments available.'}]},
     'before': {'artifact': 'West', 'work_text': 'Choose West. The municipal notice reports East closed today because of a water leak; West has appointments.'},
     'good': 'Use the appointment availability at West. Preserve that the municipal notice explicitly reports East closed; independent confirmation is a separate question.',
     'bad': 'Use the appointment availability at West. Correct the East wording: the municipal notice only mentions a water leak, so closure is our inference, not something it explicitly reports.'},
    {'id': 'constraint-control', 'origin': 'new_authored_control_not_holdout',
     'evidence': {'TASK': {'text': 'Choose the unique instrument satisfying all acceptance requirements. '
                    'The complete inventory is: A is sealed, 20 grams, red; B is sealed, 50 grams, red; '
                    'C is unsealed, 20 grams, red; D is sealed, 20 grams, blue. '
                    'All reports concern these same instruments.', 'choices': ['A', 'B', 'C', 'D']},
         'SELF': {'agent_id': 'A1'},
         'SELF_MATERIALS': [{'ref': 'S01', 'content': 'An acceptable instrument must be sealed.'}],
         'PUBLIC_REPORTS': [{'ref': 'P-S02', 'author': 'A2', 'source_ref': 'S02', 'reported_excerpt': 'An acceptable instrument must weigh less than 30 grams.'},
                            {'ref': 'P-S03', 'author': 'A3', 'source_ref': 'S03', 'reported_excerpt': 'An acceptable instrument must be red.'}]},
     'before': {'artifact': 'C', 'work_text': 'Choose C because its weight and colour satisfy two requirements, outweighing the sealing issue.'},
     'good': 'The sealing requirement excludes C. Combine sealing, weight and colour to select A. There is no statement that A is reserved.',
     'bad': 'The sealing requirement excludes C. A is reserved and unavailable, so exclude it too and choose B.'},
]

instructions = ('Solve TASK using SELF_MATERIALS and PUBLIC_REPORTS. Public reports are supplied '
                'colleague reports, not originals you personally inspected. If BEFORE is present, '
                'it is a tentative answer. If ADVICE is present, it is a colleague suggestion. '
                'Neither is guaranteed correct. Return the best final answer and its reasoning '
                'as one JSON object with exactly artifact and work_text. No tools are available.')
conditions = {'E': (False, None), 'B': (True, None), 'G': (True, 'good'), 'M': (True, 'bad')}
items = []
for case in cases:
    for arm, (before, advice) in conditions.items():
        packet = dict(case['evidence'])
        if before:
            packet['BEFORE'] = case['before']
        if advice:
            packet['ADVICE'] = {'author': 'A2', 'text': case[advice]}
        items.append({'case': case['id'], 'condition': arm, 'instructions': instructions,
                      'packet': packet,
                      'output_schema': {'type': 'object', 'additionalProperties': False,
                          'properties': {'artifact': {'type': 'string', 'enum': [c['id'] if isinstance(c, dict) else c for c in case['evidence']['TASK']['choices']]},
                                         'work_text': {'type': 'string', 'minLength': 1}},
                          'required': ['artifact', 'work_text']}})

# These are reviewable design inputs, not API payloads or an approved execution manifest.
OUT.mkdir(parents=True, exist_ok=True)
target = OUT / 'INPUTS_R3.json'
if target.exists():
    raise FileExistsError('Do not overwrite an existing prepared input set')
target.write_text(json.dumps({'status': 'design_inputs_not_live_ready', 'cases': cases,
    'inputs': items, 'proposed_repeats': 2, 'proposed_requests': 32,
    'actual_requests': 0}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'path': str(target), 'input_count': len(items), 'actual_requests': 0}))
