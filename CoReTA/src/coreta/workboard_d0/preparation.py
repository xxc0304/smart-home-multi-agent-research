"""Prepare scoped D0 diagnostics; no gold, final states or natural solving calls."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import time
from pathlib import Path

from ..handoff.__main__ import PROJECT, DESIGN, DEFAULT_TOKENIZER, configure, load_counter
from ..handoff.gateway import Journal, write_json
from ..model_client import DeepSeekClient
from ..schemas import ProtocolError
from ..workboard.artifacts import RankingAdapter, ChoiceAdapter
from ..workboard.choice_inputs import ChoicePackets
from ..workboard.contracts import Contracts as V3Contracts
from ..workboard.prompts import Prompts as V3Prompts
from .contracts import Contracts
from .prompts import Prompts
from .handoff import CompactChoicePrompts


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def lines(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def packet_from_request(row):
    return json.loads(row["payload"]["instructions"].split("\nPACKET=", 1)[1].rsplit("\nOUTPUT_SCHEMA=", 1)[0])


def hashes(paths):
    return {str(Path(p).resolve()): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}


def implementation_sources():
    return [*Path(__file__).parent.glob("*.py"), *(PROJECT / "src/coreta/workboard").glob("*.py"),
            PROJECT / "src/coreta/model_client.py", PROJECT / "src/coreta/schemas.py",
            PROJECT / "src/coreta/handoff/contracts.py", PROJECT / "src/coreta/handoff/gateway.py",
            PROJECT / "src/coreta/handoff/inputs.py", PROJECT / "src/coreta/handoff/__main__.py",
            PROJECT / "src/coreta/application_v2/inputs.py", PROJECT / "tools/workboard_d0_diagnostics.py",
            PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json", DEFAULT_TOKENIZER]


def prepare_compatibility(output, replay_root):
    output, replay_root = Path(output), Path(replay_root)
    requests = lines(replay_root / "replay-final/requests.jsonl")
    rows = read(replay_root / "SCRIPTED_stage_responses.json")
    if len(requests) != len(rows):
        raise ValueError("Engineering replay requests and expected responses differ")
    entries = [(packet_from_request(r), copy.deepcopy(s["output"])) for r, s in zip(requests, rows)]
    def find(stage, focused):
        return copy.deepcopy(next((p, v) for p, v in entries if p["STAGE"] == stage
                                  and bool(p.get("FOCUS")) == focused))
    cases = []
    for stage, focused, label in (("OBSERVE", False, "observe_null"), ("OBSERVE", True, "observe_response"),
                                  ("CHOOSE", False, "choose_new_question"), ("CHOOSE", True, "choose_addressed")):
        p, v = find(stage, focused)
        cases.append((label, stage, p, v))
    p, v = find("CHOOSE", False)
    v["next_check"] = None
    cases.append(("choose_null", "CHOOSE", p, v))
    for disposition in ("pending", "deferred"):
        p, v = find("CHOOSE", True)
        v["next_check"] = None
        v["focus_disposition"]["status"] = disposition
        cases.append(("choose_" + disposition, "CHOOSE", p, v))
    p, v = find("CHOOSE", True)
    p["STAGE"] = "FINAL_CHOOSE"
    del v["next_check"]
    cases.append(("final_choose_addressed", "FINAL_CHOOSE", p, v))
    config, _ = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    config["protocol"] = {"transport_retries_per_request": 0, "request_timeout_seconds": 120}
    client = DeepSeekClient(config, lambda *args: None, token_counter=load_counter())
    contracts = Contracts(RankingAdapter(entries[0][0]["TASK"]))
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"kind": "d0_schema_copy_only", "max_http_attempts": len(cases), "cases": [],
                "natural_solving_verified": False, "full_stage_prompts_tested": False,
                "transport_retries": 0, "format_repairs": 0,
                "source_hashes": hashes(implementation_sources() + [replay_root / "SCRIPTED_stage_responses.json",
                                                                    replay_root / "replay-final/requests.jsonl"])}
    for label, stage, packet, value in cases:
        schema = contracts.schema(stage, packet)
        contracts.decode(json.dumps(value), schema)
        contracts.validate_action(stage, value)
        cap = 2048 if stage == "OBSERVE" else 512
        instruction = ("Schema compatibility copy check only. Copy EXACTLY the JSON below. Do not solve, "
                       "explain, shorten or improve it. Return only the JSON object.\n" + json.dumps(value, ensure_ascii=False))
        payload = client.payload(instruction, schema, cap)
        count = client.size(payload)
        if count > config["generation"]["max_input_tokens"]:
            raise ProtocolError("CONTEXT_OVERFLOW", "Copy request exceeds context limit")
        write_json(output / f"{label}.request.json", payload)
        write_json(output / f"{label}.expected.json", value)
        manifest["cases"].append({"id": label, "stage": stage, "max_output_tokens": cap,
                                   "estimated_input_tokens": count})
    manifest["max_output_tokens"] = sum(c["max_output_tokens"] for c in manifest["cases"])
    manifest["prepared_hashes"] = hashes([*output.glob("*.request.json"), *output.glob("*.expected.json")])
    write_json(output / "manifest.json", manifest)
    return manifest


def run_compatibility(prepared, output, transport=None):
    prepared, output = Path(prepared), Path(output)
    manifest = read(prepared / "manifest.json")
    if hashes(manifest["source_hashes"]) != manifest["source_hashes"]:
        raise ValueError("Source snapshot changed")
    if hashes(manifest["prepared_hashes"]) != manifest["prepared_hashes"]:
        raise ValueError("Prepared copy requests changed")
    if transport is None and not os.environ.get("DEEPSEEK_API_KEY"):
        raise ValueError("Approved API key is unavailable")
    config, _ = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    config["protocol"] = {"transport_retries_per_request": 0, "request_timeout_seconds": 120}
    output.mkdir(parents=True, exist_ok=False)
    journal = Journal(output)
    client = DeepSeekClient(config, journal.log, transport=transport, token_counter=load_counter())
    report = {"kind": manifest["kind"], "execution_mode": "live_copy" if transport is None else "scripted_engineering_only",
              "status": "running", "checks": [], "actual_http_attempts": 0,
              "service_compatibility_verified": False, "natural_solving_verified": False,
              "max_http_attempts": manifest["max_http_attempts"], "full_stage_prompts_tested": False}
    write_json(output / "manifest.json", manifest)
    write_json(output / "compatibility.json", report)
    try:
        for case in manifest["cases"]:
            payload = read(prepared / f"{case['id']}.request.json")
            expected = read(prepared / f"{case['id']}.expected.json")
            schema = payload["text"]["format"]["schema"]
            journal.call_context = {"case": case["id"], "stage": case["stage"], "kind": "copy_only"}
            row = {"case": case["id"]}
            report["checks"].append(row)
            raw = client.complete(payload, deadline=time.monotonic() + 125, logical_seed=17)
            value = Contracts.decode(raw, schema)
            Contracts.validate_action(case["stage"], value)
            complete_usage = sum(all(type(u.get(k)) is int and u[k] >= 0 for k in ("input_tokens", "output_tokens"))
                                 for u in journal.usage)
            if complete_usage != client.attempts:
                raise ProtocolError("USAGE_UNKNOWN", "Missing or incomplete usage; stop bounded copy check")
            row["copy_exact"] = value == expected
            if value != expected:
                raise ProtocolError("COPY_MISMATCH", "Response differs from fixed fixture")
        report.update(status="completed", service_compatibility_verified=transport is None)
    except ProtocolError as exc:
        report.update(status="stopped_on_first_error", error={"code": exc.code, "detail": exc.detail})
    finally:
        report.update(actual_http_attempts=client.attempts if transport is None else 0,
                      transport_attempts=client.attempts, usage=journal.usage,
                      fixture_usage_not_billable=transport is not None,
                      incomplete_or_unknown_usage_attempts=client.attempts - sum(
                          all(type(u.get(k)) is int and u[k] >= 0 for k in ("input_tokens", "output_tokens"))
                          for u in journal.usage))
        write_json(output / "compatibility.json", report)
    return report


def prepare_snapshots(output, source, dataset):
    output, source, dataset = Path(output), Path(source), Path(dataset)
    output.mkdir(parents=True, exist_ok=False)
    sources = implementation_sources()
    manifest = {"kind": "d0_vs_v3_local_repair_preparation", "snapshots": [], "live_calls": 0,
                "methods": ["v3_continuation", "d0_continuation"], "repeats": 1,
                "scope": "correlated_development_checkpoints_not_end_to_end",
                "gold_read": False, "source_hashes": {}, "max_http_attempts": 0, "max_output_tokens": 0}
    config, _ = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    counter = load_counter()
    for pair in sorted(source.glob("hb-dev-*-r*")):
        requests_path = pair / "coreta_workboard/requests.jsonl"
        requests = lines(requests_path)
        sources.append(requests_path)
        packets = ChoicePackets(dataset / pair.name.rsplit("-r", 1)[0], "distributed")
        sources += sorted((dataset / pair.name.rsplit("-r", 1)[0] / "packets/distributed").glob("*.json"))
        parsed = [packet_from_request(row) for row in requests]
        for index, packet in enumerate(parsed):
            if packet["STAGE"] != "CHOOSE":
                continue
            prior = parsed[:index]
            use = next(p for p in reversed(prior) if p["STAGE"] == "CHECK_USE")
            observe = next(p for p in reversed(prior) if p["STAGE"] == "OBSERVE")
            if (use["BEFORE"]["id"], use["AFTER"]["id"]) != (packet["BEFORE"]["id"], packet["AFTER"]["id"]):
                raise ValueError("Checkpoint before/after mismatch")
            works = copy.deepcopy(use["CANDIDATES"])
            ids = {w["id"] for w in works}
            if not set(packet["CHOICES"]) <= ids:
                raise ValueError("Checkpoint references unavailable work")
            cycle = packet["BUDGET"]["cycle"]
            label = f"{pair.name}-c{cycle}"
            folder = output / label
            folder.mkdir()
            for member in packets.agents:
                write_json(folder / f"{member}.packet.json", packets.member(member))
            counts = {a: 0 for a in packets.agents}
            trials = [p for p in prior if p["STAGE"] == "TRY"]
            for p in trials:
                counts[p["TARGET_OFFER"]["author"]] += 1
            provider = use["TARGET_OFFER"]["author"]
            snapshot = {"before": packet["BEFORE"], "after": packet["AFTER"], "checks": packet["CHECKS"],
                        "visible_works": works, "public_offers": packet["PUBLIC_EVIDENCE"],
                        "previous_feedback": observe["FEEDBACK"], "target_offer": use["TARGET_OFFER"],
                        "use_record": use["USE_RECORD"], "application_source_refs": use["APPLICATION_SOURCE_REFS"],
                        "editor": packet["SELF"]["agent_id"], "attempt_counts": counts,
                        "pointer": (packets.agents.index(provider) + 1) % len(packets.agents),
                        "choices": packet["CHOICES"]}
            write_json(folder / "snapshot.json", snapshot)
            estimates = {}
            for system, contracts, prompts in (("v3_continuation", V3Contracts(ChoiceAdapter(packets.task)), V3Prompts()),
                                               ("d0_continuation", Contracts(ChoiceAdapter(packets.task)), Prompts())):
                p = copy.deepcopy(packet)
                n = len(packets.agents)
                p["BUDGET"] = {"remaining_network_attempts": n + 4, "reserved_closure_calls": 0,
                               "cycle": cycle, "scope": "one_additional_local_repair_cycle"}
                if system == "d0_continuation":
                    p.update(FOCUS=None, FOCUS_HISTORY=[], FOCUS_FEEDBACK=[],
                             FOCUS_TARGETS=sorted({"whole_goal", *(w["id"] for w in (p["BEFORE"], p["AFTER"])),
                                                   *(loc for w in (p["BEFORE"], p["AFTER"]) for loc in w["locations"])}))
                schema = contracts.schema("CHOOSE", p)
                client = DeepSeekClient(config, lambda *args: None, token_counter=counter)
                payload = client.payload(CompactChoicePrompts(prompts).render("CHOOSE", p, schema), schema, 512)
                estimates[system] = client.size(payload)
                if estimates[system] > config["generation"]["max_input_tokens"]:
                    raise ProtocolError("CONTEXT_OVERFLOW", "Initial checkpoint request too large")
                write_json(folder / f"{system}.first.request.json", payload)
            n = len(packets.agents)
            calls, cap = n + 4, 1024 + (n - 1) * 2048 + 4096 + 2 * 3072
            order = manifest["methods"] if len(manifest["snapshots"]) % 2 == 0 else manifest["methods"][::-1]
            manifest["snapshots"].append({"id": label, "pair": pair.name, "cycle": cycle,
                "source_choose_call": requests[index]["call_context"]["logical_call"],
                "members": n, "methods": order, "per_method_calls": calls, "per_method_output_cap": cap,
                "initial_input_estimates": estimates})
            manifest["max_http_attempts"] += 2 * calls
            manifest["max_output_tokens"] += 2 * cap
    if len(manifest["snapshots"]) != 18:
        raise ValueError("Expected exactly all 18 natural checkpoints")
    manifest["source_hashes"] = hashes(sources)
    manifest["prepared_hashes"] = hashes(output.glob("*/*.json"))
    write_json(output / "manifest.json", manifest)
    write_json(output / "PREPARATION_ONLY.json", {"actual_http_attempts": 0, "snapshots": 18,
               "method_units": 36, "live_launcher_implemented": False,
               "natural_stage_compliance_verified": False, "scoring_performed": False})
    return manifest
