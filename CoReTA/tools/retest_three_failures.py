"""Bounded diagnostic rerun of the three originally failed tasks, original scoring."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from coreta.revision import REVISION_SYSTEMS
from coreta.scoring import docker_math_records, score_mbpp
from coreta.state import write_json

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "engineering/THREE_FAILURES_PLAN_20261019.json"
OUT = ROOT / "runs/three-failures-retest-20261019"
TASK_IDS = ("gsm8k/train/5134", "mbpp/train/615", "mbpp/train/802")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def build():
    if PLAN.exists():
        raise ValueError("Plan already frozen")
    bundle = ROOT / "data/development-20261019"
    index = {r["task_id"]: r for r in read(bundle / "tasks.json")}
    tasks, jobs = [], []
    for task_id in TASK_IDS:
        row = index[task_id]
        path = bundle / row["path"]
        if sha(path) != row["sha256"]:
            raise ValueError("Original public task changed")
        task = {"task_id": task_id, "family": row["family"], "task_path": str(path), "sha256": sha(path)}
        tasks.append(task)
        ordered = sorted(REVISION_SYSTEMS, key=lambda s: hashlib.sha256((task_id + "|17|" + s).encode()).hexdigest())
        for system in ordered:
            jobs.append({**task, "system": system, "seed": 17,
                         "job_id": hashlib.sha256((task_id + "|" + system).encode()).hexdigest()[:16]})
    paths = [ROOT / "src/coreta" / name for name in
             ("revision.py", "run_revision.py", "model_client.py", "schemas.py", "state.py")]
    paths += [ROOT / "design/revision_prompts.json", ROOT / "design/v0.3/coreta.schema.json",
              ROOT / "config/deepseek_flash.json", ROOT / "data/tokenizer-v4.1-flash-1017/tokenizer.json",
              bundle / "tasks.json", bundle / "evaluation/math_gold.json", bundle / "evaluation/mbpp_tests.json", Path(__file__)]
    write_json(PLAN, {"version": "three-failures-diagnostic/1", "tasks": tasks, "jobs": jobs,
        "selection": "the three previously failed team tasks explicitly requested by user; no task edits",
        "scope": "original-score diagnostic with known contract questions; not an effectiveness estimate",
        "normal_call_upper_bound": sum(REVISION_SYSTEMS[j["system"]] for j in jobs),
        "failure_policy": "retain protocol degradation and continue other frozen jobs; stop on implementation failure; no automatic retry or protocol changes",
        "source_hashes": {str(p): sha(p) for p in paths}, "output": str(OUT)})
    print(json.dumps({"tasks": TASK_IDS, "jobs": len(jobs), "normal_call_bound": 114}))


def verify(plan):
    for path, expected in plan["source_hashes"].items():
        if sha(Path(path)) != expected:
            raise ValueError("Frozen source changed: " + path)
    for task in plan["tasks"]:
        if sha(Path(task["task_path"])) != task["sha256"]:
            raise ValueError("Public task changed")


def run():
    plan = read(PLAN)
    verify(plan)
    OUT.mkdir(parents=True, exist_ok=True)
    for job in plan["jobs"]:
        verify(plan)
        directory = OUT / job["job_id"]
        if directory.exists():
            raise ValueError("Existing attempt; refuse silent resume or overwrite")
        command = [sys.executable, "-m", "coreta.run_revision", "--task", job["task_path"],
                   "--system", job["system"], "--output", str(directory), "--seed", "17",
                   "--draft-bank", str(OUT / "draft-bank"), "--tokenizer",
                   str(ROOT / "data/tokenizer-v4.1-flash-1017/tokenizer.json"), "--live"]
        print(json.dumps({"starting": job["job_id"], "task_id": job["task_id"], "system": job["system"]}), flush=True)
        completed = subprocess.run(command, check=False)
        if completed.returncode or not (directory / "result.json").exists():
            raise RuntimeError("Implementation/entry failure; inspect before continuing")
        result = read(directory / "result.json")
        with (OUT / "progress.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"job_id": job["job_id"], "status": result["status"], "errors": result["errors"]}) + "\n")
    print(json.dumps({"jobs_finished": len(plan["jobs"])}))


def score():
    plan = read(PLAN)
    verify(plan)
    image = (ROOT / "engineering/SCORING_IMAGE_20261019.txt").read_text(encoding="utf-8").strip()
    evaluation = ROOT / "data/development-20261019/evaluation"
    gold = {r["task_id"]: r for r in read(evaluation / "math_gold.json")}
    tests = {r["task_id"]: r for r in read(evaluation / "mbpp_tests.json")}
    banks, rows, traces = {}, [], []
    for job in plan["jobs"]:
        directory = OUT / job["job_id"]
        result = read(directory / "result.json")
        if result["task_id"] != job["task_id"] or result["system"] != job["system"]:
            raise ValueError("Unexpected result identity")
        events = lines(directory / "events.jsonl")
        drafts = [e for e in events if e["stage"] == "draft"]
        hashes = [fingerprint(e["payload"]) for e in drafts]
        if len(hashes) != 3:
            raise ValueError("Incomplete initial bank; retain failure before comparing")
        first = job["task_id"] not in banks
        if banks.setdefault(job["task_id"], hashes) != hashes:
            raise ValueError("Initial bank differs across conditions")
        targets = [("prefinal", result["prefinal_artifact"]), ("final", result["artifact"])]
        if first:
            targets = [("draft-" + e["sent_from"], e["payload"]["artifact"]) for e in drafts] + targets
        for label, artifact in targets:
            if job["family"] == "gsm8k":
                scored = docker_math_records([{**gold[job["task_id"]], "artifact": artifact}], image)[0]
            else:
                record = {**tests[job["task_id"]], "artifact": artifact}
                folder = OUT / "scoring" / (job["job_id"] + "-" + label)
                if (folder / "launcher_result.json").exists():
                    if read(folder / "input/mbpp.json") != record or read(folder / "manifest.json")["image"] != image:
                        raise ValueError("Archived scoring differs")
                    launched = read(folder / "launcher_result.json")
                else:
                    launched = score_mbpp(record, folder, image)
                scored = launched.get("task_score", {"status": "scoring_error", "score": None})
            rows.append({"task_id": job["task_id"], "system": "shared_initial" if label.startswith("draft") else job["system"],
                         "label": label, "score": scored.get("score"), "detail": scored})
            write_json(ROOT / "engineering/THREE_FAILURES_SCORES_20261019.json", rows)
        traces.append({**result, "draft_hashes": hashes,
                       "stages": [e["stage"] for e in events],
                       "actions": [e["payload"]["next"]["action"] for e in events if e["stage"] == "apply"]})
    write_json(ROOT / "engineering/THREE_FAILURES_TRACES_20261019.json", traces)
    summary = [{"task_id": tid, "old_team_score": 0,
                "new_shared_draft_scores": [r["score"] for r in rows if r["task_id"] == tid and r["system"] == "shared_initial"],
                "new_final_scores": {r["system"]: r["score"] for r in rows if r["task_id"] == tid and r["label"] == "final"}}
               for tid in TASK_IDS]
    write_json(ROOT / "engineering/THREE_FAILURES_SUMMARY_20261019.json", {"tasks": summary,
        "shared_initials_verified": True, "normal_calls": sum(r["normal_calls"] for r in traces),
        "http_attempts": sum(r["http_attempts"] for r in traces), "format_repairs": sum(r["format_repairs"] for r in traces),
        "runtime_statuses": {r["run_id"]: r["status"] for r in traces}, "scoring_image": image})
    print(json.dumps(summary))


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
        run()


if __name__ == "__main__":
    main()
