"""Offline new-instance construction and historical interface replay. No API client."""
import json
from pathlib import Path
from fractions import Fraction
from tokenizers import Tokenizer
import local_judgment_frontend as io
import local_rule_frontend as frontend
import local_judgment_handle_contract as contract

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'runs/local-rule-confirmation-preparation-20261025-r1'
DATA = ROOT/'data/task-packs/local-rule-confirmation-20261025-v1'
OLD = ROOT/'runs/local-rule-frontend-live-20261025-r1'

def definitions():
    return [
      dict(id='rule-confirm-07',family='numeric_conversion',draft_type='wrong',
        goal='Choose the cheapest eligible device: at least 95 standard units and peak power at most 60 W. Use only the fictional exercise records.',
        public='Juniper reports 162 ticks, costs 50 credits, peak 59 W. Maple reports 147 ticks, costs 40 credits, peak 58 W.',
        private=[
          'The instrument calibration is ticks = 1.5 * standard_units + 12. Eligibility uses standard_units, so invert this relation to recover them.',
          'The current inspection confirms Juniper peak 59 W and Maple peak 58 W; these are the governing eligibility peaks, not averages.',
          'The calibration is valid for readings from 120 through 180 ticks inclusive. Both devices were measured in that documented range.'],
        choices=['Juniper','Maple','neither'],draft='Maple',
        claims=['Use (ticks - 12) * 1.5 to get standard units: Juniper 225 and Maple 202.5.',
                'Both pass the 95-unit threshold and 60 W limit.', 'Maple costs less, so choose Maple.'],
        expected='Juniper', review=[
          'Invert the equation: Juniper100 and Maple90. Maple fails95. Converting is not by itself validation of inspection or calibration range.',
          'Both governing peaks pass60. This alone does not resolve standard-unit eligibility.',
          'Both readings are inside the calibration range. Confirmation is useful only at that scope; it does not validate the draft inverse formula.']),
      dict(id='rule-confirm-08',family='time_denominator',draft_type='wrong',
        goal='Choose the cheapest service achieving at least 2.5 distinct completed jobs per minute over the entire reserved session. A costs20 credits and B costs30. Logs cover the complete processing intervals.',
        public='A reports240 completion records during60 processing minutes. B reports210 completion records during60 processing minutes.',
        private=[
          'Entire reserved session = processing minutes plus reserved idle minutes. No jobs complete during reserved idle minutes; distinct completed jobs, not completion records, are the numerator.',
          'A has30 reserved idle minutes in addition to the60 processing minutes. B has0 reserved idle minutes; no other session time is billed.',
          'A contains60 repeated completion records for already-counted jobs; all remaining A records and all210 B records have distinct job IDs.'],
        choices=['A','B','neither'],draft='A',
        claims=['A gives240/60=4 records per minute and B gives210/60=3.5.',
                'These record rates establish that both meet2.5 distinct jobs per entire reserved minute.', 'Choose cheaper A.'],
        expected='B',review=[
          'Normalize distinct counts over processing plus idle. Correct the numerator/denominator without inventing other members\' values.',
          'Session lengths90 and60; even raw A records/90 is an upper bound, not a proof of distinct rate. Need deduplication for a definitive threshold test.',
          'Distinct counts180 and210; processing rates3 and3.5 are not automatically reserved-session rates.']),
      dict(id='rule-confirm-09',family='stratified_statistics',draft_type='correct_supported_control',
        goal='Choose the model with greater expected observed success under the documented deployment mixture. Use binary observed outcomes; no significance or causal inference is requested.',
        public='Model L has9/10 successes on small jobs and20/100 on large jobs. Model M has8/10 small and60/100 large.',
        private=[
          'Expected deployment success is the deployment-weighted sum of within-group observed rates. Experimental stratum counts do not define deployment weights.',
          'Deployment uses25 percent small jobs and75 percent large jobs for both models.',
          'All trials have observed outcomes, distinct job IDs and matching small/large definitions across models. No duplicate or missing-outcome adjustment applies.'],
        choices=['L','M','not_determined'],draft='M',
        claims=['All outcomes are observed and distinct, and deployment is25% small and75% large for both models.',
                'Using deployment weights gives L=0.25*0.9+0.75*0.2=0.375 and M=0.25*0.8+0.75*0.6=0.65.',
                'M is preferred under that mixture, although L is better within small jobs.'],
        expected='M',review=[
          'The draft uses the correct weighting method; models cross by group, so no universal dominance. Conditional confirmation is acceptable, not new correction.',
          'Confirm25/75 and0.375/0.65. Do not manufacture a correction to the supported draft.',
          'Confirm no missing or duplicate outcomes and matching strata. Do not invent a data-quality problem.']),
      dict(id='rule-confirm-10',family='inventory_reconciliation',draft_type='wrong',
        goal='Serve Alpha first and then Beta if feasible, leaving at least25 usable units unallocated. Alpha requests70 units and Beta60. Only the overlap explicitly documented in the records may satisfy both requests with the same physical units.',
        public='The ledger contains150 physical units. Reservation row R10 is also listed; reservation is not automatically an additional demand.',
        private=[
          'Alpha and Beta have exactly20 units of joint demand. The same20-unit allocation satisfies that portion of both requests; all their remaining demand is disjoint.',
          'Exactly10 of the150 ledger units are damaged and unusable for either requests or the25-unit unallocated reserve. No other units are damaged.',
          'R10 reserves10 units already inside Alpha\'s70-unit demand. It adds no separate allocation and overlaps no demand except that recorded part of Alpha.'],
        choices=['both','Alpha_only','Beta_only','neither'],draft='Alpha_only',
        claims=['Inspection leaves140 usable units.', 'Subtract Alpha70 and Beta60 independently: only10 remain, below25.',
                'Therefore admit only Alpha; treat R10 as already in Alpha.'],
        expected='both',review=[
          'Union demand70+60-20=110, not130. State reliance on net usable stock when deriving feasibility.',
          'Usable140 agrees with the draft. Does not independently establish whether requests overlap.',
          'R10 is not a separate deduction; the draft already handles it. Avoid new subtraction or invented reservation semantics.']),
      dict(id='rule-confirm-11',family='dependency_and_downtime',draft_type='wrong',
        goal='Find earliest completion minutes after0. Build requires20 active minutes, test15, packing10. Work may pause and resume with no penalty; all start times are at least0. Use documented precedence, resource and availability rules.',
        public='The listed durations are active processing times, excluding any waiting and unavailability.',
        private=[
          'Test and packing each start only after build finishes. There is no test-before-packing or packing-before-test precedence.',
          'Test and packing share a single fixture and cannot run simultaneously. Build uses a separate resource.',
          'The fixture is unavailable only during[5,15). It is available from minute15 onwards with no later outage. Progress is retained across pauses.'],
        choices=['35','45','55','not_determined'],draft='55',
        claims=['Build finishes at20; test and packing then require25 active minutes on the one shared fixture.',
                'The fixture outage[5,15) contributes10 more minutes.', 'Completion is20+25+10=55.'],
        expected='45',review=[
          'Build completes no earlier than20 and both dependent steps follow it; resource and availability conditions govern concurrency and feasibility.',
          'Test+packing require25 fixture-active minutes. With build precedence this gives a conditional45 lower bound, not unconditional feasible completion.',
          'The outage ends at15, before the draft\'s post-build fixture work at20; it does not add10 to that conditional timeline. Do not invent a restart.']),
      dict(id='rule-confirm-12',family='versioned_rule_scope',draft_type='correct_supported_control',
        goal='Choose the cheapest platform supporting a5-hour secure session under its actually deployed version. All rules are fictional; no mode substitution is allowed.',
        public='Red advertises V3 and costs90 credits; Blue advertises V3 and costs70 credits. Both offer secure and ordinary modes; node counts are irrelevant to these session limits.',
        private=[
          'V2 supports secure sessions up to6 hours. V3 supports ordinary sessions up to8 hours but secure sessions only up to4 hours. All limits are inclusive and independent of node counts.',
          'The request is exactly5 hours in secure mode. Neither ordinary-mode substitution nor splitting it into separate sessions is permitted.',
          'Deployment audit: Red actually runs V2 and Blue actually runs V3. Actual deployment governs; advertisements do not override the audit.'],
        choices=['Red','Blue','neither'],draft='Red',
        claims=['Actual deployment is Red V2 and Blue V3; this is one unsplit5-hour secure request.',
                'V2 permits secure6h and V3 permits secure4h, so Red qualifies and Blue does not; ordinary8h is irrelevant.',
                'Choose Red at90 credits despite Blue being cheaper. Node counts do not affect the rules.'],
        expected='Red',review=[
          'Confirm mode-specific6/4-hour limits and inclusive bounds. A newer version is not automatically better; no node threshold is relevant.',
          'Confirm5-hour secure unsplit request; do not substitute ordinary mode to qualify Blue.',
          'Confirm actual versions; do not replace audited V2 with advertised V3.'])
    ]

