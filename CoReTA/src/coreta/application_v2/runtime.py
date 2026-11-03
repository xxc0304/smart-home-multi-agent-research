"""Application-targeted handoffs using the existing bounded scheduling framework."""
from __future__ import annotations

import copy

from ..schemas import ProtocolError
from ..handoff.gateway import write_json
from .ranking import render_ranking
from .ranking_runtime import RankingRunner
from .state import Applications


class ApplicationRunner(RankingRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application_state = Applications()
        self.model_unresolved = []
        self.request_application = None
        self.application_focus = None
        self.system = "coreta"

    @property
    def protocol(self):
        return "coreta/application-v2" if self.system == "coreta" else "coreta/ranking-baseline-v2"

    def save_state(self):
        write_json(self.journal.root / "state.json", {
            "protocol": self.protocol, "system": self.system, "driver": self.driver,
            "contributions": self.contributions, "contribution_notes": self.notes,
            "works": self.works, "reviews": self.reviews, "requests": self.requests,
            "unresolved": self.unresolved, "model_unresolved": self.model_unresolved,
            "pending": self.pending, "application_state": self.application_state.record(),
            "application_focus": self.application_focus,
            "independent": self.independent, "independent_details": self.independent_details,
            "discussion": self.discussion, "independent_selected_member": self.selected_member,
        })

    def packet(self, agent, stage, allowed=()):
        packet = super().packet(agent, stage, allowed)
        if stage not in {"CONTRIBUTE", "INDEPENDENT"}:
            packet["APPLICATION_STATE"] = self.application_state.record()
            packet["APPLICATION_FOCUS"] = copy.deepcopy(self.application_focus)
            packet["REFERENCE_INDEX"] += [{"ref": ref, "kind": "public_application"}
                                          for ref in self.application_state.units]
        return packet

    def sync_unresolved(self):
        self.unresolved = list(self.model_unresolved)
        for row in self.application_state.blocked():
            message = f"Application {row['ref']} remains {row['status']}: " + str(row["missing"] or row["reason"] or "upstream application unresolved")
            if message not in self.unresolved:
                self.unresolved.append(message)

    def apply(self):
        allowed = self.allowed()
        draft, delta = None, None
        def check(value):
            nonlocal draft, delta
            if self.application_focus:
                addressed = {a["target"] for a in value["applications"]}
                addressed.update(a["ref"] for a in value["retire_applications"])
                addressed.update(a["ref"] for a in value["excluded"])
                if self.application_focus["ref"] not in addressed:
                    raise ProtocolError("INVALID_ACTION", "Address APPLICATION_FOCUS before unrelated updates")
            candidate = copy.deepcopy(self.application_state)
            change = candidate.update(value, self.pending)
            # The candidate is committed only after every structural action check succeeds.
            draft, delta = candidate, change
        value = self.gateway.call("APPLY", self.driver, self.packet(self.driver, "APPLY", allowed), allowed, check)
        old = self.work
        old_refs = list(self.application_state.candidate_refs)
        self.application_state = draft
        self.model_unresolved = list(value["unresolved"])
        self.sync_unresolved()
        state_changed = bool(delta["new_ref"] or delta["retired"] or old_refs != draft.candidate_refs)
        if value["artifact"] is not None or (old is not None and state_changed):
            artifact = render_ranking(value["artifact"]) if value["artifact"] is not None else old["artifact"]
            history = copy.deepcopy(old["application_history"]) if old else []
            history.append({"new_application": delta["new_ref"], "replaced_application": delta["target"],
                            "retired": delta["retired"]})
            self.work = {
                "ref": f"W{len(self.works)+1}", "artifact": artifact,
                "ranking": list(value["artifact"]) if value["artifact"] is not None else list(old["ranking"]),
                "changed_text": old is None or old["artifact"] != artifact,
                "applications": copy.deepcopy(value["applications"]),
                "artifact_uses": list(draft.candidate_refs), "application_history": history,
                "excluded": copy.deepcopy(value["excluded"]), "unresolved": list(self.unresolved),
                "application_evidence_status": "model_declared_not_independently_confirmed",
                "retained_text": value["artifact"] is None,
            }
            self.works.append(copy.deepcopy(self.work))
        elif self.work:
            self.work["unresolved"] = list(self.unresolved)
        self.request_application = delta["request_target"]
        self.pending = None
        self.event("apply", member=self.driver, output=value, application_change=delta,
                   work_ref=self.work["ref"] if self.work else None)
        return value["request"]

    def intervene(self, request):
        signature = (self.request_application, tuple(sorted(request["target_refs"])), " ".join(request["question"].split()))
        if signature in self.seen_requests or not self.allowed():
            self.unresolved.append("Unserved/repeated application request: " + request["question"])
            self.event("request_skipped", request=request, application_ref=self.request_application)
            return False
        self.seen_requests.add(signature)
        recipient, reason = self.route(request)
        record = {"ref": f"Q{len(self.requests)+1}", "author": self.driver, **copy.deepcopy(request),
                  "recipient": recipient, "routing_reason": reason, "application_ref": self.request_application}
        self.requests.append(record)
        self.interventions += 1
        self.reply_counts[recipient] += 1
        self.event("request", request=record)
        refs, note = self.contribute(recipient, "REPLY")
        record["reply_refs"], record["reply_note"] = refs, note
        self.pending = {"kind": "reply", "request": copy.deepcopy(record),
                        "required_handling_refs": refs or [record["ref"]]}
        # Receiving a reply intentionally does not change U.missing or its status.
        self.event("reply_received", request_ref=record["ref"], application_ref=record["application_ref"],
                   reply_refs=refs, note=note)
        return True

    def source_refs(self):
        contributions = {c["ref"]: c for c in self.contributions}
        visited, sources = set(), set()
        def visit(ref):
            if ref in visited:
                return
            visited.add(ref)
            if ref in self.packets.owners:
                sources.add(ref)
            elif ref in contributions:
                for parent in contributions[ref]["support_refs"]:
                    visit(parent)
            elif ref in self.application_state.units:
                for binding in self.application_state.units[ref]["bindings"]:
                    visit(binding["ref"])
        for ref in self.application_state.candidate_refs:
            visit(ref)
        return sources

    def local_protocol(self):
        for agent in self.agents:
            self.contribute(agent)
        request = self.apply()
        while True:
            if request is not None and self.intervene(request):
                request = self.apply()
                continue
            if self.work is None:
                return "artifact_missing"
            stale = [row for row in self.application_state.blocked() if row["status"] == "stale"]
            if stale:
                if self.gateway.remaining < 2:
                    return "application_update_budget"
                before = {row["ref"] for row in stale}
                focus = min(stale, key=lambda row: int(row["ref"][1:]))
                self.application_focus = {"ref": focus["ref"], "reason": "declared_dependency_changed"}
                self.event("application_update_required", focus=self.application_focus)
                try:
                    request = self.apply()
                finally:
                    self.application_focus = None
                    self.save_state()
                after = {row["ref"] for row in self.application_state.blocked() if row["status"] == "stale"}
                if before == after and request is None:
                    return "application_update_unresolved"
                continue
            if len(self.reviews) >= self.gateway.limits["max_final_reviews"]:
                return "review_limit"
            review = self.review()
            if review["verdict"] == "no_defect_found":
                return "review_finished"
            if review["verdict"] == "undetermined" and (
                    not review["check_suggestion"] or not self.allowed()):
                self.unresolved.append(review["finding"])
                return "review_undetermined"
            self.gateway.require()
            request = self.apply()

    def run(self, system="coreta"):
        if system not in {"coreta", "ordinary_discussion", "independent"}:
            raise ValueError("Unsupported system")
        if self.selected_member is not None and (system != "independent" or self.selected_member not in self.agents):
            raise ValueError("Selected member is supported only for independent calibration")
        self.system = system
        result = super().run(system)
        result["protocol"] = self.protocol
        if system == "independent":
            result["independent_requested_members"] = [self.selected_member] if self.selected_member else list(self.agents)
        result["application_state"] = self.application_state.record()
        result["application_blockers"] = self.application_state.blocked()
        result["model_unresolved"] = list(self.model_unresolved)
        if result["application_blockers"] and result["status"] == "reviewed_no_defect":
            result["status"] = "best_effort_unresolved"
        write_json(self.journal.root / "result.json", result)
        return result
