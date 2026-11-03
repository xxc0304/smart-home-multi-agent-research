"""Offline-only math process wrapper and Docker code scoring launcher."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .state import write_json


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_math_platform(diagnostic):
    if not diagnostic and not sys.platform.startswith("linux"):
        raise RuntimeError("Formal math scoring requires Linux; use --diagnostic only for local adapter checks")
    if importlib.metadata.version("math-verify") != "0.9.0":
        raise RuntimeError("Math-Verify 0.9.0 is required by this scoring protocol")


def math_process(record, *, diagnostic=False, preflight=False, timeout=25):
    require_math_platform(diagnostic)
    request = {"record": record, "diagnostic": diagnostic, "preflight": preflight}
    for attempt in range(2):
        try:
            response = subprocess.run([sys.executable, "-m", "coreta.scoring_worker", "math"],
                                      input=json.dumps(request), capture_output=True, text=True,
                                      encoding="utf-8", timeout=timeout, check=False)
            if response.returncode:
                result = {"task_id": record["task_id"], "status": "scoring_error", "score": None,
                          "error_type": "worker_exit", "detail": response.stderr[-500:]}
            else:
                result = json.loads(response.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            result = {"task_id": record["task_id"], "status": "scoring_error", "score": None, "error_type": type(exc).__name__}
        result.update({"attempts": attempt + 1, "diagnostic_only": diagnostic, "math_verify_version": "0.9.0"})
        if result["status"] != "scoring_error":
            return result
    return result


def load_gold(path):
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("Gold must be a nonempty list of task_id/answer records")
    if any(not isinstance(row.get("task_id"), str) or not isinstance(row.get("answer"), str) for row in rows):
        raise ValueError("Gold task_id and answer must be strings")
    if len({row["task_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate gold task ids")
    return rows


def preflight_math(gold_path, *, diagnostic=False, image=None):
    rows = load_gold(gold_path)
    if image and diagnostic:
        raise ValueError("Docker uses formal Linux scoring, not Windows diagnostic mode")
    results = docker_math_records(rows, image, preflight=True) if image else [
        math_process(row, diagnostic=diagnostic, preflight=True) for row in rows]
    return {"gold_sha256": digest(gold_path), "diagnostic_only": diagnostic,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "math_verify_version": "0.9.0", "image": image,
            "ready": all(row["status"] == "ready" for row in results), "records": results}


def score_math_results(gold_path, preflight_path, results, *, diagnostic=False, image=None):
    report = json.loads(preflight_path.read_text(encoding="utf-8"))
    gold = {row["task_id"]: row for row in load_gold(gold_path)}
    if not report.get("ready") or report.get("gold_sha256") != digest(gold_path):
        raise ValueError("Gold preflight missing, failed, or no longer matches the gold file")
    if report.get("diagnostic_only") != diagnostic or report.get("math_verify_version") != "0.9.0":
        raise ValueError("Preflight platform/mode/version must match scoring")
    if report.get("image") != image:
        raise ValueError("Preflight and scoring must use the same image")
    if image and diagnostic:
        raise ValueError("Docker scoring cannot be labeled diagnostic")
    output = []
    seen = set()
    for result in results:
        key = (result["task_id"], result["system"], result["seed"])
        if key in seen:
            raise ValueError("Duplicate prediction trajectory")
        seen.add(key)
        if result["task_id"] not in gold:
            raise ValueError("Prediction has no gold record")
        for field in ("prefinal_artifact", "artifact"):
            record = {**gold[result["task_id"]], "artifact": result[field]}
            row = docker_math_records([record], image)[0] if image else math_process(record, diagnostic=diagnostic)
            output.append({**row, "system": result["system"], "seed": result["seed"],
                           "artifact_field": field, "trajectory_status": result["status"]})
    return output


def read_jsonl(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def subset_problems(mother_path, samples):
    ids = [row["task_id"] for row in samples]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Exactly one sample per task is required")
    if any(set(row) != {"task_id", "solution"} or not isinstance(row["solution"], str) for row in samples):
        raise ValueError("Samples must use task_id/solution full-source format")
    mother_rows = read_jsonl(mother_path)
    mother = {row["task_id"]: row for row in mother_rows}
    if len(mother) != len(mother_rows) or not set(ids).issubset(mother):
        raise ValueError("Duplicate mother-data ids or sample ids missing from mother data")
    # No test reformatting or construction: preserve each original dataset record.
    return [mother[task_id] for task_id in ids]


def docker_command(image, job, *, mode="humaneval", name):
    if not (re.fullmatch(r"sha256:[0-9a-f]{64}", image) or re.fullmatch(r"[^\s]+@sha256:[0-9a-f]{64}", image)):
        raise ValueError("Use an immutable local image id or registry digest, not a moving tag")
    if mode not in {"humaneval", "mbpp"}:
        raise ValueError("Unsupported scoring mode")
    job = job.resolve()
    return ["docker", "run", "--rm", "--pull=never", "--name", name, "--platform", "linux/amd64",
            "--network=none", "--read-only", "--user", "65532:65532", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--pids-limit=256", "--memory=4g", "--cpus=2",
            "--tmpfs", "/tmp:rw,size=1073741824,mode=1777", "--env", "HOME=/tmp", "--env", "XDG_CACHE_HOME=/tmp/cache",
            "--mount", f"type=bind,source={job / 'input'},target=/input,readonly",
            "--mount", f"type=bind,source={job / 'output'},target=/output",
            image, "python", "/opt/coreta-scoring-worker.py", mode]


def docker_math_records(records, image, *, preflight=False, timeout=180):
    # Reuse image validation and sandbox flags, omit code-input/output mounts.
    base = docker_command(image, Path.cwd(), name="coreta-math-" + uuid.uuid4().hex[:12])
    mount_start = base.index("--mount")
    command = base[:mount_start] + ["-i", image, "python", "/opt/coreta-scoring-worker.py", "math-batch"]
    name = command[command.index("--name") + 1]
    for attempt in range(2):
        try:
            response = subprocess.run(command, input=json.dumps({"records": records, "preflight": preflight}),
                                      capture_output=True, encoding="utf-8", text=True, timeout=timeout, check=False)
            break
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=30, check=False)
            if attempt:
                return [{"task_id": row["task_id"], "status": "scoring_error", "score": None,
                         "error_type": "container_timeout", "diagnostic_only": False, "attempts": 2} for row in records]
    if response.returncode:
        raise RuntimeError("Linux math worker failed: " + response.stderr[-1000:])
    rows = json.loads(response.stdout)
    if len(rows) != len(records) or any(row["task_id"] != source["task_id"] for row, source in zip(rows, records)):
        raise ValueError("Math worker result coverage mismatch")
    if any(row.get("math_verify_version") != "0.9.0" for row in rows):
        raise ValueError("Container Math-Verify version differs from the scoring protocol")
    return rows


def launch_job(command, *, timeout, run=subprocess.run):
    name = command[command.index("--name") + 1]
    try:
        completed = run(command, capture_output=True, text=True, encoding="utf-8", timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        # A killed docker client does not necessarily stop its container.
        run(["docker", "rm", "-f", name], capture_output=True, timeout=30, check=False)
        return {"status": "scoring_error", "score": None, "error_type": "container_timeout"}
    return {"status": "completed" if completed.returncode == 0 else "scoring_error", "returncode": completed.returncode,
            "stdout": completed.stdout, "stderr": completed.stderr}


def score_humaneval(samples_path, mother_path, job, image, *, timeout=1800):
    if not shutil.which("docker"):
        raise RuntimeError("Docker is unavailable; host code execution is not a fallback")
    samples = read_jsonl(samples_path)
    problems = subset_problems(mother_path, samples)
    job.mkdir(parents=True, exist_ok=False)
    (job / "input").mkdir()
    (job / "output").mkdir(mode=0o777)
    # Linux bind mount must be writable by the nonroot container user.
    (job / "output").chmod(0o777)
    for name, rows in (("samples.jsonl", samples), ("problems.jsonl", problems)):
        with (job / "input" / name).open("w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    name = "coreta-score-" + uuid.uuid4().hex[:12]
    command = docker_command(image, job, name=name)
    write_json(job / "manifest.json", {"image": image, "samples_sha256": digest(samples_path),
               "mother_sha256": digest(mother_path), "subset_sha256": digest(job / "input/problems.jsonl"),
               "task_ids": [row["task_id"] for row in samples], "command": command})
    result = launch_job(command, timeout=timeout)
    if result["status"] == "completed" and not (job / "output/samples_eval_results.json").is_file():
        result = {**result, "status": "scoring_error", "error_type": "missing_evaluator_output"}
    write_json(job / "launcher_result.json", result)
    return result


def score_mbpp(record, job, image, *, timeout=30):
    if not shutil.which("docker"):
        raise RuntimeError("Docker is unavailable; host code execution is not a fallback")
    required = {"task_id", "artifact", "test_imports", "test_list"}
    if set(record) != required or not record["test_list"]:
        raise ValueError("MBPP offline record requires task_id/artifact/test_imports/nonempty test_list")
    # Validate the image before creating job material.
    name = "coreta-mbpp-" + uuid.uuid4().hex[:12]
    command = docker_command(image, job, mode="mbpp", name=name)
    job.mkdir(parents=True, exist_ok=False)
    (job / "input").mkdir()
    (job / "output").mkdir(mode=0o777)
    (job / "output").chmod(0o777)
    write_json(job / "input/mbpp.json", record)
    write_json(job / "manifest.json", {"image": image, "input_sha256": digest(job / "input/mbpp.json"), "command": command})
    result = launch_job(command, timeout=timeout)
    output = job / "output/mbpp_score.json"
    if result["status"] == "completed":
        if output.exists():
            result["task_score"] = json.loads(output.read_text(encoding="utf-8"))
        else:
            result.update({"status": "scoring_error", "error_type": "missing_evaluator_output"})
    write_json(job / "launcher_result.json", result)
    return result


def evalplus_scores(path, expected_ids, *, system, seed):
    data = json.loads(path.read_text(encoding="utf-8"))["eval"]
    if set(data) != set(expected_ids):
        raise ValueError("Evaluator coverage must equal the planned sample task ids")
    rows = []
    allowed = {"pass", "fail", "timeout"}
    for task_id in expected_ids:
        samples = data[task_id]
        if len(samples) != 1:
            raise ValueError("pass@1 import requires one trajectory per task")
        sample = samples[0]
        base, plus = sample.get("base_status"), sample.get("plus_status")
        error = base not in allowed or plus not in allowed
        rows.append({"task_id": task_id, "system": system, "seed": seed,
                     "status": "scoring_error" if error else "scored",
                     "base_score": None if error else int(base == "pass"),
                     "plus_score": None if error else int(base == plus == "pass")})
    return rows


def main():
    parser = argparse.ArgumentParser(description="Offline scoring; never sends model requests")
    sub = parser.add_subparsers(dest="mode", required=True)
    pre = sub.add_parser("math-preflight")
    pre.add_argument("--gold", type=Path, required=True)
    pre.add_argument("--output", type=Path, required=True)
    pre.add_argument("--diagnostic", action="store_true")
    pre.add_argument("--image", help="Immutable Docker image for formal Linux scoring from Windows")
    score = sub.add_parser("math-score")
    score.add_argument("--gold", type=Path, required=True)
    score.add_argument("--preflight", type=Path, required=True)
    score.add_argument("--results", type=Path, required=True, help="JSON list of trajectory result records")
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--diagnostic", action="store_true")
    score.add_argument("--image", help="Must match the preflight's immutable Docker image")
    code = sub.add_parser("humaneval")
    code.add_argument("--samples", type=Path, required=True)
    code.add_argument("--mother-data", type=Path, required=True)
    code.add_argument("--job", type=Path, required=True)
    code.add_argument("--image", required=True)
    mbpp = sub.add_parser("mbpp")
    mbpp.add_argument("--record", type=Path, required=True, help="Offline task_id/artifact/test_imports/test_list record")
    mbpp.add_argument("--job", type=Path, required=True)
    mbpp.add_argument("--image", required=True)
    args = parser.parse_args()
    if args.mode == "humaneval":
        print(json.dumps(score_humaneval(args.samples, args.mother_data, args.job, args.image)))
        return
    if args.mode == "mbpp":
        print(json.dumps(score_mbpp(json.loads(args.record.read_text(encoding="utf-8")), args.job, args.image)))
        return
    if args.output.exists():
        parser.error("Output already exists; preserve earlier scoring records")
    if args.mode == "math-preflight":
        result = preflight_math(args.gold, diagnostic=args.diagnostic, image=args.image)
    else:
        result = score_math_results(args.gold, args.preflight, json.loads(args.results.read_text(encoding="utf-8")), diagnostic=args.diagnostic, image=args.image)
    write_json(args.output, result)


if __name__ == "__main__":
    main()
