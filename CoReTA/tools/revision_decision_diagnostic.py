"""Isolated single-APPLY diagnostics. prepare is offline; run requires --live."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from coreta.handoff.__main__ import configure, load_counter, DEFAULT_TOKENIZER
from coreta.handoff.contracts import HandoffContracts
from coreta.handoff.gateway import Gateway, Journal, write_json
from coreta.handoff.inputs import Packets, read_json
from coreta.handoff.prompts import HandoffPrompts
from coreta.handoff.ranking import render_ranking
from coreta.handoff.runtime import Runner
from coreta.schemas import ProtocolError

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "design/expertise-handoff/protocol-v1"
PROPOSAL = ROOT / "design/expertise-handoff/revision-decision-v1"
PACK = ROOT / "data/task-packs/moon-survival-v1"
SOURCE = ROOT / "runs/handoff-moon-pilot-20261021"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def delta_text():
    blocks = re.findall(r"```text\s*\n(.*?)\n```", (PROPOSAL / "PROMPT_DELTA.md").read_text(encoding="utf-8"), re.S)
    if len(blocks) != 1:
        raise ValueError("Expected exactly one APPLY delta block")
    return blocks[0]


class ArmPrompts:
    def __init__(self, arm):
        if arm not in {"current", "comparison"}:
            raise ValueError("Unknown arm")
        self.arm = arm
        self.base = HandoffPrompts(DESIGN / "PROMPTS.md")

    def render(self, stage, packet, schema):
        if stage != "APPLY":
            raise ValueError("Single-update diagnostic accepts APPLY only")
        original = self.base.render(stage, packet, schema)
        return original if self.arm == "current" else original + "\n\nREVISION_DECISION_GUIDANCE:\n" + delta_text()


def settings():
    plan = read_json(PROPOSAL / "DIAGNOSTIC_PLAN.json")
    config, defaults = configure(ROOT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    if (len(plan["checkpoints"]) != 4 or len(plan["arms"]) != 2
            or plan["repetitions_per_checkpoint_arm"] != 2 or plan["first_attempts"] != 16
            or plan["max_network_attempts_per_cell"] != 4 or plan["max_network_attempts_total"] != 64):
        raise ValueError("This tool implements the fixed 16-cell, 64-attempt design only")
    defaults = copy.deepcopy(defaults)
    for key in ("max_network_attempts_total", "format_retries_per_stage", "transport_retries_per_request",
                "request_timeout_seconds", "task_timeout_seconds"):
        source = {"max_network_attempts_total": "max_network_attempts_per_cell", "task_timeout_seconds": "cell_deadline_seconds"}.get(key, key)
        defaults["limits"][key] = plan[source]
    defaults["limits"]["max_interventions"] = 0
    defaults["max_output_tokens"]["apply"] = plan["max_output_tokens"]
    if config["generation"]["max_input_tokens"] != plan["max_input_tokens"]:
        raise ValueError("Input budget differs from diagnostic plan")
    return plan, config, defaults


def reconstruct(run_dir, checkpoint):
    """Use event prefixes and their completed outputs, never final state/results."""
    events, stages = rows(run_dir / "events.jsonl"), rows(run_dir / "stages.jsonl")
    state = {"contributions": [], "notes": [], "works": [], "reviews": [], "requests": [],
             "work": None, "unresolved": [], "pending": None}
    for event in events:
        kind = event["kind"]
        if kind == "contribution":
            logical = event["call_context"]["logical_call"]
            matches = [r for r in stages if r["call_context"]["logical_call"] == logical]
            if len(matches) != 1 or event["stage"] != "CONTRIBUTE":
                raise ValueError("Unsupported contribution prefix or ambiguous completed stage")
            output = matches[0]["output"]
            if len(event["refs"]) != len(output["items"]):
                raise ValueError("Contribution handles do not match completed output")
            for ref, item in zip(event["refs"], output["items"]):
                state["contributions"].append({"ref": ref, "author": event["member"], "stage": event["stage"], **copy.deepcopy(item)})
            state["notes"].append({"author": event["member"], "stage": event["stage"], "note": event["note"]})
        elif kind == "apply":
            value, old = event["output"], state["work"]
            if value["request"] is not None:
                raise ValueError("This fixed source prefix should not contain interventions")
            state["unresolved"] = copy.deepcopy(value["unresolved"])
            if value["artifact"] is None:
                raise ValueError("Expected complete historical candidate")
            history = copy.deepcopy(old["application_history"]) if old else []
            history += copy.deepcopy(value["applications"])
            artifact = render_ranking(value["artifact"])
            state["work"] = {"ref": event["work_ref"], "artifact": artifact,
                             "ranking": copy.deepcopy(value["artifact"]),
                             "changed_text": old is None or old["artifact"] != artifact,
                             "applications": copy.deepcopy(value["applications"]), "excluded": copy.deepcopy(value["excluded"]),
                             "application_history": history, "unresolved": copy.deepcopy(value["unresolved"]),
                             "application_evidence_status": "model_declared_not_independently_confirmed"}
            state["works"].append(copy.deepcopy(state["work"]))
            state["pending"] = None
        elif kind == "review":
            review = copy.deepcopy(event["review"])
            if not state["work"] or review["work_ref"] != state["work"]["ref"]:
                raise ValueError("Historical review is not tied to current work")
            state["reviews"].append(review)
            state["pending"] = {"kind": "review", "review": review, "required_handling_refs": [review["ref"]]}
            if review["ref"] == checkpoint["review"]:
                if state["work"]["ref"] != checkpoint["work"]:
                    raise ValueError("Checkpoint work mismatch")
                return state, event["call_context"]["logical_call"]
        else:
            raise ValueError("Unsupported event in fixed diagnostic prefix: " + kind)
    raise ValueError("Checkpoint review missing")


def attach_state(runner, state):
    for key, value in state.items():
        setattr(runner, key, copy.deepcopy(value))


def verify_past_prompt(run_dir, review_call, packet, contracts):
    candidates = [r for r in rows(run_dir / "requests.jsonl")
                  if r["call_context"].get("stage") == "APPLY"
                  and r["call_context"]["logical_call"] > review_call and r["retry"] == 0]
    if not candidates:
        raise ValueError("Historical following APPLY request missing")
    payload = candidates[0]["payload"]
    old = copy.deepcopy(packet)
    for key in ("LIMITS", "ALLOWED_REQUEST_KINDS"):
        prefix = "\n" + key + "="
        if payload["instructions"].count(prefix) != 1:
            raise ValueError("Ambiguous historical metadata")
        old[key] = json.JSONDecoder().raw_decode(payload["instructions"].split(prefix, 1)[1])[0]
    schema = contracts.schema("APPLY", {r["ref"] for r in old["REFERENCE_INDEX"]}, old["SELF"]["team"],
                              old["ALLOWED_REQUEST_KINDS"], ranking_items=[i["name"] for i in old["TASK"]["items"]])
    if schema != payload["text"]["format"]["schema"] or HandoffPrompts(DESIGN / "PROMPTS.md").render("APPLY", old, schema) != payload["instructions"]:
        raise ValueError("Reconstructed checkpoint does not match historical visible prompt")


def source_paths(plan):
    paths = [Path(__file__), ROOT / "tests/test_revision_decision_diagnostic.py", PROPOSAL / "SPEC.md", PROPOSAL / "PROMPT_DELTA.md", PROPOSAL / "DIAGNOSTIC_PLAN.json",
             DEFAULT_TOKENIZER, ROOT / "config/deepseek_flash_inspection.json", ROOT / "src/coreta/model_client.py",
             ROOT / "src/coreta/schemas.py", DESIGN / "PROMPTS.md", DESIGN / "message.schema.json", DESIGN / "runtime.defaults.json"]
    paths += list((ROOT / "src/coreta/handoff").glob("*.py"))
    for cp in plan["checkpoints"]:
        paths += [SOURCE / cp["run"] / name for name in ("events.jsonl", "stages.jsonl", "requests.jsonl", "manifest.json")]
    return sorted(set(paths))


def prepare(output):
    plan, config, defaults = settings()
    frozen = read_json(ROOT / "runs/handoff-format-readiness-20261021/freeze.json")
    for path, expected in frozen["source_hashes"].items():
        if digest(ROOT / path) != expected:
            raise ValueError("Original frozen source changed: " + path)
    contracts = HandoffContracts(DESIGN / "message.schema.json")
    counter = load_counter()
    output.mkdir(parents=True, exist_ok=False)
    checkpoints = []
    for cp in plan["checkpoints"]:
        run_dir = SOURCE / cp["run"]
        manifest = read_json(run_dir / "manifest.json")
        if manifest["system"] != "coreta" or manifest["configuration"] != config:
            raise ValueError("Historical system/model mismatch")
        packets = Packets(PACK, manifest["condition"])
        if packets.hashes != manifest["member_packet_hashes"]:
            raise ValueError("Historical member packets changed")
        state, review_call = reconstruct(run_dir, cp)
        folder = output / cp["id"]
        folder.mkdir()
        journal = Journal(folder)
        gateway = Gateway(config, defaults, contracts, ArmPrompts("current"), journal, token_counter=counter)
        runner = Runner(packets, gateway, journal, task_ordinal=manifest["task_ordinal"])
        attach_state(runner, state)
        packet = runner.packet(runner.driver, "APPLY", [])
        verify_past_prompt(run_dir, review_call, packet, contracts)
        schema = contracts.schema("APPLY", {r["ref"] for r in packet["REFERENCE_INDEX"]}, packets.agents, [],
                                  ranking_items=[i["name"] for i in packet["TASK"]["items"]])
        write_json(folder / "snapshot.json", {"checkpoint": cp, "condition": manifest["condition"],
                   "task_ordinal": manifest["task_ordinal"], "driver": runner.driver, "state": state,
                   "packet": packet, "schema": schema})
        sizes = {}
        for arm in ("current", "comparison"):
            prompt = ArmPrompts(arm).render("APPLY", packet, schema)
            (folder / f"{arm}.prompt.txt").write_text(prompt, encoding="utf-8")
            sizes[arm] = gateway.client.size(gateway.client.payload(prompt, schema, plan["max_output_tokens"]))
            if sizes[arm] > plan["max_input_tokens"]:
                raise ValueError("Prepared prompt exceeds input budget")
        checkpoints.append({"id": cp["id"], "snapshot": str((folder / "snapshot.json").relative_to(output)),
                            "input_estimates": sizes, "historical_prompt_match": True})
    cells = []
    for repetition in (1, 2):
        for cp in checkpoints:
            for arm in (("current", "comparison") if repetition == 1 else ("comparison", "current")):
                cells.append({"id": f"{len(cells)+1:02d}-{cp['id']}-{arm}-r{repetition}",
                              "checkpoint": cp["id"], "arm": arm, "repetition": repetition})
    files = [p for p in output.rglob("*") if p.is_file()]
    write_json(output / "preparation.json", {"kind": "offline_preparation_not_model_results", "real_model_calls": 0,
               "plan": plan, "configuration": config, "defaults": defaults, "checkpoints": checkpoints, "cells": cells,
               "source_hashes": {str(p.relative_to(ROOT)): digest(p) for p in source_paths(plan)},
               "packet_hashes": {str(p.relative_to(PACK)): digest(p) for p in (PACK / "packets").glob("*/*.json")},
               "prepared_hashes": {str(p.relative_to(output)): digest(p) for p in files}})
    return {"prepared": str(output), "checkpoints": len(checkpoints), "cells": len(cells), "real_model_calls": 0}


def verify_preparation(prepared):
    doc = read_json(prepared / "preparation.json")
    if doc["kind"] != "offline_preparation_not_model_results" or len(doc["cells"]) != 16:
        raise ValueError("Invalid preparation manifest")
    for base, field in ((ROOT, "source_hashes"), (PACK, "packet_hashes"), (prepared, "prepared_hashes")):
        for path, expected in doc[field].items():
            if digest(base / path) != expected:
                raise ValueError("Preparation changed: " + path)
    return doc


def execute_cell(prepared, doc, cell, output, *, transport=None):
    cp = next(c for c in doc["checkpoints"] if c["id"] == cell["checkpoint"])
    snap = read_json(prepared / cp["snapshot"])
    packets = Packets(PACK, snap["condition"])
    output.mkdir(parents=True, exist_ok=False)
    journal = Journal(output)
    gateway = Gateway(doc["configuration"], doc["defaults"], HandoffContracts(DESIGN / "message.schema.json"),
                      ArmPrompts(cell["arm"]), journal, transport=transport, token_counter=load_counter())
    runner = Runner(packets, gateway, journal, task_ordinal=snap["task_ordinal"])
    attach_state(runner, snap["state"])
    if runner.packet(runner.driver, "APPLY", []) != snap["packet"]:
        raise ValueError("Cell visible packet differs from prepared checkpoint")
    before = copy.deepcopy(runner.work)
    error = None
    try:
        runner.apply()
    except ProtocolError as exc:
        error = {"code": exc.code, "detail": exc.detail}
    runner.save_state()
    result = {"kind": "single_update_diagnostic", "cell": cell, "system": "coreta",
              "task_id": packets.task["task_id"], "condition": packets.condition, "agents": packets.agents,
              "driver": runner.driver, "status": "protocol_failure" if error else "single_update_completed",
              "stage_failure": error is not None,
              "error": error, "artifact": runner.work["artifact"], "before_artifact": before["artifact"],
              "candidate_origin": "fallback_after_failure" if error else ("new_candidate" if len(runner.works) > len(snap["state"]["works"]) else "retained_candidate"),
              "changed_ranking": before["ranking"] != runner.work["ranking"], "unresolved": runner.unresolved,
              "http_attempts": gateway.client.attempts, "format_repairs": journal.repairs,
              "usage_records": journal.usage, "uncertain_usage_attempts": journal.uncertain_attempts,
              "usage_complete": journal.uncertain_attempts == 0 and len(journal.usage) == gateway.client.attempts,
              "externally_scored": False}
    write_json(output / "result.json", result)
    return result


def run(prepared, output, live):
    if not live or not os.environ.get("DEEPSEEK_API_KEY"):
        raise ValueError("Requires explicit --live and configured DEEPSEEK_API_KEY")
    doc = verify_preparation(prepared)
    output.mkdir(parents=True, exist_ok=False)
    batch = {"kind": "retrospective_single_update_diagnostic", "status": "running", "started_at": datetime.now(timezone.utc).isoformat(),
             "preparation_sha256": digest(prepared / "preparation.json"), "max_attempts": 64, "attempts": 0, "cells": []}
    write_json(output / "batch.json", batch)
    try:
        for cell in doc["cells"]:
            verify_preparation(prepared)
            if batch["attempts"] + 4 > 64:
                raise ValueError("Cannot reserve next cell within batch cap")
            result = execute_cell(prepared, doc, cell, output / cell["id"])
            batch["attempts"] += result["http_attempts"]
            batch["cells"].append({"id": cell["id"], "status": result["status"], "attempts": result["http_attempts"]})
            if result["error"]:
                batch["status"] = "stopped_on_cell_failure"
            write_json(output / "batch.json", batch)
            print(json.dumps(batch["cells"][-1]), flush=True)
            if result["error"]:
                break
        else:
            batch["status"] = "completed"
    except KeyboardInterrupt:
        batch["status"] = "interrupted"
        raise
    except Exception as exc:
        batch["status"] = "implementation_or_input_failure"
        batch["error_type"] = type(exc).__name__
        raise
    finally:
        # Include a partially executed cell if an implementation exception interrupted it.
        batch["attempts"] = sum(len(rows(p)) for p in output.glob("*/requests.jsonl"))
        batch["ended_at"] = datetime.now(timezone.utc).isoformat()
        write_json(output / "batch.json", batch)
    return {k: batch[k] for k in ("status", "attempts")}


def score(batch_dir, output):
    # Evaluator access exists only in this explicit offline command.
    from coreta.handoff.ranking import score_run
    batch = read_json(batch_dir / "batch.json")
    reports = []
    for cell in batch["cells"]:
        result = read_json(batch_dir / cell["id"] / "result.json")
        after = score_run(PACK, result)["final"]
        before_result = {**result, "artifact": result["before_artifact"]}
        before = score_run(PACK, before_result)["final"]
        difference = after["L1_error"] - before["L1_error"]
        reports.append({"cell": result["cell"], "protocol_status": result["status"], "error": result["error"],
                        "stage_failure": result["stage_failure"],
                        "before": before, "after": after, "delta_L1": difference,
                        "direction": "improved" if difference < 0 else "worsened" if difference > 0 else "unchanged",
                        "changed_ranking": result["changed_ranking"], "candidate_origin": result["candidate_origin"],
                        "unresolved": result["unresolved"], "has_unresolved": bool(result["unresolved"]),
                        "usage_records": result["usage_records"], "usage_complete": result["usage_complete"],
                        "uncertain_usage_attempts": result["uncertain_usage_attempts"],
                        "format_repairs": result["format_repairs"], "http_attempts": result["http_attempts"],
                        "result_sha256": digest(batch_dir / cell["id"] / "result.json")})
    report = {"kind": "offline_diagnostic_scores_not_generalization_evidence", "batch_status": batch["status"], "cells": reports,
              "evaluator_sha256": digest(PACK / "offline/evaluator.json"), "feedback_to_model": False}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    return {"scored_cells": len(reports), "output": str(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run", "score"):
        command = commands.add_parser(name)
        command.add_argument("--output", type=Path, required=True)
        if name == "run":
            command.add_argument("--prepared", type=Path, required=True)
            command.add_argument("--live", action="store_true")
        if name == "score":
            command.add_argument("--batch", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output must not already exist")
    try:
        result = prepare(args.output) if args.command == "prepare" else run(args.prepared, args.output, args.live) if args.command == "run" else score(args.batch, args.output)
    except (ValueError, ProtocolError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result))
    return 2 if args.command == "run" and result["status"] != "completed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
