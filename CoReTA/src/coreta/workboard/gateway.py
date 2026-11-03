"""Reuse the existing client and journal with workboard-specific stage contracts."""
import hashlib

from ..handoff.gateway import Gateway as ExistingGateway
from ..schemas import ProtocolError


def defaults(member_count, legacy):
    limits = {**{k: legacy["limits"][k] for k in ("request_timeout_seconds", "task_timeout_seconds")},
              "max_network_attempts_total":
              member_count + (member_count - 1) * (member_count + 3) + 4,
              "format_retries_per_stage": 0, "transport_retries_per_request": 0}
    outputs = {stage: cap for stage, cap in (
        ("initial", 4096), ("observe", 2048), ("try", 4096), ("check_use", 3072),
        ("check_effect", 3072), ("choose", 512), ("finalize", 4096),
        ("final_check_use", 3072), ("final_check_effect", 3072), ("final_choose", 512))}
    return {"limits": limits, "max_output_tokens": outputs, "runtime_tools": [],
            "cycle_limit": member_count - 1, "budget_status": "development_not_experiment_frozen"}


class Gateway(ExistingGateway):
    def output_used(self):
        values = [u.get("output_tokens") for u in self.journal.usage]
        if any(type(v) is not int or v < 0 for v in values):
            raise ProtocolError("USAGE_UNKNOWN", "Cannot account for output-token budget")
        return sum(values)

    def call(self, stage, member, packet):
        self.require()
        schema = self.contracts.schema(stage, packet)
        instructions = self.prompts.render(stage, packet, schema)
        self.journal.calls += 1
        self.journal.call_context = {"logical_call": self.journal.calls, "stage": stage, "member": member}
        cap = self.outputs[stage.lower()]
        total_cap = self.limits.get("max_output_tokens_total")
        if total_cap is not None and self.output_used() + cap > total_cap:
            raise ProtocolError("OUTPUT_BUDGET", "Cannot reserve the stage output cap within total budget")
        payload = self.client.payload(instructions, schema, cap)
        repairs = []
        repair_recorded = False

        def record_repairs(raw):
            nonlocal repair_recorded
            if repairs and not repair_recorded:
                self.journal.repairs += len(repairs)
                self.journal.log("format_repairs.jsonl", {
                    "stage": stage, "kind": "identical_duplicate_keys_collapsed",
                    "keys": repairs, "raw_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                    "policy": "collapse_only_exactly_equal_duplicate_values",
                })
                repair_recorded = True

        raw = None
        try:
            raw = self.client.complete(payload, deadline=self.deadline, logical_seed=self.seed)
            value = self.contracts.decode(raw, schema, allow_identical_duplicate_keys=True,
                                           format_repairs=repairs)
            record_repairs(raw)
            self.contracts.validate_action(stage, value)
            if total_cap is not None:
                if len(self.journal.usage) != self.client.attempts:
                    raise ProtocolError("USAGE_UNKNOWN", "Missing usage for a real network attempt")
                if any(type(u.get("input_tokens")) is not int or u["input_tokens"] < 0
                       for u in self.journal.usage):
                    raise ProtocolError("USAGE_UNKNOWN", "Missing input-token accounting")
                if self.output_used() > total_cap:
                    raise ProtocolError("OUTPUT_BUDGET", "Server output exceeds total token budget")
        except ProtocolError as exc:
            if raw is not None:
                record_repairs(raw)
            self.journal.log("stage_errors.jsonl", {"stage": stage, "code": exc.code,
                                                   "detail": exc.detail, "repair": len(repairs)})
            raise
        self.journal.completed += 1
        self.journal.log("stages.jsonl", {"stage": stage, "member": member,
                                          "repair": len(repairs), "output": value})
        return value
