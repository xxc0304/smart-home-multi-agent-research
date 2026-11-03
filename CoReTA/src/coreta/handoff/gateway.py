"""Bounded calls around the existing transport, including its internal retries."""
from __future__ import annotations

import copy
import json
import time
from pathlib import Path

from ..model_client import DeepSeekClient
from ..schemas import ProtocolError
from .contracts import HandoffContracts


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class Journal:
    def __init__(self, root):
        self.root = root
        self.calls = 0
        self.completed = 0
        self.repairs = 0
        self.usage = []
        self.uncertain_attempts = 0
        self.call_context = {}

    def log(self, filename, value):
        if filename == "responses.jsonl":
            if value.get("uncertain_usage"):
                self.uncertain_attempts += 1
            usage = value.get("response", {}).get("usage")
            if isinstance(usage, dict):
                self.usage.append(usage)
        with (self.root / filename).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"call_context": self.call_context, **value}, ensure_ascii=False) + "\n")


class Gateway:
    def __init__(self, config, defaults, contracts, prompts, journal, *, transport=None, token_counter=None, seed=17):
        self.limits = defaults["limits"]
        self.outputs = defaults["max_output_tokens"]
        self.config = copy.deepcopy(config)
        self.config["protocol"] = {
            "transport_retries_per_request": self.limits["transport_retries_per_request"],
            "request_timeout_seconds": self.limits["request_timeout_seconds"],
        }
        self.client = DeepSeekClient(self.config, journal.log, transport=transport, token_counter=token_counter)
        self.contracts, self.prompts, self.journal, self.seed = contracts, prompts, journal, seed
        self.deadline = time.monotonic() + self.limits["task_timeout_seconds"]

    @property
    def remaining(self):
        return self.limits["max_network_attempts_total"] - self.client.attempts

    def require(self, slots=1):
        if time.monotonic() >= self.deadline:
            raise ProtocolError("MODEL_TIMEOUT", "Task deadline exhausted")
        if self.remaining < slots:
            raise ProtocolError("ATTEMPT_BUDGET", f"Not enough network attempts for {slots} first calls")

    def call(self, stage, member, packet, allowed=(), check=None):
        self.require()
        refs = {row["ref"] for row in packet["REFERENCE_INDEX"]}
        schema = self.contracts.schema(stage, refs, packet["SELF"]["team"], allowed,
                                       ranking_items=[i["name"] for i in packet["TASK"]["items"]])
        instruction = self.prompts.render(stage, packet, schema)
        self.journal.calls += 1
        self.journal.call_context = {"logical_call": self.journal.calls, "stage": stage, "member": member}
        cap = self.outputs.get(stage.lower(), self.outputs["apply"] if stage == "FINAL" else self.outputs["contribute"])
        original_instruction = instruction
        for repair in range(self.limits["format_retries_per_stage"] + 1):
            self.require()
            # Prevent the existing transport's internal retry from exceeding the task cap.
            self.config["protocol"]["transport_retries_per_request"] = min(
                self.limits["transport_retries_per_request"], self.remaining - 1)
            payload = self.client.payload(instruction, schema, cap)
            raw = None
            try:
                raw = self.client.complete(payload, deadline=self.deadline, logical_seed=self.seed)
                value = HandoffContracts.decode(raw, schema)
                if check is not None:
                    check(value)
                self.journal.completed += 1
                self.journal.log("stages.jsonl", {"stage": stage, "member": member,
                                                 "repair": repair, "output": value})
                return value
            except ProtocolError as exc:
                self.journal.log("stage_errors.jsonl", {"stage": stage, "code": exc.code,
                                                       "detail": exc.detail, "repair": repair})
                if exc.code not in {"SCHEMA_ERROR", "REFERENCE_ERROR", "INVALID_ACTION"} or repair >= self.limits["format_retries_per_stage"]:
                    raise
                self.journal.repairs += 1
                instruction = (original_instruction + "\nFORMAT_RECOVERY=" + json.dumps({
                    "previous_output": raw, "error": exc.detail,
                    "instruction": "Repair only the precise JSON/schema/reference/action error. Preserve substantive reasoning. Do not invent evidence or alter conclusions just to finish.",
                }, ensure_ascii=False))
        raise AssertionError("Unreachable format-recovery exit")
