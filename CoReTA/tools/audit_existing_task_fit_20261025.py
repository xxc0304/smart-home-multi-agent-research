"""Local task-content audit and native packets; no provider, prompts or model calls."""
from pathlib import Path
import json
import hashlib
import local_judgment_frontend as io

ROOT=io.ROOT
SOURCE=ROOT/'data/task-source-audit-20261021/hiddenbench.json'
AUDIT=ROOT/'research/task-fit-audit-20261025'
PACK=ROOT/'data/task-packs/hiddenbench-local-contribution-dev-20261025-v1'
# Domain/rule coverage is the selection rationale. Historical scores are not inputs.
SELECTION=[5,9,12,23]
REVIEWS={
 1:('reference','evacuation_routes','Relevant information combining blocked routes; close siblings2/3 are not independent families. Keep as a simpler reference, not selected merely to reduce accuracy.'),
 2:('reserve_sibling','evacuation_routes','Same narrative as1/3; prospective dam-release implication adds interpretation. Avoid counting three near-duplicates as broad coverage.'),
 3:('reserve_sibling','evacuation_routes','Same narrative as1/2; reachable EastTown partly inferred from absence of route blockage. Retain as optional within-family case.'),
 4:('reserve_ambiguity','identity_scope','Owner alcohol and driver identity must be distinguished; reference answer is not a fully formal unique guilt proof. Repeatedly used development case.'),
 5:('selected','comparative_personnel','Multiple desired job criteria and dispersed reference updates, sharedCV prestige versus actual fundraising/leadership. Legitimate comparative judgment; no invented equal-weight rule.'),
 6:('reserve_overlap','comparative_personnel','Qualitative pilot traits have no explicit aggregation weights. A possible later preference task, but5 has richer stated job criteria and is the present representative.'),
 7:('reserve_scoring_semantics','procurement','All proposals miss some desired criteria; do not turn every N into disqualification or silently assume equal weights. Requires explicit comparative scoring audit if reused.'),
 8:('reserve_ambiguity','criminal_inference','Driving/alibi implications need additional assumptions; not a clean primary measure of factual knowledge adoption.'),
 9:('selected','current_capability','Distinguish public ICU reputation/existence from current capacity, road status, and temporary bed availability. Pool distinct member updates; do not claim all HospitalA capabilities independently verified.'),
 10:('reserve_overlap','safety_logistics','Useful landing versus ground-distribution and gas hazard scope. Overlaps9/12 in current-status logistics; no need to include every similar task now.'),
 11:('reserve_time_scope','time_and_duration','Useful two-hour relocation versus full-day operation and within-one-hour restoration. Keep as a targeted temporal extension, not selected solely because earlier methods failed.'),
 12:('selected','exception_and_population','Tourist closure exception for emergency evacuees; combine power and vehicle-access restrictions. Stronger explicit exception scope and positive availability statement than many route variants.'),
 15:('reserve_overlap','separated_facilities','Evidence room separated from crowded shelter, security absence and access blockage. Useful candidate but redundant facility-scope coverage in this small set.'),
 18:('reserve_risk_semantics','comparative_risk','Two-week mission versus72-hour weather, food delay and conditional avalanche risk. Do not invent probabilities or turn every possibility into hard exclusion.'),
 20:('reserve_risk_semantics','comparative_risk','Possible seismic/oxygen risks versus certified shielding are comparative uncertain evidence. Official choice is not a proof of a Boolean elimination rule.'),
 21:('reference','current_transport','Explicit suspension, next-day delay and completed upgrade support a simple information-combining reference. Prior success is not evidence of specialist calibration.'),
 22:('reserve_overlap','duration_and_supply','Explicit48h goal, vehicle fuel, positive Base supplies, unsafe access. Good further duration/access candidate; retain, do not only select its earlier all-wrong outcomes.'),
 23:('selected','policy_and_booking_status','Sole-road closure, catering policy and software-calendar/phone-booking exception; venue choice is not completed booking. Do not weaken sole-road to main-road or invent Saturday confirmation.'),
 26:('reserve_overlap','comparative_storage','Roof-load risk, road blockage and watertight TownHall; indirect access and risk implications. Useful later domain variation, currently reserve.'),
 27:('reserve_duration_scope','long_horizon_capability','Ten-year seismic outlook and heavy-equipment support plus conditional year-round access. Good long-horizon extension; PineRidge every capability is not proved.'),
 30:('reserve_time_scope','financing_timing','12h lead-selection deadline is not explicitly the funding-transfer deadline; do not conflate3-day transfer and3-week committee schedule. Keep separate from clean time constraints.'),
 33:('reserve_ambiguity','route_scope','Main highway blockage does not exclude every alternative route within6h. No unsupported all-route exclusion.'),
 34:('reference','hazard_direction','Clear northward cloud and sole-road loss; useful direct safety reference, already heavily used. Communication evidence need not be indispensable.'),
 50:('reserve_risk_semantics','security_and_disruption','Potential alarm evacuation and unreliableWiFi differ from proven inability to hold meeting. Avoid converting all soft risks into hard requirements.')
}
BOUNDARIES={
 5:dict(combination='SharedCV evidence plus distributed leadership, actual fundraising, scholarship and governance updates.',
        scope_limits=['No point weights are specified; do not use the student-president +1/0/-1 scoring here.','Roberts is the dataset reference, not a mathematically unique score maximizer.','Allow justified comparisons and preserve irrelevant personal details as source data, not automatically useful contributions.']),
 9:dict(combination='A1 oxygen failure atC; A2 blocked B road; A3 cleared A pass; A4 no B critical beds.',
        scope_limits=['Existing ICU or doctor on shift does not prove current admission capacity.','Temporary absence of beds is not permanent lack of ICU.','After excludingC/B, do not invent verified A-bed counts or a completed patient transfer.']),
 12:dict(combination='A1 emergency exception; A2 sole RedLake road closure; A3 power and mobility limit; A4 collapsed vehicle bridge.',
        scope_limits=['Tourist closure does not extend to emergency evacuees under the explicit exception.','Distinguish whole population access from ability of a walking subset.','Do not imply every candidate needs the same specific medical equipment unless task evidence supports it.']),
 23:dict(combination='A1 only Lakeview road closed through weekend; A2 false online unavailability with phone acceptance; A3 no catering; A4 road safety concern.',
        scope_limits=['Only access road means no alternative ground road in the supplied task.','Possible phone booking is not an already secured booking or fully verified Saturday capacity.','Mosquito concern must not replace explicit access and catering evidence.'])
}

