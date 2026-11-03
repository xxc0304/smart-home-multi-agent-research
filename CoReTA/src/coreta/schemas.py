"""Structural contracts plus explicit runtime semantic validation."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class ProtocolError(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code, self.detail = code, detail


class Contracts:
    def __init__(self, path: Path):
        self.document = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(self.document)

    def schema(self, name: str, no_application: bool = False) -> dict:
        # Send only transitively required definitions, keeping local $refs valid.
        root = copy.deepcopy(self.document["$defs"][name])
        if name == "LeadUpdate" and no_application:
            root["properties"]["application"] = {"type": "null"}
        needed: dict[str, Any] = {}

        def visit(value):
            if isinstance(value, dict):
                ref = value.get("$ref", "")
                if ref.startswith("#/$defs/"):
                    key = ref.rsplit("/", 1)[1]
                    if key not in needed:
                        needed[key] = copy.deepcopy(self.document["$defs"][key])
                        visit(needed[key])
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(root)
        return {"$schema": self.document["$schema"], **root, "$defs": needed}

    def validate(self, name: str, value: dict, no_application=False):
        errors = sorted(Draft202012Validator(self.schema(name, no_application)).iter_errors(value),
                        key=lambda e: str(list(e.path)))
        if errors:
            raise ProtocolError("SCHEMA_ERROR", "; ".join(
                f"{list(e.path)}: {e.message}" for e in errors[:6]))
        candidate = value.get("candidate") if name == "LeadUpdate" else value if name == "Candidate" else None
        if candidate is not None:
            ids = [step["id"] for step in candidate["steps"]]
            if len(ids) != len(set(ids)):
                raise ProtocolError("SCHEMA_ERROR", "Candidate step ids must be unique")


def check_refs(value: Any, visible: set[str]):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"basis_refs", "evidence_refs", "before_refs"}:
                invalid = sorted({ref for ref in child if ref not in visible})
                if invalid:
                    suggestions = {}
                    for ref in invalid:
                        if "#" not in ref:
                            continue
                        source_id = ref.rsplit("#", 1)[0]
                        matches = sorted(candidate for candidate in visible
                                         if candidate.startswith(source_id + "#"))
                        if matches:
                            suggestions[ref] = matches[:8]
                    detail = (f"{key} contains invisible references {invalid}. "
                              f"Visible step references from the same source: {suggestions}. "
                              "Re-read REFERENCE_INDEX and cite the visible source that actually "
                              "supports the statement. These are not automatic replacements. "
                              "The same step id in another event is a different source; do not "
                              "drop a dependency merely to pass reference validation.")
                    raise ProtocolError("REFERENCE_ERROR", detail)
            check_refs(child, visible)
    elif isinstance(value, list):
        for child in value:
            check_refs(child, visible)


def check_update(value: dict, visible: set[str], actions: list[str], evidence: list[dict],
                 no_application: bool):
    check_refs(value, visible)
    decision = value["next"]
    action, recipient, request = decision["action"], decision["recipient"], decision["request"]
    if action not in actions:
        raise ProtocolError("INVALID_ACTION", "Action is not currently legal")
    if action in {"FINISH", "CONTINUE_SELF"}:
        if recipient is not None or request is not None:
            raise ProtocolError("INVALID_ACTION", "Self/finish require null recipient and request")
    else:
        kinds = {"REQUEST_HELP": "complete", "REQUEST_CHECK": "verify", "REQUEST_ALTERNATIVE": "alternative"}
        if recipient not in {"A1", "A2"} or request is None or request["kind"] != kinds[action]:
            raise ProtocolError("INVALID_ACTION", "Peer/request kind mismatch")
        ids = {step["id"] for step in value["candidate"]["steps"]}
        if any(step not in ids for step in request["target_step_ids"]):
            raise ProtocolError("REFERENCE_ERROR", "Request targets must exist in output Candidate")
        if action == "REQUEST_HELP" and not request["target_step_ids"]:
            raise ProtocolError("INVALID_ACTION", "A complete request needs a target step")
        if action == "REQUEST_CHECK" and not request["target_step_ids"] and "whole_candidate" not in request["goal"]:
            raise ProtocolError("INVALID_ACTION", "An empty verify target requires whole_candidate in goal")
    app = value["application"]
    expected = {"request_id": None, "contribution_id": None, "review_id": None}
    kinds = {"request": "request_id", "contribution": "contribution_id", "review": "review_id"}
    for item in evidence:
        if item["kind"] in kinds:
            expected[kinds[item["kind"]]] = item["event_id"]
    if no_application or not evidence:
        if app is not None:
            raise ProtocolError("SCHEMA_ERROR", "This stage requires application=null")
    elif app is None or any(app[key] != ref for key, ref in expected.items()):
        raise ProtocolError("REFERENCE_ERROR", "Application must bind this stage's evidence ids")
    if app is not None:
        ids = {step["id"] for step in value["candidate"]["steps"]}
        if not set(app["changed_step_ids"]).issubset(ids):
            raise ProtocolError("REFERENCE_ERROR", "Changed ids must exist in output Candidate")
