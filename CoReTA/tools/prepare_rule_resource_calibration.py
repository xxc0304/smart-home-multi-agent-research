"""Independent parameter instances for resource calibration, not H1 task questions."""
import argparse
import copy
from pathlib import Path
import local_judgment_frontend as io
import local_judgment_handle_contract as contract


PROBES = [
    dict(id='resource-cal-01',family='numeric_conversion',
         scenario='Fictional device calibration: a new sensor produces90 ticks. Report its standard-unit value if it is established, or state exactly what calibration information is missing. No device selection is requested.',
         rule='The new sensor uses standard units = (ticks - 6) * 1.25. This factory-specific rule is not implied by the word tick.',
         expected=105.0,negative_control='No full-task selection, H1 device name or H1 numerical coefficient is supplied.'),
    dict(id='resource-cal-02',family='inventory_reconciliation',
         scenario='A fictional stock ledger has70 physical units. Request Gamma needs24 and Delta needs18. A reservation line Q8 also appears. Determine how many distinct demanded units are established and what remains uncertain; do not assume what Q8 reserves.',
         rule='Reservation Q8 covers8 units that are already included in Gamma24. It is not separate demand. An inspection marks6 of the70 units damaged and unusable.',
         expected=dict(distinct_demand=42,usable=64,unallocated_after_both=22),negative_control='No reserve-minimum or H1 acceptance answer supplied.'),
    dict(id='resource-cal-03',family='versioned_rule_scope',
         scenario='A fictional platform is actually deployed with policy R4. A dedicated request uses96 nodes for7 hours. Is the request permitted under that policy, or what rule is needed to decide? An advertisement for another version does not establish R4 rules.',
         rule='R3 allows sessions at most5 hours. R4 allows dedicated sessions at most9 hours with at least96 nodes; otherwise its limit is5 hours. Bounds are inclusive. Actual deployed policy governs.',
         expected=True,negative_control='Different policy names, duration, node threshold and limits from the H1 task.')
]

PROMPT = (
    'Answer this independent local calibration problem using the supplied fictional records and any prior knowledge. '
    'Do not invent an organization-specific rule if it is absent. Acknowledge uncertainty precisely; '
    'reasonable uncertainty without the resource is not a false answer. '
    'Return one JSON object with conclusion, status (answer, conditional or abstain), '
    'source_ids (visible IDs only), scope and missing. Do not copy quotations; the host attaches original text. '
)


def packet(probe,condition):
    if condition not in ('with_resource','without_resource'):raise ValueError('unknown condition')
    return dict(task=dict(task_id=probe['id'],scenario=probe['scenario']),member='calibration_member',
        public_sources=[dict(ref='TASK',content=probe['scenario'])],
        own_sources=[dict(ref='RESOURCE',content=probe['rule'])] if condition=='with_resource' else [])


def prepare(output):
    output=Path(output)
    if output.exists():raise ValueError('new directory required')
    output.mkdir(parents=True);schedule=[]
    for probe in PROBES:
        for condition in ('with_resource','without_resource'):
            p=packet(probe,condition)
            import json
            io.write(output/'packets'/f'{probe["id"]}-{condition}.json',p)
            io.write(output/'requests'/f'{probe["id"]}-{condition}.json',dict(
                instructions=PROMPT+'\nPACKET='+json.dumps(p,ensure_ascii=False),schema=contract.schema(p),max_output_tokens=1536))
        for repeat in (1,2):
            order=('with_resource','without_resource') if repeat==1 else ('without_resource','with_resource')
            schedule.extend(dict(probe=probe['id'],condition=c,repeat=repeat,
                                 request=f'requests/{probe["id"]}-{c}.json') for c in order)
    io.write(output/'offline/REVIEW_POINTS.json',[dict(id=x['id'],family=x['family'],expected=x['expected'],
        expected_with='Apply the supplied rule with correct scope.',
        expected_without='State which private relationship is missing; conditional alternatives allowed. Do not score honest uncertainty as factual error.') for x in PROBES])
    io.write(output/'PLAN.json',dict(status='PREPARATION_ONLY',independent_parameter_instances=True,probes=3,
        proposed_max_requests=12,total_output_cap=18432,schedule=schedule,
        model_calls=0,not_h1=True,claims='Resource-supported rule application only, not natural expertise or autonomous discovery.',
        scientific_limit='Rules and instances differ from H1; positive calibration does not establish advantage on every H1 task. No automatic H1 launch.',
        unused_h1_families=['time_denominator','stratified_statistics','dependency_and_downtime']))
    io.write(output/'manifest.json',dict(status='OFFLINE_CALIBRATION_SNAPSHOT_NOT_RUN_READY',
        files={str(p.relative_to(output)).replace('\\','/'):io.digest(p) for p in output.rglob('*.json')},
        code_sha256=io.digest(__file__)))
    return dict(probes=3,templates=6,proposed_attempts=12,model_calls=0)


if __name__=='__main__':
    import json
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    print(json.dumps(prepare(parser.parse_args().output)))
