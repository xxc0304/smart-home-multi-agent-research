"""Offline-only scoring/navigation extraction. Never imported by a solving launcher."""
import argparse
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def analyze(root):
    root = Path(root)
    progress, manifest = read(root / "progress.json"), read(root / "manifest.json")
    rows = []
    inputs = Path(manifest["input_preparation"])
    for unit in progress["units"]:
        result_path = root / unit["checkpoint"] / unit["system"] / "result.json"
        if not result_path.exists():
            rows.append({**unit, "final_exact": None})
            continue
        result = read(result_path)
        snapshot = read(inputs / unit["checkpoint"] / "snapshot.json")
        task = unit["checkpoint"].split("-r", 1)[0]
        gold = read(PROJECT / "data/task-packs/hiddenbench-workboard-dev-v1" / task / "offline/evaluation.json")["correct_option_id"]
        works = {w["id"]: w for w in snapshot["visible_works"]}
        first = result["first_choice"]
        row = {"checkpoint": unit["checkpoint"], "system": unit["system"], "status": result["status"],
               "error": result["error"], "before_exact": snapshot["before"]["artifact"] == gold,
               "original_trial_exact": snapshot["after"]["artifact"] == gold,
               "first_choice_id": first["candidate_id"] if first else None,
               "first_choice_exact": works[first["candidate_id"]]["artifact"] == gold if first else None,
               "selected_work_id": result["selected_work_id"],
               "final_exact": result["selected_work"]["artifact"] == gold if result["status"] == "completed" else None,
               "selected_artifact": result["selected_work"]["artifact"],
               "delivery_used_fallback": result["delivery_used_fallback"],
               "actual_http_attempts": result["actual_http_attempts"],
               "input_tokens": sum(u.get("input_tokens", 0) for u in result["usage"]),
               "output_tokens": sum(u.get("output_tokens", 0) for u in result["usage"]),
               "unknown_usage": result["incomplete_or_unknown_usage_attempts"],
               "focuses_opened": len(result["focus_history"]),
               "reported_addressed": sum(f["status"] == "addressed" for f in result["focus_history"]),
               "response_offers": sum(len(f["responses"]) for f in result["focus_history"]),
               "selected_response_navigation_links": sum(a["relation"] == "selected_response"
                        for f in result["focus_history"] for a in f["applications"])}
        rows.append(row)
    summary = {"kind": "offline_local_probe_analysis", "scope": "two_selected_development_checkpoints_not_end_to_end",
               "live_status": progress["status"], "rows": rows,
               "warning": "Focus fields are navigation/model reports, not verified mechanism success. Interrupted fallback is not a completed outcome."}
    out = root / "analysis"
    out.mkdir(exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.run), ensure_ascii=False))