def build(audit=AUDIT,pack=PACK):
    audit,pack=Path(audit),Path(pack)
    if audit.exists() or pack.exists():raise ValueError('new directories required')
    data=io.read(SOURCE);by_id={x['id']:x for x in data}
    prior_split=io.read(ROOT/'data/dataset-selection-20261022/SELECTION_MANIFEST.json')
    assert len(data)==65 and len(REVIEWS)==24 and SELECTION==[5,9,12,23]
    assert io.digest(SOURCE)==prior_split['source_sha256']
    inventory=[]
    for n,(status,family,note) in REVIEWS.items():
        original=by_id[n]
        inventory.append(dict(source_id=n,status=status,family=family,members=len(original['hidden_information']),note=note,
            original_planning_split='development' if n in prior_split['development_ids'] else 'evaluation_candidate',
            current_use='development_already_used_or_development_audited',official_split=False,
            reference_answer_not_used_as_selection_rule=True))
    snapshot=[]
    for n in SELECTION:
        original=by_id[n];task_id=f'hb-local-dev-{n:03d}'
        public=[dict(ref='TASK',content=original['description'])]+[dict(ref=f'P{i+1}',content=x) for i,x in enumerate(original['shared_information'])]
        task=dict(task_id=task_id,scenario=original['description'],shared_information=original['shared_information'],
            choices=[dict(id=f'O{i+1}',text=x) for i,x in enumerate(original['possible_answers'])])
        # Neutral ids preserve all native source text, including overlapping/irrelevant facts.
        members=[f'A{i+1}' for i in range(len(original['hidden_information']))]
        private=[dict(ref=f'A{i+1}.S1',content=x) for i,x in enumerate(original['hidden_information'])]
        io.write(pack/task_id/'public/task.json',task)
        for member,source in zip(members,private):
            io.write(pack/task_id/'packets/distributed'/f'{member}.json',dict(task=task,member=member,public_sources=public,own_sources=[source]))
        io.write(pack/task_id/'packets/all_information/A1.json',dict(task=task,member='A1',public_sources=public,own_sources=private))
        io.write(pack/task_id/'packets/shared_only/A1.json',dict(task=task,member='A1',public_sources=public,own_sources=[]))
        expected=f"O{original['possible_answers'].index(original['correct_answer'])+1}"
        io.write(pack/task_id/'offline/evaluation.json',dict(reference_choice=expected,reference_name=original['correct_answer'],
            reference_kind='dataset_provided_choice_not_formal_uniqueness_proof',**BOUNDARIES[n]))
        snapshot.append(dict(task_id=task_id,source_id=n,members=members,source_record_sha256=hashlib.sha256(json.dumps(original,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
            baseline_scope='same source and budget; only contribution-stage prompt differs',
            draft_policy='No draft selected/generated yet; any future common draft shared exactly across methods; no quality filtering.'))
    io.write(pack/'dataset_manifest.json',dict(status='CONTENT_AUDITED_BASE_PACKETS_NOT_RUNTIME_READY',source_sha256=io.digest(SOURCE),
        source_hf_revision=prior_split['hf_revision'],selected_ids=SELECTION,tasks=snapshot,model_calls=0,
        official_split=False,heldout=False,selection_stage='post_prior_experiments_nonblind_content_audit',
        selection_rule='Cover stated-preference judgment,current capability,scope exception,and policy/booking reconciliation; preserve all native agents. Not based on our frontend output on these tasks (not yet run).',
        known_previous_experiment_exposure=True,requires_original_evaluation_split_reclassification=True,
        source_text_rewritten=False,hidden_fact_added=False,code_sha256=io.digest(__file__),
        files={str(p.relative_to(pack)).replace('\\','/'):io.digest(p) for p in pack.rglob('*.json')}))
    io.write(audit/'INVENTORY.json',dict(source_tasks=65,content_reviewed_ids=sorted(REVIEWS),rows=inventory,
        not_included_ids=sorted(set(by_id)-set(REVIEWS)),unseen_status='Not semantically audited in this step; no project-wide untouched/secret claim.'))
    io.write(audit/'SELECTION.json',dict(selected_ids=SELECTION,native_members=4,selected_tasks=4,
        method_outputs_on_selected_tasks='Current autonomous-question candidate not yet run on this set.',
        observed_advantage='Not established by local content inspection.',
        historical_results_role='Read for context and known confounds; not an entry threshold or favorable-outcome filter.',
        controls='No task must be failed by the ordinary method; no right-draft control or difficult draft selected by model outcomes.',
        runtime_status='BLOCKED: no frozen common drafts/runtime schedule or four-contribution integrator adapter yet.',
        base_pack=str(pack.resolve()),files_sha256=io.digest(pack/'dataset_manifest.json')))
    return dict(content_reviewed=24,selected=4,native_members=4,distributed_packets=16,diagnostic_packets=8,model_calls=0)

if __name__=='__main__':print(json.dumps(build()))