def oracle(task):
    n=int(task['id'].rsplit('-',1)[1])
    if n==7:
        v={'Juniper':Fraction(162-12,1)/Fraction(3,2),'Maple':Fraction(147-12,1)/Fraction(3,2)}
        eligible=[x for x in v if v[x]>=95 and {'Juniper':59,'Maple':58}[x]<=60]
        return min(eligible,key=lambda x:{'Juniper':50,'Maple':40}[x]), {k:float(x) for k,x in v.items()}
    if n==8:
        rates={'A':Fraction(240-60,60+30),'B':Fraction(210,60)}
        return min((x for x in rates if rates[x]>=Fraction(5,2)),key=lambda x:{'A':20,'B':30}[x]),{k:float(v) for k,v in rates.items()}
    if n==9:
        v={'L':Fraction(1,4)*Fraction(9,10)+Fraction(3,4)*Fraction(20,100),
           'M':Fraction(1,4)*Fraction(8,10)+Fraction(3,4)*Fraction(60,100)}
        return max(v,key=v.get),{k:float(x) for k,x in v.items()}
    if n==10:
        alpha=set(range(70));beta=set(range(50,110))
        assert len(alpha & beta)==20 and len(alpha | beta)==110
        remaining=150-10-len(alpha|beta)
        return ('both' if remaining>=25 else 'Alpha_only'),dict(remaining=remaining,union=110)
    if n==11:
        t=20;remaining=25
        while remaining:
            if not 5<=t<15:remaining-=1
            t+=1
        return str(t),dict(finish=t,outage_delay_after_build=0)
    if n==12:
        duration=5;limits={'Red':6,'Blue':4}
        eligible=[x for x in limits if duration<=limits[x]]
        return min(eligible,key=lambda x:{'Red':90,'Blue':70}[x]),dict(secure_limit_Red=6,secure_limit_Blue=4)
    raise ValueError(task['id'])

