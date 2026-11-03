"""Offline-only scoring and factual trace export; never imported by the pilot runtime."""
import argparse
import json
from pathlib import Path

from coreta.handoff.__main__ import PROJECT
from coreta.handoff.inputs import read_json
from coreta.handoff.gateway import write_json


def score(artifact, ranks):
    valid = (isinstance(artifact, list) and len(artifact) == len(ranks)
             and len(set(artifact)) == len(ranks) and set(artifact) == set(ranks))
    distance = sum(abs(i - ranks[name]) for i, name in enumerate(artifact, 1)) if valid else 8
    return {"deliverable": valid, "exact": int(valid and distance == 0), "l1": distance}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Score output must be new")
    gold = read_json(PROJECT / "data/task-packs/student-president-dev-v1/offline/evaluator.json")
    ranks = gold["reference_ranks_by_exact_name"]
    progress = read_json(args.run / "progress.json")
    report = {"kind": "offline_student_president_behavior_pilot", "run_status": progress["status"],
              "http_attempts": progress["http_attempts"], "pairs": [], "method_units": []}
    for pair in progress["pairs"]:
        cache = read_json(args.run / pair["pair"] / "initial/cache.json")
        initials = {m: score(w["artifact"], ranks) for m, w in cache["candidates"].items()}
        any_correct = any(s["exact"] for s in initials.values())
        initial_complete = len(initials) == 4
        all_full = initial_complete and all(s["deliverable"] for s in initials.values())
        report["pairs"].append({**pair, "initial_scores": initials, "initial_set_complete": initial_complete,
                                "initial_any_correct": any_correct,
                                "initial_all_full_answers": all_full,
                                "initial_none_correct_full_delivery": initial_complete and not any_correct,
                                "initial_all_wrong": all_full and not any_correct})
    for row in progress["units"]:
        item = dict(row)
        folder = args.run / row["pair"] / row["method"]
        if not (folder / "result.json").exists():
            report["method_units"].append(item)
            continue
        result = read_json(folder / "result.json")
        work = result["selected_work"]
        item.update(score=score(work["artifact"] if work else None, ranks), editor=result["editor"],
                    logical_calls=result["logical_calls"], http_attempts=result["http_attempts"],
                    usage=result["usage"], uncertain_usage_attempts=result["uncertain_usage_attempts"],
                    incomplete_or_unknown_usage_attempts=result["incomplete_or_unknown_usage_attempts"])
        state = read_json(folder / "state.json")
        item["candidate_trajectory"] = [{"work_id": w["id"], "author": w["author"],
                                         "initial": w["initial"], **score(w["artifact"], ranks)} for w in state["works"]]
        events = [json.loads(line) for line in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        kinds = [event["kind"] for event in events]
        item["protocol_event_counts_not_semantic_success"] = {
            key: kinds.count(key) for key in ("offer_proposed", "offer_selected", "offer_untried",
              "offer_not_applied", "trial_created", "offer_adopted", "selection_unchanged", "check_observation")}
        pair_summary = next(p for p in report["pairs"] if p["pair"] == row["pair"])
        item["all_initial_wrong_recovered"] = bool(pair_summary["initial_all_wrong"] and item["score"]["exact"])
        item["any_initial_correct_lost"] = bool(pair_summary["initial_any_correct"] and not item["score"]["exact"])
        item["semantic_review_status"] = "not_yet_manually_reviewed"
        report["method_units"].append(item)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, report)
    print(json.dumps({"output": str(args.output), "scored_units": sum("score" in r for r in report["method_units"])}))


if __name__ == "__main__":
    main()
