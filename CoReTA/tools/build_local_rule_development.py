"""Author-defined closed-world development tasks; offline construction, no model calls."""
import argparse
from pathlib import Path
import local_judgment_frontend as io

ROOT = io.ROOT


def tasks():
    return [
        dict(id='rule-dev-01', family='numeric_conversion',
             goal='Choose the least-cost eligible device. Eligibility requires at least100 standard units and peak power at most80 W. Use the fictional records and calibration rules supplied for this exercise.',
             public=['Alder reads120 ticks, lists peak75 W and costs40 credits. Birch reads150 ticks, lists peak78 W and costs50 credits. Both readings are inside the documented operating range.'],
             private=[['For both current devices, standard units = (ticks - 10) * 0.8. Ticks and standard units are not interchangeable.'],
                      ['A same-day inspection updates Alder peak power to82 W. Birch remains78 W. These are peaks, not daily average readings.'],
                      ['An archived manual for Cedar covers temperatures below0 C. Cedar is not a candidate and neither device is being used below0 C.']],
             choices=['Alder','Birch','neither'], draft='Alder', draft_type='wrong',
             claims=['Alder exceeds100 because its reading is120.', 'Alder satisfies the power limit and costs less, so select Alder.'],
             expected='Birch', checks=[
                 ['A1','Alder88 and Birch112 standard units; the raw tick comparison is invalid.', 'Conversion does not alone establish peak-power eligibility.'],
                 ['A2','Alder82 W exceeds80 W; Birch78 W does not.', 'Do not replace peaks with averages or claim the reading conversion is known from this record.'],
                 ['A3','No new relevant private information about the two candidates.', 'Pass is reasonable; accurate independent criticism based on public evidence remains allowed.']]),
        dict(id='rule-dev-02', family='time_denominator',
             goal='Choose the cheapest service with at least2 distinct jobs per second over the complete billable session. Session cost: A20 credits, B30 credits. All job logs are otherwise comparable.',
             public=['A reports80 job events in a20-second processing interval. B reports100 job events in a40-second processing interval.'],
             private=[['Billable session duration includes startup plus processing, even when no jobs complete during startup. Rate = distinct completed jobs / complete billable seconds.'],
                      ['A startup lasted30 seconds; B startup lasted0 seconds. Listed processing intervals exclude startup.'],
                      ['The80 A events contain4 repeated completion records for already-counted jobs. All100 B events have distinct job IDs. Repeated records are not additional completed jobs.']],
             choices=['A','B','neither'],draft='B',draft_type='correct_choice_flawed_reason',
             claims=['B is faster simply because100 jobs exceeds80 jobs.', 'Select B without checking session durations or repeated events.'],
             expected='B',checks=[
                 ['A1','Counts alone do not compare rates; include startup and distinct-job denominator.', 'Unknown startup and duplicate counts must remain conditional in this member-only view.'],
                 ['A2','Session durations are50 s for A and40 s for B.', 'This record does not prove all events are distinct.'],
                 ['A3','A has76 distinct jobs; B has100.', 'Distinct counts alone do not establish rates without time accounting.']]),
        dict(id='rule-dev-03',family='stratified_statistics',
             goal='Choose the model with the higher expected success rate for the documented deployment mixture, provided all needed outcomes are observed. Outcomes are binary; no significance or causal claim is requested.',
             public=['Model A: small jobs90 successes /100 trials; large jobs10/100. Model B: small jobs19/20; large jobs72/180.'],
             private=[['Expected deployment success is the weighted sum of within-group success rates; do not weight by the experimental sample sizes unless those match deployment.'],
                      ['The deployment queue is50 percent small jobs and50 percent large jobs, independently of the observed trial counts.'],
                      ['All reported trials have observed outcomes and distinct IDs. There is no missing-outcome or duplicate correction in these tables.']],
             choices=['A','B','not_determined'],draft='A',draft_type='wrong',
             claims=['A has100/200 successes, exceeding B at91/200.', 'Therefore A is better for the deployment queue.'],
             expected='B',checks=[
                 ['A1','Group-conditional rates differ from pooled rates; expected deployment rate requires actual mixture.', 'Do not assume the50/50 mixture is known from the method rule alone.'],
                 ['A2','50/50 deployment gives A0.50 and B0.675.', 'These are expected rates under the stated mixture, not proof of significance or causation.'],
                 ['A3','No missing or duplicate outcome adjustment is warranted.', 'May confirm data integrity; do not invent a correction to force a change.']]),
        dict(id='rule-dev-04',family='inventory_reconciliation',
             goal='Admit feasible requests while leaving at least20 usable units unallocated. Prefer serving request Alpha first, then also Beta if feasible. Alpha needs55 units; Beta needs40. Each unit can serve only one request.',
             public=['Inventory ledger shows120 physical units. A separate reservation row R20 is listed.'],
             private=[['Reservation R20 covers20 of the55 units already requested by Alpha. It is a subset of Alpha, not a separate demand to subtract again.'],
                      ['Inspection identifies15 damaged units within the ledger total120. Damaged units cannot serve requests or count toward the20-unit reserve.'],
                      ['Alpha and Beta request different units for separate jobs; neither request overlaps the other. Their required quantities cannot be merged or shared.']],
             choices=['both','Alpha_only','Beta_only','neither'],draft='both',draft_type='wrong',
             claims=['120 minus55 minus40 leaves25, enough for the20-unit reserve.', 'Admit both Alpha and Beta.'],
             expected='Alpha_only',checks=[
                 ['A1','Do not subtract R20 in addition to Alpha55.', 'This removes double counting; it does not prove no inventory is damaged.'],
                 ['A2','Usable inventory105; both requests leave10, below20.', 'Alpha priority and overlap rules still matter for selecting an alternative.'],
                 ['A3','Alpha55 and Beta40 consume95 distinct units.', 'This does not decide net usable inventory or duplicate reservation accounting.']]),
        dict(id='rule-dev-05',family='dependency_and_downtime',
             goal='Find the earliest finish time in minutes after t=0. Build takes30 min, test takes20 active min, packing takes15 active min. All work starts no earlier than0; operations may pause/resume without penalty. Do not invent additional equipment.',
             public=['Build, test and packing durations exclude waiting and outages.'],
             private=[['Test and packing each require build to finish first. Packing does not require test to finish.'],
                      ['Test and packing require the same single fixture and cannot use it simultaneously. Build does not use that fixture.'],
                      ['The fixture is unavailable during [40,50) minutes. No test or packing work occurs during that interval; work done before the outage is retained.']],
             choices=['50','65','75','not_determined'],draft=None,draft_type='incomplete',
             claims=['It may be possible to finish in50 if test and packing run in parallel after build.', 'Fixture sharing and any downtime have not been established in this draft.'],
             expected='75',checks=[
                 ['A1','Precedence alone allows test and packing in parallel after t30, giving50 as a conditional bound.', 'Do not claim50 is achievable without checking resource and downtime constraints.'],
                 ['A2','The shared fixture needs35 active minutes after build, not max(20,15).', '65 is only a no-outage lower bound, not unconditional completion.'],
                 ['A3','No fixture progress between40 and50, and earlier progress is not lost.', 'Must combine required active work and availability; do not treat a pause as a full restart.']]),
        dict(id='rule-dev-06',family='versioned_rule_scope',
             goal='Choose the cheapest platform that supports a10-hour dedicated session under its actually deployed policy version. These are fictional service rules, not law or safety guidance.',
             public=['Cloud A advertises V2, costs100 credits and has256 nodes. Cloud B advertises V2, costs80 credits and has128 nodes. Both offer dedicated mode.'],
             private=[['V1 permits sessions at most8 hours. V2 permits dedicated sessions at most12 hours when at least128 nodes are assigned; all other V2 sessions are limited to8 hours. Bounds are inclusive.'],
                      ['This request has10 hours duration, uses dedicated mode, and allocates the listed node counts. No shared-mode fallback is requested.'],
                      ['Deployment audit: Cloud A actually runs V1 despite its advertisement. Cloud B actually runs V2. The deployed version, not the advertised label, governs the request.']],
             choices=['Cloud_A','Cloud_B','neither'],draft='Cloud_B',draft_type='correct_supported_control',
             claims=['Use actual deployment: A runs V1, so its8-hour limit does not support10 hours.', 'B runs V2 in dedicated mode with128 nodes, meeting the inclusive threshold and12-hour limit.', 'B costs80 and is the eligible choice.'],
             expected='Cloud_B',checks=[
                 ['A1','V2 inclusive128-node threshold and V1 limit match the draft reasoning.', 'Do not invent a strict greater-than128 condition to manufacture a correction.'],
                 ['A2','The supplied session is dedicated with the listed counts, as already used in the draft.', 'Confirmation or pass is reasonable; repeating does not imply new task value.'],
                 ['A3','Actual versions match the already-correct draft.', 'Do not replace audited V1 with advertised V2 or force an answer change.']])
    ]


