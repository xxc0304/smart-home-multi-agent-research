"""Bounded schema-copy checks; no task solving, full prompts or capability claims."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from coreta.handoff.__main__ import configure, load_counter, PROJECT, DESIGN
from coreta.handoff.gateway import Journal, write_json
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
from coreta.workboard.artifacts import RankingAdapter
from coreta.workboard.contracts import Contracts


def cases():
    # Artificial labels and input order, unrelated to any scored task.
    names = ["fixture_a", "fixture_b", "fixture_c", "fixture_d"]
    adapter = RankingAdapter({"items": [{"name": n} for n in names]})
    contracts = Contracts(adapter)
    work = {"artifact": names, "work_text": "Copy fixture only.", "open_points": []}
    packet = {"REFERENCE_INDEX": [{"ref": "T"}, {"ref": "W1"}, {"ref": "O1"}],
              "TARGETS": ["whole_goal", "W1", "W1:artifact:L1"],
              "CANDIDATES": [{"id": "W1", "deliverable_shape": True}], "CHOICES": ["W1"]}
    mutation = {"action": "new", "candidate_id": None, "work": work,
                "use_record": "Copying fixture, not applying knowledge.", "reason": None,
                "declared_sources": ["T"]}
    check = {"finding": "unable", "observation": "Schema-copy fixture.", "scope": "No truth check."}
    output = [("initial", "INITIAL", work, packet),
              ("offer", "OBSERVE", {"action": "offer", "offer": {"target": "W1:artifact:L1",
                "knowledge": "Fixture only.", "support": [{"ref": "T", "excerpt": "Fixture"}] * 20,
                "proposed_use": "Copy only."}}, packet),
              ("try_new", "TRY", mutation, packet),
              ("check_use", "CHECK_USE", check, packet),
              ("check_effect", "CHECK_EFFECT", check, packet),
              ("choose", "CHOOSE", {"candidate_id": "W1", "reason": "Copy only."}, packet),
              ("finalize_reuse", "FINALIZE", {**mutation, "action": "reuse", "candidate_id": "W1", "work": None}, packet),
              ("final_check_use", "FINAL_CHECK_USE", check, packet),
              ("final_check_effect", "FINAL_CHECK_EFFECT", check, packet),
              ("final_choose", "FINAL_CHOOSE", {"candidate_id": "W1", "reason": "Copy only."}, packet),
              ("pass", "OBSERVE", {"action": "pass", "offer": None}, packet),
              ("finalize_no_complete_candidate", "FINALIZE", {**mutation, "work": {**work, "artifact": None}},
               {**packet, "CANDIDATES": [{"id": "W1", "deliverable_shape": False}]})]
    # Include explanations as model outputs, not just null-valued copied actions.
    # These remain copy fixtures and cannot establish natural solving reliability.
    for stage in ("TRY", "FINALIZE"):
        for action in ("reuse", "new"):
            explained = {**mutation, "action": action,
                         "candidate_id": "W1" if action == "reuse" else None,
                         "work": None if action == "reuse" else work,
                         "reason": "This is a fixture selection explanation, not evidence of correctness."}
            output.append((f"{stage.lower()}_{action}_explained", stage, explained, packet))
    prepared = []
    for label, stage, value, context in output:
        schema = contracts.schema(stage, context)
        contracts.decode(json.dumps(value), schema)
        contracts.validate_action(stage, value)
        prepared.append((label, stage, value, schema))
    return contracts, prepared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output directory must be new")
    if args.live and not os.environ.get("DEEPSEEK_API_KEY"):
        parser.error("DEEPSEEK_API_KEY is not configured")
    config, _ = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    config["protocol"] = {"transport_retries_per_request": 0, "request_timeout_seconds": 60}
    contracts, prepared = cases()
    args.output.mkdir(parents=True, exist_ok=False)
    journal = Journal(args.output)
    client = DeepSeekClient(config, journal.log, token_counter=load_counter())
    paths = list((PROJECT / "src/coreta/workboard").glob("*.py")) + [Path(__file__), PROJECT / "src/coreta/model_client.py"]
    report = {"kind": "workboard_schema_copy_only", "started_at": datetime.now(timezone.utc).isoformat(),
              "live": args.live, "max_http_attempts": len(prepared), "actual_attempts": 0,
              "transport_retries": 0, "format_repairs": 0, "scoring_performed": False,
              "full_stage_prompts_tested": False, "checks": [], "passed": False,
              "source_hashes": {str(p.relative_to(PROJECT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    write_json(args.output / "compatibility.json", report)
    for label, stage, value, schema in prepared:
        instruction = ("Schema compatibility copy check only. Copy EXACTLY the JSON object below, including all repeated "
                       "array entries and null fields. Do not solve, evaluate, shorten, repair or improve its contents.\n"
                       + json.dumps(value, ensure_ascii=False))
        payload = client.payload(instruction, schema, 2048)
        write_json(args.output / f"{label}.request.json", payload)
        write_json(args.output / f"{label}.expected.json", value)
    if not args.live:
        report.update(status="prepared_only", local_fixture_validation=True)
        write_json(args.output / "compatibility.json", report)
        print(json.dumps({"prepared_cases": len(prepared), "actual_attempts": 0}))
        return 0
    try:
        for label, stage, value, schema in prepared:
            payload = json.loads((args.output / f"{label}.request.json").read_text(encoding="utf-8"))
            journal.call_context = {"case": label, "stage": stage, "kind": "schema_copy_only"}
            row = {"case": label, "stage": stage}
            report["checks"].append(row)
            try:
                raw = client.complete(payload, deadline=time.monotonic() + 65, logical_seed=17)
                decoded = contracts.decode(raw, schema)
                contracts.validate_action(stage, decoded)
                row.update(schema_valid=True, action_valid=True, copy_exact=decoded == value)
                if decoded != value:
                    raise ProtocolError("COPY_MISMATCH", "Response differs from fixed fixture")
            except ProtocolError as exc:
                row.update(error={"code": exc.code, "detail": exc.detail})
                raise
            finally:
                report.update(actual_attempts=client.attempts, usage=journal.usage,
                              uncertain_usage_attempts=journal.uncertain_attempts)
                write_json(args.output / "compatibility.json", report)
        report.update(passed=True, status="completed")
    except ProtocolError:
        report.update(status="stopped_on_first_error")
    finally:
        write_json(args.output / "compatibility.json", report)
    print(json.dumps({k: report[k] for k in ("passed", "status", "actual_attempts")}))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
