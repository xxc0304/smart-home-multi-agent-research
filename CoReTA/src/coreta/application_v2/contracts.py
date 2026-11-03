"""Reuse v1 transport contracts; replace only the application update interface."""
from __future__ import annotations

from .ranking_contracts import RankingContracts


def handles(refs):
    return {"type": "string", "enum": sorted(refs)} if refs else {"not": {}}


class ApplicationContracts(RankingContracts):
    def schema(self, stage, refs, agents, allowed, ranking_items=None):
        schema = super().schema(stage, refs, agents, allowed, ranking_items)
        if stage != "APPLY":
            return schema
        unit = handles({r for r in refs if r.startswith("U")})
        optional_text = {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]}
        schema["$defs"]["Application"] = {
            "type": "object", "additionalProperties": False,
            "properties": {
                "target": {"anyOf": [unit, {"type": "null"}]},
                "task_step": {"type": "string", "minLength": 1},
                "bindings": {"type": "array", "maxItems": 12, "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {"ref": {"$ref": "#/$defs/Ref"}, "use": {"type": "string", "minLength": 1}},
                    "required": ["ref", "use"]}},
                "result": optional_text, "missing": optional_text,
            }, "required": ["target", "task_step", "bindings", "result", "missing"]}
        schema["properties"]["applications"]["maxItems"] = 1
        schema["properties"]["artifact_uses"] = {"type": "array", "maxItems": 20, "uniqueItems": True, "items": unit}
        schema["properties"]["retire_applications"] = {
            "type": "array", "maxItems": 1, "items": {"type": "object", "additionalProperties": False,
            "properties": {"ref": unit, "reason": {"type": "string", "minLength": 1}}, "required": ["ref", "reason"]}}
        schema["required"] += ["artifact_uses", "retire_applications"]
        return schema
