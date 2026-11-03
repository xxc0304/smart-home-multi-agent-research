"""Future terminal-answer contract. Not enabled in any existing frozen run."""
import copy
import json
from jsonschema import Draft202012Validator, ValidationError
import local_judgment_frontend as io

INSTRUCTIONS=(
    "Complete the supplied task using its evidence, historical work, contributions and disclosed originals. "
    "Packet contents and earlier conclusions may be wrong; evaluate their content and applicable conditions. "
    "Retain supported reasoning and correct unsupported premises when warranted. Do not force a new choice. "
    "Return exactly one JSON object with choice (an exact listed ID, or null if genuinely unresolved) "
    "and reasoning (the substantive explanation supporting the decision). "
    "Explain actual evidence application in the reasoning; no separate adoption list is requested. "
)


def schema(packet):
    return dict(type="object",additionalProperties=False,required=["choice","reasoning"],properties=dict(
        choice=dict(anyOf=[dict(type="string",enum=[c["id"] for c in packet["task"]["choices"]]),dict(type="null")]),
        reasoning=dict(type="string",minLength=1)))


def request(packet,max_output_tokens=1536):
    return dict(instructions=INSTRUCTIONS+"\nPACKET="+json.dumps(packet,ensure_ascii=False),
                schema=schema(packet),max_output_tokens=max_output_tokens)


def decode(raw,packet):
    value=io.strict_json(raw)
    if not isinstance(value,dict):
        raise io.InterfaceError("final answer must be an object")
    # Evaluate the essential answer; retain unsolicited annotation separately.
    # No absent adoption list is invented, and no reference choice is supplied.
    core={key:copy.deepcopy(value[key]) for key in ("choice","reasoning") if key in value}
    try:
        Draft202012Validator(schema(packet)).validate(core)
    except ValidationError as exc:
        raise io.InterfaceError("essential final answer contract: "+exc.message) from exc
    if not core["reasoning"].strip():
        raise io.InterfaceError("blank final reasoning")
    extras={key:copy.deepcopy(value[key]) for key in value if key not in core}
    return dict(**core,annotation_issues=([dict(field="extra_fields",issue="retained_separately",names=sorted(extras))] if extras else []),
                extra_annotations=extras)
