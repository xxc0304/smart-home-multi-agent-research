"""Manual semantic audit and service-usage aggregation; no online evaluator."""
import json
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[2]
LIVE=PROJECT/'runs/evidence-focus-live-20261023-r1'

# Human labels after reading every full observation/scope. No keyword scoring.
NOTES={
 1:'Approves Pine inference demotion and says no reported content lost; never identifies explicit reported danger.',
 2:'Highlight still yields drift-only reading and approval of downgrade.',
 3:'Quotes W4 explicit danger but calls downgrade supported. Misattributes extra W4 Cedar excerpt as residual AFTER content despite VERSION_PAIR.',
 4:'Describes W4 danger as inference and approves downgrade; O3 omission criticism does not address target.',
 5:'Quotes full explicit report, then calls reducing source attribution a supported narrowing and says no content lost.',
 6:'Approves demotion; minor erroneous O5 omission is self-corrected, then faults provenance already explicitly via O5.',
 7:'Highlights Cedar caution and washout; omits explicit Pine-danger content in source report.',
 8:'Quotes W4 danger report, but evaluates against shared task facts rather than preserving reported S01 content; downgrade endorsed.',
 9:'Approves demotion; also wrongly says cannot directly access visible W5 public artifact, confusing source originals and public text.',
 10:'Quotes danger phrasing but calls W6 more faithful; public-report boundary otherwise correctly limited.',
 11:'Approves inference demotion and calls no loss; misses report-fidelity issue.',
 12:'Quotes full W4 S01-danger sentence yet calls demotion a genuine faithfulness improvement.',
 13:'Explicitly quotes W4 danger, calls it as though verified, then approves weaker report as legitimate because S01 unavailable.',
 14:'Reasons if S01 only says north and criticizes flat Pine rejection; ignores W4 expressly reporting danger.',
 15:'Approves softened Pine inference; falsely says O5 absent while actual declarations include it.',
 16:'Says no supported W4 content lost and approves inference framing.',
 17:'Says inference is correct strength for a source I cannot read, conflating original verification with fidelity to public report.',
 18:'Quotes old danger statement and approves downgrade; wrongly treats Cedar route/supply absence from partial excerpt and omitted Maple discussion as revision defects.',
 19:'Says genuine softening from W4 Cedar claim, never distinguishes explicit Pine report.',
 20:'Approves Pine inference framing; does not use appended explicit report as counterevidence.',
 21:'Mentions W4 dangerous statement but says it merely treats drift as verified plume-path fact and no reported information lost.',
 22:'Only evaluates Cedar softening and source-declaration matters; misses Pine report loss.',
 23:'Quotes exact full old S01-danger sentence, then says shared information does not certify danger so demotion more faithful.',
 24:'Approves inference downgrade and falsely says O4 absent despite its presence in declared_sources.',
}
EXPLICIT={3,5,8,10,12,13,18,21,23}


def main():
    stages=[json.loads(x) for x in (LIVE/'stages.jsonl').read_text(encoding='utf-8').splitlines()]
    responses=[json.loads(x) for x in (LIVE/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(stages)==len(responses)==len(NOTES)==24
    usage={r['call_context']['logical_call']:r['response']['usage'] for r in responses}
    rows=[]
    for item in stages:
        c=item['call_context'];n=c['logical_call']
        rows.append({**c,'primary_report_loss_detected':'no','partial_recognition':False,
            'old_explicit_danger_statement_discussed_manual':n in EXPLICIT,
            'manual_reason':NOTES[n],'observation_verbatim':item['output']['observation'],
            'scope_verbatim':item['output']['scope'],'finding':item['output']['finding'],'usage':usage[n]})
    summary={}
    for condition in ['F','H','L']:
        selected=[r for r in rows if r['condition']==condition]
        summary[condition]={'completed':len(selected),'detected':0,'partial':0,
            'explicit_danger_statement_discussed':sum(r['old_explicit_danger_statement_discussed_manual'] for r in selected),
            'input_tokens':sum(r['usage']['input_tokens'] for r in selected),
            'output_tokens':sum(r['usage']['output_tokens'] for r in selected),
            'by_input':[{'system':system,'stage':stage,'detected':0,'reviews':sum(r['system']==system and r['stage']==stage for r in selected)}
                        for system in ['v3_continuation','d0_continuation'] for stage in ['CHECK_USE','CHECK_EFFECT']]}
    result={'kind':'manual_evidence_focus_diagnostic_audit','labeler':'executor_manual_not_independent',
            'scope':'one_task_related_contexts_not_final_answer_efficacy','summary':summary,'rows':rows}
    Path(__file__).with_name('SEMANTIC_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
