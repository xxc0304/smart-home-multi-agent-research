"""Retest archived task756 with unchanged public input and shared new drafts."""
import argparse
import hashlib
import json
from pathlib import Path

import revision_pilot
from coreta.revision import REVISION_SYSTEMS
from coreta.scoring import score_mbpp
from coreta.state import write_json

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "engineering/ARCHIVED_FAILURE_RETEST_PLAN_20261019.json"
OUT = ROOT / "runs/archived-failure-retest-20261019"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    if PLAN.exists():
        raise ValueError("Plan already frozen")
    old = read(ROOT / "engineering/PILOT_INITIAL_DRAFT_DIAGNOSTIC_20261019.json")
    scores = read(ROOT / "engineering/DEVELOPMENT_PILOT_SCORES_20261019.json")
    failed = [r for r in old["records"] if r["score"] == 0]
    wrong_ids = sorted({r["task_id"] for r in failed} | {r["task_id"] for r in scores if r["score"] == 0})
    write_json(ROOT / "engineering/ARCHIVED_FAILURE_INVENTORY_20261019.json", {
        "scope": "CoReTA E1 scored initial drafts and pre/final artifacts; earlier E0 failure is same task802",
        "source_hashes": {name: sha(ROOT / "engineering" / name) for name in
            ("PILOT_INITIAL_DRAFT_DIAGNOSTIC_20261019.json", "DEVELOPMENT_PILOT_SCORES_20261019.json")},
        "unique_task_ids": wrong_ids, "failed_initial_records": failed,
        "e1_zero_score_rows": len([r for r in scores if r["score"] == 0]),
        "decisions": {
            "gsm8k/train/5134": "percent-base conflict and noninteger literal count; retain original score; not a clean reasoning-failure case",
            "mbpp/train/615": "row/column contract conflict; retain original score; no silent reinterpretation",
            "mbpp/train/802": "some tests not cyclic-sortable; retain original score; not a clean whole-task failure",
            "mbpp/train/756": "A1/A2 return Match/None rather than tested bool; A0 passes; original public return contract not explicit; selected interface-error retest, not all-initial-wrong evidence"},
        "new_model_calls_at_freeze": 0})
    index = read(ROOT / "data/development-20261019/tasks.json")
    row = next(r for r in index if r["task_id"] == "mbpp/train/756")
    task_path = ROOT / "data/development-20261019" / row["path"]
    if sha(task_path) != row["sha256"]:
        raise ValueError("Original public task changed")
    task = {"task_id": row["task_id"], "family": "mbpp", "task_path": str(task_path), "sha256": row["sha256"]}
    systems = sorted(REVISION_SYSTEMS, key=lambda s: hashlib.sha256((row["task_id"] + "|17|" + s).encode()).hexdigest())
    jobs = [{**task, "system": system, "seed": 17,
             "job_id": hashlib.sha256((task["task_id"] + "|" + system).encode()).hexdigest()[:16]} for system in systems]
    paths = [ROOT / "src/coreta" / name for name in
             ("revision.py", "run_revision.py", "model_client.py", "schemas.py", "state.py")]
    paths += [ROOT / "design/revision_prompts.json", ROOT / "design/v0.3/coreta.schema.json",
              ROOT / "config/deepseek_flash.json", ROOT / "data/tokenizer-v4.1-flash-1017/tokenizer.json",
              Path(__file__), ROOT / "tools/revision_pilot.py"]
    write_json(PLAN, {"version": "archived-failure-retest/1", "purpose": "old interface-error task, diagnostic subset",
        "selection": "only archived task with observed member interface failures selected for original-contract retest; three contract-questioned whole-team failures not silently treated as model failures",
        "limitations": "task756 also does not explicitly specify bool; original assertions retained; A0 already passed; not an all-wrong recovery test",
        "tasks": [task], "jobs": jobs, "output": str(OUT), "normal_call_upper_bound": 38,
        "source_hashes": {str(path): sha(path) for path in paths}})
    print(json.dumps({"old_error_tasks": wrong_ids, "selected_retest": row["task_id"], "jobs": 4}))


def score():
    plan = read(PLAN)
    image = (ROOT / "engineering/SCORING_IMAGE_20261019.txt").read_text(encoding="utf-8").strip()
    tests = next(r for r in read(ROOT / "data/development-20261019/evaluation/mbpp_tests.json")
                 if r["task_id"] == "mbpp/train/756")
    results, items, bank = [], [], None
    for job in plan["jobs"]:
        directory = OUT / job["job_id"]
        result = read(directory / "result.json")
        events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        drafts = [e for e in events if e["stage"] == "draft"]
        hashes = [hashlib.sha256(json.dumps(e["payload"], sort_keys=True).encode()).hexdigest() for e in drafts]
        if len(hashes) != 3 or (bank is not None and hashes != bank):
            raise ValueError("Initial draft identity check failed")
        bank = hashes
        targets = [("prefinal", result["prefinal_artifact"]), ("final", result["artifact"])]
        if not items:
            targets = [("draft-" + e["sent_from"], e["payload"]["artifact"]) for e in drafts] + targets
        for label, artifact in targets:
            record = {**tests, "artifact": artifact}
            folder = OUT / "scoring" / (job["job_id"] + "-" + label)
            if (folder / "launcher_result.json").exists():
                if read(folder / "input/mbpp.json") != record or read(folder / "manifest.json")["image"] != image:
                    raise ValueError("Existing scoring material changed")
                launch = read(folder / "launcher_result.json")
            else:
                launch = score_mbpp(record, folder, image)
            item = {"system": "shared_initial" if label.startswith("draft") else job["system"], "label": label,
                    "detail": launch.get("task_score", {"status": "scoring_error", "score": None})}
            items.append(item)
            write_json(ROOT / "engineering/ARCHIVED_FAILURE_RETEST_SCORES_20261019.json", items)
        results.append({**result, "draft_hashes": hashes,
                        "stages": [e["stage"] for e in events],
                        "actions": [e["payload"]["next"]["action"] for e in events if e["stage"] == "apply"]})
    write_json(ROOT / "engineering/ARCHIVED_FAILURE_RETEST_RESULTS_20261019.json", results)
    print(json.dumps({"shared_initial_scores": [r["detail"].get("score") for r in items if r["system"] == "shared_initial"],
                      "final_scores": {r["system"]: r["detail"].get("score") for r in items if r["label"] == "final"}}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "run", "score"))
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.mode == "build":
        build()
    elif args.mode == "score":
        score()
    elif not args.live:
        parser.error("Explicit --live required")
    else:
        revision_pilot.PLAN, revision_pilot.OUT = PLAN, OUT
        revision_pilot.run()


if __name__ == "__main__":
    main()
