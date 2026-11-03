"""V2 stage roots with task-derived permutation length; frozen decode reused."""
import copy
from ..handoff.contracts import HandoffContracts


class RankingContracts(HandoffContracts):
    def schema(self, stage, refs, agents, allowed, ranking_items=None):
        ranking = None
        if ranking_items is not None:
            if len(ranking_items) not in {4, 15} or len(set(ranking_items)) != len(ranking_items):
                raise ValueError("Ranking contract requires 4 or 15 unique public item names")
            ranking = {"type": "array", "minItems": len(ranking_items), "maxItems": len(ranking_items), "uniqueItems": True,
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
