"""Declared application dependencies; these states never certify semantic truth."""
from __future__ import annotations

import copy

from ..schemas import ProtocolError

TERMINAL = {"retired", "superseded"}


def fail(detail):
    raise ProtocolError("INVALID_ACTION", detail)


class Applications:
    def __init__(self):
        self.units = {}
        self.candidate_refs = []
        self.last_ref = None

    def record(self):
        return {"units": copy.deepcopy(list(self.units.values())), "candidate_refs": list(self.candidate_refs),
                "last_ref": self.last_ref}

    def descendants(self, ref):
        reached, frontier = set(), [ref]
        while frontier:
            source = frontier.pop()
            for name, row in self.units.items():
                if name not in reached and any(b["ref"] == source for b in row["bindings"]):
                    reached.add(name)
                    frontier.append(name)
        return reached

    def invalidate(self, ref, reason):
        for name in self.descendants(ref):
            row = self.units[name]
            if row["status"] not in TERMINAL:
                row["status"] = "stale"
                row["stale_reason"] = reason

    def blocked(self, refs=None):
        """Return declared incomplete dependencies, including provisional ancestors."""
        found, visited = [], set()
        def visit(ref):
            if ref in visited:
                return
            visited.add(ref)
            row = self.units[ref]
            if row["status"] != "applied_declared":
                found.append({"ref": ref, "status": row["status"], "missing": row["missing"],
                              "reason": row.get("stale_reason")})
            for binding in row["bindings"]:
                if binding["ref"] in self.units:
                    visit(binding["ref"])
        for ref in self.candidate_refs if refs is None else refs:
            visit(ref)
        return found

    def request_target(self, request):
        explicit = {r for r in request["target_refs"] if r in self.units}
        if len(explicit) > 1:
            fail("One request may target only one tracked application")
        if explicit:
            target = next(iter(explicit))
        elif self.last_ref is not None and self.units[self.last_ref]["status"] not in TERMINAL:
            target = self.last_ref
        else:
            pending = [r for r, u in self.units.items() if u["status"] not in TERMINAL and u["missing"]]
            if len(pending) != 1:
                fail("Request needs one explicit or unambiguous tracked application")
            target = pending[0]
        if self.units[target]["status"] in TERMINAL:
            fail("Cannot request work for a retired/superseded application")
        return target

    def update(self, value, pending=None):
        """Called on a transaction copy after schema/reference validation."""
        updates = value["applications"]
        app = updates[0] if updates else None
        target = app["target"] if app else None
        retired = {row["ref"] for row in value["retire_applications"]}
        excluded = {row["ref"] for row in value["excluded"]}
        if target in retired:
            fail("Cannot replace and retire the same application in one update")
        for ref in retired | ({target} if target else set()):
            if ref not in self.units or self.units[ref]["status"] in TERMINAL:
                fail("Application target must be a current or stale existing U")
        binding_refs = {b["ref"] for b in app["bindings"]} if app else set()
        if app and app["result"] is None and app["missing"] is None:
            fail("An application requires a concrete result or a necessary missing input/operation")
        forbidden = set(retired)
        if target:
            forbidden |= {target} | self.descendants(target)
        for ref in retired:
            forbidden |= self.descendants(ref)
        for ref in binding_refs & set(self.units):
            if ref in forbidden or self.units[ref]["status"] in TERMINAL | {"stale"}:
                fail("A new application cannot use its replaced self, invalidated descendants or obsolete U as input")
        if pending:
            expected = set(pending["required_handling_refs"])
            review_targets = ({ref for ref in pending["review"]["target_refs"]
                               if ref in self.units and self.units[ref]["status"] not in TERMINAL}
                              if pending["kind"] == "review" else set())
            requested = pending["request"]["application_ref"] if pending["kind"] == "reply" else None
            if len(review_targets) == 1:
                requested = next(iter(review_targets))
            path_retired = requested is not None and requested in retired
            if not path_retired and not expected <= binding_refs | excluded:
                raise ProtocolError("REFERENCE_ERROR", "Address every new reply/review ref through bindings or excluded")
            if pending["kind"] == "reply":
                all_rejected = expected <= excluded and not expected & binding_refs
                if not all_rejected and target != requested and not path_retired:
                    fail("Accepted reply must update its original application, not an unrelated step")
            elif pending["kind"] == "review":
                if len(review_targets) == 1 and expected & binding_refs:
                    reviewed = next(iter(review_targets))
                    if target != reviewed and reviewed not in retired:
                        fail("Accepted review of one current U must update or retire that application")
        before_refs = list(self.candidate_refs)
        for row in value["retire_applications"]:
            ref = row["ref"]
            self.units[ref]["status"] = "retired"
            self.units[ref]["retire_reason"] = row["reason"]
            self.invalidate(ref, "Dependency retired: " + ref)
        new_ref = None
        if app:
            if target:
                self.units[target]["status"] = "superseded"
                self.invalidate(target, "Dependency superseded: " + target)
            new_ref = f"U{len(self.units)+1}"
            status = "waiting" if app["result"] is None else "provisional" if app["missing"] else "applied_declared"
            upstream = [r for r in binding_refs if r in self.units]
            if status == "applied_declared" and self.blocked(upstream):
                status = "provisional"
            self.units[new_ref] = {"ref": new_ref, **copy.deepcopy(app), "status": status,
                                   "evidence_status": "model_declared_not_independently_confirmed"}
            self.last_ref = new_ref
        mapping = {target: new_ref} if target else {}
        expected_refs = {mapping.get(r, r) for r in before_refs if r not in retired | excluded}
        proposed = {mapping.get(r, r) for r in value["artifact_uses"] if r not in retired}
        if new_ref:
            proposed.add(new_ref)
        if not expected_refs <= proposed:
            fail("Cannot silently drop existing candidate U associations; exclude or retire explicitly")
        for ref in proposed:
            if ref not in self.units or self.units[ref]["status"] in TERMINAL:
                fail("Candidate references an obsolete/retired application")
        self.candidate_refs = sorted(proposed, key=lambda r: int(r[1:]))
        waiting = [u for u in self.units.values() if u["status"] not in TERMINAL and u["missing"]]
        if len(waiting) > 1:
            fail("First version supports one explicit unresolved handoff at a time")
        request_target = None
        if value["request"]:
            routed = copy.deepcopy(value["request"])
            routed["target_refs"] = [mapping.get(r, r) for r in routed["target_refs"]]
            request_target = self.request_target(routed)
        return {"new_ref": new_ref, "target": target, "retired": sorted(retired), "request_target": request_target}
