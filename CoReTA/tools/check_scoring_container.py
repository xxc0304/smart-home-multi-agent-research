"""Real Linux container integration checks, using official references/empty answers only."""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as parquet

from coreta.scoring import docker_math_records, evalplus_scores, preflight_math, read_jsonl, score_humaneval, score_mbpp
from coreta.state import write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "image": args.image,
              "scope": "engineering fixtures, official reference implementations and empty answers; no model capability evidence",
              "real_model_calls": 0, "checks": []}
    def record(name, passed, details):
        report["checks"].append({"name": name, "passed": bool(passed), "details": details})
        write_json(args.output / "report.json", report)
        print(json.dumps({"check": name, "passed": bool(passed)}), flush=True)
    probe = subprocess.run(["docker", "run", "--rm", "--network=none", "--read-only", "--user", "65532:65532",
                            args.image, "python", "-c", "import os,sys,json,importlib.metadata as m;print(json.dumps({'uid':os.getuid(),'platform':sys.platform,'python':sys.version,'packages':{d.metadata['Name']:d.version for d in m.distributions()}}))"],
                           capture_output=True, text=True, encoding="utf-8", timeout=60, check=False)
    if probe.returncode:
        raise RuntimeError(probe.stderr)
    versions = json.loads(probe.stdout)
    write_json(args.output / "container_environment.json", versions)
    record("linux_nonroot_versions", versions["uid"] == 65532 and versions["platform"] == "linux", {"platform": versions["platform"], "uid": versions["uid"]})
    mathematics = docker_math_records([
        {"task_id": "fixture-equivalence", "answer": r"\frac{1}{2}", "artifact": r"\boxed{0.5}"},
        {"task_id": "fixture-wrong", "answer": "2", "artifact": r"\boxed{3}"},
        {"task_id": "fixture-empty", "answer": "2", "artifact": ""},
        {"task_id": "fixture-last-box", "answer": "2", "artifact": r"first \boxed{3}; final \boxed{2}"}], args.image)
    write_json(args.output / "math_fixture_scores.json", mathematics)
    record("linux_math_scoring", [r["score"] for r in mathematics] == [1, 0, 0, 1], mathematics)
    gold = args.data_root / "development-20261019/evaluation/math_gold.json"
    ready = preflight_math(gold, image=args.image)
    write_json(args.output / "development_math_preflight.json", ready)
    record("development_math_gold_preflight", ready["ready"], {"tasks": len(ready["records"]), "ready": ready["ready"]})
    mother = args.data_root / "source/HumanEvalPlus-v0.1.10.jsonl.gz"
    selected = sorted(read_jsonl(mother), key=lambda row: int(row["task_id"].split("/")[-1]))[:2]
    for variant in ("official_reference", "empty_answer"):
        samples = args.output / (variant + ".jsonl")
        with samples.open("w", encoding="utf-8") as stream:
            for row in selected:
                solution = row["prompt"] + row["canonical_solution"] if variant == "official_reference" else ""
                stream.write(json.dumps({"task_id": row["task_id"], "solution": solution}) + "\n")
        job = args.output / ("humaneval_" + variant)
        outcome = score_humaneval(samples, mother, job, args.image, timeout=180)
        details = outcome
        passed = False
        if outcome["status"] == "completed":
            scores = evalplus_scores(job / "output/samples_eval_results.json", [r["task_id"] for r in selected], system="engineering_fixture", seed=0)
            expected = 1 if variant == "official_reference" else 0
            passed = all(s["base_score"] == s["plus_score"] == expected for s in scores)
            details = scores
        record("humaneval_" + variant, passed, details)
    mbpp_records = json.loads((args.data_root / "development-20261019/evaluation/mbpp_tests.json").read_text(encoding="utf-8"))
    first = mbpp_records[0]
    source_rows = parquet.read_table(args.data_root / "source/mbpp-sanitized-train.parquet").to_pylist()
    original = next(row for row in source_rows if row["task_id"] == int(first["task_id"].split("/")[-1]))
    for variant in ("official_reference", "empty_answer"):
        payload = {**first, "artifact": original["code"] if variant == "official_reference" else ""}
        outcome = score_mbpp(payload, args.output / ("mbpp_" + variant), args.image)
        expected = 1 if variant == "official_reference" else 0
        record("mbpp_" + variant, outcome.get("task_score", {}).get("score") == expected, outcome)
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["success"] = all(row["passed"] for row in report["checks"])
    write_json(args.output / "report.json", report)
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
