"""Opt-in constructive protocol. Does not change the archived v0.3 runner."""
from __future__ import annotations

import copy
import hashlib
import json
import time
from pathlib import Path

from .schemas import Contracts, ProtocolError, check_refs
from .state import reference_index, write_json

REVISION_SYSTEMS = {"coreta_revision": 14, "independent_aggregate": 4,
                    "static_debate": 10, "independent_refine": 10}

def obj(**properties):
    return {"type": "object", "properties": properties, "required": list(properties),
            "additionalProperties": False}


def text(limit=3000):
    return {"type": "string", "minLength": 1, "maxLength": limit}


def array(items, limit=12):
    return {"type": "array", "items": items, "maxItems": limit}


def choice(*values):
    return {"type": "string", "enum": list(values)}


class RevisionContracts(Contracts):
    def __init__(self, legacy_path):
        super().__init__(legacy_path)
        defs = self.document["$defs"]
        refs = array(text(120))
        proposal = obj(description=text(), blocking={"type": "boolean"}, target_refs=refs,
                       existing_issue_id={"anyOf": [text(30), {"type": "null"}]})
        contribution = obj(status=choice("provided", "cannot_help"), body=text(6000),
                           basis_refs=refs, attempted_issue_ids=array(text(30), 6), issues=array(proposal, 6))
        check = obj(target_refs=refs, method=text(), observation=text(),
                    conclusion=choice("supported", "defect", "unresolved"), scope=text())
        resolution = obj(issue_id=text(30), status=choice("open", "addressed", "dismissed"),
                         reason=text(), evidence_refs=refs, changed_step_ids=array(text(3), 8))
        decision = obj(action=choice("REQUEST_HELP", "REQUEST_ALTERNATIVE", "REQUEST_CHECK",
                                     "CONTINUE_SELF", "FINISH_COMPLETE", "FINISH_STALLED"),
                       recipient=choice("A0", "A1", "A2", "none"), goal=text(),
                       deliverable=text(), check_plan=text(), issue_ids=array(text(30), 6), reason=text())
        defs.update({
            "Synthesis": obj(candidate={"$ref": "#/$defs/Candidate"}, issues=array(proposal, 6)),
            "Constructive": contribution,
            "Inspection": obj(checks={"type": "array", "items": check, "minItems": 1, "maxItems": 6},
                              issues=array(proposal, 6)),
            "RevisionUpdate": obj(candidate={"$ref": "#/$defs/Candidate"},
                                  resolutions=array(resolution, 40), issues=array(proposal, 6),
                                  application=text(5000), next=decision),
        })
        defs["RevisionDecision"] = decision
        defs["Event"] = obj(event_id=text(120), schema_version={"const": "coreta/0.4-candidate"},
                            sent_from=choice("A0", "A1", "A2"), base_version={"type": "integer"},
                            stage=choice("draft", "refine_draft", "synthesize", "build", "inspect", "apply", "request", "work", "final"),
                            task_id=text(100), payload={"anyOf": [{"$ref": "#/$defs/" + name} for name in
                                ("Candidate", "Synthesis", "Constructive", "Inspection", "RevisionUpdate",
                                 "RevisionDecision", "Final")]})
        self.document["$id"] = "https://example.invalid/coreta/design/0.4-candidate/schema.json"
        self.document["title"] = "CoReTA constructive revision contract"


