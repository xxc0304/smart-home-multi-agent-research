"""Common compact decision handoff for both local diagnostic conditions."""


class CompactChoicePrompts:
    def __init__(self, base):
        self.base = base

    def render(self, stage, packet, schema):
        text = self.base.render(stage, packet, schema)
        if stage != "CHOOSE":
            return text
        prefix, body = text.split("\nPACKET=", 1)
        return (prefix + "\nDecision handoff budget: the ENTIRE JSON must fit 512 output tokens. "
                "Keep reason within 80 English words: decisive evidence/conflict and limits only; "
                "do not retell the task, all candidates or the entire reasoning. When present, "
                "next_check.question and next_check.check each use at most 30 words, and "
                "focus_disposition.reason at most 30 words. Use exact IDs. Return the complete "
                "JSON including nullable fields; do not trade missing fields for a long explanation.\nPACKET=" + body)