def main():
    if DATA.exists() or OUT.exists():raise ValueError('new directories required; never overwrite')
    tasks=definitions(); historical=io.read(OLD/'review.json')['rows']
    assert len(tasks)==6 and sum(t['draft_type']=='correct_supported_control' for t in tasks)==2
    hand_answers=['Juniper','B','M','both','45','Red']
    tokenizer=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
    schedule=[];replay=[];max_input=0;max_output=0;offline=[]
    for idx,entry in enumerate(tasks):
        assert len(entry['private'])==len(entry['review'])==3
        answer,trace=oracle(entry)
        assert answer==entry['expected']==hand_answers[idx]
        if entry['draft_type']=='wrong':assert answer!=entry['draft']
        else:assert answer==entry['draft']
        task=dict(task_id=entry['id'],scenario=entry['goal'],shared_information=[entry['public']],
                  choices=[dict(id=x,text=x) for x in entry['choices']],
                  instruction='A contribution stage may give a local or conditional finding or abstain; it need not solve the whole task.')
        public=[dict(ref='TASK',content=entry['goal']),dict(ref='P1',content=entry['public'])]
        draft=dict(draft_id='W0',artifact=entry['draft'],reason=' '.join(entry['claims']),
                   claims=[dict(id=f'D{i+1}',text=x) for i,x in enumerate(entry['claims'])])
        io.write(DATA/entry['id']/'public/task.json',task);io.write(DATA/entry['id']/'public/W0.json',draft)
        offline.append(dict(task_id=entry['id'],family=entry['family'],draft_type=entry['draft_type'],expected=answer,
                            oracle_trace=trace,member_review_points={f'A{i+1}':x for i,x in enumerate(entry['review'])}))
        for member_index,source in enumerate(entry['private'],1):
            member=f'A{member_index}'
            packet=dict(task=task,member=member,public_sources=public,
                        own_sources=[dict(ref=f'{member}.S1',content=source)],historical_work=draft)
            io.write(DATA/entry['id']/'packets'/f'{member}.json',packet)
            for repeat in (1,2):
                order=frontend.METHODS if (idx+repeat)%2 else frontend.METHODS[::-1]
                for method in order:
                    prior=[r for r in historical if r['task']==f'rule-dev-{idx+1:02d}' and r['member']==member and r['method']==method]
                    first=next(r for r in prior if r['stage']=='first')
                    second=next(r for r in prior if r['stage']=='second')
                    raw_first=(OLD/f"{first['slot']:02d}.raw.txt").read_text(encoding='utf-8')
                    decoded=frontend.decode_first(raw_first,packet)
                    second_packet=frontend.second_packet(packet,decoded)
                    raw_second=(OLD/f"{second['slot']:02d}.raw.txt").read_text(encoding='utf-8')
                    decoded_second,_=contract.decode(raw_second,'second',second_packet)
                    assert not decoded['annotation_issues'] and not decoded_second['annotation_issues']
                    for stage,payload_packet in [('first',packet),('second',second_packet)]:
                        slot=len(schedule)+1
                        req=frontend.request(stage,method,payload_packet)
                        estimated=len(tokenizer.encode(req['instructions']+json.dumps(req['schema'],ensure_ascii=False),add_special_tokens=False).ids)
                        max_input=max(max_input,estimated)
                        raw=raw_first if stage=='first' else raw_second
                        max_output=max(max_output,len(tokenizer.encode(raw,add_special_tokens=False).ids))
                        row=dict(slot=slot,task=entry['id'],member=member,repeat=repeat,method=method,stage=stage,
                                 group=f"{entry['id']}/{member}/r{repeat}/{method}")
                        schedule.append(row)
                        io.write(OUT/'preview_requests'/f'{slot:03d}.json',req)
                        replay.append(dict(slot=slot,historical_raw=f"{(first if stage=='first' else second)['slot']:02d}.raw.txt",
                                           estimated_input_tokens=estimated,status='decoded',semantic_validation=False))
    assert len(schedule)==144 and max_input<8192 and max_output<=1536
    # All pairs share the exact original packet; no current peer outputs or offline fields enter.
    for row in schedule:
        req=io.read(OUT/'preview_requests'/f"{row['slot']:03d}.json")
        packet=json.loads(req['instructions'].split('\nPACKET=',1)[1])
        assert [s['ref'] for s in packet['own_sources']]==[row['member']+'.S1']
        assert set(packet)==({'task','member','public_sources','own_sources','historical_work'} if row['stage']=='first' else {'task','member','public_sources','own_sources','earlier_work'})
    io.write(DATA/'offline/REVIEW_POINTS.json',offline)
    io.write(DATA/'manifest.json',dict(status='PROSPECTIVE_SAME_FAMILY_CONFIRMATION_INSTANCES',model_calls=0,
        official_benchmark=False,independent_holdout=False,constructed_after_previous_results=True,outcome_based_new_task_selection=False,
        task_count=6,packets=18,resource_advantage_measured=False,
        files={str(p.relative_to(DATA)).replace('\\','/'):io.digest(p) for p in DATA.rglob('*.json')}))
    io.write(OUT/'PLAN.json',dict(status='OFFLINE_PREPARATION_NOT_AUTHORIZED',max_requests=144,total_output_cap=221184,
        source_manifest_sha256=io.digest(DATA/'manifest.json'),schedule=schedule,
        second_stage_preview='Historical first text replay only. Live stage2 must be built from actual corresponding first text.',
        unchanged_candidate_code={str(p.relative_to(ROOT)).replace('\\','/'):io.digest(p) for p in [Path(frontend.__file__),Path(contract.__file__)]}))
    io.write(OUT/'LOCAL_CHECKS.json',dict(status='PASSED_OFFLINE_CONSTRUCTION_NOT_LIVE_READY',model_calls=0,
        oracle_checks=6,packet_count=18,planned_slots=144,historical_unique_raws=72,decoded_replay_slots=144,
        max_estimated_input_tokens=max_input,input_limit=8192,max_replayed_output_tokens=max_output,output_limit=1536,
        annotation_issues=0,replay=replay,
        limitations=['Historical reply content belongs to old tasks: interface coverage only, no semantic evidence on new tasks.',
                     'Input estimate covers observed replay text, not a worst-case first response.',
                     'New live runner/repeat isolation, interrupted exports and fresh manifest launch gates remain unimplemented.']))
    print(json.dumps(dict(tasks=6,packets=18,slots=144,replay_slots=144,max_input=max_input,max_replayed_output=max_output,model_calls=0)))

if __name__=='__main__':main()