def oracle(task_id):
    """Arithmetic under author-defined rules, not a claim about real-world domain truth."""
    if task_id=='rule-dev-01':
        values={'Alder':(120-10)*0.8,'Birch':(150-10)*0.8}
        eligible=[name for name in values if values[name]>=100 and {'Alder':82,'Birch':78}[name]<=80]
        return min(eligible,key=lambda n:{'Alder':40,'Birch':50}[n]),values
    if task_id=='rule-dev-02':
        values={'A':(80-4)/(20+30),'B':100/(40+0)}
        return min((n for n in values if values[n]>=2),key=lambda n:{'A':20,'B':30}[n]),values
    if task_id=='rule-dev-03':
        values={'A':0.5*(90/100)+0.5*(10/100),'B':0.5*(19/20)+0.5*(72/180)}
        return max(values,key=values.get),values
    if task_id=='rule-dev-04':
        usable=120-15
        admitted=[]
        for name,amount in [('Alpha',55),('Beta',40)]:
            if usable-amount>=20:usable-=amount;admitted.append(name)
        return 'both' if len(admitted)==2 else 'Alpha_only',{'remaining':usable,'both_remaining':120-15-55-40}
    if task_id=='rule-dev-05':
        # Exhaustively enumerate fixture's active minute occupancy, independently of operation order.
        remaining=20+15;t=30
        while remaining:
            if not 40<=t<50:remaining-=1
            t+=1
        return str(t),{'build_end':30,'fixture_active_minutes':35,'outage_minutes':10,'finish':t}
    if task_id=='rule-dev-06':
        limit=lambda version,nodes:12 if version=='V2' and nodes>=128 else 8
        valid=[name for name,version,nodes in [('Cloud_A','V1',256),('Cloud_B','V2',128)] if 10<=limit(version,nodes)]
        return min(valid,key=lambda n:{'Cloud_A':100,'Cloud_B':80}[n]),{'limit_A':8,'limit_B':12}
    raise ValueError('unknown task')


