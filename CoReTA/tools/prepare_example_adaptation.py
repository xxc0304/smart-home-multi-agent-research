"""Single fixed manual demonstration bank and historical/synthetic diagnostic cases."""
import json
from pathlib import Path
import local_judgment_frontend as io
import example_adaptation_probe as front

ROOT=io.ROOT
SPEC=ROOT/'research/example-adaptation-20261026-v1'


def bank():
    # Both conditions have the SAME episode facts and correct action. Only presentation differs.
    episodes=[
        dict(id='load',facts='A parcel requires a carrier with payload at least 14 kg. Carrier Neral can carry 11 kg and costs 2 credits; carrier Vexo can carry 16 kg and costs 4. A colleague correctly reports Neral\'s 11 kg limit.',
            application='Reject Neral for this parcel and use Vexo. The colleague need not solve the entire task for the 11 < 14 exclusion to matter.',
            explanation='The payload limit is a necessary requirement, not a preference. Being cheaper cannot repair the violation. This conclusion concerns this parcel and does not say Neral is generally useless. It depends on the stated capacities, not on the colleague\'s identity.',
            error='Keep Neral because it is cheaper and the colleague\'s payload observation does not independently establish the best carrier.',
            why='The error treats inability to solve the whole task as a reason to ignore a valid necessary exclusion; price only distinguishes feasible carriers.'),
        dict(id='scope',facts='For powered cutters, policy P requires certificate K. The current task needs a hand saw. Both Nima and Ordo are hand saws satisfying the size requirement; Nima costs less. A colleague infers Nima must be rejected because it lacks K.',
            application='Reject the proposed certificate exclusion and retain Nima. The cited rule covers powered cutters, not the hand saw used here.',
            explanation='The source rule itself can be correct while its application is wrong. Match the rule\'s population to the actual object before excluding a candidate. Do not invent a certificate requirement for hand saws or trust a derived claim just because its author quoted a real rule.',
            error='Exclude Nima because a colleague cited a real safety policy and stated the certificate requirement confidently.',
            why='The rule\'s scope does not match the current object; a valid citation does not make this particular use valid.'),
        dict(id='partial',facts='A token qualifies if its issued count is at most 7 AND its seal is intact. Token Ulmo has count 9 and an intact seal. Token Tavi has count 5, but its seal status is unknown. A colleague correctly points out Ulmo violates the count limit.',
            application='Exclude Ulmo while keeping Tavi\'s qualification conditional on its seal. The observation is useful even though it cannot prove Tavi fully qualifies.',
            explanation='A necessary condition can establish one exclusion without establishing the alternative. Preserve that partial consequence. Unknown seal status is not a known failed seal; if a decision is required, separate best available choice from certification.',
            error='Keep Ulmo because the colleague cannot certify Tavi, so the count observation is insufficient to change anything.',
            why='Failure to prove the alternative does not remove Ulmo\'s known violation. Retain uncertainty about Tavi without turning Ulmo into a qualified token.'),
        dict(id='unsupported',facts='The task accepts either round or square markers if they have a readable serial. Both markers Fena and Kor have readable serials; Fena is cheaper. A colleague says only square markers count, citing no additional requirement.',
            application='Do not add the colleague\'s square-only restriction; retain Fena if it is cheaper. The actual task permits both shapes.',
            explanation='A proposed restriction must come from the task or applicable evidence. Check it against the supplied acceptance rule rather than adopting it because it is specific or confident. Rejecting an unsupported inference does not mean ignoring the colleague\'s valid observations.',
            error='Switch to Kor because a specific new restriction should be followed whenever another member raises it.',
            why='Specificity and authorship do not create a requirement; the proposed restriction conflicts with the task\'s stated acceptance rule.'),
    ]
    positives=[];contrasts=[]
    for e in episodes:
        positives.append(dict(scenario=e['facts'],correct_application=e['application'],supporting_explanation=e['explanation']))
        contrasts.append(dict(scenario=e['facts'],incorrect_application=e['error'],why_incorrect=e['why'],correct_application=e['application']))
    return dict(positive_examples=positives,contrastive_examples=contrasts)


def control(identifier,scenario,choices,sources,claim,old):
    task=dict(task_id=identifier,scenario=scenario,choices=[dict(id=f'option_{i+1}',text=name) for i,name in enumerate(choices)],
              instruction='Choose the cheapest feasible option using the supplied task facts; do not invent requirements.')
    packet=dict(task=task,member='A1',public_sources=[dict(ref=f'PUBLIC.{i+1}',content=text) for i,text in enumerate(sources)],
        own_sources=[],historical_author='A1',historical_work=dict(reason='The cheaper option was preferred before examining the colleague finding.',artifact=old),
        shared_contributions={'A2':dict(text=claim)},execution_report=None,
        local_question='How does the colleague finding affect feasibility under the actual task requirements?',
        local_reconstruction=dict(author='A2',text=claim))
    return dict(case_id=identifier,kind='authored_safety_control',packet=packet)


