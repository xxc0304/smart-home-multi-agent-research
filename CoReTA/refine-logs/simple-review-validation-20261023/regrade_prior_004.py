"""Revised manual004 labels; preserve original results and independently inspectable notes."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ORIGINAL=ROOT/'refine-logs/review-replacement-validation-20261023/SEMANTIC_AUDIT.json'

# joint constraint rejection, contains definite false criticism, evidence note
REVISED={
 1:('no','no','Accepts car constraint and option3; records access limits. Repeating draft unresolved speed is overcautious but not itself an objection to joint reasoning.'),
 2:('yes','yes','Calls son-driver an unsupported premise and joint constraints contradictory; shared omission is not counterevidence. Also criticizes reversion merely because initial option already3.'),
 3:('yes','yes','Explicitly says son joint fit is overreach because own S02 lacks male/car/father; attributed other-source facts can be combined. Owner ambiguity remains separate.'),
 4:('yes','yes','Says son-driver is added inference, not joint fit, because T does not specify; overlooks combined car/age/male constraints.'),
 5:('no','no','Accepts result and no unsupported generalization; repeats unnecessary driver/speed caution but does not reject inference.'),
 6:('yes','yes','Says son-driver not in any source and hence unsupported strengthening despite citing all joint constraints. Gender excludes Y; not a reason to invalidate combination.'),
 7:('no','no','Accepts application/result, notes source scope; does not demand rejection of combined result.'),
 8:('yes','yes','Declares no support for son110kmh because shared explicit speeding onlyZ, and says Y branch dropped without argument despite male exclusion.'),
 9:('uncertain','uncertain','Validly says father-indirect phrase alone does not establish driver and causal drinking gloss interpretive; also ends by calling overall son conclusion overstrong. Narrow vs global critique unclear.'),
 10:('yes','yes','Objects son driver not stated in T and Z exclusion too firm despite direct car evidence. Validly notes father-causal gloss and unhelpful future check separately.'),
 11:('no','yes','No clear rejection of joint fit, but falsely claims car-versus-motorcycle answer only partially supplied when O3 directly gives the constraint.'),
 12:('yes','yes','Treats car-owner alcohol as driver identity, then calls joint car/age/male constraints inconsistent and son assignment unsupported. Actual owner/driver wording ambiguous, not proof combination fails.'),
 13:('uncertain','yes','Father-indirect phrase alone warrants interpretation caution; does not clearly isolate joint fit. Definite false author/access criticism remains: A2 cannot readS03 so criticizes A3 claiming ownS03.'),
 14:('yes','yes','Rejects son-driver because not independently stated, then falsely says driver limitation dropped; exact AFTER open point says no task fact he drove or sped.'),
 15:('yes','yes','Treats valid joint result as beyond scope of ownS02 plus inaccessible reports; falsely says driver limit removed although retained. Father-alone argument may still need qualification.'),
 16:('yes','yes','Says son-driver no source support; implies father responsibility points toX while ignoring indirect relation. Falsely says draft dropped driver limitation though open point retained.'),
}


def main():
    original=json.loads(ORIGINAL.read_text(encoding='utf-8'))
    rows=[]
    for r in original['rows']:
        if '004' not in r['task']:continue
        n=r['logical_call'];joint,false,note=REVISED[n]
        rows.append({**r,'prior_false_criticism':r['false_criticism'],'false_criticism':false,
                     'joint_constraint_erroneously_rejected':joint,'regrade_evidence_note':note})
    assert len(rows)==len(REVISED)==16
    summary={}
    for cond in ['A','B']:
        selected=[r for r in rows if r['condition']==cond]
        summary[cond]={'outputs':len(selected),
            'false_criticism_definite':sum(r['false_criticism']=='yes' for r in selected),
            'false_criticism_uncertain':sum(r['false_criticism']=='uncertain' for r in selected),
            'joint_inference_wrongly_rejected':sum(r['joint_constraint_erroneously_rejected']=='yes' for r in selected),
            'joint_rejection_uncertain':sum(r['joint_constraint_erroneously_rejected']=='uncertain' for r in selected)}
    out={'kind':'revised_manual004_audit','labeler':'executor_not_independent_output_readjudication',
         'scope':'prior32probe004subset_only_not_new_model_results',
         'note':'A=old duties; B=replacement duties of prior run, not upcoming C/S conditions.',
         'summary':summary,'rows':rows}
    Path(__file__).with_name('PRIOR_004_REGRADE.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
