"""Bounded, work-visible collaboration. Protocol completion never certifies truth."""
from __future__ import annotations

import copy
import json

from . import PROTOCOL
from .artifacts import Board
from .provenance import describe_sources
from ..handoff.gateway import write_json
from ..schemas import ProtocolError


class Runner:
    def __init__(self, packets, gateway, journal, adapter, *, task_ordinal=1, initial_cache=None):
        self.packets, self.gateway, self.journal = packets, gateway, journal
        self.agents = list(packets.agents)
        if len(self.agents) < 3:
            raise ProtocolError("INPUT_ERROR", "Main workboard prototype requires at least three members")
        self.editor = self.agents[task_ordinal % len(self.agents)]
        self.board = Board(adapter)
        self.offers, self.published, self.feedback, self.checks, self.attempted = [], [], [], [], []
        self.tool_observations = []
        self.counts = {a: 0 for a in self.agents}
        self.pointer = (self.agents.index(self.editor) + 1) % len(self.agents)
        self.cycle = 0
        self.closure_complete = False
        self.stop_reason = "not_started"
        self.initial_cache = copy.deepcopy(initial_cache)

    def event(self, kind, **value):
        self.journal.log("events.jsonl", {"kind": kind, "cycle": self.cycle, **copy.deepcopy(value)})
        self.save_state()

    def save_state(self):
        write_json(self.journal.root / "state.json", {
            "protocol": PROTOCOL, "editor": self.editor, "current": self.board.current,
            "fallback": self.board.fallback, "works": self.board.snapshot(),
            "initials": self.board.initials, "offers": self.offers, "public_offer_ids":
            [o["ref"] for o in self.published], "feedback": self.feedback, "checks": self.checks,
            "attempted_offers": self.attempted, "attempt_counts": self.counts,
            "pointer": self.pointer, "cycle": self.cycle, "tool_observations": self.tool_observations,
            "closure_complete": self.closure_complete, "stop_reason": self.stop_reason})

    def record_observation(self, artifact_id, invocation, input_value, raw_output, exit_status):
        """Trusted host integration only; never invoked from a model text declaration."""
        if artifact_id not in self.board.ids():
            raise ProtocolError("REFERENCE_ERROR", "Tool observation refers to an unknown artifact")
        self.tool_observations.append(copy.deepcopy({"artifact_id": artifact_id, "invocation": invocation,
            "input": input_value, "raw_output": raw_output, "exit_status": exit_status}))
        self.event("tool_observation", observation=self.tool_observations[-1])

    def packet(self, member, stage, **extra):
        p = self.packets.member(member)
        p["STAGE"] = stage
        p["BUDGET"] = {"remaining_network_attempts": self.gateway.remaining,
                       "reserved_closure_calls": 4, "cycle": self.cycle}
        visible = {}
        if stage != "INITIAL":
            p["CURRENT_WORK"] = self.board.get(self.board.current)
            if p["CURRENT_WORK"]:
                visible[p["CURRENT_WORK"]["id"]] = p["CURRENT_WORK"]
            # Published offers are evidence claims, never full access to their source originals.
            p["PUBLIC_EVIDENCE"] = copy.deepcopy(self.published)
            p["REFERENCE_INDEX"] += [{"ref": o["ref"], "kind": "public_offer_unverified_excerpts"}
                                      for o in self.published]
        if stage in {"OBSERVE", "TRY", "FINALIZE", "CHECK_USE", "CHECK_EFFECT",
                     "FINAL_CHECK_USE", "FINAL_CHECK_EFFECT"}:
            p["CANDIDATES"] = self.board.snapshot()
            visible.update({w["id"]: w for w in p["CANDIDATES"]})
        if stage in {"OBSERVE", "FINALIZE"}:
            p["FEEDBACK"] = copy.deepcopy(self.feedback)
        if stage == "OBSERVE":
            p["TARGETS"] = sorted(self.board.targets())
        p.update(copy.deepcopy(extra))
        for key in ("BEFORE", "AFTER", "FALLBACK", "FINAL_PROPOSAL"):
            if p.get(key):
                visible[p[key]["id"]] = p[key]
        p["REFERENCE_INDEX"] += [{"ref": ref, "kind": "visible_work"} for ref in visible]
        p["TOOL_OBSERVATIONS"] = copy.deepcopy([o for o in self.tool_observations
                                                if o["artifact_id"] in visible])
        return describe_sources(p)

    def next_peer(self, excluded, *, after=None):
        start = self.agents.index(after or self.editor)
        return next(self.agents[(start + step) % len(self.agents)]
                    for step in range(1, len(self.agents) + 1)
                    if self.agents[(start + step) % len(self.agents)] not in excluded)

    def choose_offer(self, batch):
        offer = min(batch, key=lambda o: (self.counts[o["author"]],
                    (self.agents.index(o["author"]) - self.pointer) % len(self.agents)))
        self.counts[offer["author"]] += 1
        self.pointer = (self.agents.index(offer["author"]) + 1) % len(self.agents)
        self.attempted.append(offer["ref"])
        return offer

    def materialize(self, value, *, base):
        if value["action"] == "reuse":
            return value["candidate_id"]
        return self.board.add(value["work"], self.editor, base=base, sources=value["declared_sources"])

    def before_application(self, offer):
        """Optional variant hook; baseline packets and call order stay unchanged."""
        return {}

    def run_checks(self, provider, before, after, *, offer=None, use_record=None,
                   declared_sources=(), final=False):
        other = self.next_peer({self.editor, provider}, after=provider)
        common = {"BEFORE": self.board.get(before), "AFTER": self.board.get(after),
                  "TARGET_OFFER": copy.deepcopy(offer), "DIFF": self.board.diff(before, after),
                  "APPLICATION_SOURCE_REFS": list(declared_sources)}
        use_stage, effect_stage = (("FINAL_CHECK_USE", "FINAL_CHECK_EFFECT") if final
                                   else ("CHECK_USE", "CHECK_EFFECT"))
        if final:
            common.update(FINAL_PROPOSAL=self.board.get(after), FALLBACK=self.board.get(self.board.fallback))
        use_packet = self.packet(provider, use_stage, **common, USE_RECORD=use_record)
        effect_packet = self.packet(other, effect_stage, **common)
        # Both packets precede both calls: no newly emitted peer verdict can enter the other input.
        rows = []
        for member, stage, packet in ((provider, use_stage, use_packet), (other, effect_stage, effect_packet)):
            value = self.gateway.call(stage, member, packet)
            row = {"stage": stage, "member": member, "before": before, "after": after, **value}
            rows.append(row)
            self.checks.append(copy.deepcopy(row))
            self.event("check_observation", check=row)
        return rows

    def initialize(self):
        if self.initial_cache is not None:
            if (self.initial_cache.get("member_packet_hashes") != self.packets.hashes
                    or set(self.initial_cache.get("candidates", {})) != set(self.agents)):
                raise ProtocolError("INPUT_ERROR", "Shared initial cache does not match this member packet set")
            for member in self.agents:
                packet = self.packet(member, "INITIAL")
                value = self.gateway.contracts.decode(json.dumps(self.initial_cache["candidates"][member]),
                                                      self.gateway.contracts.schema("INITIAL", packet))
                ref = self.board.add(value, member, initial=True)
                self.board.initialize(self.editor, self.agents)
                self.event("initial_cached", member=member, work=ref,
                           origin=self.initial_cache.get("origin"))
            return
        for member in self.agents:
            try:
                value = self.gateway.call("INITIAL", member, self.packet(member, "INITIAL"))
            except ProtocolError as exc:
                self.event("initial_failed", member=member, code=exc.code, detail=exc.detail)
                if exc.code not in {"SCHEMA_ERROR", "REFERENCE_ERROR", "INVALID_ACTION"}:
                    raise
                continue
            ref = self.board.add(value, member, initial=True)
            self.board.initialize(self.editor, self.agents)
            self.event("initial_candidate", member=member, work=ref)
        if self.board.current is None:
            raise ProtocolError("NO_CANDIDATE", "Every initial call failed to create a work")

    def collaborate(self):
        self.stop_reason = "cycle_limit"
        for cycle in range(1, len(self.agents)):
            # Reserve the entire possible cycle and four closing calls before starting it.
            if self.gateway.remaining < len(self.agents) + 3 + 4:
                self.stop_reason = "cycle_budget_reserved_for_closure"
                break
            self.cycle = cycle
            base = self.board.current
            batch = []
            for member in self.agents:
                if member == self.editor:
                    continue
                value = self.gateway.call("OBSERVE", member, self.packet(member, "OBSERVE"))
                for previous in self.feedback:
                    if previous["kind"] == "unable_to_apply" and previous["offer"]["author"] == member:
                        previous["reason_delivered_to_provider"] = True
                if value["action"] == "pass":
                    self.event("pass", member=member, base_version=base)
                    continue
                offer = {"ref": f"O{len(self.offers) + 1}", "author": member,
                         "base_version": base, **value["offer"]}
                self.offers.append(copy.deepcopy(offer))
                batch.append(offer)
                self.event("offer_proposed", offer=offer)
            self.published.extend(copy.deepcopy(batch))
            if not batch:
                self.stop_reason = "all_pass"
                break
            selected = self.choose_offer(batch)
            for o in batch:
                self.event("offer_selected" if o["ref"] == selected["ref"] else "offer_untried",
                           offer_ref=o["ref"], base_version=base)
            application_context = self.before_application(selected)
            value = self.gateway.call("TRY", self.editor, self.packet(self.editor, "TRY", TARGET_OFFER=selected,
                                                                        **application_context))
            if value["action"] == "unable":
                row = {"kind": "unable_to_apply", "offer": selected, "reason": value["reason"],
                       "base_version": base, "reason_delivered_to_provider": False}
                self.feedback.append(row)
                self.event("offer_not_applied", feedback=row)
                continue
            trial = self.materialize(value, base=base)
            self.event("trial_created", offer_ref=selected["ref"], before=base, after=trial,
                       use_record=value["use_record"], declared_sources=value["declared_sources"])
            checks = self.run_checks(selected["author"], base, trial, offer=selected,
                                     use_record=value["use_record"], declared_sources=value["declared_sources"])
            choice = self.gateway.call("CHOOSE", self.editor, self.packet(self.editor, "CHOOSE",
                BEFORE=self.board.get(base), AFTER=self.board.get(trial), CHECKS=checks,
                CHOICES=list(dict.fromkeys([base, trial]))))
            self.board.promote(choice["candidate_id"])
            self.feedback.append({"kind": "application_feedback", "offer": selected,
                "before": base, "after": trial, "use_record": value["use_record"],
                "checks": checks, "decision": choice})
            event_kind = ("selection_unchanged" if base == trial else
                          "offer_adopted" if choice["candidate_id"] == trial else "offer_not_adopted")
            self.event(event_kind,
                       offer_ref=selected["ref"], decision=choice)

    def closing_checker(self, ref, declared_sources):
        work = self.board.get(ref)
        if work["initial"] and work["author"] != self.editor:
            return work["author"]
        sources = set(declared_sources)
        for offer in reversed(self.published):
            if offer["ref"] in sources and offer["author"] != self.editor:
                return offer["author"]
        for candidate in reversed(self.board.snapshot()):
            if candidate["id"] in sources and candidate["author"] != self.editor:
                return candidate["author"]
        return self.next_peer({self.editor})

    def finalize(self):
        self.gateway.require(4)
        base = self.board.current
        value = self.gateway.call("FINALIZE", self.editor, self.packet(self.editor, "FINALIZE",
                                                                      FALLBACK=self.board.get(self.board.fallback)))
        proposal = self.materialize(value, base=base)
        self.event("final_proposal", work=proposal, use_record=value["use_record"],
                   declared_sources=value["declared_sources"])
        provider = self.closing_checker(proposal, value["declared_sources"])
        checks = self.run_checks(provider, base, proposal, use_record=value["use_record"],
                                 declared_sources=value["declared_sources"], final=True)
        choices = [ref for ref in dict.fromkeys([proposal, self.board.fallback])
                   if ref and self.board.get(ref)["deliverable_shape"]]
        if not choices:
            raise ProtocolError("NO_DELIVERABLE", "No final proposal or fallback has a deliverable shape")
        choice = self.gateway.call("FINAL_CHOOSE", self.editor, self.packet(self.editor, "FINAL_CHOOSE",
            FINAL_PROPOSAL=self.board.get(proposal), FALLBACK=self.board.get(self.board.fallback),
            CHECKS=checks, CHOICES=choices))
        self.board.promote(choice["candidate_id"])
        self.closure_complete = True
        self.event("final_selection", decision=choice)

    def run(self):
        error = None
        try:
            self.initialize()
            self.collaborate()
            self.finalize()
        except ProtocolError as exc:
            error = {"code": exc.code, "detail": exc.detail}
            self.stop_reason = exc.code
            self.event("interrupted", error=error)
        selected = self.board.current if self.closure_complete else self.board.fallback
        work = self.board.get(selected)
        result = {"protocol": PROTOCOL, "system": "coreta_workboard", "task_id": self.packets.task["task_id"],
                  "status": "completed" if self.closure_complete else ("interrupted" if work else "delivery_failure"),
                  "stop_reason": self.stop_reason, "error": error, "editor": self.editor,
                  "selected_work_id": selected, "selected_work": work,
                  "artifact": self.board.adapter.render(work["artifact"]) if work else None,
                  "closure_complete": self.closure_complete, "truth_status": "not_certified",
                  "logical_calls": self.journal.calls, "http_attempts": self.gateway.client.attempts,
                  "format_repairs": self.journal.repairs, "usage": self.journal.usage,
                  "uncertain_usage_attempts": self.journal.uncertain_attempts,
                  "incomplete_or_unknown_usage_attempts": self.gateway.client.attempts - sum(
                      type(u.get("input_tokens")) is int and u["input_tokens"] >= 0
                      and type(u.get("output_tokens")) is int and u["output_tokens"] >= 0
                      for u in self.journal.usage)}
        self.save_state()
        write_json(self.journal.root / "result.json", result)
        return result
