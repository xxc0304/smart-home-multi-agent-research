"""Finite-candidate checks. Source grounding is provenance, never semantic proof."""
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Condition:
    id: str
    field: str
    op: str
    value: object
    kind: str  # task_requirement or member_interpretation
    source: str
    quote: str


class ConditionBoard:
    def __init__(self, candidates, sources):
        self.candidates = candidates
        self.sources = sources
        self.conditions = {}
        self.history = []
        self.version = 0

    def add(self, condition):
        if condition.id in self.conditions:
            raise ValueError("condition id already exists")
        self._validate(condition)
        self.conditions[condition.id] = condition
        self.version += 1
        self.history.append({"action": "add", "condition": asdict(condition),
                             "version": self.version})

    def _validate(self, c):
        if c.kind not in {"task_requirement", "member_interpretation"}:
            raise ValueError("unknown condition kind")
        if c.op not in {"eq", "lt", "le", "gt", "ge"}:
            raise ValueError("unsupported operator")
        if not c.quote or c.quote not in self.sources.get(c.source, ""):
            raise ValueError("quote missing from source")
        # No eval or generated code. Missing candidate fields remain unknown.
        if not c.id or not c.field:
            raise ValueError("empty id or field")

    def check(self, candidate_id):
        candidate = self.candidates[candidate_id]
        results = []
        for c in self.conditions.values():
            actual = candidate.get(c.field)
            if actual is None:
                status = "unknown"
            else:
                try:
                    if c.op == "eq":
                        passed = type(actual) is type(c.value) and actual == c.value
                    else:
                        if type(actual) not in {int, float} or type(c.value) not in {int, float}:
                            raise TypeError("ordered comparisons require numbers")
                        passed = {"lt": lambda: actual < c.value,
                                  "le": lambda: actual <= c.value,
                                  "gt": lambda: actual > c.value,
                                  "ge": lambda: actual >= c.value}[c.op]()
                    status = "consistent" if passed else "violates"
                except TypeError:
                    status = "unknown"
            results.append({"condition": c.id, "kind": c.kind,
                            "actual": actual, "status": status})
        return {"candidate": candidate_id, "version": self.version, "checks": results}

    def revise(self, condition_id, replacement, reason, source, quote):
        """Record an attributable revision; do not certify its explanation as true."""
        old = self.conditions[condition_id]
        if not reason.strip() or not quote or quote not in self.sources.get(source, ""):
            raise ValueError("revision requires reason and source span")
        if replacement is not None:
            if replacement.id != condition_id:
                raise ValueError("revision must keep condition id")
            self._validate(replacement)
        before = {key: self.check(key) for key in self.candidates}
        if replacement is None:
            del self.conditions[condition_id]
        else:
            self.conditions[condition_id] = replacement
        self.version += 1
        after = {key: self.check(key) for key in self.candidates}
        self.history.append({"action": "revise", "old": asdict(old),
            "new": asdict(replacement) if replacement else None, "reason": reason,
            "source": source, "quote": quote, "before": before, "after": after,
            "version": self.version})

    def submit(self, candidate_id, expected_version, responses=None, best_effort=False):
        if expected_version != self.version:
            raise ValueError("stale check version")
        report = self.check(candidate_id)
        hard = [r for r in report["checks"] if r["kind"] == "task_requirement"
                and r["status"] == "violates"]
        outstanding = [r for r in report["checks"] if r["status"] != "consistent"]
        responses = responses or {}
        for r in outstanding:
            if not isinstance(responses.get(r["condition"]), str) or not responses[r["condition"]].strip():
                raise ValueError("each conflict or unknown requires an explicit response")
        if hard and not best_effort:
            raise ValueError("task requirement violated")
        # Explicit responses do not clear conflicts. Best effort never becomes a pass.
        report["status"] = "unresolved" if outstanding else "consistent_with_encoded_conditions"
        report["responses"] = responses
        report["best_effort"] = best_effort
        return report