class RevisionRunner:
    CAP = 14

    def __init__(self, task, directory, run_id, contracts, client, config, prompts, seed=17,
                 system="coreta_revision", draft_bank=None):
        if system not in REVISION_SYSTEMS:
            raise ValueError("Unknown revision comparison system")
        self.system, self.CAP = system, REVISION_SYSTEMS[system]
        self.draft_bank = Path(draft_bank) if draft_bank else None
        self.final_candidates = []
        self.task, self.directory, self.run_id = task, Path(directory), run_id
        self.contracts, self.client, self.config, self.prompts = contracts, client, config, prompts
        self.seed, self.calls, self.repairs = seed, 0, 0
        self.events, self.drafts, self.issues, self.attempts = [], [], {}, []
        self.current, self.version = None, -1
        self.deadline = time.monotonic() + config["protocol"]["task_timeout_seconds"]

    def log(self, name, value):
        with (self.directory / name).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(value, ensure_ascii=False) + "\n")

    def emit(self, stage, actor, payload):
        event = {"event_id": f"{self.run_id}:e{len(self.events):04d}", "schema_version": "coreta/0.4-candidate",
                 "sent_from": actor, "base_version": self.version, "stage": stage,
                 "task_id": self.task["task_id"], "payload": copy.deepcopy(payload)}
        self.contracts.validate("Event", event)
        self.log("events.jsonl", event)
        self.events.append(event)
        return event

    def view(self):
        # Keep the complete audit on disk; avoid duplicating its full history in every call.
        projected = []
        for issue in self.issues.values():
            item = copy.deepcopy(issue)
            item["handling_events"] = item["handling_events"][-1:]
            item["related_events"] = item.get("related_events", [])[-2:]
            projected.append(item)
        return {"task": self.task, "drafts": self.drafts, "current": self.current,
                "issues": projected, "attempts": self.attempts}

    def call(self, stage, actor, schema_name, material, validate=None):
        if self.calls >= self.CAP - (stage != "final"):
            raise ProtocolError("CALL_LIMIT", "Reserved final output budget reached")
        self.calls += 1
        schema = self.contracts.schema(schema_name)
        visible = reference_index(material)
        prompt = self.prompts["system"] + "\n" + self.prompts[stage]
        prompt += "\n" + json.dumps({"ACTOR": actor, "MATERIAL": material,
                                    "REFERENCE_INDEX": visible, "OUTPUT_SCHEMA": schema}, ensure_ascii=False)
        payload = self.client.payload(prompt, schema, self.config["generation"]["max_output_tokens"][stage])
        for attempt in range(2):
            raw = ""
            try:
                raw = self.client.complete(payload, deadline=self.deadline,
                                           logical_seed=f"{self.seed}|{stage}|{actor}|{self.calls}")
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ProtocolError("INVALID_JSON", "Output must be one JSON object") from exc
                self.contracts.validate(schema_name, value)
                check_refs(value, set(visible))
                self.check_targets(value, set(visible))
                for proposal in value.get("issues", []):
                    existing = proposal["existing_issue_id"]
                    if existing is not None and existing not in self.issues:
                        raise ProtocolError("REFERENCE_ERROR", "existing_issue_id must reference a visible issue")
                candidate = value.get("candidate") if isinstance(value, dict) else None
                if candidate is not None:
                    self.contracts.validate("Candidate", candidate)
                if schema_name == "Inspection" and any(not row["target_refs"] for row in value["checks"]):
                    raise ProtocolError("REFERENCE_ERROR", "Each performed check must identify visible targets")
                if validate:
                    validate(value)
                return value
            except ProtocolError as exc:
                self.log("validation.jsonl", {"stage": stage, "code": exc.code, "detail": exc.detail,
                                              "raw": raw, "attempt": attempt})
                if (exc.code not in {"SCHEMA_ERROR", "INVALID_JSON", "REFERENCE_ERROR", "INVALID_ACTION"}
                        or attempt or self.repairs >= self.config["protocol"]["max_format_repairs"]):
                    raise
                self.repairs += 1
                payload = self.client.payload(prompt + "\nSTRUCTURAL_ERROR=" + exc.detail +
                                              "\nPREVIOUS_OUTPUT=" + raw +
                                              "\nRepair the output using the same visible material.", schema,
                                              self.config["generation"]["max_output_tokens"][stage])

    @staticmethod
    def check_targets(value, visible):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "target_refs" and any(ref not in visible for ref in child):
                    raise ProtocolError("REFERENCE_ERROR", "target_refs must be visible")
                RevisionRunner.check_targets(child, visible)
        elif isinstance(value, list):
            for child in value:
                RevisionRunner.check_targets(child, visible)

    def proposed_issues(self, issues, event_id, registry):
        for proposal in issues:
            existing = proposal.get("existing_issue_id")
            if existing is not None:
                issue = registry[existing]
                issue.setdefault("related_events", []).append({"event_id": event_id, **copy.deepcopy(proposal)})
                if proposal["blocking"] and issue["status"] in {"addressed", "dismissed"}:
                    issue["status"] = "open"
                continue
            issue_id = f"i{len(registry) + 1:04d}"
            registry[issue_id] = {**copy.deepcopy(proposal), "issue_id": issue_id, "status": "open",
                                  "source_event_id": event_id, "version": self.version,
                                  "handling_events": []}

    def record(self, stage, actor, value):
        event = self.emit(stage, actor, value)
        self.proposed_issues(value.get("issues", []), event["event_id"], self.issues)
        return event

    def validate_work(self, value):
        if not set(value["attempted_issue_ids"]).issubset(self.issues):
            raise ProtocolError("REFERENCE_ERROR", "Attempted issues must exist in the visible registry")

    def candidate_commit(self, stage, value, registry):
        before = copy.deepcopy(self.current)
        event = self.emit(stage, "A0", value)
        self.version += 1
        self.current = {"version": self.version, "source_event_id": event["event_id"],
                        "candidate": copy.deepcopy(value["candidate"])}
        self.issues = registry
        old = before["candidate"] if before else {"artifact": "", "steps": []}
        prior = {s["id"]: s for s in old["steps"]}
        after = {s["id"]: s for s in value["candidate"]["steps"]}
        self.log("commits.jsonl", {"event_id": event["event_id"], "before": before, "after": self.current,
                                  "issues": self.issues, "artifact_changed": old["artifact"] != value["candidate"]["artifact"],
                                  "changed_steps": [key for key in sorted(prior.keys() | after.keys())
                                                    if prior.get(key) != after.get(key)]})
        return event

    def update_registry(self, value):
        registry = copy.deepcopy(self.issues)
        ids = {step["id"] for step in value["candidate"]["steps"]}
        before = {s["id"]: s for s in self.current["candidate"]["steps"]} if self.current else {}
        changed = {s["id"] for s in value["candidate"]["steps"] if before.get(s["id"]) != s}
        seen = set()
        for row in value["resolutions"]:
            key = row["issue_id"]
            if key not in registry or key in seen or not set(row["changed_step_ids"]).issubset(ids):
                raise ProtocolError("REFERENCE_ERROR", "Resolution needs a unique visible issue and output step ids")
            if not set(row["changed_step_ids"]).issubset(changed):
                raise ProtocolError("REFERENCE_ERROR", "Resolution changed_step_ids must actually change from current")
            seen.add(key)
            if row["status"] in {"addressed", "dismissed"} and not (row["evidence_refs"] or row["changed_step_ids"]):
                raise ProtocolError("REFERENCE_ERROR", "Closing an issue requires evidence or output steps")
            registry[key]["status"] = row["status"]
            registry[key]["handling_events"].append({"version": self.version + 1, **copy.deepcopy(row)})
        self.proposed_issues(value["issues"], f"{self.run_id}:e{len(self.events):04d}", registry)
        return registry

    def validate_update(self, value):
        registry = self.update_registry(value)
        decision = value["next"]
        action = decision["action"]
        if not set(decision["issue_ids"]).issubset(self.issues):
            raise ProtocolError("REFERENCE_ERROR", "Decision may target only visible issue ids")
        blockers = [i for i in registry.values() if i["blocking"] and i["status"] in {"open", "in_progress"}]
        if action == "FINISH_COMPLETE" and blockers:
            raise ProtocolError("INVALID_ACTION", "Open blocking issues prevent normal completion")
        if action == "FINISH_STALLED":
            open_ids = {i["issue_id"] for i in blockers}
            attempted = set().union(*(set(a["issue_ids"]) for a in self.attempts)) if self.attempts else set()
            if not open_ids or not open_ids.issubset(attempted):
                raise ProtocolError("INVALID_ACTION", "Stalled requires an actual attempt on each blocking issue")
        expected = "none" if action.startswith("FINISH") else "A0" if action == "CONTINUE_SELF" else None
        if expected and decision["recipient"] != expected:
            raise ProtocolError("INVALID_ACTION", "Recipient does not match action")
        if expected is None and decision["recipient"] not in {"A1", "A2"}:
            raise ProtocolError("INVALID_ACTION", "Peer work needs A1 or A2")
        if not action.startswith("FINISH"):
            fingerprint = self.fingerprint(decision)
            if any(a["fingerprint"] == fingerprint for a in self.attempts):
                raise ProtocolError("INVALID_ACTION", "Repeat work must change target, method or recipient")

    @staticmethod
    def fingerprint(decision):
        return hashlib.sha256(json.dumps({k: decision[k] for k in
            ("action", "recipient", "goal", "deliverable", "check_plan", "issue_ids")}, sort_keys=True).encode()).hexdigest()

    def apply(self, evidence, remaining):
        value = self.call("apply", "A0", "RevisionUpdate", {**self.view(), "evidence": evidence,
                          "remaining_work_turns": remaining}, self.validate_update)
        registry = self.update_registry(value)
        self.candidate_commit("apply", value, registry)
        return value["next"]

    def initial_drafts(self):
        for actor in ("A0", "A1", "A2"):
            cache = None
            material = {"task": self.task, "actor": actor, "seed": self.seed,
                        "config": self.config, "system_prompt": self.prompts["system"],
                        "draft_prompt": self.prompts["draft"], "schema": self.contracts.schema("Candidate")}
            fingerprint = hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()
            if self.draft_bank:
                self.draft_bank.mkdir(parents=True, exist_ok=True)
                cache = self.draft_bank / (fingerprint + ".json")
            if cache and cache.exists():
                saved = json.loads(cache.read_text(encoding="utf-8"))
                if saved["fingerprint"] != fingerprint:
                    raise ProtocolError("REFERENCE_ERROR", "Shared draft fingerprint mismatch")
                value = saved["candidate"]
                self.contracts.validate("Candidate", value)
                check_refs(value, set())
                self.calls += 1
                self.log("cache.jsonl", {"actor": actor, "fingerprint": fingerprint, "deployment_call_counted": True})
            else:
                value = self.call("draft", actor, "Candidate", {"task": self.task})
                if cache:
                    try:
                        with cache.open("x", encoding="utf-8") as stream:
                            stream.write(json.dumps({"fingerprint": fingerprint, "candidate": value}, ensure_ascii=False))
                    except FileExistsError as exc:
                        raise ProtocolError("MODEL_UNAVAILABLE", "Concurrent draft writer; use sequential jobs") from exc
            event = self.emit("draft", actor, value)
            self.drafts.append(event)
            if actor == "A0":
                self.current = {"version": 0, "source_event_id": event["event_id"], "candidate": value}
                self.version = 0

    def baseline(self):
        current = {e["sent_from"]: e for e in self.drafts}
        if self.system != "independent_aggregate":
            for _ in range(2):
                frozen, updated = copy.deepcopy(current), {}
                for actor in ("A0", "A1", "A2"):
                    visible = [frozen[actor]] if self.system == "independent_refine" else list(frozen.values())
                    value = self.call("refine_draft", actor, "Candidate", {"task": self.task,
                                      "mode": self.system, "previous_candidates": visible})
                    updated[actor] = self.emit("refine_draft", actor, value)
                    if actor == "A0":
                        self.version += 1
                        self.current = {"version": self.version, "source_event_id": updated[actor]["event_id"],
                                        "candidate": copy.deepcopy(value)}
                current = updated
        self.final_candidates = list(current.values())
        return "complete"

    def collaborate(self):
        value = self.call("synthesize", "A0", "Synthesis", self.view())
        registry = copy.deepcopy(self.issues)
        self.proposed_issues(value["issues"], f"{self.run_id}:e{len(self.events):04d}", registry)
        self.candidate_commit("synthesize", value, registry)
        build = self.call("build", "A1", "Constructive", self.view(), self.validate_work)
        built = self.record("build", "A1", build)
        self.attempts.append({"event_id": built["event_id"], "issue_ids": build["attempted_issue_ids"], "fingerprint": "bootstrap"})
        review = self.call("inspect", "A2", "Inspection", {**self.view(), "subject": built})
        checked = self.record("inspect", "A2", review)
        decision = self.apply([built, checked], 2)
        for turn in range(3):
            action = decision["action"]
            if action.startswith("FINISH"):
                return "complete" if action == "FINISH_COMPLETE" else "stalled"
            if turn == 2 or self.calls + (2 if action == "REQUEST_CHECK" else 3) + 1 > self.CAP:
                return "budget_exhausted"
            for key in decision["issue_ids"]:
                if self.issues[key]["status"] == "open":
                    self.issues[key]["status"] = "in_progress"
            request = self.emit("request", "A0", decision)
            actor = decision["recipient"]
            material = {**self.view(), "request": request}
            if action == "REQUEST_CHECK":
                value = self.call("inspect", actor, "Inspection", material)
                evidence = [request, self.record("inspect", actor, value)]
            else:
                value = self.call("work", actor, "Constructive", material, self.validate_work)
                contribution = self.record("work", actor, value)
                evidence = [request, contribution]
                if value["status"] == "provided":
                    checker = "A1" if actor == "A2" else "A2"
                    reviewed = self.call("inspect", checker, "Inspection", {**self.view(), "request": request,
                                                                                "subject": contribution})
                    evidence.append(self.record("inspect", checker, reviewed))
            for key in decision["issue_ids"]:
                if self.issues[key]["status"] == "in_progress":
                    self.issues[key]["status"] = "open"
            self.attempts.append({"event_id": evidence[-1]["event_id"],
                                  "issue_ids": decision["issue_ids"] if action == "REQUEST_CHECK" else value["attempted_issue_ids"],
                                  "fingerprint": self.fingerprint(decision)})
            decision = self.apply(evidence, 1 - turn)

    def run_drafts(self):
        """Independent calibration only; never synthesize or finalize a solution."""
        errors, status = [], "completed"
        try:
            self.initial_drafts()
        except ProtocolError as exc:
            status = "incomplete"
            errors.append({"code": exc.code, "detail": exc.detail})
        result = {"task_id": self.task["task_id"], "run_id": self.run_id,
                  "phase": "draft_screen", "seed": self.seed, "status": status,
                  "draft_count": len(self.drafts), "normal_calls": self.calls,
                  "format_repairs": self.repairs, "http_attempts": self.client.attempts,
                  "errors": errors}
        write_json(self.directory / "draft_result.json", result)
        return result

    def run(self):
        errors, status, stop = [], "completed", "not_started"
        try:
            self.initial_drafts()
            stop = self.collaborate() if self.system == "coreta_revision" else self.baseline()
        except ProtocolError as exc:
            status, stop = "degraded", "runtime_error"
            errors.append({"code": exc.code, "detail": exc.detail})
        prefinal = self.current["candidate"]["artifact"] if self.current else ""
        artifact = prefinal
        if self.current:
            try:
                # Current includes the complete latest solution. Supply the constructive
                # evidence once, not every historical candidate and repeated issue table.
                evidence = [e for e in self.events if e["stage"] in {"build", "work", "inspect"}]
                value = self.call("final", "A0", "Final", {**self.view(), "stop_reason": stop,
                                  "evidence": evidence[-3:], "final_candidates": self.final_candidates})
                self.emit("final", "A0", value)
                artifact = value["artifact"]
            except ProtocolError as exc:
                status = "degraded"
                errors.append({"code": exc.code, "detail": exc.detail})
        else:
            status = "failed"
        result = {"task_id": self.task["task_id"], "run_id": self.run_id, "system": self.system, "seed": self.seed,
                  "status": status, "stop_reason": stop, "artifact": artifact, "prefinal_artifact": prefinal,
                  "finalizer_changed": artifact != prefinal,
                  "normal_calls": self.calls, "format_repairs": self.repairs,
                  "http_attempts": self.client.attempts, "issues": self.issues, "errors": errors}
        write_json(self.directory / "result.json", result)
        return result
