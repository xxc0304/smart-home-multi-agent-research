"""Small stage schemas, populated from visible state; no fixed reference capacity."""
from __future__ import annotations

from ..handoff.contracts import HandoffContracts
from ..schemas import ProtocolError


TEXT = {"type": "string", "minLength": 1}

ACTION_GUIDANCE = (
    "For reuse: set candidate_id to an existing allowed ID, work=null, and provide use_record. "
    "For new: provide work and use_record, candidate_id=null. "
    "For either successful action, reason may be null or a nonempty explanation. "
    "For unable (TRY only): provide reason, set work/candidate_id/use_record=null, "
    "and declared_sources=[]. Reasons do not replace actual use_record or evidence. "
)


def obj(**fields):
    return {"type": "object", "additionalProperties": False, "properties": fields,
            "required": list(fields)}


def nullable(schema):
    return {"anyOf": [schema, {"type": "null"}]}


def handles(values):
    return {"type": "string", "enum": sorted(values)} if values else {"not": {}}


class Contracts:
    decode = staticmethod(HandoffContracts.decode)

    def __init__(self, adapter):
        self.adapter = adapter

    def schema(self, stage, packet):
        refs = {r["ref"] for r in packet["REFERENCE_INDEX"]}
        work = obj(artifact=self.adapter.schema(), work_text=TEXT,
                   open_points={"type": "array", "items": TEXT})
        if stage in {"INITIAL", "DISCUSS"}:
            return work
        if stage == "OBSERVE":
            support = {"type": "array", "items": obj(ref=handles(refs), excerpt=TEXT)}
            offer = obj(target=handles(packet["TARGETS"]), knowledge=TEXT, support=support, proposed_use=TEXT)
            return obj(action={"enum": ["pass", "offer"]}, offer=nullable(offer))
        if stage in {"TRY", "FINALIZE"}:
            ids = {w["id"] for w in packet["CANDIDATES"]
                   if stage == "TRY" or w["deliverable_shape"]}
            actions = ["reuse", "new", "unable"] if stage == "TRY" else ["reuse", "new"]
            return obj(action={"enum": actions}, candidate_id=nullable(handles(ids)),
                       work=nullable(work), use_record=nullable(TEXT),
                       reason={**nullable(TEXT), "description": "Optional explanation for reuse/new; required for unable."},
                       declared_sources={"type": "array", "items": handles(refs),
                                         "description": "Cite directly accessible originals or visible public O/W carriers. Reported original IDs are not accessible merely because peers mention them; see SOURCE_ACCESS.",
                                         "uniqueItems": True, "maxItems": len(refs)})
        if stage in {"CHECK_USE", "CHECK_EFFECT", "FINAL_CHECK_USE", "FINAL_CHECK_EFFECT"}:
            return obj(finding={"enum": ["issue", "no_issue_found", "unable"]}, observation=TEXT, scope=TEXT)
        if stage in {"CHOOSE", "FINAL_CHOOSE"}:
            return obj(candidate_id=handles(packet["CHOICES"]), reason=TEXT)
        raise ProtocolError("INVALID_ACTION", f"Unknown workboard stage: {stage}")

    @staticmethod
    def validate_action(stage, value):
        if stage == "OBSERVE":
            if (value["action"] == "offer") != (value["offer"] is not None):
                raise ProtocolError("INVALID_ACTION", "offer requires content; pass requires null offer")
        if stage in {"TRY", "FINALIZE"}:
            action = value["action"]
            valid = ((action == "new" and value["work"] is not None and value["candidate_id"] is None
                      and value["use_record"] is not None)
                     or (action == "reuse" and value["candidate_id"] is not None and value["work"] is None
                         and value["use_record"] is not None)
                     or (stage == "TRY" and action == "unable" and value["work"] is None and value["candidate_id"] is None
                         and value["reason"] is not None and value["use_record"] is None
                         and not value["declared_sources"]))
            if not valid:
                raise ProtocolError("INVALID_ACTION", "Inconsistent action payload: " + ACTION_GUIDANCE)
