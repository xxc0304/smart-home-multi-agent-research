"""Score archived shared initial drafts offline; never generate or modify pilot answers."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from coreta.batch import sha, verify_plan
from coreta.scoring import docker_math_records, load_gold, score_mbpp
from coreta.state import write_json


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    p = args.project.resolve()
    plan = read(p / "engineering/DEVELOPMENT_PILOT_TOKENIZER_PLAN_20261019.json")
    verify_plan(plan)
    root = p / "runs/development-pilot-20261019"
    plan_path = p / "engineering/DEVELOPMENT_PILOT_TOKENIZER_PLAN_20261019.json"
    if read(root / "batch_binding.json")["plan_sha256"] != sha(plan_path):
        raise ValueError("Plan binding mismatch")
    bundle = Path(plan["bundle"])
    image = (p / "engineering/SCORING_IMAGE_20261019.txt").read_text(encoding="utf-8").strip()
    gold_path = bundle / "evaluation/math_gold.json"
    preflight = read(p / "engineering/container-check-20261019-final/development_math_preflight.json")
    if not preflight["ready"] or preflight["diagnostic_only"] or preflight["gold_sha256"] != sha(gold_path) or preflight["image"] != image:
        raise ValueError("Scoring preflight mismatch")
    gold = {r["task_id"]: r for r in load_gold(gold_path)}
    tests = {r["task_id"]: r for r in read(bundle / "evaluation/mbpp_tests.json")}
    args.output.mkdir(parents=True, exist_ok=False)
    drafts, decisions = [], []
    for job in plan["jobs"]:
        if job["system"] != "coreta":
            continue
        directory = root / job["job_id"] / "attempt_0001"
        events = [json.loads(x) for x in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        initial = [e for e in events if e["kind"] == "draft"]
        if [e["sent_from"] for e in initial] != ["A0", "A1", "A2"]:
            raise ValueError("Expected exactly three initial drafts")
        for event in initial:
            drafts.append({"task_id": job["task_id"], "family": job["family"], "actor": event["sent_from"],
                           "artifact": event["payload"]["artifact"], "event_id": event["event_id"],
                           "run_directory": str(directory), "event_log_sha256": sha(directory / "events.jsonl")})
        for request in map(json.loads, (directory / "requests.jsonl").read_text(encoding="utf-8").splitlines()):
            text = request["payload"]["instructions"]
            if "STAGE = \"bootstrap\"" in text:
                decisions.append({"task_id": job["task_id"], "attempt": request["attempt"],
                                  "remaining_two_explicit": "REMAINING_WORK_TURNS = 2" in text,
                                  "all_five_actions_supplied": all(action in text.split("LEGAL_ACTIONS = ")[-1].split("\n")[0]
                                                                   for action in ("CONTINUE_SELF", "REQUEST_HELP", "REQUEST_CHECK", "REQUEST_ALTERNATIVE", "FINISH")),
                                  "all_three_drafts_supplied": all(e["event_id"] in text for e in initial),
                                  "max_output_tokens": request["payload"]["max_output_tokens"]})
    output = []
    for family in ("gsm8k", "mbpp"):
        rows = [r for r in drafts if r["family"] == family]
        if family == "gsm8k":
            records = [{"task_id": r["task_id"], "answer": gold[r["task_id"]]["answer"], "artifact": r["artifact"]} for r in rows]
            scored = docker_math_records(records, image)
            for row, score in zip(rows, scored, strict=True):
                if row["task_id"] != score["task_id"]:
                    raise ValueError("Math score order mismatch")
                output.append({k: v for k, v in row.items() if k != "artifact"} | {"scorer": score, "score": score["score"]})
        else:
            for index, row in enumerate(rows):
                launched = score_mbpp({**tests[row["task_id"]], "artifact": row["artifact"]}, args.output / f"code-{index:03d}", image)
                score = launched.get("task_score", {"status": "scoring_error", "score": None})
                output.append({k: v for k, v in row.items() if k != "artifact"} | {"scorer": score, "score": score["score"]})
        print(json.dumps({"family": family, "scored_initial_drafts": len(rows)}), flush=True)
    grouped = defaultdict(dict)
    for row in output:
        grouped[row["task_id"]][row["actor"]] = row["score"]
    if len(grouped) != 20 or any(set(v) != {"A0", "A1", "A2"} for v in grouped.values()):
        raise ValueError("Initial draft coverage mismatch")
    task_rows = []
    for task, scores in sorted(grouped.items()):
        resolved = all(s in (0, 1) for s in scores.values())
        task_rows.append({"task_id": task, "scores": scores,
                          "a0_wrong_peer_passes": scores["A0"] == 0 and any(scores[a] == 1 for a in ("A1", "A2")) if resolved else None,
                          "oracle_pass": max(scores.values()) if resolved else None})
    report = {"scope": "posthoc diagnostic of archived initial drafts, not new model experiments or causal complementarity evidence",
              "new_model_calls": 0, "image": image, "plan_sha256": sha(plan_path), "records": output,
              "task_scores": task_rows, "decision_inputs": decisions,
              "actor_successes": {a: sum(r["score"] == 1 for r in output if r["actor"] == a) for a in ("A0", "A1", "A2")},
              "unresolved_scorer_records": sum(r["score"] is None for r in output),
              "a0_wrong_peer_passes_tasks": [r["task_id"] for r in task_rows if r["a0_wrong_peer_passes"]],
              "all_three_fail_tasks": [r["task_id"] for r in task_rows if set(r["scores"].values()) == {0}]}
    write_json(args.output / "summary.json", report)


if __name__ == "__main__":
    main()
