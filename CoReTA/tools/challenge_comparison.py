"""Frozen comparison on a manually reviewed challenge slice from train sources."""
from __future__ import annotations

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
PLAN = ROOT / "engineering/CHALLENGE_COMPARISON_PLAN_20261019.json"
OUT = ROOT / "runs/challenge-comparison-20261019"
TASK_IDS = (
    "gsm8k/train/310", "gsm8k/train/3750", "gsm8k/train/7446", "gsm8k/train/5129",
    "mbpp/train/721", "mbpp/train/751", "mbpp/train/622",
)


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path: Path):
    return [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def build():
    if PLAN.exists() or OUT.exists():
        raise ValueError("Plan or output already exists; refusing to overwrite")
    bundle = ROOT / "data/complementarity-challenge-20261019"
    index = {row["task_id"]: row for row in read(bundle / "tasks.json")}
    tasks, jobs = [], []
    for task_id in TASK_IDS:
        row = index[task_id]
        path = bundle / row["path"]
        if sha(path) != row["sha256"]:
            raise ValueError("Public task hash mismatch: " + task_id)
        task = {"task_id": task_id, "family": row["family"], "task_path": str(path), "sha256": sha(path)}
        tasks.append(task)
        for system in sorted(REVISION_SYSTEMS, key=lambda name: hashlib.sha256((task_id + "|17|" + name).encode()).hexdigest()):
            jobs.append({**task, "system": system, "seed": 17,
                         "job_id": hashlib.sha256((task_id + "|" + system).encode()).hexdigest()[:16]})

    evaldir = bundle / "evaluation"
    source_paths = [ROOT / "src/coreta" / name for name in
                    ("revision.py", "run_revision.py", "model_client.py", "schemas.py", "state.py")]
    source_paths += [ROOT / "design/revision_prompts.json", ROOT / "design/v0.3/coreta.schema.json",
                     ROOT / "config/deepseek_flash.json", ROOT / "data/tokenizer-v4.1-flash-1017/tokenizer.json",
                     bundle / "manifest.json", bundle / "tasks.json", evaldir / "math_gold.json", evaldir / "mbpp_tests.json",
                     ROOT / "engineering/CHALLENGE_TASK_REVIEW_20261019.md",
                     ROOT / "tools/prepare_challenge_tasks.py", Path(__file__)]
    write_json(PLAN, {
        "version": "challenge-comparison/1",
        "purpose": "single-seed development challenge diagnostic; not formal evaluation",
        "tasks": tasks,
        "jobs": jobs,
        "selection": "seven predeclared untried train tasks selected by multi-step reference solution or algorithm/test complexity, manually checked against frozen prompts and offline scores before model generation",
        "conditions": list(REVISION_SYSTEMS),
        "seed": 17,
        "normal_call_upper_bound": sum(REVISION_SYSTEMS[job["system"]] for job in jobs),
        "failure_policy": "retain protocol degradation and continue frozen jobs; stop on implementation/entry failure; no automatic retry, task replacement or protocol change",
        "generation_visibility": "public task only; no gold answers, tests, scoring results or prior task attempts",
        "source_hashes": {str(path): sha(path) for path in source_paths},
        "output": str(OUT),
    })
    print(json.dumps({"plan": str(PLAN), "tasks": TASK_IDS, "jobs": len(jobs),
                      "normal_call_upper_bound": sum(REVISION_SYSTEMS[job["system"]] for job in jobs)}))


def verify(plan):
    for path, expected in plan["source_hashes"].items():
        if sha(Path(path)) != expected:
            raise ValueError("Frozen source changed: " + path)
    for task in plan["tasks"]:
        if sha(Path(task["task_path"])) != task["sha256"]:
            raise ValueError("Frozen public task changed: " + task["task_id"])


def run():
    plan = read(PLAN)
    verify(plan)
    OUT.mkdir(parents=True, exist_ok=False)
    for job in plan["jobs"]:
        verify(plan)
        folder = OUT / job["job_id"]
        if folder.exists():
            raise ValueError("Existing job directory; refusing resume or overwrite: " + str(folder))
        command = [sys.executable, "-m", "coreta.run_revision", "--task", job["task_path"],
                   "--system", job["system"], "--seed", "17", "--output", str(folder),
                   "--tokenizer", str(ROOT / "data/tokenizer-v4.1-flash-1017/tokenizer.json"),
                   "--draft-bank", str(OUT / "draft-bank"), "--live"]
        print(json.dumps({"starting": job["job_id"], "task_id": job["task_id"], "system": job["system"]}), flush=True)
        completed = subprocess.run(command, check=False)
        result_path = folder / "result.json"
        if completed.returncode or not result_path.exists():
            raise RuntimeError("Implementation/entry failure; batch stopped: " + job["job_id"])
        result = read(result_path)
        with (OUT / "progress.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"job_id": job["job_id"], "status": result["status"],
                                     "stop_reason": result["stop_reason"], "errors": result["errors"]}) + "\n")
    print(json.dumps({"jobs_finished": len(plan["jobs"])}))