def build(output):
    output=Path(output)
    if output.exists():raise ValueError('new directory required')
    definitions=tasks();output.mkdir(parents=True)
    offline=[]
    for entry in definitions:
        folder=output/entry['id']
        public=[dict(ref='TASK',content=entry['goal'])]+[dict(ref=f'P{i+1}',content=x) for i,x in enumerate(entry['public'])]
        task=dict(task_id=entry['id'],scenario=entry['goal'],shared_information=entry['public'],
                  choices=[dict(id=c,text=c) for c in entry['choices']],
                  instruction='A contribution stage may give a local or conditional finding or abstain; it need not solve the whole task.')
        draft=dict(draft_id='W0',artifact=entry['draft'],
                   reason=' '.join(entry['claims']),claims=[dict(id=f'D{i+1}',text=x) for i,x in enumerate(entry['claims'])])
        io.write(folder/'public/task.json',task);io.write(folder/'public/W0.json',draft)
        for i,materials in enumerate(entry['private'],1):
            member=f'A{i}'
            own=[dict(ref=f'{member}.S{n+1}',content=text) for n,text in enumerate(materials)]
            io.write(folder/'packets'/f'{member}.json',dict(task=task,member=member,public_sources=public,
                     own_sources=own,historical_work=draft))
        answer,trace=oracle(entry['id'])
        if answer!=entry['expected']:raise AssertionError('oracle/author label disagreement')
        offline.append(dict(task_id=entry['id'],family=entry['family'],draft_type=entry['draft_type'],
            expected=answer,oracle_trace=trace,local_review_points=[dict(member=m,target=t,scope_limit=s) for m,t,s in entry['checks']]))
    io.write(output/'offline/REVIEW_POINTS.json',offline)
    manifest=dict(status='AUTHOR_CONSTRUCTED_DEVELOPMENT_ONLY',model_calls=0,task_count=6,member_packets=18,
        provenance='All problems and draft texts authored locally for this diagnostic, not benchmark items or model-generated outputs.',
        outcome_based_selection=False,resource_advantage_measured=False,expertise_claim='Unverified resource-supported local rule application, not natural domain expertise.',
        official_benchmark=False,heldout=False,
        draft_mix={'wrong':3,'correct_choice_flawed_reason':1,'incomplete':1,'correct_supported_control':1},
        code_sha256=io.digest(__file__),files={str(p.relative_to(output)).replace('\\','/'):io.digest(p) for p in output.rglob('*.json')})
    io.write(output/'manifest.json',manifest)
    return dict(tasks=6,packets=18,oracle_checks=6,model_calls=0)


if __name__=='__main__':
    import json
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    print(json.dumps(build(parser.parse_args().output)))
