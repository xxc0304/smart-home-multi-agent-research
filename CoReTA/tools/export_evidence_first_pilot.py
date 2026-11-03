"""Offline reference-choice export; never imported by the live request builder."""
import argparse
import json
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def export(prepared,run):
    prepared,run=Path(prepared),Path(run)
    plan=read(prepared/"PLAN.json");progress=read(run/"progress.json");review=read(run/"review.json")
    roster=plan["schedule"];by_slot={r["slot"]:r for r in review["rows"]}
    assert set(by_slot)=={r["slot"] for r in roster}
    references={task:read(prepared/f"OFFLINE_{task}.json") for task in plan["tasks"]}
    finals=[];summary={}
    for expected in roster:
        row=by_slot[expected["slot"]]
        assert {key:row[key] for key in expected}==expected
        if row["stage"]!="integrate":
            continue
        readable=row["status"]=="readable"
        answer=row.get("answer") or {}
        choice=answer.get("choice") if readable else None
        ref=references[row["task"]]["reference_choice"]
        outcome="technical_unknown" if not readable else "unresolved" if choice is None else "reference_match" if choice==ref else "reference_mismatch"
        finals.append(dict(slot=row["slot"],task=row["task"],repeat=row["repeat"],method=row["method"],status=row["status"],
                           choice=choice,reference=ref,reference_match=(choice==ref) if readable else None,outcome=outcome,
                           reasoning=answer.get("reasoning"),annotation_issues=answer.get("annotation_issues")))
    for method in ("ordinary","evidence_first"):
        selected=[r for r in finals if r["method"]==method]
        summary[method]=dict(planned=len(selected),readable=sum(r["status"]=="readable" for r in selected),
            reference_matches=sum(r["outcome"]=="reference_match" for r in selected),
            reference_mismatches=sum(r["outcome"]=="reference_mismatch" for r in selected),
            unresolved=sum(r["outcome"]=="unresolved" for r in selected),
            technical_unknown=sum(r["outcome"]=="technical_unknown" for r in selected))
    fixture=progress["mode"]!="live"
    report=dict(scope="TECHNICAL_FIXTURE_NOT_EXPERIMENTAL_RESULTS" if fixture else "DEVELOPMENT_PILOT_REFERENCE_AGREEMENT",
                mode=progress["mode"],execution_status=progress["status"],client_attempts=progress["attempts"],
                paid_live_requests=0 if fixture else progress["attempts"],by_method=summary,finals=finals,
                semantic_application="Not automatically scored. Correctness, applicability and harms require whole-text review.",
                reference_caution="005 reference agreement is not a formal unique-maximizer proof; no invented criterion weights.",
                technical_policy="Missing or blocked outputs remain null/technical_unknown, never silently counted as wrong or filled.",
                usage=dict(input_tokens=progress["input_tokens"],output_tokens=progress["output_tokens"],unknown_usage=progress["unknown_usage"]))
    (run/"SCORES.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared",required=True,type=Path)
    parser.add_argument("--run",required=True,type=Path)
    args=parser.parse_args()
    result=export(args.prepared,args.run)
    print(json.dumps({key:result[key] for key in ("scope","execution_status","by_method","paid_live_requests")},ensure_ascii=False))
