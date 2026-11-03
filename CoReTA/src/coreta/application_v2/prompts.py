"""Four existing call types, with explicit application and handoff state."""
from __future__ import annotations

import json

from ..handoff.prompts import HandoffPrompts, COMMON
from .ranking_prompts import RankingPrompts

APPLY = """Advance the actual task. Applications track only an important cross-member use or
disputed step, not every thought. Return zero or one application update with target (an existing
U or null), task_step, bindings (visible ref plus its precise use), result, and missing. Give an
actual intermediate result/operation/decision; mark a necessary missing input/operation honestly.
A speculative complete ranking can coexist with an unresolved application. Existing knowledge,
derivation and manual calculation are allowed; do not pretend to execute tools.

For a reply, handle the original U named in its request: use its new C in a revision of that U,
partly apply it while retaining the real missing input, explicitly reject the unhelpful C, or
retire that U with a reason. Receipt or agreement does not resolve a dependency. Explain the
binding and any cleared missing input in result/binding.use; a valid counterexample needs no full
replacement, but a proposed replacement still needs task support. Doubt alone does not prove
the opposite ordering. Neither member identity nor source ownership proves a comparison.

artifact is an ordered array of all 15 exact public item names, each once, or null if not yet
available. artifact_uses lists existing U dependencies; the program associates your one new U
automatically and remaps a replaced U. Do not invent future U IDs. Preserve current associations
unless explicitly excluded or retired. retire_applications is at most one ref/reason; retiring a
use does not delete its source C. Historical/obsolete U can be discussed but not bound as current
inputs. Do not use a replaced U or its affected descendants to justify its replacement.
If APPLICATION_FOCUS is present, update, retire or explicitly exclude that U before unrelated
changes. Excluding it does not repair downstream uses that still depend on it.
Visible W/Q/V may be bound as conversation context. Dependency propagation follows only direct
U bindings; list each actual tracked U input explicitly instead of relying on an indirect W/Q/V/C
reference. If an accepted review targets one current U, update or retire that same application;
otherwise explicitly reject the review. Excluding a U from the candidate alone does not retire
its path or free the single explicit-missing slot.

Use excluded for precise rejections and unresolved for consequential unknowns. Do not force a
request or change just to demonstrate collaboration. When a concrete available fact/check would
distinguish alternatives, request it within ALLOWED_REQUEST_KINDS and target one U or the sources
of your newly proposed application. Otherwise keep limitations and submit the best candidate.
No extra role, vote or repeated general endorsement certifies correctness. Keep reasoning local.
"""


class ApplicationPrompts:
    def __init__(self, path):
        self.base = HandoffPrompts(path)
        self.ranking_base = RankingPrompts(path)

    def render(self, stage, packet, schema):
        if stage == "APPLY":
            n = len(packet["TASK"]["items"])
            instruction = APPLY if n == 15 else APPLY.replace("all 15 exact", f"all {n} exact")
            return COMMON + "\n" + instruction + "\nMEMBER_PACKET=" + json.dumps(packet, ensure_ascii=False)
        renderer = self.base if len(packet["TASK"]["items"]) == 15 else self.ranking_base
        original = renderer.render(stage, packet, schema)
        if stage in {"REPLY", "REVIEW"}:
            original += ("\nAPPLICATION_STATE=" + json.dumps(packet.get("APPLICATION_STATE"), ensure_ascii=False)
                         + "\nCheck the concrete use, input binding and result when relevant. U states are bookkeeping, "
                           "not truth labels. Acknowledge inability when no discriminating check is possible. "
                           "You may cite visible U in the reference index; do not assume another member's private raw material is accessible.")
        return original
