"""Aggregate preserved live usage and explicit human semantic annotations; no keyword scoring."""
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
LIVE = PROJECT / 'runs/review-replacement-live-20261023-r1'

# Manual annotations after reading the complete observation/scope and corresponding frozen packet.
# no = no concrete instance identified under this rubric; not a proof of full correctness.
# Columns: logical_call, access_error, false_criticism, evidence/comment.
MANUAL = [
 (1,'no','no',"Directly reads S02/T; recognizes car exclusion and records indirect S01/S03."),
 (2,'no','yes',"Criticizes reverting because option_3 was already W3, as though this invalidates rejection of public W4. A candidate can be reconsidered without the selected before option changing. Other driver/speed concerns are legitimate."),
 (3,'no','uncertain',"Correct A2/S02 identity and car constraint; calls a disclosed conditional joint-fit an overreach. Whether this is excessive criticism is ambiguous."),
 (4,'no','uncertain',"Correct A1/S01 identity and explicit car constraint. Flags driver premise with qualification; alleged loss of speed-location limit is partly covered by residual open point."),
 (5,'no','no',"A2/S02 direct, expressly accepts car constraint; flags rather than denies son-driver inference."),
 (6,'no','uncertain',"Correctly identifies W3→W5 and car constraint; alleges A2's recorded current position conflicts with reconsideration, but contribution reconsideration is not necessarily a new final preference."),
 (7,'no','no',"Checks its S02 directly; maintains separate peer-report limits and disclosed uncertainty."),
 (8,'no','yes',"Claims W5 drops Mrs.Y without argument; W5 explicitly says Mrs.Y is excluded by S03's 'a man'. Legitimate driver/owner uncertainty also present."),
 (9,'no','no',"A2/T/S02 identity correct; accepts vehicle repair; separates inference from direct source text."),
 (10,'no','uncertain',"A1 knows S01 directly and cites it; criticism of 'excluded' despite conditional peer-report boundary may be excessive, but not labeled definite."),
 (11,'no','yes',"Claims O3 does not supply the car-versus-motorcycle confirmation. O3 explicitly states car-type constraint affirmatively counts against option_1 and rules out the motorcyclist."),
 (12,'no','uncertain',"Correct A1/S01 boundary. Owner/alcohol ambiguity real; treating indirect father responsibility as pointing toward father rather than son may misread the relation, but mixed judgment retained uncertain."),
 (13,'yes','yes',"A2 calls A3-authored W5's 'My direct original S03' a provenance defect because A2 cannot access S03; confuses work author and checker."),
 (14,'no','yes',"Says W5 silently drops uncertainty that son drove; AFTER open point explicitly says 'no task fact says he drove or sped'. Other driver-identity concerns valid."),
 (15,'no','yes',"Says AFTER no longer records son not shown driving, only unexplained speed; same open point explicitly records both."),
 (16,'no','yes',"Says W5 loses explicit driver limitation; AFTER open point retains 'no task fact says he drove or sped'. Car constraint is acknowledged."),
 (17,'yes','yes',"A2 maps its S01 inaccessibility onto A1-authored W6, claiming 'My own direct original S01' overstates access. A1 really holds S01."),
 (18,'no','no',"Focuses on real discrepancy between recorded W4 base and text claiming revised from W5; does not detect Pine-danger report loss."),
 (19,'no','no',"A2/S02 correct, correctly distinguishes A1 indirect access, but approves Pine inference framing and misses explicit W4 danger report."),
 (20,'no','yes',"Claims APPLICATION_SOURCE_REFS omits O4 despite exact frozen list [O5,O4,S01,T,W4,W5]; cross-offer retention is permitted. Misses Pine report loss."),
 (21,'no','no',"A2/S02 identity correct; says no supported content dropped but does not notice W4 explicit Pine-danger report."),
 (22,'no','no',"A3/S03 boundary correct; accepts inference framing and says no reported information lost. Primary error missed."),
 (23,'yes','yes',"A2 attributes its SOURCE_ACCESS S02 to A1, wrongly faults A1's indirect S02 statement. Scope says originals 'not read by me' alone is not counted; role mapping error is explicit."),
 (24,'yes','yes',"A3 faults A1-authored W6's direct S01 statement because A3 only holds S03; asks to rewrite A1's source as peer-reported."),
 (25,'no','yes',"Calls S02 restatement near-direct despite opening 'O5 answers from A2\'s directly read original S02 (which I still cannot read myself)'; explicit carrier already present. Primary error missed."),
 (26,'yes','uncertain',"A3 refers to 'my directly read S01/S03', then scope correctly limits originals to S03/T. Internal access contradiction. Mild Cedar-direction critique not definite false label."),
 (27,'yes','yes',"A2 calls Q1 'my Q1' (A1 authored it) and says 'I cannot read S02'. Also demands inaccessible S03 citation although O4 carrier declared; violates existing source convention."),
 (28,'no','uncertain',"A3 source boundary correct; finding issue partly based on O3 redundancy explicitly described as not incorrect. No clear substantive issue; retained uncertain."),
 (29,'yes','no',"A2 says S02 wording cannot be independently confirmed by me and 'I cannot access' S02 despite included own original; no_issue_found, so not counted as false criticism."),
 (30,'yes','yes',"A3 scope misnames self A1 and assigns S03 to A1; urges editor to declare inaccessible S03 because checker holds it. Editor must cite actual public carrier O4."),
 (31,'no','yes',"A2/S02 correct but calls omission of private S03 a declaration gap despite O4 declared and indirect reliance explicit; contradicts existing carrier citation convention."),
 (32,'no','no',"A3/T/S03 identity correct; recognizes O4 citation, but endorses Pine inference and never flags original report loss."),
]


