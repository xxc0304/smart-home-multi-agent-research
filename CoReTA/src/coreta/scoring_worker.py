"""Offline worker: invoked in an isolated process or Docker, never by the agent runtime."""
from __future__ import annotations

import contextlib
import importlib.metadata
import json
import os
import re
import shutil
import sys
from pathlib import Path


def final_boxed(artifact):
    """Extract the last boxed expression, including balanced nested LaTeX braces."""
    matches = list(re.finditer(r"\\boxed\s*\{", artifact))
    if not matches:
        return artifact
    start = matches[-1].start()
    brace = matches[-1].end() - 1
    depth = 0
    for position in range(brace, len(artifact)):
        char = artifact[position]
        slashes = 0
        cursor = position - 1
        while cursor >= 0 and artifact[cursor] == "\\":
            slashes += 1
            cursor -= 1
        if slashes % 2:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return artifact[start:position + 1]
    raise ValueError("Final boxed expression has unbalanced braces")


def math_record(record, *, diagnostic=False, preflight=False):
    from math_verify import ExprExtractionConfig, LatexExtractionConfig, parse, verify
    if not diagnostic and not sys.platform.startswith("linux"):
        raise RuntimeError("Formal Math-Verify scoring requires Linux")
    timeout = 0 if diagnostic else 5
    gold = parse("$" + record["answer"] + "$", extraction_config=[LatexExtractionConfig()],
                 extraction_mode="first_match", fallback_mode="first_match", parsing_timeout=timeout,
                 raise_on_error=True)
    if not gold or all(isinstance(item, str) for item in gold):
        return {"task_id": record["task_id"], "status": "gold_unparseable", "score": None}
    if preflight:
        return {"task_id": record["task_id"], "status": "ready", "score": None,
                "gold_parsed": [str(item) for item in gold]}
    try:
        prediction_text = final_boxed(record["artifact"])
    except ValueError:
        return {"task_id": record["task_id"], "status": "prediction_unparseable", "score": 0}
    prediction = parse(prediction_text, extraction_config=[LatexExtractionConfig(boxed_match_priority=0), ExprExtractionConfig()],
                       extraction_mode="first_match", fallback_mode="first_match", parsing_timeout=timeout,
                       raise_on_error=True)
    if not prediction or all(isinstance(item, str) for item in prediction):
        return {"task_id": record["task_id"], "status": "prediction_unparseable", "score": 0}
    score = int(verify(gold, prediction, timeout_seconds=timeout, raise_on_error=True))
    return {"task_id": record["task_id"], "status": "scored", "score": score}


def code_job():
    if not sys.platform.startswith("linux") or not Path("/.dockerenv").exists():
        raise RuntimeError("Code worker requires Linux Docker")
    # The only supported code path uses fixed container paths; no arbitrary host evaluator.
    os.environ["HUMANEVAL_OVERRIDE_PATH"] = "/input/problems.jsonl"
    from evalplus.evaluate import evaluate
    # v0.3.1 writes results next to samples, so copy samples to the writable output mount.
    shutil.copyfile("/input/samples.jsonl", "/output/samples.jsonl")
    evaluate(dataset="humaneval", samples="/output/samples.jsonl", base_only=False,
             parallel=1, mini=False, noextreme=False, version="v0.1.10")
    Path("/output/evaluator_versions.json").write_text(json.dumps(
        {"evalplus": importlib.metadata.version("evalplus"), "dataset_version": "v0.1.10",
         "mini": False, "noextreme": False}), encoding="utf-8")


def mbpp_job():
    if not sys.platform.startswith("linux") or not Path("/.dockerenv").exists():
        raise RuntimeError("MBPP code worker requires Linux Docker")
    data = json.loads(Path("/input/mbpp.json").read_text(encoding="utf-8"))
    namespace = {"__name__": "__candidate__"}
    try:
        imports = [compile(text, "<official-import>", "exec") for text in data["test_imports"]]
        tests = [compile(text, "<official-assertion>", "exec") for text in data["test_list"]]
        for statement in imports:
            exec(statement, namespace)
    except Exception as exc:
        result = {"task_id": data["task_id"], "status": "scoring_error", "score": None, "error_type": type(exc).__name__}
        Path("/output/mbpp_score.json").write_text(json.dumps(result), encoding="utf-8")
        return
    # This function is reachable only from the container entry, never the host launcher.
    try:
        exec(compile(data["artifact"], "<candidate>", "exec"), namespace)
        for statement in tests:
            exec(statement, namespace)
    except Exception as exc:
        result = {"task_id": data["task_id"], "status": "candidate_failed", "score": 0, "error_type": type(exc).__name__}
    else:
        result = {"task_id": data["task_id"], "status": "scored", "score": 1}
    Path("/output/mbpp_score.json").write_text(json.dumps(result), encoding="utf-8")


def main():
    mode = sys.argv[1]
    if mode in {"humaneval", "mbpp"}:
        if not Path("/.dockerenv").exists():
            raise RuntimeError("Code scoring is allowed only inside the Docker scoring container")
        if mode == "humaneval":
            code_job()
        else:
            mbpp_job()
        return
    data = json.load(sys.stdin)
    from math_verify.errors import TimeoutException
    if mode == "math-batch":
        results = []
        for record in data["records"]:
            for attempt in range(2):
                try:
                    with contextlib.redirect_stdout(sys.stderr):
                        result = math_record(record, diagnostic=False, preflight=data["preflight"])
                except (Exception, TimeoutException) as exc:
                    result = {"task_id": record["task_id"], "status": "scoring_error", "score": None,
                              "error_type": type(exc).__name__, "detail": str(exc)[:300]}
                result.update({"attempts": attempt + 1, "diagnostic_only": False,
                               "math_verify_version": importlib.metadata.version("math-verify")})
                if result["status"] != "scoring_error":
                    break
            results.append(result)
        print(json.dumps(results))
        return
    try:
        with contextlib.redirect_stdout(sys.stderr):
            result = math_record(data["record"], diagnostic=data["diagnostic"], preflight=data["preflight"])
    except (Exception, TimeoutException) as exc:
        result = {"task_id": data["record"]["task_id"], "status": "scoring_error", "score": None,
                  "error_type": type(exc).__name__, "detail": str(exc)[:300]}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
