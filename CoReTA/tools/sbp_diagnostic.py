"""Prepare isolated SBP diagnostics; real requests require run --live."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

from coreta.application_v2.contracts import ApplicationContracts
from coreta.application_v2.inputs import Packets
from coreta.application_v2.prompts import ApplicationPrompts
from coreta.application_v2.ranking import render_ranking
from coreta.application_v2.runtime import ApplicationRunner
from coreta.handoff.__main__ import DESIGN, DEFAULT_TOKENIZER, configure, load_counter
from coreta.handoff.contracts import HandoffContracts
from coreta.handoff.gateway import Gateway, Journal, write_json
from coreta.schemas import ProtocolError

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "refine-logs/sbp-diagnostic-v1"
PACK = ROOT / "data/task-packs/student-president-dev-v1"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def frozen_sources():
    paths = list((ROOT / "src/coreta").rglob("*.py"))
    paths += [Path(__file__), PLAN / "matrix.json", PLAN / "fixtures.json",
              DESIGN / "message.schema.json", DESIGN / "PROMPTS.md", DESIGN / "runtime.defaults.json",
              ROOT / "config/deepseek_flash_inspection.json", DEFAULT_TOKENIZER]
    paths += list((PACK / "packets/concentrated_A1").glob("*.json"))
    paths.append(PACK / "public/task.json")
    return {str(p.resolve()): digest(p) for p in paths}


class DiagnosticContracts(ApplicationContracts):
    """Isolated reference-capacity repair; retain enums and uniqueness."""
    def schema(self, stage, refs, agents, allowed, ranking_items=None):
        schema = super().schema(stage, refs, agents, allowed, ranking_items)
        if "Refs" in schema.get("$defs", {}):
            schema["$defs"]["Refs"]["maxItems"] = len(refs)
        if stage == "APPLY" and "Application" in schema.get("$defs", {}):
            # Bindings must accommodate accumulated visible public evidence while
            # remaining bounded by the current ref set and the dynamic Ref enum.
            schema["$defs"]["Application"]["properties"]["bindings"]["maxItems"] = len(refs)
        return schema


class DiagnosticRunner(ApplicationRunner):
    def __init__(self, *args, cell, fixture=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cell = cell
        self.fixture = fixture
        self.diagnostic_outputs = {}
        if cell["block"] == "initial_generation":
            self.selected_member = "A1"
        if fixture:
            self.contributions = copy.deepcopy(fixture["contributions"])
            ranking = [f"Candidate {c}" for c in "ABCD"]
            self.work = {"ref": "W1", "artifact": render_ranking(ranking), "ranking": ranking,
                         "unresolved": [], "application_history": [], "artifact_uses": [],
                         "changed_text": True, "origin": "controlled_A2_shared_only_fallback_not_scored"}
            self.works = [copy.deepcopy(self.work)]
            # Identical content objects; only the method's normal packet field differs.
            self.discussion = copy.deepcopy(self.contributions)

    def packet(self, agent, stage, allowed=()):
        packet = super().packet(agent, stage, allowed)
        if self.cell["block"] == "initial_generation":
            # Existing contribution renderer requires this key. Empty in both arms;
            # independent rendering omits it, so neither arm receives directory facts.
            packet["DIRECTORY"] = []
        elif self.fixture and stage in {"DISCUSS", "FINAL"}:
            # Public C handles are visible, private S handles remain owner-only.
            packet["REFERENCE_INDEX"] += [
                {"ref": c["ref"], "kind": "public_contribution"} for c in self.contributions]
        return packet

    def full_answer(self, agent):
        if self.cell["block"] != "initial_generation":
            return super().full_answer(agent)
        if agent != "A1":
            return None
        stage = "INDEPENDENT" if self.cell["arm"] == "independent" else "CONTRIBUTE"
        output = self.gateway.call(stage, agent, self.packet(agent, stage))
        self.diagnostic_outputs[agent] = output
        if stage == "INDEPENDENT":
            self.independent[agent] = render_ranking(output["ranking"])
            self.independent_details[agent] = copy.deepcopy(output)
        self.event("diagnostic_initial_output", stage=stage, member=agent, output=output)
        return output

    def contribute(self, agent, stage="CONTRIBUTE"):
        if self.fixture and stage == "CONTRIBUTE":
            return [c["ref"] for c in self.contributions if c["author"] == agent], "Controlled input; no model call"
        return super().contribute(agent, stage)

    def ordinary(self):
        # Only the initial generation/publication is replaced; retain original 2x4 + FINAL schedule.
        for round_number in range(2):
            for agent in self.agents:
                value = self.gateway.call("DISCUSS", agent, self.packet(agent, "DISCUSS"))
                self.discussion.append({"author": agent, "kind": "discussion", "round": round_number + 1,
                                        "text": value["text"]})
                self.event("discussion", member=agent, round=round_number + 1, text=value["text"])
        value = self.gateway.call("FINAL", self.driver, self.packet(self.driver, "FINAL"))
        old = self.work
        self.work = {"ref": f"W{len(self.works)+1}", "artifact": render_ranking(value["ranking"]),
                     "ranking": value["ranking"], "explanation": value["explanation"], "unresolved": [],
                     "application_history": [], "changed_text": old["ranking"] != value["ranking"]}
        self.works.append(copy.deepcopy(self.work))
        self.event("ordinary_final", structured=value)
        return "discussion_finished"

    def run(self, system="coreta"):
        result = super().run(system)
        result.update(diagnostic_block=self.cell["block"], diagnostic_arm=self.cell["arm"],
                      diagnostic_cell=self.cell["id"], controlled_initial_content=bool(self.fixture))
        if self.cell["block"] == "initial_generation":
            result["diagnostic_initial_outputs"] = copy.deepcopy(self.diagnostic_outputs)
            result["complete_ranking_required"] = self.cell["arm"] == "independent"
        write_json(self.journal.root / "result.json", result)
        return result


def build(cell, output, counter, *, transport=None):
    config, defaults = configure(ROOT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    defaults = copy.deepcopy(defaults)
    defaults["limits"]["max_network_attempts_total"] = cell["max_http_attempts"]
    defaults["max_output_tokens"].update(contribute=3072, reply=3072, review=3072, apply=6144)
    if cell["block"] == "initial_generation":
        defaults["max_output_tokens"].update(independent=3072)
    else:
        defaults["max_output_tokens"].update(discuss=3072, final=6144)
    fixtures = read(PLAN / "fixtures.json")["fixtures"]
    correct, wrong = fixtures
    require(correct["fixture_id"] == "correct" and wrong["fixture_id"] == "derived_error", "Fixture order changed")
    require(correct["contributions"][4:] == wrong["contributions"][4:], "Nonexpert input changed")
    for a, b in zip(correct["contributions"][:4], wrong["contributions"][:4]):
        require(a["content"].split("Reported shared subtotal=")[0] == b["content"].split("Reported shared subtotal=")[0], "Primitive facts changed")
        candidate = a["content"].split('.')[0]
        require((a == b) == (candidate in {"Candidate B", "Candidate C"}), "Unexpected injected difference")
    fixture = next((f for f in fixtures if f["fixture_id"] == cell.get("fixture_id")), None)
    packets = Packets(PACK, "concentrated_A1")
    journal = Journal(output)
    gateway = Gateway(config, defaults, DiagnosticContracts(DESIGN / "message.schema.json"),
                      ApplicationPrompts(DESIGN / "PROMPTS.md"), journal, transport=transport, token_counter=counter)
    runner = DiagnosticRunner(packets, gateway, journal, cell=cell, fixture=fixture)
    runner.system = "coreta" if cell["arm"] == "coreta" else "independent" if cell["block"] == "initial_generation" else "ordinary_discussion"
    return runner


def first_request(runner):
    cell = runner.cell
    if cell["block"] == "initial_generation":
        stage = "INDEPENDENT" if cell["arm"] == "independent" else "CONTRIBUTE"
        agent, allowed = "A1", []
    else:
        stage = "APPLY" if cell["arm"] == "coreta" else "DISCUSS"
        agent = runner.driver if stage == "APPLY" else runner.agents[0]
        allowed = runner.allowed() if stage == "APPLY" else []
    packet = runner.packet(agent, stage, allowed)
    schema = runner.gateway.contracts.schema(stage, {r["ref"] for r in packet["REFERENCE_INDEX"]},
                                             runner.agents, allowed, ranking_items=[i["name"] for i in runner.packets.task["items"]])
    cap = runner.gateway.outputs.get(stage.lower(), 3072)
    payload = runner.gateway.client.payload(runner.gateway.prompts.render(stage, packet, schema), schema, cap)
    return {"stage": stage, "member": agent, "packet": packet, "payload": payload,
            "estimated_input_tokens": runner.gateway.client.size(payload)}


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def validate_plan():
    matrix = read(PLAN / "matrix.json")
    require(len(matrix["cells"]) == 36 and len({c["id"] for c in matrix["cells"]}) == 36, "Unexpected matrix")
    require(sum(c["max_http_attempts"] for c in matrix["cells"]) == 288, "Unexpected budget")
    for filename, expected in matrix["input_sha256"].items():
        path = Path(filename)
        if not path.is_absolute():
            path = ROOT.parent / path
        require(digest(path) == expected, "Input changed: " + filename)
    return matrix


def prepare(output):
    matrix = validate_plan()
    counter = load_counter()
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for cell in matrix["cells"]:
        folder = output / cell["id"]
        folder.mkdir()
        runner = build(cell, folder, counter)
        initial = first_request(runner)
        require(initial["estimated_input_tokens"] <= 32768, "Initial input overflow")
        write_json(folder / "initial.json", initial)
        write_json(folder / "manifest.json", {"cell": cell, "config": runner.gateway.config,
                                             "defaults": {"limits": runner.gateway.limits, "outputs": runner.gateway.outputs},
                                             "sampling_seed_sent": False, "synthetic": bool(runner.fixture)})
        rows.append({"id": cell["id"], "initial_sha256": digest(folder / "initial.json"),
                     "manifest_sha256": digest(folder / "manifest.json"),
                     "estimated_input_tokens": initial["estimated_input_tokens"]})
    write_json(output / "prepared.json", {"kind": "prepared_diagnostic_not_results", "network_requests": 0,
                                          "cells": rows, "source_sha256": frozen_sources()})


def check(prepared):
    """Read-only, network-free acceptance checks; does not pretend model output is real."""
    matrix = validate_plan()
    frozen = read(prepared / "prepared.json")
    for filename, expected in frozen["source_sha256"].items():
        require(digest(Path(filename)) == expected, "Prepared source changed: " + filename)
    requests = {}
    for row in frozen["cells"]:
        folder = prepared / row["id"]
        require(digest(folder / "initial.json") == row["initial_sha256"], "Prepared request changed")
        require(digest(folder / "manifest.json") == row["manifest_sha256"], "Prepared manifest changed")
        data = read(folder / "initial.json")
        require(data["estimated_input_tokens"] <= 32768, "Overflow")
        text = canonical(data)
        require("offline_evaluation" not in text and '"injected_errors"' not in text, "Offline metadata leaked")
        requests[row["id"]] = data
    for r in range(1, 13):
        require(requests[f"I-r{r:02d}-independent"]["packet"] == requests[f"I-r{r:02d}-contribute"]["packet"], "D1 unequal data")
    fixtures = read(PLAN / "fixtures.json")["fixtures"]
    for fixture in fixtures:
        cs = fixture["contributions"]
        require(len(cs) == 7 and [c["ref"] for c in cs] == [f"C{i}" for i in range(1, 8)], "Invalid fixed IDs")
        for r in range(1, 4):
            a = requests[f"H-{fixture['fixture_id']}-r{r}-ordinary_discussion"]["packet"]
            b = requests[f"H-{fixture['fixture_id']}-r{r}-coreta"]["packet"]
            require(a["PUBLIC_DISCUSSION"] == b["CONTRIBUTIONS"] == cs, "Unequal public content")
            # First speaker differs by design; compare all member private permissions directly.
            packets = Packets(PACK, "concentrated_A1")
            for member in packets.agents:
                require(len(packets.member(member)["SELF_MATERIALS"]) == (16 if member == "A1" else 0), "Private access mismatch")
        for c in cs:
            own = Packets(PACK, "concentrated_A1").member(c["author"])
            refs = {row["ref"] for row in own["REFERENCE_INDEX"]}
            require(set(c["support_refs"]) <= refs, "Fixture cites inaccessible source")
            for material in own["SELF_MATERIALS"]:
                if material["ref"] in c["support_refs"]:
                    require(material["content"] in c["content"], "Fixture altered a raw fact")
    refs = {"T"} | {f"S{i:02d}" for i in range(1, 17)}
    contract = DiagnosticContracts(DESIGN / "message.schema.json")
    schema = contract.schema("CONTRIBUTE", refs, ["A1", "A2", "A3", "A4"], [], ranking_items=None)
    example = {"items": [{"content": "Capacity example only", "support": "Offline shape check",
                          "support_refs": sorted(refs), "conditions": [], "needs": []}], "note": "Not a model result"}
    HandoffContracts.decode(json.dumps(example), schema)
    for bad_refs in [["T", "T"], ["S99"]]:
        bad = copy.deepcopy(example)
        bad["items"][0]["support_refs"] = bad_refs
        try:
            HandoffContracts.decode(json.dumps(bad), schema)
        except ProtocolError:
            pass
        else:
            raise ValueError("Invalid or duplicate references accepted")
    apply_refs = {"T", "W1", "V1", "Q1"} | {f"C{i}" for i in range(1, 16)}
    apply_schema = contract.schema("APPLY", apply_refs, ["A1", "A2", "A3", "A4"], ["ask", "check", "probe"],
                                   ranking_items=[f"Candidate {c}" for c in "ABCD"])
    application = {"target": None, "task_step": "Accumulated public evidence", "bindings": [
        {"ref": ref, "use": "Visible public evidence"} for ref in sorted(apply_refs)],
        "result": "Bounded shape acceptance only", "missing": None}
    apply_example = {"artifact": [f"Candidate {c}" for c in "ABCD"], "applications": [application],
                     "artifact_uses": [], "retire_applications": [], "excluded": [], "unresolved": [], "request": None}
    require(apply_schema["$defs"]["Application"]["properties"]["bindings"]["maxItems"] == len(apply_refs),
            "Bindings cap does not match visible reference capacity")
    HandoffContracts.decode(json.dumps(apply_example), apply_schema)
    return {"network_requests": 0, "prepared_cells": len(matrix["cells"]), "identical_D1_inputs": True,
            "identical_D2_public_content": True, "owner_only_private_sources": True,
            "reference_17_capacity": True, "invalid_and_duplicate_refs_rejected": True,
            "fifteen_application_bindings": True, "bindings_bounded_by_visible_refs": True,
            "limits": "Static first-request and schema shapes checked; full scheduling is covered by the scripted path acceptance."}


def run(prepared, output, block=None):
    check(prepared)
    counter = load_counter()
    matrix = validate_plan()
    output.mkdir(parents=True, exist_ok=False)
    selected = [c for c in matrix["cells"] if block is None or c["block"] == block]
    if block == "controlled_coordination":
        require(len(selected) == 12, "Expected all twelve controlled coordination cells")
    report = {"kind": "real_controlled_diagnostic", "status": "running", "cells": [], "active_cell": None,
              "prepared_manifest_sha256": digest(prepared / "prepared.json"), "scoring_feedback": False,
              "matrix_cell_ids": [c["id"] for c in selected], "block": block or "all"}
    try:
        for cell in selected:
            report["active_cell"] = cell["id"]
            write_json(output / "batch.json", report)
            folder = output / cell["id"]
            folder.mkdir()
            runner = build(cell, folder, counter)
            require(first_request(runner) == read(prepared / cell["id"] / "initial.json"), "Live initial input differs")
            write_json(folder / "manifest.json", read(prepared / cell["id"] / "manifest.json"))
            write_json(folder / "injection.json", {"synthetic": bool(runner.fixture), "fixture": runner.fixture})
            try:
                result = runner.run(runner.system)
            except BaseException as exc:
                runner.save_state()
                write_json(folder / "interruption.json", {"type": type(exc).__name__})
                raise
            if cell["block"] == "initial_generation":
                write_json(folder / "diagnostic_outputs.json", runner.diagnostic_outputs)
                delivered = "A1" in runner.diagnostic_outputs
            else:
                delivered = runner.work is not None and len(runner.work.get("ranking", [])) == 4
            clean = (delivered and result["status"] not in {"protocol_failure", "budget_exhausted"}
                     and result["format_repairs"] == 0 and result["usage_complete"]
                     and result["http_attempts"] == result["logical_calls"])
            report["cells"].append({"id": cell["id"], "clean": clean, "status": result["status"],
                                    "http_attempts": result["http_attempts"], "logical_calls": result["logical_calls"],
                                    "format_repairs": result["format_repairs"]})
            report["active_cell"] = None
            if not clean:
                report["status"] = "stopped_for_diagnosis"
                break
        else:
            report["status"] = "completed"
    except BaseException as exc:
        report["status"] = "interrupted_or_runner_error"
        report["error_type"] = type(exc).__name__
        raise
    finally:
        write_json(output / "batch.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "check", "run"])
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--block", choices=["initial_generation", "controlled_coordination"])
    args = parser.parse_args()
    if args.command == "prepare":
        if args.output is None:
            parser.error("prepare requires --output")
        prepare(args.output)
    elif args.command == "check":
        if args.prepared is None:
            parser.error("check requires --prepared")
        report = check(args.prepared)
        if args.output:
            with args.output.open("x", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        print(json.dumps(report))
    else:
        if not args.live or not os.environ.get("DEEPSEEK_API_KEY") or args.output is None or args.prepared is None:
            parser.error("run requires --prepared, --output, --live and configured DEEPSEEK_API_KEY")
        report = run(args.prepared, args.output, args.block)
        print(json.dumps(report))
        return 0 if report["status"] == "completed" else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
