"""Explicit bounded batch plans. Planning never calls the model or scorer."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from .protocol import SYSTEM_CAPS
from .run import PROJECT
from .schemas import Contracts
from .state import write_json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_plan(bundle, config, design, *, split="engineering", systems=None, seed=17, tokenizer=None):
    systems = systems or ["independent_aggregate", "static_debate", "coreta"]
    if split not in {"engineering", "pilot"} or len(set(systems)) != len(systems) or any(s not in SYSTEM_CAPS for s in systems):
        raise ValueError("Invalid development split or repeated/unknown system")
    bundle, config, design = bundle.resolve(), config.resolve(), design.resolve()
    rows = json.loads((bundle / "tasks.json").read_text(encoding="utf-8"))
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest["task_index_sha256"] != sha(bundle / "tasks.json"):
        raise ValueError("Development task index changed after selection")
    contracts = Contracts(design / "coreta.schema.json")
    jobs = []
    seen = set()
    for row in rows:
        if not row[split]:
            continue
        path = (bundle / row["path"]).resolve()
        if not path.is_relative_to(bundle / "public") or sha(path) != row["sha256"]:
            raise ValueError("Only frozen public task files may enter a runtime plan")
        task = json.loads(path.read_text(encoding="utf-8"))
        contracts.validate("PublicTask", task)
        if task["task_id"] != row["task_id"] or task["task_id"] in seen:
            raise ValueError("Task index id mismatch or duplicate")
        seen.add(task["task_id"])
        order = sorted(systems, key=lambda s: hashlib.sha256(f"coreta-order-v1|{task['task_id']}|{seed}|{s}".encode()).hexdigest())
        for system in order:
            job_id = hashlib.sha256(f"{task['task_id']}|{seed}|{system}".encode()).hexdigest()[:20]
            jobs.append({"job_id": job_id, "task_id": task["task_id"], "family": row["family"],
                         "task_path": str(path), "task_sha256": row["sha256"], "system": system, "seed": seed})
    if not jobs:
        raise ValueError("Selected development split is empty")
    counting = {"mode": "conservative_utf8_bytes", "tokenizer": None}
    if tokenizer is not None:
        tokenizer = tokenizer.resolve()
        counting = {"mode": "local_tokenizer_estimate", "tokenizer": str(tokenizer), "sha256": sha(tokenizer)}
    return {"version": "coreta-batch/1", "input_counting": counting, "split": split, "bundle": str(bundle), "config": str(config),
            "design_root": str(design), "source_hashes": {str(p): sha(p) for p in
            (config, design / "coreta.schema.json", design / "PROMPTS.md", bundle / "manifest.json")},
            "task_count": len(seen), "job_count": len(jobs), "jobs": jobs,
            "normal_call_upper_bound": sum(SYSTEM_CAPS[job["system"]] for job in jobs),
            "model_calls_executed": 0}


def verify_plan(plan):
    if plan.get("version") != "coreta-batch/1":
        raise ValueError("Unsupported batch plan")
    counting = plan.get("input_counting", {})
    if counting.get("tokenizer") and sha(Path(counting["tokenizer"])) != counting["sha256"]:
        raise ValueError("Tokenizer changed after planning")
    for path, expected in plan["source_hashes"].items():
        if sha(Path(path)) != expected:
            raise ValueError("Batch source changed; create a new plan")
    for job in plan["jobs"]:
        if sha(Path(job["task_path"])) != job["task_sha256"]:
            raise ValueError("Public task changed after planning")


def completed_job(directory, job):
    for attempt in sorted(directory.glob("attempt_*")):
        result = attempt / "result.json"
        if not result.exists():
            continue
        row = json.loads(result.read_text(encoding="utf-8"))
        if any(row[key] != job[key] for key in ("task_id", "system", "seed")):
            raise ValueError("Existing result does not belong to its planned job")
        return True
    return False


def run_batch(plan_path, root, *, max_jobs, live=False, execute=subprocess.run):
    if not live or max_jobs < 1:
        raise ValueError("Execution requires --live and a positive --max-jobs bound")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    verify_plan(plan)
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise ValueError("DEEPSEEK_API_KEY is not configured; no batch jobs were started")
    root.mkdir(parents=True, exist_ok=True)
    binding = root / "batch_binding.json"
    plan_digest = sha(plan_path)
    if binding.exists():
        if json.loads(binding.read_text(encoding="utf-8"))["plan_sha256"] != plan_digest:
            raise ValueError("Run directory belongs to a different plan")
    else:
        write_json(binding, {"plan_sha256": plan_digest, "plan_path": str(plan_path.resolve())})
    config = json.loads(Path(plan["config"]).read_text(encoding="utf-8"))
    timeout = config["protocol"]["task_timeout_seconds"] + 60
    report = {"jobs_started": 0, "jobs_skipped_complete": 0, "attempts": []}
    for job in plan["jobs"]:
        job_root = root / job["job_id"]
        if completed_job(job_root, job):
            report["jobs_skipped_complete"] += 1
            continue
        if report["jobs_started"] >= max_jobs:
            break
        verify_plan(plan)
        job_root.mkdir(exist_ok=True)
        indices = [int(p.name.removeprefix("attempt_")) for p in job_root.glob("attempt_*") if p.is_dir()]
        attempt = job_root / f"attempt_{max(indices, default=0) + 1:04d}"
        command = [sys.executable, "-m", "coreta.run", "--task", job["task_path"], "--config", plan["config"],
                   "--design-root", plan["design_root"], "--system", job["system"], "--seed", str(job["seed"]),
                   "--output", str(attempt.resolve()), "--draft-bank", str((root / "draft-bank").resolve()), "--live"]
        if plan.get("input_counting", {}).get("tokenizer"):
            command.extend(["--tokenizer", plan["input_counting"]["tokenizer"]])
        report["jobs_started"] += 1
        try:
            process = execute(command, capture_output=True, text=True, encoding="utf-8", timeout=timeout, check=False)
            record = {"job_id": job["job_id"], "attempt": str(attempt), "returncode": process.returncode,
                      "stdout": process.stdout, "stderr": process.stderr}
        except subprocess.TimeoutExpired:
            record = {"job_id": job["job_id"], "attempt": str(attempt), "error": "outer_task_timeout"}
        result_path = attempt / "result.json"
        if record.get("returncode") == 0:
            if not result_path.exists():
                record["stop_reason"] = "missing_result"
            else:
                result = json.loads(result_path.read_text(encoding="utf-8"))
                if any(result.get(key) != job[key] for key in ("task_id", "system", "seed")):
                    record["stop_reason"] = "result_identity_mismatch"
                elif any(error.get("code") in {"MODEL_UNAVAILABLE", "MODEL_TIMEOUT"} for error in result.get("errors", [])):
                    record["stop_reason"] = "model_infrastructure_failure"
                    record["errors"] = result["errors"]
        report["attempts"].append(record)
        with (root / "batch_attempts.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        # Do not silently continue an entire campaign after an implementation/entry failure.
        if record.get("returncode") != 0 or record.get("stop_reason"):
            report["stop_reason"] = record.get("stop_reason", record.get("error", "process_failure"))
            break
    return report


def main():
    parser = argparse.ArgumentParser(description="Plan or explicitly run a bounded development batch")
    sub = parser.add_subparsers(dest="mode", required=True)
    build = sub.add_parser("plan")
    build.add_argument("--bundle", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--split", choices=["engineering", "pilot"], default="engineering")
    build.add_argument("--systems", nargs="+", choices=list(SYSTEM_CAPS), default=None)
    build.add_argument("--seed", type=int, default=17)
    build.add_argument("--tokenizer", type=Path)
    build.add_argument("--config", type=Path, default=PROJECT / "config/deepseek_flash.json")
    build.add_argument("--design-root", type=Path, default=PROJECT / "design/v0.3")
    run = sub.add_parser("run")
    run.add_argument("--plan", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--max-jobs", type=int, required=True)
    run.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.mode == "plan":
        if args.output.exists():
            parser.error("Plan output already exists")
        plan = build_plan(args.bundle, args.config, args.design_root, split=args.split, systems=args.systems, seed=args.seed, tokenizer=args.tokenizer)
        write_json(args.output, plan)
        print(json.dumps({key: plan[key] for key in ("task_count", "job_count", "normal_call_upper_bound", "model_calls_executed")}))
    else:
        print(json.dumps(run_batch(args.plan, args.output, max_jobs=args.max_jobs, live=args.live), ensure_ascii=False))


if __name__ == "__main__":
    main()