def main():
    if SPEC.exists():raise ValueError('new spec version required')
    examples=bank()
    io.write(SPEC/'EXAMPLES.json',examples)
    parent=ROOT/'runs/local-reconstruction-live-20261026-r1'
    review=io.read(parent/'review.json')['rows']
    indices=[]
    for row in review:
        if row['stage']!='final' or row['method']!='visible_draft':continue
        actual=io.read(parent/'actual_requests'/f"{row['slot']:03d}.json")
        packet=io.strict_json(actual['instructions'].split('\nPACKET=',1)[1])
        case=dict(case_id=row['case_id'],kind='historical_development_regression',packet=packet)
        io.write(SPEC/'cases'/f"{row['case_id']}.json",case)
        indices.append(dict(case_id=row['case_id'],kind=case['kind'],task=row['case_id'][:3],
            parent_slot=row['slot'],source=str((parent/'actual_requests'/f"{row['slot']:03d}.json").relative_to(ROOT)),
            source_sha256=io.digest(parent/'actual_requests'/f"{row['slot']:03d}.json")))
    controls=[
        control('control-storage','Choose the cheapest backup store with at least 18 GiB of usable space.',
            ['Daro','Evin'],['Daro has 20 GiB total and reserves 4 GiB; price 2. Evin has 22 GiB total and reserves 2 GiB; price 5. Usable space is total minus reserved.'],
            'Daro has only 16 GiB usable (20 minus 4), below the task minimum.','option_1'),
        control('control-parallel','A validation batch starts with 20 minutes of setup, followed by independent 10-minute and 15-minute checks that may run in parallel. Finish within 40 minutes and choose the cheaper feasible batch.',
            ['Lira','Mova'],['Lira uses that setup/check procedure, has unlimited workers for the two checks, and costs 2. Mova takes 38 minutes and costs 5. No other dependencies or shared resources apply.'],
            'Lira takes 20+10+15=45 minutes, so reject it for missing the deadline.','option_1'),
        control('control-edition','Choose a compatible reader for edition 1 documents at the lowest price.',
            ['Zali','Wero'],['Both readers support edition 1. Zali costs 1 and Wero costs 3. The rule requiring an online validation key applies only to edition 2 documents. Zali lacks that key; Wero has it.'],
            'Reject Zali because the validation-key rule means it cannot read the current documents.','option_1'),
        control('control-window','Starting no earlier than minute 10, execute an uninterrupted 6-minute job and finish by minute 18. Choose the cheaper feasible workstation. Time intervals are half-open.',
            ['Ruvo','Sena'],['Ruvo is available during [10,18) except outage [12,14), and costs 1. Sena is continuously available during [10,18), and costs 4. Work cannot pause or run during an outage.'],
            'Ruvo cannot fit 6 uninterrupted minutes: its available segments are 2 and 4 minutes. Sena can.','option_1'),
    ]
    # Offline deterministic checks; no labels in model packet.
    storage=[20-4,22-2];assert storage==[16,20]
    parallel=20+max(10,15);assert parallel==35
    feasible=[start for start in range(10,13) if not (start<14 and start+6>12)]
    assert not feasible
    labels={
        'control-storage':dict(choice='option_2',action='update',finding='supported',basis=dict(usable=storage,minimum=18)),
        'control-parallel':dict(choice='option_1',action='retain',finding='unsupported',basis=dict(duration=parallel,deadline=40)),
        'control-edition':dict(choice='option_1',action='retain',finding='out_of_scope',basis='edition 2 rule does not apply to edition 1'),
        'control-window':dict(choice='option_2',action='update',finding='supported',basis=dict(ruvo_segments=[2,4],required_continuous=6)),
    }
    for case in controls:
        io.write(SPEC/'cases'/f"{case['case_id']}.json",case)
        indices.append(dict(case_id=case['case_id'],kind=case['kind'],task=case['case_id'],source='new authored deterministic control'))
    io.write(SPEC/'CASE_INDEX.json',indices)
    io.write(SPEC/'offline_only/CONTROL_LABELS.json',labels)
    schedule=[]
    for repeat in [1,2]:
        for ci,entry in enumerate(indices):
            start=(ci+repeat-1)%3
            methods=front.METHODS[start:]+front.METHODS[:start]
            for method in methods:
                schedule.append(dict(slot=len(schedule)+1,case_id=entry['case_id'],kind=entry['kind'],method=method,repeat=repeat))
    io.write(SPEC/'DESIGN.json',dict(status='offline_spec_not_authorized',schedule=schedule,
        max_requests=72,max_output_tokens=110592,max_input_tokens=524288,per_output=1536,per_input=16384,
        retries=0,no_auto_expand=True,demonstration_bank='one fixed manually authored bank; no selection by this trial results',
        primary_scope='old-task regression plus separately scored authored controls, not unseen benchmark generalization',
        split='demonstrations use carrier/tool/token/marker tasks; controls use storage/parallelism/edition/time windows; abstract logical patterns intentionally transfer'))
    io.write(SPEC/'SOURCE_MANIFEST.json',dict(
        parent_files={e['source']:e['source_sha256'] for e in indices if e.get('source_sha256')},
        code_sha256={str(p.relative_to(ROOT)):io.digest(p) for p in [Path(__file__),Path(front.__file__)]},
        files={x.relative_to(SPEC).as_posix():io.digest(x) for x in SPEC.rglob('*.json')}))
    print(json.dumps(dict(cases=len(indices),historical=8,authored_controls=4,demonstrations=4,planned_requests=len(schedule),new_api_calls=0)))


if __name__=='__main__':main()
