"""Network-free scripted acceptance for the isolated diagnostic adapter."""
import argparse
import copy
import json
import urllib.error
from pathlib import Path

from sbp_diagnostic import build, validate_plan, write_json, require
from coreta.handoff.__main__ import load_counter


def scripted(runner, counters):
    stage = runner.journal.call_context["stage"]
    counters[stage] = counters.get(stage, 0) + 1
    names = [f"Candidate {c}" for c in "ABCD"]  # Arbitrary valid array, not a scored oracle.
    if stage in {"CONTRIBUTE", "REPLY"}:
        return {"items": [{"content": "Scripted shape only; no correctness claim", "support": "Scripted acceptance",
                            "support_refs": ["T"] + [f"S{i:02d}" for i in range(1, 17)],
                            "conditions": [], "needs": []}], "note": "Scripted, not a model result"}
    if stage in {"INDEPENDENT", "FINAL"}:
        return {"ranking": names, "explanation": "Scripted, not a model result"}
    if stage == "DISCUSS":
        return {"text": "Scripted turn; no substantive evidence"}
    if stage == "APPLY":
        current = runner.application_state.last_ref
        bindings = [{"ref": "T", "use": "Scripted input binding"}]
        if runner.pending:
            bindings += [{"ref": ref, "use": "Scripted original-application handling"}
                         for ref in runner.pending["required_handling_refs"]]
        request = {"kind": "ask", "recipient": "A1", "target_refs": ["T"],
                   "question": "Scripted source request", "impact": "Scripted dependency"} if current is None else None
        return {"artifact": names, "applications": [{"target": current, "task_step": "Scripted application",
                                                      "bindings": bindings, "result": "Scripted result",
                                                      "missing": "Scripted input missing" if request else None}],
                "artifact_uses": list(runner.application_state.candidate_refs), "retire_applications": [],
                "excluded": [], "unresolved": ["Scripted input missing"] if request else [], "request": request}
    if stage == "REVIEW":
        return {"verdict": "issue" if counters[stage] == 1 else "no_defect_found",
                "finding": "Scripted review; no semantic correctness claim",
                "target_refs": [runner.application_state.last_ref], "check_suggestion": "Scripted revision"}
    raise ValueError(stage)


def execute(cell, output, counter, mode="normal"):
    output.mkdir()
    holder, counters = {}, {}
    failures = 0

    def transport(payload, timeout):
        nonlocal failures
        if mode != "normal" and failures == 0:
            failures += 1
            if mode == "transport_retry":
                raise urllib.error.URLError("Scripted, no network")
            if mode == "interrupt":
                raise KeyboardInterrupt("Scripted interruption")
            if mode == "truncate":
                return {"status": "incomplete", "usage": {"input_tokens": 1, "output_tokens": 1}}
            if mode == "bad_schema":
                value = {"bad": True}
            else:
                raise ValueError(mode)
        else:
            value = scripted(holder["runner"], counters)
        return {"status": "completed", "usage": {"input_tokens": 1, "output_tokens": 1},
                "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(value)}]}]}

    runner = build(cell, output, counter, transport=transport)
    holder["runner"] = runner
    try:
        result = runner.run(runner.system)
    except KeyboardInterrupt:
        runner.save_state()
        require((output / "state.json").exists(), "Interrupted state not saved")
        return {"cell": cell["id"], "mode": mode, "interruption_saved": True,
                "simulated_transport_attempts": runner.gateway.client.attempts}
    require(result["status"] not in {"protocol_failure", "budget_exhausted"}, "Scripted path failed: " + str(result["error"]))
    expected = 1 if cell["block"] == "initial_generation" else 6 if cell["arm"] == "coreta" else 9
    require(result["logical_calls"] == expected, "Wrong logical-call schedule")
    require(result["http_attempts"] == expected + (mode != "normal"), "Attempt accounting incorrect")
    if cell["arm"] == "coreta":
        require(len(runner.requests) == 1 and len(runner.reviews) == 2, "Handoff/review schedule missing")
        require(runner.application_state.last_ref == "U3", "Original application revisions missing")
        require(runner.contributions[-1]["ref"] == "C8", "Injected IDs collide with new reply")
    if mode in {"bad_schema", "truncate"}:
        require(result["format_repairs"] == 1, "Format recovery not recorded")
    if mode == "transport_retry":
        require(result["uncertain_usage_attempts"] == 1 and not result["usage_complete"], "Transport recovery hidden")
    return {"cell": cell["id"], "mode": mode, "logical_calls": result["logical_calls"],
            "simulated_transport_attempts": result["http_attempts"], "format_repairs": result["format_repairs"],
            "status": result["status"], "scripted_not_model_result": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    counter = load_counter()
    cells = validate_plan()["cells"]
    report = {"kind": "scripted_adapter_acceptance_not_model_results", "real_network_requests": 0, "cases": []}
    write_json(args.output / "acceptance.json", report)
    try:
        for cell in cells:
            report["cases"].append(execute(cell, args.output / cell["id"], counter))
        cell = next(c for c in cells if c["arm"] == "coreta")
        for mode in ["bad_schema", "transport_retry", "truncate", "interrupt"]:
            report["cases"].append(execute(copy.deepcopy(cell), args.output / mode, counter, mode))
        report["status"] = "passed"
    except BaseException as exc:
        report["status"] = "failed"
        report["error_type"] = type(exc).__name__
        raise
    finally:
        write_json(args.output / "acceptance.json", report)
    print(json.dumps({"status": report["status"], "cases": len(report["cases"]), "real_network_requests": 0}))


if __name__ == "__main__":
    main()
