"""Append-only contribution/work state and bounded, task-directed scheduling."""
from __future__ import annotations

import copy
import time

from ..schemas import ProtocolError
from .gateway import write_json
from .ranking import render_ranking


class Runner:
    def __init__(self, packets, gateway, journal, *, task_ordinal=1):
        self.packets, self.gateway, self.journal = packets, gateway, journal
        self.agents = packets.agents
        self.driver = self.agents[task_ordinal % len(self.agents)]
        self.contributions, self.notes, self.works = [], [], []
        self.reviews, self.requests, self.events, self.discussion = [], [], [], []
        self.independent = {}
        self.independent_details = {}
        self.work = None
        self.unresolved = []
        self.pending = None
        self.reply_counts = {agent: 0 for agent in self.agents}
        self.seen_requests = set()
        self.interventions = 0
        self.started = time.monotonic()

    def event(self, kind, **fields):
        event = {"event_number": len(self.events) + 1, "kind": kind, **copy.deepcopy(fields)}
        self.events.append(event)
        self.journal.log("events.jsonl", event)
        self.save_state()

    def save_state(self):
        write_json(self.journal.root / "state.json", {
            "driver": self.driver, "contributions": self.contributions, "contribution_notes": self.notes,
            "works": self.works, "reviews": self.reviews, "requests": self.requests,
            "unresolved": self.unresolved, "pending": self.pending,
            "independent": self.independent, "independent_details": self.independent_details,
            "discussion": self.discussion,
        })

    def packet(self, agent, stage, allowed=()):
        packet = self.packets.member(agent)
        if stage == "CONTRIBUTE" or stage == "INDEPENDENT":
            return packet
        if stage in {"DISCUSS", "FINAL"}:
            packet["PUBLIC_DISCUSSION"] = copy.deepcopy(self.discussion)
            return packet
        packet["CONTRIBUTIONS"] = copy.deepcopy(self.contributions)
        packet["CONTRIBUTION_NOTES"] = copy.deepcopy(self.notes)
        packet["CURRENT_WORK"] = copy.deepcopy(self.work)
        if packet["CURRENT_WORK"] and "ranking" in packet["CURRENT_WORK"]:
            # The same order need not appear twice as both array and formatted text.
            packet["CURRENT_WORK"].pop("artifact", None)
            # The history already contains the current applications in full.
            if packet["CURRENT_WORK"].get("application_history"):
                packet["CURRENT_WORK"].pop("applications", None)
        packet["UNRESOLVED"] = list(self.unresolved)
        packet["NEW_MESSAGE"] = copy.deepcopy(self.pending)
        packet["LATEST_REVIEW"] = copy.deepcopy(self.reviews[-1]) if self.reviews else None
        packet["LIMITS"] = {
            "network_attempts_remaining": self.gateway.remaining,
            "interventions_remaining": self.gateway.limits["max_interventions"] - self.interventions,
            "final_reviews_remaining": self.gateway.limits["max_final_reviews"] - len(self.reviews),
        }
        packet["ALLOWED_REQUEST_KINDS"] = list(allowed)
        public_refs = [{"ref": c["ref"], "kind": "public_contribution"} for c in self.contributions]
        if self.work:
            public_refs.append({"ref": self.work["ref"], "kind": "current_work"})
        if self.requests:
            public_refs.append({"ref": self.requests[-1]["ref"], "kind": "request_and_reply"})
        if self.reviews:
            public_refs.append({"ref": self.reviews[-1]["ref"], "kind": "review"})
        packet["REFERENCE_INDEX"] += public_refs
        if stage == "REPLY":
            packet["REQUEST"] = copy.deepcopy(self.requests[-1])
            packet["RELEVANT_MESSAGES"] = copy.deepcopy(self.contributions)
        return packet

    def contribute(self, agent, stage="CONTRIBUTE"):
        value = self.gateway.call(stage, agent, self.packet(agent, stage), check=self.check_contribution)
        refs = []
        for item in value["items"]:
            ref = f"C{len(self.contributions) + 1}"
            self.contributions.append({"ref": ref, "author": agent, "stage": stage, **copy.deepcopy(item)})
            refs.append(ref)
        self.notes.append({"author": agent, "stage": stage, "note": value["note"]})
        self.event("contribution", member=agent, stage=stage, refs=refs, note=value["note"])
        return refs, value["note"]

    @staticmethod
    def check_contribution(value):
        if not value["items"] and not value["note"].strip():
            raise ProtocolError("SCHEMA_ERROR", "items=[] requires a specific inability note")

    def allowed(self):
        # A request spends a REPLY call, followed by APPLY and preferably REVIEW.
        if (self.interventions < self.gateway.limits["max_interventions"]
                and self.gateway.remaining >= 3):
            return ["ask", "check", "probe"]
        return []

    def apply(self):
        allowed = self.allowed()
        packet = self.packet(self.driver, "APPLY", allowed)
        expected = set(self.pending.get("required_handling_refs", [])) if self.pending else set()

        def check(value):
            handled = {ref for app in value["applications"] for ref in app["refs"]}
            handled.update(row["ref"] for row in value["excluded"])
            if not expected.issubset(handled):
                raise ProtocolError("REFERENCE_ERROR", f"Address new reply/review refs in applications or excluded: {sorted(expected - handled)}")
            if value["request"] and value["request"]["kind"] not in allowed:
                raise ProtocolError("INVALID_ACTION", "No intervention budget for this request")
        value = self.gateway.call("APPLY", self.driver, packet, allowed, check)
        old = self.work
        self.unresolved = list(value["unresolved"])
        if value["artifact"] is not None:
            history = copy.deepcopy(old["application_history"]) if old else []
            history += copy.deepcopy(value["applications"])
            self.work = {
                "ref": f"W{len(self.works) + 1}", "artifact": render_ranking(value["artifact"]),
                "ranking": list(value["artifact"]),
                "changed_text": old is None or old["artifact"] != render_ranking(value["artifact"]),
                "applications": copy.deepcopy(value["applications"]),
                "excluded": copy.deepcopy(value["excluded"]),
                "application_history": history, "unresolved": list(self.unresolved),
                "application_evidence_status": "model_declared_not_independently_confirmed",
            }
            self.works.append(copy.deepcopy(self.work))
        elif self.work:
            # Keep the last complete candidate; retain this turn's application records as metadata.
            self.work["application_history"] += copy.deepcopy(value["applications"])
            self.work["unresolved"] = list(self.unresolved)
        self.pending = None
        self.event("apply", member=self.driver, output=value,
                   work_ref=self.work["ref"] if self.work else None)
        return value["request"]

    def route(self, request):
        if request["recipient"] is not None:
            return request["recipient"], "model_selected_valid_member"
        authors = {c["author"] for c in self.contributions if c["ref"] in request["target_refs"]}
        if request["kind"] == "ask" and len(authors) == 1:
            return next(iter(authors)), "single_target_contribution_author"
        peers = [a for a in self.agents if a != self.driver]
        return min(peers, key=lambda a: (self.reply_counts[a], self.agents.index(a))), "bounded_fallback_not_expert_oracle"

    def intervene(self, request):
        signature = (tuple(sorted(request["target_refs"])), " ".join(request["question"].split()))
        if signature in self.seen_requests:
            self.unresolved.append("Repeated request stopped without new evidence: " + request["question"])
            self.event("request_skipped", reason="exact_duplicate", request=request)
            return False
        if not self.allowed():
            self.unresolved.append("Unserved request: " + request["question"])
            self.event("request_skipped", reason="intervention_or_attempt_budget", request=request)
            return False
        self.seen_requests.add(signature)
        recipient, route_reason = self.route(request)
        record = {"ref": f"Q{len(self.requests) + 1}", "author": self.driver,
                  **copy.deepcopy(request), "recipient": recipient, "routing_reason": route_reason}
        self.requests.append(record)
        self.interventions += 1
        self.reply_counts[recipient] += 1
        self.event("request", request=record)
        refs, note = self.contribute(recipient, "REPLY")
        record["reply_refs"], record["reply_note"] = refs, note
        self.pending = {"kind": "reply", "request": copy.deepcopy(record),
                        "required_handling_refs": refs or [record["ref"]]}
        self.event("reply_received", request_ref=record["ref"], reply_refs=refs, note=note)
        return True

    def source_refs(self):
        by_ref = {c["ref"]: c for c in self.contributions}
        works_by_ref = {w["ref"]: w for w in self.works}
        found, visited = set(), set()

        def visit(ref):
            if ref in visited:
                return
            visited.add(ref)
            if ref in self.packets.owners:
                found.add(ref)
            elif ref in by_ref:
                for parent in by_ref[ref]["support_refs"]:
                    visit(parent)
            elif ref in works_by_ref:
                for app in works_by_ref[ref]["application_history"]:
                    for parent in app["refs"]:
                        visit(parent)
        if self.work:
            for app in self.work["application_history"]:
                for ref in app["refs"]:
                    visit(ref)
        return found

    def review(self):
        sources = self.source_refs()
        peers = [a for a in self.agents if a != self.driver]
        coverage = {a: len({ref for ref in sources if a in self.packets.owners.get(ref, set())}) for a in peers}
        reviewer = min(peers, key=lambda a: (-coverage[a], self.reply_counts[a], self.agents.index(a)))
        value = self.gateway.call("REVIEW", reviewer, self.packet(reviewer, "REVIEW"))
        record = {"ref": f"V{len(self.reviews) + 1}", "author": reviewer,
                  "work_ref": self.work["ref"], "source_permission_coverage": coverage[reviewer],
                  "declared_sources_count": len(sources), "epistemic_independence_guaranteed": False,
                  **copy.deepcopy(value)}
        self.reviews.append(record)
        self.pending = {"kind": "review", "review": copy.deepcopy(record),
                        "required_handling_refs": [record["ref"]]}
        self.event("review", review=record)
        return record

    def local_protocol(self):
        for agent in self.agents:
            self.contribute(agent)
        request = self.apply()
        while True:
            if request is not None:
                if self.intervene(request):
                    request = self.apply()
                    continue
            if self.work is None:
                return "artifact_missing"
            if len(self.reviews) >= self.gateway.limits["max_final_reviews"]:
                return "review_limit"
            review = self.review()
            if review["verdict"] == "no_defect_found":
                return "review_finished"
            if review["verdict"] == "undetermined" and (
                    not review["check_suggestion"] or not self.allowed()):
                self.unresolved.append(review["finding"])
                return "review_undetermined"
            # A final review may still be followed by one revision, labelled unreviewed.
            self.gateway.require()
            request = self.apply()

    def full_answer(self, agent):
        value = self.gateway.call("INDEPENDENT", agent, self.packet(agent, "INDEPENDENT"))
        artifact = render_ranking(value["ranking"])
        self.independent[agent] = artifact
        self.independent_details[agent] = copy.deepcopy(value)
        self.event("independent_answer", member=agent, artifact=artifact, structured=value)
        return artifact

    def ordinary(self):
        # Collect all independent answers BEFORE publishing them into any discussion packet.
        for agent in self.agents:
            self.full_answer(agent)
        for agent in self.agents:
            self.discussion.append({"author": agent, "kind": "initial",
                                    **copy.deepcopy(self.independent_details[agent])})
        self.work = {"ref": "W1", "artifact": self.independent[self.driver], "unresolved": [],
                     "ranking": list(self.independent_details[self.driver]["ranking"]),
                     "explanation": self.independent_details[self.driver]["explanation"],
                     "application_history": [], "changed_text": True,
                     "origin": "driver_initial_fallback_not_selected_by_score"}
        self.works.append(copy.deepcopy(self.work))
        self.event("ordinary_initial_fallback", work_ref=self.work["ref"])
        for round_number in range(2):
            for agent in self.agents:
                value = self.gateway.call("DISCUSS", agent, self.packet(agent, "DISCUSS"))
                self.discussion.append({"author": agent, "kind": "discussion", "round": round_number + 1, "text": value["text"]})
                self.event("discussion", member=agent, round=round_number + 1, text=value["text"])
        value = self.gateway.call("FINAL", self.driver, self.packet(self.driver, "FINAL"))
        artifact = render_ranking(value["ranking"])
        self.work = {"ref": f"W{len(self.works) + 1}", "artifact": artifact, "unresolved": [],
                     "ranking": list(value["ranking"]), "explanation": value["explanation"],
                     "application_history": [], "changed_text": artifact != self.work["artifact"]}
        self.works.append(copy.deepcopy(self.work))
        self.event("ordinary_final", artifact=artifact, structured=value)
        return "discussion_finished"

    def run(self, system):
        stop, error, status = None, None, None
        try:
            if system == "coreta":
                stop = self.local_protocol()
            elif system == "ordinary_discussion":
                stop = self.ordinary()
            elif system == "independent":
                for agent in self.agents:
                    self.full_answer(agent)
                stop = "independent_answers_collected"
            else:
                raise ValueError("Unsupported system")
        except ProtocolError as exc:
            error = {"code": exc.code, "detail": exc.detail}
            stop = exc.code
            status = "budget_exhausted" if exc.code in {"ATTEMPT_BUDGET", "MODEL_TIMEOUT"} else "protocol_failure"
        latest = copy.deepcopy(self.reviews[-1]) if self.reviews else None
        review_current = bool(latest and self.work and latest["work_ref"] == self.work["ref"])
        if status is None:
            if system == "independent":
                status = "independent_collected"
            elif not self.work:
                status = "protocol_failure"
            elif review_current and latest["verdict"] == "no_defect_found" and not self.unresolved:
                status = "reviewed_no_defect"
            elif self.unresolved or (review_current and latest["verdict"] != "no_defect_found"):
                status = "best_effort_unresolved"
            else:
                status = "best_effort_unreviewed"
        result = {
            "protocol": "coreta/local-contribution-v1", "system": system,
            "task_id": self.packets.task["task_id"], "condition": self.packets.condition,
            "agents": self.agents,
            "driver": self.driver, "status": status, "stop_reason": stop, "error": error,
            "artifact": self.work["artifact"] if self.work else None,
            "work_ref": self.work["ref"] if self.work else None,
            "unresolved": self.unresolved, "latest_review": latest,
            "latest_review_applies_to_current_work": review_current,
            "independent_answers": self.independent,
            "independent_answer_details": self.independent_details,
            "interventions": self.interventions, "final_reviews": len(self.reviews),
            "logical_calls": self.journal.calls, "completed_calls": self.journal.completed,
            "format_repairs": self.journal.repairs, "http_attempts": self.gateway.client.attempts,
            "duration_seconds": time.monotonic() - self.started,
            "usage_records": self.journal.usage, "uncertain_usage_attempts": self.journal.uncertain_attempts,
            "usage_complete": self.journal.uncertain_attempts == 0 and len(self.journal.usage) == self.gateway.client.attempts,
            "input_count_mode": self.gateway.client.count_mode,
            "seed_sent": False, "externally_scored": False,
        }
        self.save_state()
        write_json(self.journal.root / "result.json", result)
        return result
