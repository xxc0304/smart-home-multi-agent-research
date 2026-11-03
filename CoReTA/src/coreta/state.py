"""Append-only records and projections. Never retrieve data through model references."""
from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class State:
    def __init__(self, task: dict, run_id: str, directory: Path, contracts):
        self.task, self.run_id, self.directory, self.contracts = task, run_id, directory, contracts
        self.events: list[dict] = []
        self.drafts: dict[str, dict] = {}
        self.current = None
        self.version = 0
        self.applications: list[dict] = []
        self.bundles: list[list[dict]] = []

    def log(self, filename: str, value):
        with (self.directory / filename).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(value, ensure_ascii=False) + "\n")

    def emit(self, kind, sender, payload, *, recipient="A0", parents=(), base_version=None):
        event = {"schema_version": "coreta/0.3", "run_id": self.run_id,
                 "task_id": self.task["task_id"], "sequence": len(self.events),
                 "event_id": f"{self.run_id}:e{len(self.events):04d}", "kind": kind,
                 "sent_from": sender, "send_to": recipient, "cause_by": kind,
                 "parent_ids": list(parents), "base_version": base_version,
                 "created_at": datetime.now(timezone.utc).isoformat(), "payload": copy.deepcopy(payload)}
        self.contracts.validate("Event", event)
        if any(parent not in {e["event_id"] for e in self.events} for parent in parents):
            raise ValueError("Unknown event parent")
        self.events.append(event)
        self.log("events.jsonl", event)
        return event

    @staticmethod
    def wrap(event):
        return {key: copy.deepcopy(event[key]) for key in ("event_id", "sent_from", "base_version", "payload")}

    def current_view(self):
        return copy.deepcopy(self.current)

    def set_initial(self, event):
        self.current = {"version": 0, "source_event_id": event["event_id"], "candidate": copy.deepcopy(event["payload"])}

    def commit(self, payload, parents, no_application=False):
        event = self.emit("lead_update", "A0", payload, parents=parents, base_version=self.version)
        self.version += 1
        self.current = {"version": self.version, "source_event_id": event["event_id"],
                        "candidate": copy.deepcopy(payload["candidate"])}
        if not no_application and payload["application"] is not None:
            self.applications.append({"event_id": event["event_id"], "payload": copy.deepcopy(payload["application"])})
        return event


def reference_index(value) -> list[str]:
    refs: set[str] = set()

    def walk(item):
        if isinstance(item, dict):
            if "event_id" in item:
                refs.add(item["event_id"])
                payload = item.get("payload", {})
                if "steps" in payload:
                    refs.update(f"{item['event_id']}#{step['id']}" for step in payload["steps"])
            if "version" in item and "candidate" in item:
                refs.add(item["source_event_id"])
                refs.update(f"v{item['version']}:{step['id']}" for step in item["candidate"]["steps"])
                # The source event owns this candidate too. Expose the event/step
                # form alongside the version/step form so references generated
                # from the visible source_event_id are valid and unambiguous.
                refs.update(f"{item['source_event_id']}#{step['id']}"
                            for step in item["candidate"]["steps"])
            for key, child in item.items():
                # A citation does not grant visibility of its target.
                if key not in {"basis_refs", "evidence_refs", "before_refs", "parent_ids"}:
                    walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
    walk(value)
    return sorted(refs)