def main():
    rows = [json.loads(x) for x in (LIVE / 'stages.jsonl').read_text(encoding='utf-8').splitlines()]
    responses = [json.loads(x) for x in (LIVE / 'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    lookup = {x['call_context']['logical_call']: x for x in responses}
    manual = {x[0]: x[1:] for x in MANUAL}
    assert len(rows) == len(manual) == len(responses) == 32
    annotated = []
    for row in rows:
        c = row['call_context']; access, false, reason = manual[c['logical_call']]
        usage = lookup[c['logical_call']]['response']['usage']
        is034 = '034' in c['task']
        annotated.append({**c, 'finding': row['output']['finding'],
            'pine_report_loss_detected': 'no' if is034 else 'not_applicable',
            'vehicle_constraint_preserved': 'not_applicable' if is034 else 'yes',
            'access_error': access, 'false_criticism': false, 'manual_evidence_note': reason,
            'observation_verbatim': row['output']['observation'], 'scope_verbatim': row['output']['scope'],
            'usage': usage})
    summary = {}
    for cond in ('A','B'):
        selected = [r for r in annotated if r['condition'] == cond]
        summary[cond] = {'reviews': len(selected),
            'pine_report_loss_detected': sum(r['pine_report_loss_detected']=='yes' for r in selected),
            'pine_applicable_reviews': sum(r['pine_report_loss_detected']!='not_applicable' for r in selected),
            'vehicle_constraint_preserved': sum(r['vehicle_constraint_preserved']=='yes' for r in selected),
            'vehicle_applicable_reviews': sum(r['vehicle_constraint_preserved']!='not_applicable' for r in selected),
            'access_errors': sum(r['access_error']=='yes' for r in selected),
            'false_criticism_definite': sum(r['false_criticism']=='yes' for r in selected),
            'false_criticism_uncertain': sum(r['false_criticism']=='uncertain' for r in selected),
            'input_tokens': sum(r['usage']['input_tokens'] for r in selected),
            'output_tokens': sum(r['usage']['output_tokens'] for r in selected)}
    out = {'kind': 'manual_fixed_review_probe_audit', 'labeler': 'executor_manual_not_independent',
           'scope': 'two_selected_tasks_correlated_versions_roles_repeats_not_independent_sample',
           'rubric': 'refine-logs/review-replacement-validation-20261023/RUBRIC.md',
           'summary': summary, 'rows': annotated}
    target = Path(__file__).with_name('SEMANTIC_AUDIT.json')
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
