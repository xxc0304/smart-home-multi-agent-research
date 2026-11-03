"""Offline coverage, scoring and descriptive summaries for a frozen development plan."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from coreta.batch import sha, verify_plan
from coreta.scoring import score_math_results, score_mbpp
from coreta.state import write_json


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-file", type=Path, required=True)
    parser.add_argument("--math-preflight", type=Path, required=True)
    args = parser.parse_args()
    plan = read(args.plan)
    verify_plan(plan)
    if read(args.runs / "batch_binding.json")["plan_sha256"] != sha(args.plan):
        raise ValueError("Run directory does not match the plan")
    expected = {(j["task_id"], j["system"], j["seed"]) for j in plan["jobs"]}
    if len(expected) != len(plan["jobs"]):
        raise ValueError("Duplicate planned trajectory")
    trajectories = []
    missing = []
    for job in plan["jobs"]:
        paths = sorted((args.runs / job["job_id"]).glob("attempt_*/result.json"))
        if len(paths) != 1:
            missing.append({"job_id": job["job_id"], "results_found": len(paths)})
            continue
        result = read(paths[0])
        if any(result.get(k) != job[k] for k in ("task_id", "system", "seed")):
            raise ValueError("Result identity mismatch")
        trajectories.append((job, result, paths[0].parent))
    if missing:
        raise ValueError(f"Coverage incomplete or ambiguous: {missing}")
    args.output.mkdir(parents=True, exist_ok=False)
    image = args.image_file.read_text(encoding="utf-8").strip()
    bundle = Path(plan["bundle"])
    mbpp = {r["task_id"]: r for r in read(bundle / "evaluation/mbpp_tests.json")}
    scores, run_rows = [], []
    for index, (job, result, directory) in enumerate(trajectories, 1):
        if job["family"] == "gsm8k":
            rows = score_math_results(bundle / "evaluation/math_gold.json", args.math_preflight, [result], image=image)
        elif job["family"] == "mbpp":
            rows = []
            for field in ("prefinal_artifact", "artifact"):
                scored = score_mbpp({**mbpp[result["task_id"]], "artifact": result[field]},
                                    args.output / f"{job['job_id']}-{field}", image)
                raw = scored.get("task_score", {"status": "scoring_error", "score": None})
                rows.append({**raw, "task_id": result["task_id"], "system": result["system"],
                             "seed": result["seed"], "artifact_field": field,
                             "trajectory_status": result["status"], "diagnostic_only": False})
        else:
            raise ValueError("Unsupported development task family")
        scores.extend({**row, "family": job["family"]} for row in rows)
        events = lines(directory / "events.jsonl")
        requests = lines(directory / "requests.jsonl")
        responses = lines(directory / "responses.jsonl")
        actions = Counter(e["payload"]["next"]["action"] for e in events if e["kind"] == "lead_update")
        contributions = Counter(e["payload"]["status"] for e in events if e["kind"] == "contribution")
        applications = [e["payload"]["application"] for e in events
                        if e["kind"] == "lead_update" and e["payload"].get("application")]
        usage = Counter()
        returned_models = set()
        for response in responses:
            body = response.get("response", {})
            if body.get("model"):
                returned_models.add(body["model"])
            for key in ("input_tokens", "output_tokens", "total_tokens"):
                usage[key] += body.get("usage", {}).get(key, 0)
        bank_hashes = {e["sent_from"]: hashlib.sha256(json.dumps(e["payload"], sort_keys=True).encode()).hexdigest()
                       for e in events[:3] if e["kind"] == "draft"}
        row = {**{key: result[key] for key in ("task_id", "system", "seed", "status", "normal_calls",
                                               "format_repairs", "http_attempts", "errors")},
               "family": job["family"], "directory": str(directory.resolve()),
               "result_sha256": sha(directory / "result.json"), "actions": dict(actions),
               "contributions": dict(contributions), "request_events": sum(e["kind"] == "request" for e in events),
               "application_dispositions": dict(Counter(a["disposition"] for a in applications)),
               "application_outcomes_self_reported": dict(Counter(a["application_outcome"] for a in applications)),
               "context_pruning_events": len(lines(directory / "context.jsonl")), "usage": dict(usage),
               "returned_models": sorted(returned_models), "initial_draft_hashes": bank_hashes,
               "transport_errors": sum(r.get("status") == "transport_error" for r in responses),
               "incomplete_responses": sum(r.get("response", {}).get("status") not in (None, "completed") for r in responses),
               "input_count_estimates": [r.get("estimated_input_count") for r in requests]}
        run_rows.append(row)
        write_json(args.output / "scores.partial.json", scores)
        write_json(args.output / "runs.partial.json", run_rows)
        print(json.dumps({"scored_trajectories": index, "total": len(trajectories),
                          "task_id": result["task_id"], "system": result["system"]}), flush=True)
    observed = {(r["task_id"], r["system"], r["seed"], r["artifact_field"]) for r in scores}
    if observed != {(*key, field) for key in expected for field in ("artifact", "prefinal_artifact")}:
        raise ValueError("Scored metric coverage mismatch")
    groups = defaultdict(list)
    for row in scores:
        groups[(row["family"], row["system"], row["artifact_field"])].append(row)
    descriptive = []
    for (family, system, field), rows in sorted(groups.items()):
        unresolved = sum(r["score"] is None for r in rows)
        successes = sum(r["score"] == 1 for r in rows)
        descriptive.append({"family": family, "system": system, "artifact_field": field,
                            "planned": len(rows), "successes": successes, "unresolved": unresolved,
                            "accuracy": successes / len(rows) if unresolved == 0 else None})
    pairings = []
    by_task = defaultdict(dict)
    for row in scores:
        if row["artifact_field"] == "artifact":
            by_task[(row["family"], row["task_id"])][row["system"]] = row["score"]
    for family in sorted({j["family"] for j in plan["jobs"]}):
        for other in ("static_debate", "independent_aggregate"):
            counts = Counter()
            for (fam, task), values in by_task.items():
                if fam != family:
                    continue
                left, right = values["coreta"], values[other]
                outcome = "unresolved" if left is None or right is None else "win" if left > right else "loss" if left < right else "tie"
                counts[outcome] += 1
            pairings.append({"family": family, "left": "coreta", "right": other, "counts": dict(counts)})
    draft_checks = []
    for task in sorted({j["task_id"] for j in plan["jobs"]}):
        rows = [r for r in run_rows if r["task_id"] == task]
        same = all(r["initial_draft_hashes"] == rows[0]["initial_draft_hashes"] for r in rows)
        complete = set(rows[0]["initial_draft_hashes"]) == {"A0", "A1", "A2"}
        draft_checks.append({"task_id": task, "same_three_drafts": same and complete})
    report = {"scope": "single-repetition development pilot; descriptive, no formal effectiveness or causal claim",
              "plan_sha256": sha(args.plan), "scoring_image": image,
              "evaluation_sha256": {"math_gold": sha(bundle / "evaluation/math_gold.json"),
                                    "mbpp_tests": sha(bundle / "evaluation/mbpp_tests.json"),
                                    "math_preflight": sha(args.math_preflight)},
              "coverage_complete": True, "trajectories": len(trajectories), "metric_records": len(scores),
              "all_shared_drafts_verified": all(r["same_three_drafts"] for r in draft_checks),
              "shared_draft_checks": draft_checks, "descriptive_scores": descriptive, "paired_outcomes": pairings,
              "runs": run_rows}
    write_json(args.output / "scores.json", scores)
    write_json(args.output / "summary.json", report)


if __name__ == "__main__":
    main()
