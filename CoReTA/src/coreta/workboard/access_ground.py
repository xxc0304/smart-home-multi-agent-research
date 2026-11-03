"""Permission-clarified comparator; no structured issue ledger or extra calls."""
from .grounded import GroundRunner, GroundPrompts
from .issue_loop import (CHECK_STAGES, ACCESS_GUIDANCE, WORK_VIEW_GUIDANCE,
                         attach_access_context, deduplicate_work_views)
from .runtime import Runner
from ..handoff.gateway import write_json


VARIANT = "ground_access_only_v2"


class AccessPrompts(GroundPrompts):
    def render(self, stage, packet, schema):
        return WORK_VIEW_GUIDANCE + (ACCESS_GUIDANCE if stage in CHECK_STAGES else "") + super().render(stage, packet, schema)


class AccessRunner(GroundRunner):
    def packet(self, member, stage, **extra):
        packet = super().packet(member, stage, **extra)
        packet["METHOD_VARIANT"] = VARIANT
        if stage in CHECK_STAGES:
            attach_access_context(packet, self.editor, {
                agent: {"T", *(m["ref"] for m in self.packets.member(agent)["SELF_MATERIALS"])}
                for agent in self.agents})
        return deduplicate_work_views(packet)

    def ground_packet(self, offer):
        packet = super().ground_packet(offer)
        packet["METHOD_VARIANT"] = VARIANT
        return packet

    def save_state(self):
        Runner.save_state(self)
        write_json(self.journal.root / "method_variant.json", {"variant": VARIANT,
            "ordinary_cycle": "observe_peers,ground,try,check_use,choose",
            "finalization": "unchanged_two_checks", "truth_status": "not_certified"})

    def run(self):
        result = Runner.run(self)
        result["method_variant"] = VARIANT
        write_json(self.journal.root / "result.json", result)
        return result
