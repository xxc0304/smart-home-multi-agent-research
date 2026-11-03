"""Offline official-label scoring; never imported by the experiment runtime."""
import argparse
import hashlib
import json
from pathlib import Path


def read(path): return json.loads(path.read_text(encoding="utf-8"))


def score(artifact,evaluation):
    valid=isinstance(artifact,str) and artifact in {c["id"] for c in evaluation["choices"]}
    return {"deliverable":valid,"exact":int(valid and artifact==evaluation["correct_option_id"])}


def score_run(run,output):
    if output.exists(): raise ValueError("New score output required")
    manifest=read(run/"manifest.json");progress=read(run/"progress.json")
    dataset=Path(manifest["dataset"]);data_manifest=read(dataset/"dataset_manifest.json")
    report={"kind":"offline_hiddenbench_development_scores","status":progress["status"],
            "http_attempts":progress["http_attempts"],"pairs":[],"units":[],"references":[]}
    for pair in manifest["pairs"]:
        path=Path(pair["pack"])/"offline/evaluation.json"
        if hashlib.sha256(path.read_bytes()).hexdigest()!=data_manifest["file_hashes"][str(path.relative_to(dataset))]:
            raise ValueError("Offline evaluator changed after projection")
        evaluation=read(path);folder=run/pair["id"]
        cache=folder/"initial/cache.json"
        initial=read(cache)["candidates"] if cache.exists() else {}
        scores={m:score(w["artifact"],evaluation) for m,w in initial.items()}
        pair_row={"pair":pair["id"],"task_id":pair["task_id"],"initial_scores":scores,
                  "all_initial_full_and_wrong":len(scores)==pair["members"] and
                    all(s["deliverable"] and not s["exact"] for s in scores.values()),
                  "any_initial_correct":any(s["exact"] for s in scores.values())}
        report["pairs"].append(pair_row)
        for method in pair["methods"]:
            row=dict(next(r for r in progress["units"] if r["pair"]==pair["id"] and r["method"]==method))
            result_path=folder/method/"result.json"
            if result_path.exists():
                result=read(result_path);work=result["selected_work"]
                row["score"]=score(work["artifact"] if work else None,evaluation)
                state=read(folder/method/"state.json")
                row["correct_candidate_available_but_not_delivered"]=bool(
                    not row["score"]["exact"] and any(score(w["artifact"],evaluation)["exact"] for w in state["works"]))
                row["any_initial_correct_lost"]=bool(pair_row["any_initial_correct"] and not row["score"]["exact"])
                row["full_initial_failure_recovered"]=bool(pair_row["all_initial_full_and_wrong"] and row["score"]["exact"])
                row["usage"]=result["usage"]
                row["semantic_use_review"]="not_inferred_from_ids_or_event_counts"
            report["units"].append(row)
        for mode in manifest["reference_modes"]:
            row=dict(next(r for r in progress["references"] if r["pair"]==pair["id"] and r["mode"]==mode))
            path=folder/mode/"reference_result.json"
            if path.exists():row.update(score=score(read(path)["output"]["artifact"],evaluation),usage=read(path)["usage"])
            report["references"].append(row)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--run",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path);args=parser.parse_args()
    r=score_run(args.run,args.output);print(json.dumps({"scored_units":sum('score' in u for u in r['units'])}))
