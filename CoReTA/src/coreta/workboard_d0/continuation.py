"""One additional local repair cycle from a frozen pre-CHOOSE checkpoint. No scoring."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

from ..handoff.__main__ import PROJECT, DESIGN, configure, load_counter
from ..handoff.gateway import Journal, write_json
from ..schemas import ProtocolError
from ..workboard.artifacts import ChoiceAdapter
from ..workboard.choice_inputs import ChoicePackets
from ..workboard.contracts import Contracts as V3Contracts
from ..workboard.prompts import Prompts as V3Prompts
from ..workboard.runtime import Runner as V3Runner
from ..workboard.gateway import Gateway, defaults
from .contracts import Contracts
from .prompts import Prompts
from .handoff import CompactChoicePrompts
from .runtime import Runner as D0Runner
from .preparation import hashes, implementation_sources, read


class FrozenPackets:
    def __init__(self, folder):
        self.members = {p.stem.split(".", 1)[0]: read(p) for p in Path(folder).glob("A*.packet.json")}
        if not self.members:
            raise ValueError("No frozen member packets")
        for p in self.members.values():
            ChoicePackets._validate(p)
        first = next(iter(self.members.values()))
        self.task, self.agents = first["TASK"], first["SELF"]["team"]
        if set(self.agents) != set(self.members) or len(self.agents) not in {3, 4}:
            raise ValueError("Frozen roster mismatch")
        for a, p in self.members.items():
            if p["SELF"] != {"agent_id": a, "team": self.agents} or p["TASK"] != self.task:
                raise ValueError("Frozen identity/task mismatch")
        self.hashes = {}

    def member(self, name):
        return copy.deepcopy(self.members[name])


class LocalMixin:
    is_d0 = False

    def packet(self, member, stage, **extra):
        p = super().packet(member, stage, **extra)
        p["BUDGET"].update(reserved_closure_calls=0, scope="one_additional_local_repair_cycle")
        return p

    def choose_local(self, base, trial, checks, *, original=None):
        focus_id = (self.active_focus() or {}).get("id") if self.is_d0 else None
        p = self.packet(self.editor, "CHOOSE", BEFORE=self.board.get(base), AFTER=self.board.get(trial),
                        CHECKS=checks, CHOICES=list(dict.fromkeys([base, trial])))
        if original is not None:
            schema = self.gateway.contracts.schema("CHOOSE", p)
            payload = self.gateway.client.payload(self.gateway.prompts.render("CHOOSE", p, schema), schema, 512)
            if payload != original:
                raise ProtocolError("INPUT_ERROR", "Restored first request differs from frozen request")
        choice = self.gateway.call("CHOOSE", self.editor, p)
        self.board.promote(choice["candidate_id"])
        if self.is_d0:
            self.record_choice(choice, base, trial, focus_id)
        self.event("local_selection", decision=choice, before=base, after=trial)
        return choice

    def one_cycle(self):
        self.cycle += 1
        base = self.board.current
        snapshots = ([(m, self.packet(m, "OBSERVE")) for m in self.agents if m != self.editor]
                     if self.is_d0 else ((m, None) for m in self.agents if m != self.editor))
        batch = []
        for member, p in snapshots:
            if p is None:
                p = self.packet(member, "OBSERVE")
            value = self.gateway.call("OBSERVE", member, p)
            if value["action"] == "pass":
                self.event("pass", member=member, base_version=base)
                continue
            offer = {"ref": f"O{len(self.offers) + 1}", "author": member,
                     "base_version": base, **value["offer"]}
            self.offers.append(copy.deepcopy(offer))
            batch.append(offer)
            self.event("offer_proposed", offer=offer)
        self.published.extend(copy.deepcopy(batch))
        if self.is_d0:
            for offer in batch:
                if offer["responds_to"]:
                    f = next(f for f in self.focus_history if f["id"] == offer["responds_to"])
                    f["responses"].append(offer["ref"])
                    self.event("focus_response", focus_id=f["id"], offer_ref=offer["ref"])
        if not batch:
            self.stop_reason = "all_pass"
            return
        selected = self.choose_offer(batch)
        for offer in batch:
            self.event("offer_selected" if offer["ref"] == selected["ref"] else "offer_untried",
                       offer_ref=offer["ref"], base_version=base)
        focus_id = (self.active_focus() or {}).get("id") if self.is_d0 else None
        value = self.gateway.call("TRY", self.editor, self.packet(self.editor, "TRY", TARGET_OFFER=selected))
        if value["action"] == "unable":
            row = {"kind": "unable_to_apply", "offer": selected, "reason": value["reason"],
                   "base_version": base, "reason_delivered_to_provider": False}
            if self.is_d0:
                row["focus_id"] = focus_id
            self.feedback.append(row)
            self.event("offer_not_applied", feedback=row)
            self.stop_reason = "unable_after_first_selection"
            return
        trial = self.materialize(value, base=base)
        self.event("trial_created", offer_ref=selected["ref"], before=base, after=trial,
                   use_record=value["use_record"], declared_sources=value["declared_sources"])
        if self.is_d0:
            for f in self.focus_history:
                if f["id"] in {focus_id, selected["responds_to"]}:
                    f["applications"].append({"cycle": self.cycle, "offer_ref": selected["ref"],
                        "before": base, "after": trial,
                        "relation": "selected_response" if f["id"] == selected["responds_to"] else "active_context_only"})
        checks = self.run_checks(selected["author"], base, trial, offer=selected,
                                 use_record=value["use_record"], declared_sources=value["declared_sources"])
        choice = self.choose_local(base, trial, checks)
        row = {"kind": "application_feedback", "offer": selected, "before": base, "after": trial,
               "use_record": value["use_record"], "checks": checks, "decision": choice}
        if self.is_d0:
            row["focus_id"] = focus_id
        self.feedback.append(row)
        self.stop_reason = "local_cycle_limit"


class LocalV3Runner(LocalMixin, V3Runner):
    pass


class LocalD0Runner(LocalMixin, D0Runner):
    is_d0 = True


def engine(folder, checkpoint, system, config, legacy, counter, transport=None):
    packets = FrozenPackets(checkpoint)
    snapshot = read(Path(checkpoint) / "snapshot.json")
    adapter = ChoiceAdapter(packets.task)
    n = len(packets.agents)
    settings = defaults(n, legacy)
    settings["limits"].update(max_network_attempts_total=n + 4,
                              max_output_tokens_total=1024 + (n - 1) * 2048 + 4096 + 2 * 3072)
    d0 = system == "d0_continuation"
    if system not in {"v3_continuation", "d0_continuation"}:
        raise ValueError("Unknown continuation method")
    gateway = Gateway(config, settings, Contracts(adapter) if d0 else V3Contracts(adapter),
                      CompactChoicePrompts(Prompts() if d0 else V3Prompts()), Journal(Path(folder)),
                      transport=transport, token_counter=counter)
    runner = (LocalD0Runner if d0 else LocalV3Runner)(packets, gateway, gateway.journal, adapter,
                         task_ordinal=packets.agents.index(snapshot["editor"]))
    runner.board._works = {w["id"]: copy.deepcopy(w) for w in snapshot["visible_works"]}
    runner.board.initials = {w["author"]: w["id"] for w in snapshot["visible_works"] if w["initial"]}
    runner.board.current = snapshot["before"]["id"]
    if not runner.board.get(runner.board.current)["deliverable_shape"]:
        raise ValueError("Local checkpoints require a complete before work")
    runner.board.fallback = runner.board.current
    runner.published = copy.deepcopy(snapshot["public_offers"])
    runner.offers = copy.deepcopy(snapshot["public_offers"])
    runner.feedback = copy.deepcopy(snapshot["previous_feedback"])
    runner.counts = copy.deepcopy(snapshot["attempt_counts"])
    runner.pointer = snapshot["pointer"]
    first = read(Path(checkpoint) / f"{system}.first.request.json")
    first_packet = json.loads(first["instructions"].split("\nPACKET=", 1)[1].rsplit("\nOUTPUT_SCHEMA=", 1)[0])
    runner.cycle = first_packet["BUDGET"]["cycle"]
    return runner, snapshot, first


def run_unit(folder, checkpoint, system, config, legacy, counter, transport=None):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    runner, snapshot, first = engine(folder, checkpoint, system, config, legacy, counter, transport)
    error, first_choice = None, None
    try:
        first_choice = runner.choose_local(snapshot["before"]["id"], snapshot["after"]["id"],
                                            snapshot["checks"], original=first)
        row = {"kind": "application_feedback", "offer": snapshot["target_offer"],
               "before": snapshot["before"]["id"], "after": snapshot["after"]["id"],
               "use_record": snapshot["use_record"], "checks": snapshot["checks"], "decision": first_choice}
        runner.feedback.append(row)
        runner.one_cycle()
    except ProtocolError as exc:
        error = {"code": exc.code, "detail": exc.detail}
        runner.stop_reason = exc.code
        runner.event("interrupted", error=error)
    if runner.is_d0:
        for focus in runner.focus_history:
            if focus["status"] == "pending":
                focus["status"] = "deferred"
                runner.event("focus_deferred", focus_id=focus["id"], reason=runner.stop_reason)
    current = runner.board.get(runner.board.current)
    selected = runner.board.current if not error and current["deliverable_shape"] else runner.board.fallback
    work = runner.board.get(selected)
    usage = runner.journal.usage
    result = {"kind": "one_cycle_local_repair", "system": system, "protocol": "coreta/local-repair-v1",
              "status": "interrupted" if error else "completed" if work else "delivery_failure",
              "scope": "not_end_to_end", "truth_status": "not_certified", "error": error,
              "stop_reason": runner.stop_reason, "first_choice": first_choice,
              "selected_work_id": selected, "selected_work": work,
              "delivery_used_fallback": selected != runner.board.current,
              "actual_http_attempts": runner.gateway.client.attempts if transport is None else 0,
              "transport_attempts": runner.gateway.client.attempts,
              "usage": usage, "execution_mode": "live_natural" if transport is None else "scripted_engineering_only",
              "fixture_usage_not_billable": transport is not None,
              "incomplete_or_unknown_usage_attempts": runner.gateway.client.attempts - sum(
                  all(type(u.get(k)) is int and u[k] >= 0 for k in ("input_tokens", "output_tokens")) for u in usage),
              "focus_history": copy.deepcopy(runner.focus_history) if runner.is_d0 else []}
    runner.save_state()
    write_json(folder / "result.json", result)
    return result


def prepare_run(inputs, output, ids):
    inputs, output = Path(inputs), Path(output)
    source = read(inputs / "manifest.json")
    if hashes(source["source_hashes"]) != source["source_hashes"] or hashes(source["prepared_hashes"]) != source["prepared_hashes"]:
        raise ValueError("Frozen input preparation changed")
    chosen = [row for row in source["snapshots"] if row["id"] in ids]
    if len(set(ids)) != len(ids) or {r["id"] for r in chosen} != set(ids):
        raise ValueError("Unknown or duplicate requested checkpoint")
    output.mkdir(parents=True, exist_ok=False)
    for row in chosen:
        dest = output / row["id"]
        dest.mkdir()
        for p in (inputs / row["id"]).glob("*.json"):
            (dest / p.name).write_bytes(p.read_bytes())
    manifest = {"kind": "d0_local_repair_natural_probe", "scope": "selected_development_cases_not_main_result",
                "snapshots": chosen, "source_hashes": hashes(implementation_sources() + [Path(__file__),
                    PROJECT / "tools/workboard_d0_continuation.py"]),
                "prepared_hashes": hashes(output.glob("*/*.json")),
                "max_http_attempts": sum(2 * row["per_method_calls"] for row in chosen),
                "max_output_tokens": sum(2 * row["per_method_output_cap"] for row in chosen),
                "transport_retries": 0, "format_repairs": 0, "sampling_seed_sent": False,
                "gold_read": False, "input_preparation": str(inputs.resolve())}
    write_json(output / "manifest.json", manifest)
    return manifest


def run_batch(prepared, output, transport_factory=None):
    prepared, output = Path(prepared), Path(output)
    manifest = read(prepared / "manifest.json")
    for field in ("source_hashes", "prepared_hashes"):
        if hashes(manifest[field]) != manifest[field]:
            raise ValueError("Stale execution snapshot: " + field)
    if transport_factory is None and not os.environ.get("DEEPSEEK_API_KEY"):
        raise ValueError("Approved API key unavailable")
    config, legacy = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "manifest.json", manifest)
    progress = {"kind": manifest["kind"], "status": "running", "actual_http_attempts": 0,
                "max_http_attempts": manifest["max_http_attempts"], "units": [
                    {"checkpoint": row["id"], "system": system, "status": "not_started"}
                    for row in manifest["snapshots"] for system in row["methods"]]}
    write_json(output / "progress.json", progress)
    for row in progress["units"]:
        row["status"] = "running"
        write_json(output / "progress.json", progress)
        transport = transport_factory(row) if transport_factory else None
        result = run_unit(output / row["checkpoint"] / row["system"], prepared / row["checkpoint"],
                          row["system"], config, legacy, load_counter(), transport)
        row.update(status=result["status"], actual_http_attempts=result["actual_http_attempts"],
                   selected_work_id=result["selected_work_id"], error=result["error"])
        progress["actual_http_attempts"] += result["actual_http_attempts"]
        if result["status"] != "completed":
            progress["status"] = "stopped_on_first_error"
            break
        write_json(output / "progress.json", progress)
    else:
        progress["status"] = "completed"
    write_json(output / "progress.json", progress)
    return progress
