"""Five bounded schema-copy canaries. No task solving, scoring or capability claims."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from coreta.handoff.__main__ import configure, load_counter, DEFAULT_TOKENIZER
from coreta.handoff.contracts import HandoffContracts
from coreta.handoff.gateway import Journal, write_json
from coreta.handoff.inputs import read_json
from coreta.handoff.ranking import render_ranking, parse_ranking
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "design/expertise-handoff/protocol-v1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.live or not os.environ.get("DEEPSEEK_API_KEY"):
        parser.error("Requires explicit --live and configured DEEPSEEK_API_KEY")
    if args.output.exists():
        parser.error("Output directory must be new")
    config, _ = configure(ROOT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    config["protocol"] = {"transport_retries_per_request": 0, "request_timeout_seconds": 120}
    counter = load_counter()
    # Only public display names are read. This is deliberately NOT a moon solution.
    names = [i["name"] for i in read_json(ROOT / "data/task-packs/moon-survival-v1/public/task.json")["items"]]
    cases = [
        ("CONTRIBUTE", {"items": [{"content": "Copy check only", "support": "Public format fixture",
                                  "support_refs": ["T"], "conditions": [], "needs": []}], "note": "compatibility_only"}),
        ("APPLY", {"artifact": names, "applications": [{"refs": ["C1"], "result": "Copied public display order only"}],
                   "excluded": [], "unresolved": [], "request": {"kind": "ask", "recipient": "A1",
                   "target_refs": ["C1"], "question": "Copy check?", "impact": "Format only"}}),
        ("REVIEW", {"verdict": "undetermined", "finding": "Format copy check only",
                    "target_refs": ["W1"], "check_suggestion": None}),
        ("INDEPENDENT", {"explanation": "Copied public display order; no task solution attempted", "ranking": names}),
        ("DISCUSS", {"text": "Public discussion format copy check only"}),
    ]
    contracts = HandoffContracts(DESIGN / "message.schema.json")
    args.output.mkdir(parents=True, exist_ok=False)
    journal = Journal(args.output)
    client = DeepSeekClient(config, journal.log, token_counter=counter)
    paths = [Path(__file__), DEFAULT_TOKENIZER, ROOT / "config/deepseek_flash_inspection.json",
             DESIGN / "message.schema.json", ROOT / "src/coreta/model_client.py"]
    paths += sorted((ROOT / "src/coreta/handoff").glob("*.py"))
    report = {"kind": "compatibility_only_not_experiment", "started_at": datetime.now(timezone.utc).isoformat(),
              "model": config["model"], "endpoint": config["base_url"] + "/responses",
              "max_requests": 5, "retries": 0, "scoring_performed": False, "full_stage_prompts_tested": False,
              "test": "Copy specified public data using actual stage schemas and production transport",
              "source_hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              "checks": [], "passed": False}
    write_json(args.output / "compatibility.json", report)
    for stage, expected in cases:
        schema = contracts.schema(stage, {"T", "C1", "W1"}, ["A1", "A2", "A3"],
                                  ["ask", "check", "probe"], ranking_items=names)
        contracts.decode(json.dumps(expected), schema)
        instruction = ("This is an API compatibility copy check, not a reasoning or ranking task. "
                       "Return exactly the following JSON value, preserving array order and fields. "
                       "Use the supplied response-format schema. Do not solve any task.\n" + json.dumps(expected))
        payload = client.payload(instruction, schema, 1024)
        journal.call_context = {"stage": stage, "kind": "compatibility_only"}
        row = {"stage": stage, "estimated_input": client.size(payload), "count_mode": client.count_mode}
        try:
            raw = client.complete(payload, deadline=time.monotonic() + 125, logical_seed=17)
            value = contracts.decode(raw, schema)
            row["schema_valid"] = True
            row["copy_exact"] = value == expected
            if stage in {"APPLY", "INDEPENDENT"}:
                ranking = value["artifact"] if stage == "APPLY" else value["ranking"]
                _, error = parse_ranking(render_ranking(ranking), set(names))
                if error:
                    raise ProtocolError("SCHEMA_ERROR", error)
                row["deterministic_render_parse_valid"] = True
            if value != expected:
                raise ProtocolError("COPY_MISMATCH", "Schema valid but copy target not preserved")
            row["passed"] = True
        except ProtocolError as exc:
            row.update(passed=False, code=exc.code, detail=exc.detail)
        report["checks"].append(row)
        report["actual_attempts"] = client.attempts
        report["usage"] = journal.usage
        report["passed"] = len(report["checks"]) == 5 and all(r["passed"] for r in report["checks"])
        write_json(args.output / "compatibility.json", report)
        print(json.dumps(row), flush=True)
        if not row["passed"]:
            break
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
