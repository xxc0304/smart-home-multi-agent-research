"""Offline paired scoring and trace accounting for the frozen revision comparison."""
import ast
import hashlib
import json
from pathlib import Path

from coreta.scoring import docker_math_records, score_mbpp
from coreta.state import write_json

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def ast_body(artifact):
    try:
        tree = ast.parse(artifact)
        for node in ast.walk(tree):
            if hasattr(node, "body") and isinstance(node.body, list) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                    node.body = node.body[1:]
        return ast.dump(tree, include_attributes=False)
    except SyntaxError:
        return None


def main():
    plan = read(ROOT / "engineering/REVISION_COMPARISON_PLAN_20261019.json")
    output = Path(plan["output"])
    image = (ROOT / "engineering/SCORING_IMAGE_20261019.txt").read_text().strip()
    evaluation = ROOT / "data/development-20261019/evaluation"
    gold = {r["task_id"]: r for r in read(evaluation / "math_gold.json")}
    tests = {r["task_id"]: r for r in read(evaluation / "mbpp_tests.json")}
    rows, results, banks = [], [], {}
    for job in plan["jobs"]:
        folder = output / job["job_id"]
        result = read(folder / "result.json")
        if result["task_id"] != job["task_id"] or result["system"] != job["system"]:
            raise ValueError("Result does not match frozen job")
        events = lines(folder / "events.jsonl")
        drafts = [e for e in events if e["stage"] == "draft"]
        hashes = [digest(e["payload"]) for e in drafts]
        if len(hashes) != 3:
            raise ValueError("Missing initial drafts")
        prior = banks.setdefault(job["task_id"], hashes)
        if prior != hashes:
            raise ValueError("Conditions did not share identical initial candidate payloads")
        requests = lines(folder / "requests.jsonl")
        responses = lines(folder / "responses.jsonl")
        commits = lines(folder / "commits.jsonl")
        core_changes = None
        if job["family"] == "mbpp":
            final_tree = ast_body(result["artifact"])
            core_changes = {e["sent_from"]: (final_tree != ast_body(e["payload"]["artifact"]))
                            if final_tree is not None else None for e in drafts}
        results.append({"task_id": job["task_id"], "system": job["system"], "job_id": job["job_id"],
            "status": result["status"], "stop_reason": result["stop_reason"], "normal_calls": result["normal_calls"],
            "http_attempts": result["http_attempts"], "format_repairs": result["format_repairs"],
            "draft_hashes": hashes, "cached_drafts": len(lines(folder / "cache.jsonl")),
            "final_code_ast_differs_from_drafts": core_changes,
            "actions": [e["payload"]["next"]["action"] for e in events if e["stage"] == "apply"],
            "stages": [e["stage"] for e in events], "issues": result.get("issues", {}), "errors": result["errors"],
            "max_sent_input_estimate": max((r["estimated_input_count"] for r in requests), default=0),
            "reported_usage": [r["response"].get("usage") for r in responses if "response" in r],
            "commit_changes": [{"artifact_changed": c["artifact_changed"], "changed_steps": c["changed_steps"]} for c in commits]})
        targets = [("prefinal", result["prefinal_artifact"]), ("final", result["artifact"])]
        if not any(row["task_id"] == job["task_id"] for row in rows):
            targets = [("draft-" + e["sent_from"], e["payload"]["artifact"]) for e in drafts] + targets
        for label, artifact in targets:
            task_id = job["task_id"]
            if task_id in gold:
                scored = docker_math_records([{**gold[task_id], "artifact": artifact}], image)[0]
            else:
                record = {**tests[task_id], "artifact": artifact}
                score_job = output / "scoring" / (job["job_id"] + "-" + label)
                if (score_job / "launcher_result.json").exists():
                    if read(score_job / "input/mbpp.json") != record or read(score_job / "manifest.json")["image"] != image:
                        raise ValueError("Cached scoring material changed")
                    launched = read(score_job / "launcher_result.json")
                else:
                    launched = score_mbpp(record, score_job, image)
                scored = launched.get("task_score", {"status": "scoring_error", "score": None})
            rows.append({"task_id": task_id, "system": "shared_initial" if label.startswith("draft") else job["system"],
                         "label": label, "job_id": job["job_id"], "score": scored.get("score"), "detail": scored})
            write_json(ROOT / "engineering/REVISION_COMPARISON_SCORES_20261019.json", rows)
    write_json(ROOT / "engineering/REVISION_COMPARISON_TRACES_20261019.json", results)
    summary = []
    for task in plan["tasks"]:
        task_id = task["task_id"]
        task_rows = [r for r in rows if r["task_id"] == task_id]
        initial = [r["score"] for r in task_rows if r["system"] == "shared_initial"]
        summary.append({"task_id": task_id, "shared_draft_scores": initial,
            "all_initial_wrong": len(initial) == 3 and all(s == 0 for s in initial),
            "final_scores": {r["system"]: r["score"] for r in task_rows if r["label"] == "final"}})
    write_json(ROOT / "engineering/REVISION_COMPARISON_SUMMARY_20261019.json", {
        "tasks": summary, "job_count": len(results), "identical_shared_initials_verified": True,
        "normal_calls": sum(r["normal_calls"] for r in results),
        "http_attempts": sum(r["http_attempts"] for r in results),
        "format_repairs": sum(r["format_repairs"] for r in results),
        "scoring_image": image, "scope": "two selected development tasks; no significance or effectiveness claim"})
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
