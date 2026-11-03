"""Load versioned stage text from the design instead of duplicating instructions."""
from __future__ import annotations

import json
import re
from pathlib import Path


class Prompts:
    def __init__(self, path: Path):
        text = path.read_text(encoding="utf-8")
        self.blocks = re.findall(r"```text\s*\n(.*?)```", text, re.S)
        if len(self.blocks) != 8:
            raise ValueError("Expected eight versioned prompt blocks; review template mapping")
        self.system = self.blocks[0].strip()
        self.mapping = {"draft": 1, "review": 2, "lead_update": 3,
                        "contribution": 4, "final": 5, "no_application": 6, "repair": 7}

    def render(self, stage, values):
        text = self.blocks[self.mapping[stage]]
        for key, value in values.items():
            encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            text = text.replace("{{" + key + "}}", encoded)
        if re.search(r"\{\{\w+\}\}", text):
            raise ValueError(f"Unfilled prompt variables in {stage}")
        return text.strip()

    def instructions(self, stage, values, visible):
        return self.system + "\n\n" + self.render(stage, values) + "\nREFERENCE_INDEX=" + json.dumps(visible)


BASELINE_INSTRUCTIONS = {
    "solo_refine": "Re-examine this candidate against the task. Correct mistakes or complete missing parts and return an updated Candidate. You may keep the answer if justified.",
    "static_debate": "Consider the other candidates as additional arguments. Identify concrete agreements or disagreements, then produce your best updated Candidate. You may repair the reasoning or develop a new solution.",
}
