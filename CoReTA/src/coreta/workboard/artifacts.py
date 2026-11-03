"""Task-native artifacts and immutable-by-copy work storage. No evaluator access."""
from __future__ import annotations

import copy
import difflib
import json


class TextAdapter:
    def schema(self):
        return {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]}

    def deliverable(self, artifact):
        return isinstance(artifact, str) and bool(artifact.strip())

    def render(self, artifact):
        return artifact if artifact is not None else ""


class RankingAdapter:
    def __init__(self, task):
        self.names = tuple(item["name"] for item in task["items"])

    def schema(self):
        return {"anyOf": [{"type": "array", "items": {"enum": list(self.names)},
                            "uniqueItems": True, "maxItems": len(self.names)}, {"type": "null"}]}

    def deliverable(self, artifact):
        return (isinstance(artifact, list) and len(artifact) == len(self.names)
                and set(artifact) == set(self.names))

    def render(self, artifact):
        return "\n".join(f"{i}. {name}" for i, name in enumerate(artifact or [], 1))


class ChoiceAdapter:
    def __init__(self, task):
        self.ids = tuple(c["id"] for c in task["choices"])
        if len(self.ids) < 2 or len(set(self.ids)) != len(self.ids):
            raise ValueError("Choice IDs must be unique and contain at least two options")

    def schema(self):
        return {"anyOf": [{"type": "string", "enum": list(self.ids)}, {"type": "null"}]}

    def deliverable(self, artifact):
        return isinstance(artifact, str) and artifact in self.ids

    def render(self, artifact):
        return artifact if self.deliverable(artifact) else ""


class Board:
    def __init__(self, adapter):
        self.adapter = adapter
        self._works = {}
        self.initials = {}
        self.current = None
        self.fallback = None

    def add(self, work, author, *, base=None, sources=None, initial=False):
        ref = f"W{len(self._works) + 1}"
        row = {"id": ref, "author": author, "base_version": base,
               "declared_sources": list(sources or ()),
               "source_declaration_status": "not_collected" if sources is None else "collected",
               "initial": initial, **copy.deepcopy(work)}
        row["deliverable_shape"] = self.adapter.deliverable(row["artifact"])
        lines = {"artifact": self.adapter.render(row["artifact"]).splitlines(),
                 "work_text": row["work_text"].splitlines()}
        row["locations"] = {f"{ref}:{field}:L{i}": line for field, values in lines.items()
                            for i, line in enumerate(values, 1)}
        self._works[ref] = row
        if initial:
            self.initials[author] = ref
        return ref

    def get(self, ref):
        return copy.deepcopy(self._works[ref]) if ref else None

    def snapshot(self):
        return copy.deepcopy(list(self._works.values()))

    def ids(self):
        return set(self._works)

    def targets(self):
        return {"whole_goal", *self._works, *(loc for w in self._works.values() for loc in w["locations"])}

    def promote(self, ref):
        self.current = ref
        if self._works[ref]["deliverable_shape"]:
            self.fallback = ref

    def initialize(self, editor, agents):
        ordered = [editor] + [a for a in agents if a != editor]
        ref = next((self.initials[a] for a in ordered if a in self.initials), None)
        if ref:
            self.promote(ref)
        if self.fallback is None:
            self.fallback = next((self.initials[a] for a in agents if a in self.initials
                                  and self._works[self.initials[a]]["deliverable_shape"]), None)

    def diff(self, before, after):
        old, new = self.get(before), self.get(after)
        return "\n".join(difflib.unified_diff(
            json.dumps({k: old[k] for k in ("artifact", "work_text", "open_points")}, ensure_ascii=False, indent=2).splitlines(),
            json.dumps({k: new[k] for k in ("artifact", "work_text", "open_points")}, ensure_ascii=False, indent=2).splitlines(),
            fromfile=before, tofile=after, lineterm=""))
