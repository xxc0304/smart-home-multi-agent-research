"""Targeted follow-through without new judge roles or mandatory disagreement."""
from ..workboard.prompts import Prompts as BasePrompts


GUIDANCE = (
    "D0 FOCUS is a pending question, not an authoritative defect. FOCUS_FEEDBACK carries related "
    "historical checks and use records. FOCUS_HISTORY and its refs are "
    "public reports, not direct original-source access. Read author and version identities carefully. "
    "Recheck whether the question still applies after the work changed. A quote may be reported "
    "accurately or inaccurately; no host quote authentication is provided. Distinguish supplied "
    "observations, your reasoning and planned checks. Agreement, citations and addressed status "
    "do not certify truth. Never invent a disagreement just to fill a field. "
)

STAGE_GUIDANCE = {
    "OBSERVE": "You may answer a focus with available evidence, a conditional calculation or a valid "
               "counterexample, or offer more important help. Set offer.responds_to to its focus ID "
               "only when actually responding, otherwise null. Use ordinary support/proposed_use. "
               "Identify what result distinguishes the disputed claims, or explain the limit. Passing is allowed.",
    "TRY": "Read FOCUS and APPLICATION_FEEDBACK alongside the selected contribution. Actually revise "
           "the affected step or reuse an existing artifact; in use_record say which question you "
           "handled, what evidence/result you used and what changed downstream. Keep independently "
           "supported contributions. A rebuttal or check is not automatically a complete repair.",
    "CHECK_USE": "Check the actual interpretation and application of any focus response. You may "
                 "withdraw your prior claim. A report of completing a check is not its proof.",
    "CHECK_EFFECT": "Examine the actual consequence of any focus response, including whether its "
                    "proposed check really distinguishes the competing interpretations. Critiques can be wrong.",
    "CHOOSE": "Choose an existing version, then report focus_disposition for the input FOCUS or null "
              "if not assessed. addressed only reports your conclusion with reasons. Set next_check "
              "to one consequential, still-unclear question and a feasible check, or null. Existing "
              "visible evidence can settle a question without another cycle. Do not prefer old work "
              "automatically. The host may have no next-cycle budget; never claim a future check happened.",
    "FINALIZE": "Consider pending/deferred focuses, their responses and actual versions in your "
                "best-effort assembly. Do not fabricate verification or drop useful independent knowledge.",
    "FINAL_CHOOSE": "Report focus_disposition for the input FOCUS or null. You cannot schedule another "
                    "check or generate a new repair. Unresolved questions remain unresolved at delivery.",
}


class Prompts(BasePrompts):
    def render(self, stage, packet, schema):
        text = super().render(stage, packet, schema)
        if stage == "INITIAL":
            return text
        # Keep the established PACKET/OUTPUT_SCHEMA envelope for transports and audit tools.
        prefix, body = text.split("\nPACKET=", 1)
        return prefix + "\n" + GUIDANCE + STAGE_GUIDANCE.get(stage, "") + "\nPACKET=" + body