def score():
    plan = read(PLAN)
    verify(plan)
    image = (ROOT / "engineering/SCORING_IMAGE_20261019.txt").read_text(encoding="utf-8").strip()
    evaluation = ROOT / "data/complementarity-challenge-20261019/evaluation"
    gold = {row["task_id"]: row for row in read(evaluation / "math_gold.json")}
    tests = {row["task_id"]: row for row in read(evaluation / "mbpp_tests.json")}
    banks, rows, traces = {}, [], []
    for job in plan["jobs"]:
        folder = OUT / job["job_id"]
        result = read(folder / "result.json")
        if result["task_id"] != job["task_id"] or result["system"] != job["system"]:
            raise ValueError("Result does not match frozen job")
        events = lines(folder / "events.jsonl")
        drafts = [event for event in events if event["stage"] == "draft"]
        hashes = [fingerprint(event["payload"]) for event in drafts]
        if len(hashes) != 3:
            raise ValueError("Missing initial drafts; preserve this failure and stop scoring")
        first = job["task_id"] not in banks
        if banks.setdefault(job["task_id"], hashes) != hashes:
            raise ValueError("Conditions did not share identical initial drafts")
        targets = [("prefinal", result["prefinal_artifact"]), ("final", result["artifact"])]
        if first:
            targets = [("draft-" + event["sent_from"], event["payload"]["artifact"]) for event in drafts] + targets
        for label, artifact in targets:
            if job["family"] == "gsm8k":
                scored = docker_math_records([{**gold[job["task_id"]], "artifact": artifact}], image)[0]
            else:
                record = {**tests[job["task_id"]], "artifact": artifact}
                score_job = OUT / "scoring" / (job["job_id"] + "-" + label)
                launched = score_mbpp(record, score_job, image)
                scored = launched.get("task_score", {"status": "scoring_error", "score": None})
            rows.append({"task_id": job["task_id"], "system": "shared_initial" if label.startswith("draft-") else job["system"],
                         "label": label, "job_id": job["job_id"], "score": scored.get("score"), "detail": scored})
    write_json(ROOT / "engineering/CHALLENGE_COMPARISON_SCORES_20261019.json", rows)
    for job in plan["jobs"]:
        folder = OUT / job["job_id"]
        result = read(folder / "result.json")
        events = lines(folder / "events.jsonl")
        traces.append({**result, "draft_hashes": [fingerprint(event["payload"]) for event in events if event["stage"] == "draft"],
                       "stages": [event["stage"] for event in events],
                       "actions": [event["payload"]["next"]["action"] for event in events if event["stage"] == "apply"]})
    write_json(ROOT / "engineering/CHALLENGE_COMPARISON_TRACES_20261019.json", traces)
    summaries = []
    for task in plan["tasks"]:
        tid = task["task_id"]
        task_rows = [row for row in rows if row["task_id"] == tid]
        drafts = [row["score"] for row in task_rows if row["system"] == "shared_initial"]
        summaries.append({"task_id": tid, "family": task["family"], "shared_initial_scores": drafts,
                          "all_initial_wrong": len(drafts) == 3 and all(score == 0 for score in drafts),
                          "final_scores": {row["system"]: row["score"] for row in task_rows if row["label"] == "final"},
                          "statuses": {row["system"]: row["status"] for row in traces if row["task_id"] == tid}})
    summary = {"tasks": summaries, "job_count": len(traces), "shared_initials_verified": True,
               "normal_calls": sum(row["normal_calls"] for row in traces),
               "http_attempts": sum(row["http_attempts"] for row in traces),
               "format_repairs": sum(row["format_repairs"] for row in traces),
               "scoring_image": image, "scope": "six manually reviewed development tasks, one seed; no population or equal-cost claim"}
    write_json(ROOT / "engineering/CHALLENGE_COMPARISON_SUMMARY_20261019.json", summary)
    report = ["# 挑战任务小规模对照：原始结果", "", "日期：2026-10-19。单seed开发诊断，不作总体效果推断。", "",
              "| 任务 | 初稿A0/A1/A2 | CoReTA | 静态讨论 | 独立综合 | 独立继续推理 |", "|---|---:|---:|---:|---:|---:|"]
    for row in summaries:
        scores = row["final_scores"]
        report.append(f"| `{row['task_id']}` | {row['shared_initial_scores']} | {scores.get('coreta_revision')} | {scores.get('static_debate')} | {scores.get('independent_aggregate')} | {scores.get('independent_refine')} |")
    report += ["", f"共{len(traces)}条轨迹，{summary['normal_calls']}次逻辑调用、{summary['http_attempts']}次HTTP尝试、{summary['format_repairs']}次格式修复。", "",
               "评分是原始gold/测试分数；`all_initial_wrong`只表示三份完整初稿都未通过，不代表已核实存在可互补的局部信息。详见对应轨迹和离线评分明细。"]
    (ROOT / "engineering/CHALLENGE_COMPARISON_REPORT_20261019.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "run", "score"))
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.mode == "build":
        build()
    elif args.mode == "run":
        if not args.live:
            parser.error("Explicit --live required")
        run()
    else:
        score()


if __name__ == "__main__":
    main()
