"""Frozen two-task, four-condition development comparison. No gold enters generation."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from coreta.revision import REVISION_SYSTEMS
from coreta.state import write_json

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "engineering/REVISION_COMPARISON_PLAN_20261019.json"
OUT = ROOT / "runs/revision-comparison-20261019"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    if PLAN.exists():
        raise ValueError("Frozen plan already exists")
    bundle = ROOT / "data/development-20261019"
    audit_path = ROOT / "engineering/DEVELOPMENT_POOL_QUALITY_AUDIT_20261019.json"
    audits = {r["task_id"]: r for r in json.loads(audit_path.read_text(encoding="utf-8"))["records"]}
    index = json.loads((bundle / "tasks.json").read_text(encoding="utf-8"))
    selected, exclusions = [], []
    for family in ("gsm8k", "mbpp"):
        eligible = []
        for row in index:
            if row["family"] != family:
                continue
            if row["pilot"] or audits[row["task_id"]]["findings"]:
                exclusions.append({"task_id": row["task_id"], "reason": "previous pilot" if row["pilot"] else "static-review finding"})
                continue
            path = bundle / row["path"]
            if sha(path) != row["sha256"]:
                raise ValueError("Public task hash mismatch")
            task = json.loads(path.read_text(encoding="utf-8"))
            eligible.append((len(task["prompt"]), row["task_id"], row, path))
        length, _, row, path = sorted(eligible, key=lambda item: (-item[0], item[1]))[0]
        selected.append({"task_id": row["task_id"], "family": family, "task_path": str(path),
                         "sha256": sha(path), "prompt_characters": length})
    sources = [ROOT / "config/deepseek_flash.json", ROOT / "design/revision_prompts.json",
               ROOT / "design/v0.3/coreta.schema.json", ROOT / "src/coreta/revision.py",
               ROOT / "src/coreta/run_revision.py", ROOT / "src/coreta/model_client.py",
               ROOT / "src/coreta/schemas.py", ROOT / "src/coreta/state.py", Path(__file__),
               bundle / "tasks.json", audit_path, ROOT / "data/tokenizer-v4.1-flash-1017/tokenizer.json"]
    jobs = []
    for task in selected:
        ordered = sorted(REVISION_SYSTEMS, key=lambda s: hashlib.sha256((task["task_id"] + "|17|" + s).encode()).hexdigest())
        for system in ordered:
            jobs.append({**task, "system": system, "seed": 17,
                         "job_id": hashlib.sha256((task["task_id"] + "|" + system).encode()).hexdigest()[:16]})
    write_json(PLAN, {"version": "revision-comparison/1", "purpose": "development; not formal evaluation",
        "selection": "one longest public prompt per family among non-pilot tasks with no prior static-review finding; ties by task id",
        "limitations": "prompt length is not validated difficulty; review was local/posthoc, not blind; this is a selected development subset",
        "tasks": selected, "exclusions": exclusions, "jobs": jobs, "output": str(OUT),
        "normal_call_upper_bound": sum(REVISION_SYSTEMS[j["system"]] for j in jobs),
        "source_hashes": {str(p): sha(p) for p in sources}})
    print(json.dumps({"plan": str(PLAN), "tasks": selected, "jobs": len(jobs)}))


def verify(plan):
    for path, expected in plan["source_hashes"].items():
        if sha(Path(path)) != expected:
            raise ValueError("Frozen source changed: " + path)
    for task in plan["tasks"]:
        if sha(Path(task["task_path"])) != task["sha256"]:
            raise ValueError("Frozen public task changed")


def run():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    verify(plan)
    OUT.mkdir(parents=True, exist_ok=True)
    for job in plan["jobs"]:
        verify(plan)
        output = OUT / job["job_id"]
        if output.exists():
            raise ValueError("Existing job directory; inspect before any resume: " + str(output))
        command = [sys.executable, "-m", "coreta.run_revision", "--task", job["task_path"],
                   "--system", job["system"], "--seed", "17", "--output", str(output),
                   "--tokenizer", str(ROOT / "data/tokenizer-v4.1-flash-1017/tokenizer.json"),
                   "--draft-bank", str(OUT / "draft-bank"), "--live"]
        print(json.dumps({"starting": job["job_id"], "task_id": job["task_id"], "system": job["system"]}), flush=True)
        completed = subprocess.run(command, check=False)
        result_path = output / "result.json"
        if completed.returncode or not result_path.exists():
            raise RuntimeError("Job failed; batch stopped: " + job["job_id"])
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result["status"] != "completed":
            raise RuntimeError("Protocol degradation; batch stopped: " + job["job_id"])
    print(json.dumps({"jobs_completed": len(plan["jobs"])}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "run"))
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.mode == "build":
        build()
    elif not args.live:
        parser.error("Explicit --live required; no jobs launched")
    else:
        run()


if __name__ == "__main__":
    main()
