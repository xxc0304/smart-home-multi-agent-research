"""Small output contracts, dynamically restricted to the current visible state."""
from __future__ import annotations

import copy
import json

from jsonschema import Draft202012Validator

from ..schemas import ProtocolError


class HandoffContracts:
    def __init__(self, path):
        self.document = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(self.document)

    def schema(self, stage, refs, agents, allowed, ranking_items=None):
        ranking = None
        if ranking_items is not None:
            if len(ranking_items) != 15 or len(set(ranking_items)) != 15:
                raise ValueError("Ranking contract requires 15 unique public item names")
            ranking = {"type": "array", "minItems": 15, "maxItems": 15, "uniqueItems": True,
                       "items": {"type": "string", "enum": list(ranking_items)}}
        if stage in {"INDEPENDENT", "FINAL", "APPLY"} and ranking is None:
            raise ValueError("Answer-producing stages require public ranking items")
        if stage in {"INDEPENDENT", "FINAL"} and ranking is not None:
            return {"type": "object", "additionalProperties": False,
                    "properties": {"explanation": {"type": "string"}, "ranking": ranking},
                    "required": ["explanation", "ranking"]}
        if stage in {"INDEPENDENT", "DISCUSS", "FINAL"}:
            return {"type": "object", "additionalProperties": False,
                    "properties": {"text": {"type": "string", "minLength": 1}}, "required": ["text"]}
        name = {"CONTRIBUTE": "ContributionOutput", "REPLY": "ContributionOutput",
                "APPLY": "ApplyOutput", "REVIEW": "ReviewOutput"}[stage]
        definitions = copy.deepcopy(self.document["$defs"])
        definitions["Ref"] = {"type": "string", "enum": sorted(refs)}
        definitions["Agent"] = {"type": "string", "enum": list(agents)}
        definitions["Request"]["properties"]["kind"] = {"enum": list(allowed)} if allowed else {"not": {}}
        root = copy.deepcopy(definitions[name])
        if stage == "APPLY" and ranking is not None:
            root["properties"]["artifact"] = {"anyOf": [ranking, {"type": "null"}]}
        if stage == "APPLY" and not allowed:
            root["properties"]["request"] = {"type": "null"}
        needed = {}

        def visit(node):
            if isinstance(node, dict):
                ref = node.get("$ref", "")
                if ref.startswith("#/$defs/"):
                    key = ref.rsplit("/", 1)[1]
                    if key not in needed:
                        needed[key] = definitions[key]
                        visit(needed[key])
                for child in node.values():
                    visit(child)
            elif isinstance(node, list):
                for child in node:
                    visit(child)
        visit(root)
        return {"$schema": self.document["$schema"], **root, "$defs": needed}

    @staticmethod
    def decode(raw, schema, *, allow_identical_duplicate_keys=False, format_repairs=None):
        def pairs(entries):
            result = {}
            for key, value in entries:
                if key in result:
                    previous = json.dumps(result[key], ensure_ascii=False, sort_keys=True,
                                          separators=(",", ":"))
                    current = json.dumps(value, ensure_ascii=False, sort_keys=True,
                                         separators=(",", ":"))
                    if allow_identical_duplicate_keys and previous == current:
                        if format_repairs is not None:
                            format_repairs.append(key)
                        continue
                    raise ValueError(f"Duplicate key: {key}")
                result[key] = value
            return result
        try:
            value = json.loads(raw, object_pairs_hook=pairs,
                               parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        except (ValueError, TypeError) as exc:
            raise ProtocolError("SCHEMA_ERROR", f"JSON parsing: {exc}") from exc
        errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(list(e.path)))
        if errors:
            raise ProtocolError("SCHEMA_ERROR", "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:6]))
        return value
