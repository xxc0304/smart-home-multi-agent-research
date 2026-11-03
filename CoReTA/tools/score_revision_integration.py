"""Offline scoring for the two frozen revision E0 tasks; never sends model requests."""
import json
from pathlib import Path

from coreta.scoring import docker_math_records, score_mbpp
from coreta.state import write_json


ROOT = Path(__file__).resolve().parents[1]


def main():
    root = ROOT / "runs/revision-e0-20261019"
    image = (ROOT / "engineering/SCORING_IMAGE_20261019.txt").read_text().strip()
    gold = {r["task_id"]: r for r in json.loads((ROOT / "data/development-20261019/evaluation/math_gold.json").read_text())}
    tests = {r["task_id"]: r for r in json.loads((ROOT / "data/development-20261019/evaluation/mbpp_tests.json").read_text())}
    scores, traces = [], []
    folders = ["math6388-attempt2", "code607-attempt1"]
    if (root / "code607-attempt2/result.json").exists():
        folders.append("code607-attempt2")
    for folder in folders:
        directory = root / folder
        result = json.loads((directory / "result.json").read_text(encoding="utf-8"))
        events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        artifacts = [("draft-" + e["sent_from"], e["payload"]["artifact"]) for e in events if e["stage"] == "draft"]
        artifacts += [("prefinal", result["prefinal_artifact"]), ("final", result["artifact"])]
        task_id = result["task_id"]
        for label, artifact in artifacts:
            if task_id in gold:
                scored = docker_math_records([{**gold[task_id], "artifact": artifact}], image)[0]
            else:
                record = {**tests[task_id], "artifact": artifact}
                job = root / "scoring" / (folder + "-" + label)
                if (job / "launcher_result.json").exists():
                    if json.loads((job / "input/mbpp.json").read_text(encoding="utf-8")) != record:
                        raise ValueError("Archived scoring input differs; refuse score reuse")
                    manifest = json.loads((job / "manifest.json").read_text(encoding="utf-8"))
                    if manifest["image"] != image:
                        raise ValueError("Archived scoring image differs")
                    launched = json.loads((job / "launcher_result.json").read_text(encoding="utf-8"))
                else:
                    launched = score_mbpp(record, job, image)
                scored = launched.get("task_score", {"status": "scoring_error", "score": None})
            scores.append({"task_id": task_id, "attempt_directory": folder, "artifact_label": label, "result": scored})
            write_json(ROOT / "engineering/REVISION_LIVE_SCORES_20261019.json", scores)
        requests = [json.loads(line) for line in (directory / "requests.jsonl").read_text(encoding="utf-8").splitlines()]
        traces.append({"task_id": task_id, "run_directory": str(directory.relative_to(ROOT)),
                       "status": result["status"], "stop_reason": result["stop_reason"],
                       "normal_calls": result["normal_calls"], "format_repairs": result["format_repairs"],
                       "http_attempts": result["http_attempts"], "errors": result["errors"],
                       "stages": [{"stage": e["stage"], "actor": e["sent_from"]} for e in events],
                       "max_estimated_input": max(r["estimated_input_count"] for r in requests),
                       "issues": result["issues"]})
    write_json(ROOT / "engineering/REVISION_LIVE_TRACE_SUMMARY_20261019.json", traces)
    print(json.dumps({"scored_artifacts": len(scores), "trajectories": len(traces)}))


if __name__ == "__main__":
    main()
