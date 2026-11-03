"""Prepare and explicitly run eight paired development units; never reads offline scores."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

from coreta.application_v2.inputs import Packets
from coreta.handoff.__main__ import PROJECT, DESIGN, DEFAULT_TOKENIZER, configure, load_counter
from coreta.handoff.gateway import Journal, write_json
from coreta.handoff.inputs import read_json
from coreta.schemas import ProtocolError
from coreta.workboard.artifacts import RankingAdapter
from coreta.workboard.baseline import DiscussionRunner, DiscussionPrompts
from coreta.workboard.contracts import Contracts
from coreta.workboard.gateway import Gateway, defaults
from coreta.workboard.prompts import Prompts
from coreta.workboard.runtime import Runner


PACK = PROJECT / "data/task-packs/student-president-dev-v1"


def settings(legacy, system):
    result = defaults(4, legacy)
    result["limits"].update(max_network_attempts_total=4 if system == "initial" else 25,
                           max_output_tokens_total=16384 if system == "initial" else 61440)
    result["max_output_tokens"].update(discuss=2304)
    if system == "ordinary_discussion":
        result["max_output_tokens"]["finalize"] = 6144
    result["budget_status"] = "frozen_student_president_behavior_pilot_v1"
    return result


def pairs():
    return [
        {"id": "distributed-r1", "condition": "distributed", "replicate": 1, "ordinal": 1,
         "methods": ["ordinary_discussion", "coreta_workboard"]},
        {"id": "concentrated-r1", "condition": "concentrated_A1", "replicate": 1, "ordinal": 1,
         "methods": ["coreta_workboard", "ordinary_discussion"]},
        {"id": "distributed-r2", "condition": "distributed", "replicate": 2, "ordinal": 2,
         "methods": ["coreta_workboard", "ordinary_discussion"]},
        {"id": "concentrated-r2", "condition": "concentrated_A1", "replicate": 2, "ordinal": 2,
         "methods": ["ordinary_discussion", "coreta_workboard"]},
    ]


def sources():
    paths = list((PROJECT / "src/coreta/workboard").glob("*.py"))
    paths += [Path(__file__), PROJECT / "src/coreta/model_client.py", PROJECT / "src/coreta/schemas.py",
              PROJECT / "src/coreta/application_v2/inputs.py", PROJECT / "src/coreta/handoff/inputs.py",
              PROJECT / "src/coreta/handoff/gateway.py", PROJECT / "src/coreta/handoff/contracts.py",
              PROJECT / "src/coreta/handoff/__main__.py", PROJECT / "config/deepseek_flash_inspection.json",
              DESIGN / "runtime.defaults.json", DEFAULT_TOKENIZER]
    for condition in ("distributed", "concentrated_A1"):
        paths += sorted((PACK / "packets" / condition).glob("*.json"))
    return {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def engine(folder, packets, config, legacy, system, ordinal, counter, *, cache=None, transport=None):
    journal = Journal(folder)
    adapter = RankingAdapter(packets.task)
    cls = DiscussionRunner if system == "ordinary_discussion" else Runner
    prompts = DiscussionPrompts() if system == "ordinary_discussion" else Prompts()
    gateway = Gateway(config, settings(legacy, system), Contracts(adapter), prompts, journal,
                      token_counter=counter, transport=transport)
    return cls(packets, gateway, journal, adapter, task_ordinal=ordinal, initial_cache=cache)


def prepare(folder):
    config, legacy = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    counter = load_counter()
    manifest = {"kind": "student_president_workboard_behavior_pilot_v1", "method_units": 8,
                "max_http_attempts": 216, "transport_retries": 0, "format_repairs": 0,
                "sampling_seed_sent": False, "scoring_feedback": False,
                "scope": "one_development_scenario_not_general_effectiveness",
                "source_hashes": sources(), "configuration": config,
                "settings": {s: settings(legacy, s) for s in ("initial", "coreta_workboard", "ordinary_discussion")},
                "pairs": pairs(), "initial_context_estimates": {}}
    folder.mkdir(parents=True, exist_ok=False)
    for pair in manifest["pairs"]:
        packets = Packets(PACK, pair["condition"])
        sub = folder / pair["id"]
        sub.mkdir()
        runner = engine(sub, packets, config, legacy, "initial", pair["ordinal"], counter)
        for member in packets.agents:
            p = runner.packet(member, "INITIAL")
            schema = runner.gateway.contracts.schema("INITIAL", p)
            payload = runner.gateway.client.payload(runner.gateway.prompts.render("INITIAL", p, schema), schema, 4096)
            size = runner.gateway.client.size(payload)
            if size > config["generation"]["max_input_tokens"]:
                raise ProtocolError("CONTEXT_OVERFLOW", "Initial request exceeds frozen input cap")
            write_json(sub / f"{member}.request.json", payload)
            manifest["initial_context_estimates"][pair["id"] + "/" + member] = size
    write_json(folder / "manifest.json", manifest)
    return manifest


def run(prepared, output):
    manifest = read_json(prepared / "manifest.json")
    if manifest["source_hashes"] != sources():
        raise ProtocolError("INPUT_ERROR", "Prepared source/packet snapshot is stale; prepare a new version")
    config, legacy = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    counter = load_counter()
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "manifest.json", manifest)
    summary = {"kind": manifest["kind"], "status": "running", "http_attempts": 0,
               "max_http_attempts": 216, "pairs": [], "units": [
                   {"pair": p["id"], "method": m, "status": "not_started"}
                   for p in manifest["pairs"] for m in p["methods"]]}
    write_json(output / "progress.json", summary)
    try:
        for pair in manifest["pairs"]:
            packets = Packets(PACK, pair["condition"])
            pairfolder = output / pair["id"]
            initfolder = pairfolder / "initial"
            initfolder.mkdir(parents=True)
            initial = engine(initfolder, packets, config, legacy, "initial", pair["ordinal"], counter)
            cache = {"origin": str(initfolder.resolve()), "member_packet_hashes": packets.hashes, "candidates": {}}
            pair_report = {"pair": pair["id"], "initial_status": "running", "initial_http_attempts": 0}
            summary["pairs"].append(pair_report)
            try:
                for member in packets.agents:
                    packet = initial.packet(member, "INITIAL")
                    expected = read_json(prepared / pair["id"] / f"{member}.request.json")
                    schema = initial.gateway.contracts.schema("INITIAL", packet)
                    payload = initial.gateway.client.payload(initial.gateway.prompts.render("INITIAL", packet, schema), schema, 4096)
                    # Budget remaining decreases between calls; compare against preparation with that one field normalized.
                    prepared_packet = json.loads(expected["instructions"].split("\nPACKET=", 1)[1].split("\nOUTPUT_SCHEMA=", 1)[0])
                    prepared_packet["BUDGET"] = packet["BUDGET"]
                    expected["instructions"] = initial.gateway.prompts.render("INITIAL", prepared_packet, schema)
                    if payload != expected:
                        raise ProtocolError("INPUT_ERROR", "Live initial request diverges from prepared packet")
                    cache["candidates"][member] = initial.gateway.call("INITIAL", member, packet)
            finally:
                pair_report["initial_http_attempts"] = initial.gateway.client.attempts
                pair_report["initial_usage"] = copy.deepcopy(initial.journal.usage)
                pair_report["initial_incomplete_or_unknown_usage_attempts"] = initial.gateway.client.attempts - sum(
                    type(u.get("input_tokens")) is int and u["input_tokens"] >= 0
                    and type(u.get("output_tokens")) is int and u["output_tokens"] >= 0
                    for u in initial.journal.usage)
                summary["http_attempts"] += initial.gateway.client.attempts
                write_json(initfolder / "cache.json", cache)
                write_json(output / "progress.json", summary)
            pair_report["initial_status"] = "completed"
            for method in pair["methods"]:
                row = next(u for u in summary["units"] if u["pair"] == pair["id"] and u["method"] == method)
                row["status"] = "running"
                folder = pairfolder / method
                folder.mkdir()
                runner = engine(folder, packets, config, legacy, method, pair["ordinal"], counter, cache=cache)
                try:
                    result = runner.run()
                    row.update(status=result["status"], stop_reason=result["stop_reason"],
                               selected_work_id=result["selected_work_id"], result_path=str((folder / "result.json").resolve()))
                    if result["status"] != "completed":
                        raise ProtocolError("PILOT_STOP", f"Technical stop in {pair['id']}/{method}: {result['stop_reason']}")
                finally:
                    row["http_attempts"] = runner.gateway.client.attempts
                    summary["http_attempts"] += runner.gateway.client.attempts
                    write_json(output / "progress.json", summary)
            print(json.dumps({"pair_completed": pair["id"], "http_attempts": summary["http_attempts"]}), flush=True)
        summary["status"] = "completed"
    except Exception as exc:
        for p in summary["pairs"]:
            if p["initial_status"] == "running":
                p["initial_status"] = "interrupted"
        for u in summary["units"]:
            if u["status"] == "running":
                u["status"] = "implementation_error"
        summary.update(status="stopped_on_first_technical_error", error={"type": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        write_json(output / "progress.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--output", type=Path, required=True)
    execute = sub.add_parser("run")
    execute.add_argument("--prepared", type=Path, required=True)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output must be new; no in-place resume")
    if args.command == "run" and (not args.live or not os.environ.get("DEEPSEEK_API_KEY")):
        parser.error("Requires --live and configured DEEPSEEK_API_KEY")
    try:
        value = prepare(args.output) if args.command == "prepare" else run(args.prepared, args.output)
        print(json.dumps({"command": args.command, "output": str(args.output), "status": value.get("status", "prepared")}))
    except (ProtocolError, ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
