"""Single-task orchestration for the three-agent protocol and controlled baselines."""
from __future__ import annotations

import copy
import hashlib
import json
import time

from .prompts import BASELINE_INSTRUCTIONS
from .schemas import ProtocolError, check_refs, check_update
from .state import State, reference_index, write_json


SYSTEM_CAPS = {"single_finalized": 2, "solo_refine": 4, "independent_aggregate": 4,
               "static_debate": 10, "coreta": 12, "generic_help": 12, "no_application_record": 12}
ACTIONS = ["CONTINUE_SELF", "REQUEST_HELP", "REQUEST_CHECK", "REQUEST_ALTERNATIVE", "FINISH"]


class Runner:
    def __init__(self, state: State, client, prompts, config, *, system="coreta", seed=17, draft_bank=None):
        if system not in SYSTEM_CAPS:
            raise ValueError("Unknown system")
        self.state, self.client, self.prompts, self.config = state, client, prompts, config
        self.system, self.seed = system, seed
        self.no_app = system == "no_application_record"
        self.calls = self.repairs = 0
        self.deadline = time.monotonic() + config["protocol"]["task_timeout_seconds"]
        self.dropped = set()
        self.draft_bank = draft_bank

    def call(self, stage, actor, name, values, *, check=None, history=None, baseline=None):
        cap = SYSTEM_CAPS[self.system]
        if self.calls >= cap - (stage != "final"):
            raise ProtocolError("CALL_LIMIT", "Normal-call budget reached; finalizer reserved")
        schema = self.state.contracts.schema(name, self.no_app)
        self.calls += 1
        visible = []
        # Optional history is removed oldest bundle first, without modifying task/current/drafts.
        kept = list(history or [])
        while True:
            local = copy.deepcopy(values)
            if kept:
                local["applications_json"] = [row for _, rows in kept for row in rows]
            elif "applications_json" in local:
                local["applications_json"] = []
            visible = reference_index(local)
            local["visible_reference_index"] = visible
            for key in ("candidate_schema", "review_schema", "lead_update_schema", "contribution_schema",
                        "final_schema", "no_application_lead_update_schema"):
                local[key] = schema
            if baseline:
                instructions = self.prompts.system + "\n" + BASELINE_INSTRUCTIONS[baseline] + "\n" + json.dumps(
                    {"PUBLIC_TASK": self.state.task, "MATERIAL": values, "REFERENCE_INDEX": visible,
                     "OUTPUT_SCHEMA": schema}, ensure_ascii=False)
            else:
                instructions = self.prompts.instructions("no_application" if self.no_app and stage == "lead_update" else stage,
                                                        local, visible)
            payload = self.client.payload(instructions, schema, self.config["generation"]["max_output_tokens"][stage])
            if self.client.size(payload) <= self.config["generation"]["max_input_tokens"]:
                break
            if not kept:
                raise ProtocolError("CONTEXT_OVERFLOW", "Required stage material exceeds input budget")
            bundle_id, _ = kept.pop(0)
            self.dropped.add(bundle_id)
            self.state.log("context.jsonl", {"stage": stage, "removed_history_bundle": bundle_id})
        seed_material = f"{self.seed}|{self.state.task['task_id']}|{actor}|{stage}|{self.calls}"
        # Initial drafts are independent of the chosen system/earlier calls.
        if stage == "draft" and baseline is None:
            seed_material = f"{self.seed}|{self.state.task['task_id']}|{actor}|draft"
        logical_seed = int(hashlib.sha256(seed_material.encode()).hexdigest()[:8], 16)
        raw = ""
        original_instructions = instructions
        for attempt in range(2):
            try:
                raw = self.client.complete(payload, deadline=self.deadline, logical_seed=logical_seed)
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ProtocolError("INVALID_JSON", "Output must be one JSON object") from exc
                self.state.contracts.validate(name, value, self.no_app)
                check_refs(value, set(visible))
                if check:
                    check(value, set(visible))
                self.state.log("parsed.jsonl", {"stage": stage, "actor": actor, "repair": bool(attempt), "payload": value})
                return value
            except ProtocolError as exc:
                repairable = exc.code in {"INVALID_JSON", "SCHEMA_ERROR", "REFERENCE_ERROR", "INVALID_ACTION", "STALE_VERSION"}
                if not repairable or attempt or self.repairs >= self.config["protocol"]["max_format_repairs"]:
                    raise
                self.repairs += 1
                repair = self.prompts.render("repair", {"validation_errors": [exc.detail],
                                                       "raw_previous_output": raw, "stage_schema": schema})
                # Same original task, view and stage instructions; only structural feedback appended.
                payload = self.client.payload(original_instructions + "\n" + repair, schema,
                                              self.config["generation"]["max_output_tokens"][stage])

    def base(self):
        return {"public_task_json": self.state.task}

    def draft(self, actor):
        cache = None
        if self.draft_bank:
            self.draft_bank.mkdir(parents=True, exist_ok=True)
            material = {"task": self.state.task, "actor": actor, "seed": self.seed, "config": self.config,
                        "prompt": self.prompts.blocks[0:2], "schema": self.state.contracts.schema("Candidate")}
            key = hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()
            cache = self.draft_bank / (key + ".json")
        if cache and cache.exists():
            value = json.loads(cache.read_text(encoding="utf-8"))
            self.state.contracts.validate("Candidate", value)
            check_refs(value, set())
            self.calls += 1
            self.state.log("cache.jsonl", {"actor": actor, "source": str(cache), "deployment_call_counted": True})
        else:
            value = self.call("draft", actor, "Candidate", self.base())
            if cache:
                # Exclusive creation prevents a second writer from silently replacing the shared draw.
                try:
                    with cache.open("x", encoding="utf-8") as stream:
                        stream.write(json.dumps(value, ensure_ascii=False))
                except FileExistsError as exc:
                    raise ProtocolError("MODEL_UNAVAILABLE", "Concurrent draft-bank writer; run shared-bank jobs sequentially") from exc
        event = self.state.emit("draft", actor, value, recipient="archive")
        self.state.drafts[actor] = event
        if actor == "A0":
            self.state.set_initial(event)
        return event

    def review(self, actor, subject, request=None):
        if request is not None and request["base_version"] != self.state.version:
            raise ProtocolError("STALE_VERSION", "Request does not target the current candidate version")
        values = {**self.base(), "own_draft_json": self.state.wrap(self.state.drafts[actor]),
                  "candidate_json": self.state.current_view(),
                  "request_or_null": self.state.wrap(request) if request else None,
                  "subject_json": self.state.wrap(subject), "subject_event_id": subject["event_id"]}
        def check(value, _):
            if value["subject_id"] != subject["event_id"]:
                raise ProtocolError("REFERENCE_ERROR", "Review subject_id mismatch")
        value = self.call("review", actor, "Review", values, check=check)
        return self.state.emit("review", actor, value, parents=[subject["event_id"]], base_version=self.state.version)

    def update(self, evidence, remaining, stage):
        legal = ACTIONS if remaining else ["FINISH"]
        values = {**self.base(), "initial_drafts_json": [self.state.wrap(self.state.drafts[a]) for a in ("A0", "A1", "A2")],
                  "candidate_json": self.state.current_view(), "current_version": self.state.version,
                  "evidence_json": [self.state.wrap(e) for e in evidence],
                  "bootstrap_or_apply_or_continue": stage, "legal_actions_json": legal,
                  "remaining_turns": remaining}
        if not self.no_app:
            values["applications_json"] = []
        def check(value, visible):
            check_update(value, visible, legal, evidence, self.no_app)
        history = [] if self.no_app else [(row["event_id"], [row]) for row in self.state.applications
                                          if row["event_id"] not in self.dropped]
        value = self.call("lead_update", "A0", "LeadUpdate", values, check=check, history=history)
        event = self.state.commit(value, [e["event_id"] for e in evidence], self.no_app)
        return value["next"], event

    @staticmethod
    def generic(request):
        return {"kind": request["kind"], "goal": "Review the current solution and offer any useful correction, completion, counterexample, or alternative approach.",
                "target_step_ids": [], "current_attempt": "See the current candidate",
                "deliverable": "Provide a useful correction, completion, or alternative approach",
                "check_plan": "Check against the public task", "reason_for_recipient": "Scheduled peer for this interaction"}

    def collaborate(self):
        bootstrap = self.review("A2", self.state.drafts["A0"])
        self.state.bundles.append([bootstrap])
        decision, lead = self.update([bootstrap], self.config["protocol"]["max_work_turns"], "bootstrap")
        for turn in range(self.config["protocol"]["max_work_turns"]):
            action = decision["action"]
            if action == "FINISH":
                break
            remaining = self.config["protocol"]["max_work_turns"] - turn - 1
            if action == "CONTINUE_SELF":
                decision, lead = self.update([], remaining, "continue")
                continue
            recipient = decision["recipient"]
            actual = copy.deepcopy(decision["request"])
            if self.system == "generic_help" and action != "REQUEST_CHECK":
                actual = self.generic(actual)
            request = self.state.emit("request", "A0", actual, recipient=recipient,
                                      parents=[lead["event_id"]], base_version=self.state.version)
            evidence = [request]
            if action == "REQUEST_CHECK":
                # Projection exposes only the current candidate, never raw Decision/Application.
                subject = {**lead, "payload": self.state.current_view()["candidate"]}
                evidence.append(self.review(recipient, subject, request))
            else:
                values = {**self.base(), "own_draft_json": self.state.wrap(self.state.drafts[recipient]),
                          "candidate_json": self.state.current_view(), "request_event_id": request["event_id"],
                          "request_json": self.state.wrap(request)}
                def check(value, _):
                    if value["request_id"] != request["event_id"]:
                        raise ProtocolError("REFERENCE_ERROR", "Contribution request_id mismatch")
                value = self.call("contribution", recipient, "Contribution", values, check=check)
                contribution = self.state.emit("contribution", recipient, value, parents=[request["event_id"]],
                                               base_version=self.state.version)
                evidence.append(contribution)
                if value["status"] == "provided":
                    checker = "A2" if recipient == "A1" else "A1"
                    evidence.append(self.review(checker, contribution, request))
            self.state.bundles.append(evidence)
            decision, lead = self.update(evidence, remaining, "apply")

    def baseline(self):
        if self.system in {"single_finalized", "independent_aggregate"}:
            return []
        current = {actor: self.state.drafts[actor] for actor in self.state.drafts}
        for _ in range(2):
            frozen = copy.deepcopy(current)
            updated = {}
            for actor in current:
                peers = [self.state.wrap(e) for e in frozen.values()]
                value = self.call("draft", actor, "Candidate", {"candidates": peers}, baseline=self.system)
                updated[actor] = self.state.emit("draft", actor, value, recipient="archive",
                                                  parents=[e["event_id"] for e in frozen.values()])
                if actor == "A0":
                    # Preserve the last valid A0 artifact even if a later peer call fails.
                    self.state.current = {"version": 0, "source_event_id": updated[actor]["event_id"],
                                          "candidate": copy.deepcopy(value)}
            current = updated
        # Separate candidate projection for scoring; does not change main-protocol versions.
        self.state.current = {"version": 0, "source_event_id": current["A0"]["event_id"],
                              "candidate": current["A0"]["payload"]}
        return list(current.values())

    def finish(self, last_candidates):
        initial = [self.state.wrap(self.state.drafts[a]) for a in self.state.drafts]
        evidence = list(initial)
        optional = []
        if self.system == "solo_refine":
            evidence.append(self.state.current_view())
        elif self.system == "static_debate":
            evidence.extend(self.state.wrap(e) for e in last_candidates)
        elif self.system in {"coreta", "generic_help", "no_application_record"}:
            evidence.append(self.state.current_view())
            optional = [[self.state.wrap(e) for e in bundle] for bundle in self.state.bundles]
            if not self.no_app:
                # Add applications to the corresponding interaction bundle.
                for app in self.state.applications:
                    target = app["payload"]
                    for bundle in optional:
                        ids = {row["event_id"] for row in bundle}
                        if any(target[key] in ids for key in ("request_id", "contribution_id", "review_id")):
                            bundle.append(copy.deepcopy(app))
                            break
        while True:
            flattened = [item for bundle in optional for item in bundle]
            flattened.sort(key=lambda item: next((e["sequence"] for e in self.state.events if e["event_id"] == item["event_id"]), -1))
            values = {**self.base(), "condition_evidence_package": evidence + flattened}
            visible = reference_index(values)
            schema = self.state.contracts.schema("Final")
            instructions = self.prompts.instructions("final", {**values, "final_schema": schema}, visible)
            payload = self.client.payload(instructions, schema, self.config["generation"]["max_output_tokens"]["final"])
            if self.client.size(payload) <= self.config["generation"]["max_input_tokens"]:
                break
            # Bootstrap is fixed; only completed work bundles may be pruned.
            if len(optional) <= 1:
                raise ProtocolError("CONTEXT_OVERFLOW", "Required finalizer input exceeds budget")
            removed = optional.pop(1)
            self.state.log("context.jsonl", {"stage": "final", "removed_event_ids": [e["event_id"] for e in removed]})
        value = self.call("final", "A0", "Final", values)
        self.state.emit("final", "A0", value, recipient="archive", base_version=self.state.version)
        return value["artifact"]

    def run(self):
        status, errors, last = "completed", [], []
        try:
            actors = ("A0",) if self.system in {"single_finalized", "solo_refine"} else ("A0", "A1", "A2")
            for actor in actors:
                self.draft(actor)
            if self.system in {"coreta", "generic_help", "no_application_record"}:
                self.collaborate()
            else:
                last = self.baseline()
        except ProtocolError as exc:
            status = "degraded"
            errors.append({"code": exc.code, "detail": exc.detail})
            self.state.emit("runtime_error", "runtime", {**errors[-1], "failed_event_id": None}, recipient="archive")
        prefinal = self.state.current_view()["candidate"]["artifact"] if self.state.current else ""
        artifact = prefinal
        if self.state.current:
            try:
                artifact = self.finish(last)
            except ProtocolError as exc:
                status = "degraded"
                errors.append({"code": exc.code, "detail": exc.detail})
                self.state.emit("runtime_error", "runtime", {**errors[-1], "failed_event_id": None}, recipient="archive")
        else:
            status = "failed"
        result = {"task_id": self.state.task["task_id"], "system": self.system, "run_id": self.state.run_id,
                  "seed": self.seed, "status": status, "artifact": artifact, "prefinal_artifact": prefinal,
                  "finalizer_changed": artifact != prefinal, "normal_calls": self.calls,
                  "format_repairs": self.repairs, "http_attempts": self.client.attempts, "errors": errors}
        write_json(self.state.directory / "result.json", result)
        return result
