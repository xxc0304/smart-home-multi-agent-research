"""D0 adds nullable navigation fields; existing source constraints stay intact."""
from ..workboard.contracts import Contracts as BaseContracts, TEXT, obj, nullable, handles
from ..schemas import ProtocolError


class Contracts(BaseContracts):
    def schema(self, stage, packet):
        schema = super().schema(stage, packet)
        focus = packet.get("FOCUS")
        if stage == "OBSERVE":
            offer = schema["properties"]["offer"]["anyOf"][0]
            offer["properties"]["responds_to"] = nullable(handles(
                {f["id"] for f in packet["FOCUS_HISTORY"]}))
            offer["required"].append("responds_to")
        if stage in {"CHOOSE", "FINAL_CHOOSE"}:
            schema["properties"]["focus_disposition"] = (nullable(obj(
                focus_id=handles({focus["id"]}), status={"enum": ["addressed", "pending", "deferred"]},
                reason=TEXT)) if focus else {"type": "null"})
            schema["required"].append("focus_disposition")
        if stage == "CHOOSE":
            refs = {r["ref"] for r in packet["REFERENCE_INDEX"]}
            schema["properties"]["next_check"] = nullable(obj(
                target=handles(packet["FOCUS_TARGETS"]), question=TEXT, check=TEXT,
                refs={"type": "array", "items": handles(refs), "uniqueItems": True,
                      "maxItems": len(refs)}))
            schema["required"].append("next_check")
        return schema

    @staticmethod
    def validate_action(stage, value):
        BaseContracts.validate_action(stage, value)
        if stage in {"CHOOSE", "FINAL_CHOOSE"}:
            disposition = value["focus_disposition"]
            if disposition is not None and not disposition["reason"].strip():
                raise ProtocolError("INVALID_ACTION", "Focus disposition needs a concrete reason")
