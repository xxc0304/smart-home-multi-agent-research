"""Three bounded APPLY schema-copy checks; no task solving or effect evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from coreta.application_v2.contracts import ApplicationContracts
from coreta.application_v2.state import Applications
from coreta.handoff.__main__ import configure, load_counter
from coreta.handoff.gateway import Journal, write_json
from coreta.handoff.inputs import read_json
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "design/expertise-handoff/protocol-v1"


def cases(names):
    new = {"artifact": names, "applications": [{"target": None, "task_step": "Format copy operation",
        "bindings": [{"ref": "C1", "use": "Public copy fixture"}], "result": None, "missing": "Copy fixture input"}],
        "artifact_uses": [], "retire_applications": [], "excluded": [], "unresolved": [],
        "request": {"kind": "ask", "recipient": "A1", "target_refs": ["C1"],
                    "question": "Format copy check only?", "impact": "Compatibility only"}}
    revision = {"artifact": None, "applications": [{"target": "U1", "task_step": "Format copy operation",
        "bindings": [{"ref": "C1", "use": "Public copy fixture supplies the missing input"}],
        "result": "Copied fixture value, not a task solution", "missing": None}],
        "artifact_uses": ["U1"], "retire_applications": [], "excluded": [], "unresolved": [], "request": None}
    retirement = {"artifact": None, "applications": [], "artifact_uses": [],
        "retire_applications": [{"ref": "U2", "reason": "Copy fixture path complete"}],
        "excluded": [], "unresolved": [], "request": None}
    return [("empty_registry_new_application", new, {"T", "C1"}, ["ask", "check", "probe"]),
            ("existing_application_revision", revision, {"T", "C1", "U1"}, ["ask", "check", "probe"]),
            ("retirement_no_request_budget", retirement, {"T", "C1", "U1", "U2"}, [])]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.live or not os.environ.get("DEEPSEEK_API_KEY"):
        parser.error("Requires --live and configured DEEPSEEK_API_KEY")
    if args.output.exists():
        parser.error("Output directory must be new")
    config, _ = configure(ROOT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    config["protocol"] = {"transport_retries_per_request": 0, "request_timeout_seconds": 60}
    contracts = ApplicationContracts(DESIGN / "message.schema.json")
    names = [i["name"] for i in read_json(ROOT / "data/task-packs/moon-survival-v1/public/task.json")["items"]]
    # Preflight every fixed value locally before making any network request.
    state, prepared = Applications(), []
    for name, value, refs, allowed in cases(names):
        schema = contracts.schema("APPLY", refs, ["A1", "A2", "A3"], allowed, names)
        contracts.decode(json.dumps(value), schema)
        state.update(value)
        prepared.append((name, value, schema))
    args.output.mkdir(parents=True, exist_ok=False)
    journal = Journal(args.output)
    client = DeepSeekClient(config, journal.log, token_counter=load_counter())
    paths = [Path(__file__), ROOT / "src/coreta/model_client.py", DESIGN / "message.schema.json"]
    paths += list((ROOT / "src/coreta/application_v2").glob("*.py"))
    report = {"kind": "v2_schema_copy_compatibility_not_model_experiment", "started_at": datetime.now(timezone.utc).isoformat(),
              "model": config["model"], "endpoint": config["base_url"] + "/responses", "max_http_attempts": 3,
              "transport_retries": 0, "format_repairs": 0, "full_stage_prompts_tested": False,
              "scoring_performed": False, "checks": [], "passed": False, "actual_attempts": 0,
              "source_hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    write_json(args.output / "compatibility.json", report)
    try:
        for name, value, schema in prepared:
            instruction = ("API format compatibility check only. Copy exactly the specified JSON object using the supplied schema. "
                           "Preserve all values and array order. No task solving or ranking reasoning.\n" + json.dumps(value))
            payload = client.payload(instruction, schema, 1024)
            journal.call_context = {"case": name, "stage": "APPLY", "kind": "compatibility_only"}
            row = {"case": name, "estimated_input_tokens": client.size(payload)}
            try:
                raw = client.complete(payload, deadline=time.monotonic() + 65, logical_seed=17)
                decoded = contracts.decode(raw, schema)
                row.update(schema_valid=True, copy_exact=decoded == value)
                if decoded != value:
                    raise ProtocolError("COPY_MISMATCH", "Schema valid but fixed copy target changed")
                row["passed"] = True
            except ProtocolError as exc:
                row.update(passed=False, code=exc.code, detail=exc.detail)
            report["checks"].append(row)
            print(json.dumps(row), flush=True)
            if not row["passed"]:
                break
    finally:
        report.update(actual_attempts=client.attempts, usage=journal.usage,
                      uncertain_usage_attempts=journal.uncertain_attempts,
                      ended_at=datetime.now(timezone.utc).isoformat())
        report["passed"] = len(report["checks"]) == 3 and all(r["passed"] for r in report["checks"])
        write_json(args.output / "compatibility.json", report)
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
