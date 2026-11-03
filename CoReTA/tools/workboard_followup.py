"""Bounded one-step provenance probes and a historical controlled-input retest. No gold reads."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from coreta.application_v2.inputs import Packets
from coreta.handoff.__main__ import PROJECT, DESIGN, configure, load_counter
from coreta.handoff.gateway import write_json
from coreta.schemas import ProtocolError

spec = importlib.util.spec_from_file_location("followup_pilot", PROJECT / "tools/workboard_pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
HISTORY = PROJECT / "refine-logs/sbp-diagnostic-v1/fixtures.json"
TRANSCRIPT = PROJECT / "runs/workboard-pilot-live-20261022-r3/concentrated-r2/ordinary_discussion/requests.jsonl"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def variant(packet, marked):
    packet = copy.deepcopy(packet)
    if marked:
        for work in packet["CANDIDATES"]:
            # Native INITIAL/DISCUSS never requested a declaration in this transcript.
            assert work["declared_sources"] == []
            work["source_declaration_status"] = "not_collected_in_INITIAL_or_DISCUSS"
        packet["SOURCE_DECLARATION_NOTE"] = (
            "These INITIAL/DISCUSS outputs were not asked to supply declared_sources. Their empty lists "
            "mean that declarations were not collected, not that the authors used no materials. "
            "This supplies no new evidence and does not verify any report or grant original access."
        )
    return packet


def historical_cache(packets):
    fixture = next(f for f in read(HISTORY)["fixtures"] if f["fixture_id"] == "derived_error")
    candidates = {}
    for member in packets.agents:
        records = [c for c in fixture["contributions"] if c["author"] == member]
        # Preserve every substantive field verbatim; old protocol C handles are not new references.
        text = "\n\n".join("Contribution text: " + c["content"] + "\nEvidence statement: " + c["support"]
            + "\nOriginal source references: " + json.dumps(c["support_refs"], ensure_ascii=False)
            + "\nConditions: " + json.dumps(c["conditions"], ensure_ascii=False)
            + "\nNeeds: " + json.dumps(c["needs"], ensure_ascii=False) for c in records)
        artifact = None
        if member != "A1":
            assert all("shared-only order A>B>C>D" in c["content"] for c in records)
            artifact = ["Candidate A", "Candidate B", "Candidate C", "Candidate D"]
        candidates[member] = {"artifact": artifact, "work_text": text, "open_points": []}
    return {"origin": "historical_controlled_fixture_not_model_initials", "member_packet_hashes": packets.hashes,
            "candidates": candidates}


def prepare(folder, *, historical_only=False):
    if folder.exists(): raise ValueError("Preparation must be new")
    folder.mkdir(parents=True)
    config, legacy = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    counter = load_counter()
    packets = Packets(pilot.PACK, "concentrated_A1")
    manifest = {"kind": "historical_input_standalone" if historical_only else "workboard_followup_diagnostics",
                "max_http_attempts": 100 if historical_only else 108,
                "source_hashes": {**pilot.sources(), str(Path(__file__).resolve()): digest(Path(__file__)),
                                  str(HISTORY): digest(HISTORY), str(TRANSCRIPT): digest(TRANSCRIPT)},
                "probes": [], "legacy_pairs": [], "sampling_seed_sent": False,
                "scoring_feedback": False, "stop_on_first_technical_error": True}
    transcript = [json.loads(line) for line in TRANSCRIPT.read_text(encoding="utf-8").splitlines()]
    for checkpoint in (() if historical_only else (7, 25)):
        record = next(r for r in transcript if r["call_context"]["logical_call"] == checkpoint)
        stage = record["call_context"]["stage"]
        assert record["call_context"]["member"] == "A3"
        packet = json.loads(record["payload"]["instructions"].split("\nPACKET=", 1)[1].split("\nOUTPUT_SCHEMA=", 1)[0])
        for repeat in (1, 2):
            for marked in ((False, True) if repeat == 1 else (True, False)):
                label = "not_collected" if marked else "original"
                uid = f"probe-c{checkpoint}-r{repeat}-{label}"
                data = variant(packet, marked)
                runner = pilot.engine(folder / "_unused", packets, config, legacy, "ordinary_discussion", 2, counter)
                schema = runner.gateway.contracts.schema(stage, data)
                payload = runner.gateway.client.payload(runner.gateway.prompts.render(stage, data, schema), schema,
                                                        runner.gateway.outputs[stage.lower()])
                if not marked: assert payload == record["payload"], "Control must exactly reproduce old request"
                estimate = runner.gateway.client.size(payload)
                if estimate > config["generation"]["max_input_tokens"]:
                    raise ValueError("Probe exceeds context budget")
                write_json(folder / f"{uid}.json", {"packet": data, "payload": payload})
                manifest["probes"].append({"id": uid, "checkpoint": checkpoint, "stage": stage,
                                           "repeat": repeat, "variant": label, "member": "A3",
                                           "execution_calls": 1, "preserved_historical_budget": True})
    cache = historical_cache(packets)
    write_json(folder / "historical_cache.json", cache)
    for repeat in (1, 2):
        methods = ["ordinary_discussion", "coreta_workboard"] if repeat == 1 else ["coreta_workboard", "ordinary_discussion"]
        manifest["legacy_pairs"].append({"id": f"historical-r{repeat}", "ordinal": repeat, "methods": methods})
    manifest["prepared_file_hashes"] = {p.name: digest(p) for p in folder.glob("*.json")}
    write_json(folder / "manifest.json", manifest)
    return manifest


def run(prepared, output, transport_factory=None):
    manifest = read(prepared / "manifest.json")
    for path, expected in manifest["source_hashes"].items():
        if digest(Path(path)) != expected: raise ValueError("Source/fixture/transcript snapshot changed")
    for path, expected in manifest["prepared_file_hashes"].items():
        if digest(prepared / path) != expected: raise ValueError("Prepared input changed")
    if output.exists(): raise ValueError("Output must be new; no resume")
    output.mkdir(parents=True)
    write_json(output / "manifest.json", manifest)
    progress = {"status": "running", "http_attempts": 0, "max_http_attempts": manifest["max_http_attempts"],
                "probes": [{**p, "status": "not_started"} for p in manifest["probes"]],
                "units": [{"pair": p["id"], "method": m, "ordinal": p["ordinal"], "status": "not_started"}
                          for p in manifest["legacy_pairs"] for m in p["methods"]]}
    write_json(output / "progress.json", progress)
    config, legacy = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    counter = load_counter(); packets = Packets(pilot.PACK, "concentrated_A1")
    try:
        for row in progress["probes"]:
            source = read(prepared / f"{row['id']}.json")
            folder = output / row["id"]; folder.mkdir()
            runner = pilot.engine(folder, packets, config, legacy, "ordinary_discussion", 2, counter,
                                  transport=transport_factory(row) if transport_factory else None)
            runner.gateway.limits["max_network_attempts_total"] = 1
            row["status"] = "running"
            try:
                stage = row["stage"]; packet = source["packet"]
                schema = runner.gateway.contracts.schema(stage, packet)
                payload = runner.gateway.client.payload(runner.gateway.prompts.render(stage, packet, schema), schema,
                                                        runner.gateway.outputs[stage.lower()])
                if payload != source["payload"]: raise ValueError("Probe request differs from preparation")
                value = runner.gateway.call(stage, row["member"], packet)
                write_json(output / row["id"] / "probe_result.json", {
                    "kind": "one_step_continuation_not_full_team_run", "output": value, "usage": runner.journal.usage})
                row["status"] = "completed"
            finally:
                row["http_attempts"] = runner.gateway.client.attempts
                progress["http_attempts"] += runner.gateway.client.attempts
                if row["status"] == "running": row["status"] = "interrupted"
                write_json(output / "progress.json", progress)
        cache = read(prepared / "historical_cache.json")
        for row in progress["units"]:
            folder = output / row["pair"] / row["method"]; folder.mkdir(parents=True)
            runner = pilot.engine(folder, packets, config, legacy, row["method"],
                                  row["ordinal"], counter, cache=cache,
                                  transport=transport_factory(row) if transport_factory else None)
            row["status"] = "running"
            try:
                result = runner.run()
                row.update(status=result["status"], stop_reason=result["stop_reason"])
            finally:
                row["http_attempts"] = runner.gateway.client.attempts
                progress["http_attempts"] += runner.gateway.client.attempts
                if row["status"] == "running": row["status"] = "implementation_error"
                write_json(output / "progress.json", progress)
            if result["status"] != "completed" or result["incomplete_or_unknown_usage_attempts"]:
                raise ProtocolError("TECHNICAL_STOP", f"Historical unit stopped: {row['pair']}/{row['method']}")
            print(json.dumps({"unit_completed": row["pair"] + "/" + row["method"],
                              "http_attempts": progress["http_attempts"]}), flush=True)
        progress["status"] = "completed"
    except Exception as exc:
        progress.update(status="stopped_on_first_technical_error", error={"type": type(exc).__name__, "detail": str(exc)})
        raise
    finally:
        write_json(output / "progress.json", progress)
    return progress


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run"])
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--historical-only", action="store_true", help="Prepare an independent historical-input batch; no probe reruns")
    args = parser.parse_args()
    if args.command == "run" and (not args.live or not os.environ.get("DEEPSEEK_API_KEY")):
        parser.error("Real execution requires --live and configured key")
    value = prepare(args.output, historical_only=args.historical_only) if args.command == "prepare" else run(args.prepared, args.output)
    print(json.dumps({"status": value.get("status", "prepared"), "output": str(args.output)}))
