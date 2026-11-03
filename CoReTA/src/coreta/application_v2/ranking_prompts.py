"""Adapt stage instructions before serializing task data; never replace in data."""
import json
from ..handoff.prompts import HandoffPrompts, COMMON, INDEPENDENT, FINAL


class RankingPrompts(HandoffPrompts):
    def __init__(self, path):
        super().__init__(path)
        self.templates["REVIEW"] = self.templates["REVIEW"].replace(
            "No survival simulator\nor external ranking check is available.",
            "No external reference ranking or scoring feedback is available.")

    def render(self, stage, packet, schema):
        n = len(packet["TASK"]["items"])
        if n == 15:
            return super().render(stage, packet, schema)
        if stage in {"INDEPENDENT", "FINAL"}:
            instruction = {"INDEPENDENT": INDEPENDENT, "FINAL": FINAL}[stage].replace("15 exact", f"{n} exact")
            instruction = instruction.replace("from most to least important", "from best to worst according to TASK")
            view = dict(packet)
            if stage == "INDEPENDENT":
                view.pop("DIRECTORY", None)
            return COMMON + "\n" + instruction + "\nMEMBER_PACKET_AND_PUBLIC_MESSAGES=" + json.dumps(view, ensure_ascii=False)
        return super().render(stage, packet, schema)
