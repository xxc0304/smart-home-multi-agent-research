"""Offline, scripted later-stage payload sizing; never calls a remote model."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from coreta.handoff.__main__ import configure, load_counter, DEFAULT_TOKENIZER
from coreta.handoff.contracts import HandoffContracts
from coreta.handoff.gateway import Gateway, Journal
from coreta.handoff.inputs import Packets
from coreta.handoff.prompts import HandoffPrompts
from coreta.handoff.runtime import Runner

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "design/expertise-handoff/protocol-v1"
PACK = ROOT / "data/task-packs/moon-survival-v1"
COUNTER = load_counter()


def local_reply(value):
    return {"status": "completed", "output": [{"type": "message", "content": [
        {"type": "output_text", "text": json.dumps(value)}]}]}


def probe(condition, applications_per_turn, words_per_application, repair_stress=False):
    config, defaults = configure(ROOT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    packets = Packets(PACK, condition)
    names = [item["name"] for item in packets.task["items"]]
    contribution = {"items": [{
        "content": "reason " * 90, "support": "basis " * 12,
        "support_refs": ["T"], "conditions": ["Applies to the public task"],
        "needs": ["Confirm applicability if evidence changes"],
    } for _ in range(3)], "note": "Offline payload sizing fixture"}

    def req(number):
        return {"kind": "ask", "recipient": "A1", "target_refs": ["C1"],
                "question": f"Check a concrete dependency {number}", "impact": "May affect the order"}

    def apply(refs, request=None):
        return {"artifact": names, "applications": [{"refs": refs, "result": "applied " * words_per_application}
                for _ in range(applications_per_turn)], "excluded": [], "unresolved": [], "request": request}

    outputs = [copy.deepcopy(contribution) for _ in range(3)]
    outputs.append(apply(["C1", "C4", "C7"], req(1)))
    for index in range(3):
        outputs.append(copy.deepcopy(contribution))
        outputs.append(apply([f"C{10+3*index+j}" for j in range(3)], req(index + 2) if index < 2 else None))
    outputs.extend([
        {"verdict": "issue", "finding": "Fixture scope check", "target_refs": ["W4"], "check_suggestion": "Inspect applicability"},
        apply(["V1"]),
        {"verdict": "issue", "finding": "Fixture final objection", "target_refs": ["W5"], "check_suggestion": None},
        apply(["V2"]),
    ])
    if repair_stress:
        # Late schema failure near the output ceiling; preserve its full recovery input.
        bad = apply(["V2"])
        bad["artifact"] = "invalid " * 5000
        outputs.insert(len(outputs) - 1, bad)
    with tempfile.TemporaryDirectory(prefix="coreta-payload-fixture-") as temp:
        journal = Journal(Path(temp))
        seen = []
        def transport(payload, timeout):
            seen.append({"stage": journal.call_context["stage"], "member": journal.call_context["member"],
                         "estimated_input": gateway.client.size(payload)})
            if not outputs:
                raise AssertionError("Unexpected scripted sizing call")
            return local_reply(outputs.pop(0))
        gateway = Gateway(config, defaults, HandoffContracts(DESIGN / "message.schema.json"),
                          HandoffPrompts(DESIGN / "PROMPTS.md"), journal, transport=transport, token_counter=COUNTER)
        runner = Runner(packets, gateway, journal)
        with patch("urllib.request.urlopen", side_effect=AssertionError("Network forbidden in payload sizing")):
            result = runner.run("coreta")
        # A rejected payload is recorded before dispatch, so measure it explicitly from the last context.
        limit = config["generation"]["max_input_tokens"]
        peak = max((row["estimated_input"] for row in seen), default=0)
        return {"condition": condition, "applications_per_apply": applications_per_turn,
                "words_per_application": words_per_application,
                "approx_words_per_contribution_reply": 350,
                "expected_scripted_first_attempts": 14, "repair_stress": repair_stress,
                "expected_attempts_with_recovery": 15 if repair_stress else 14,
                "completed_attempts": len(seen), "format_repairs": result["format_repairs"],
                "status": result["status"], "stop_reason": result["stop_reason"],
                "peak_dispatched_input_estimate": peak, "configured_limit": limit,
                "count_mode": gateway.client.count_mode, "calls": seen,
                "all_script_consumed": not outputs, "real_model_calls": 0}


def main():
    parser = argparse.ArgumentParser(description="Offline representative and stress payload sizes")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reports = [probe(condition, applications, words) for condition in ("distributed_r0", "concentrated_A1")
               for applications, words in ((3, 40), (6, 100))]
    reports += [probe(condition, 6, 100, repair_stress=True)
                for condition in ("distributed_r0", "concentrated_A1")]
    # Ordinary discussion: three full answers and six substantial public turns.
    config, defaults = configure(ROOT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    for condition in ("distributed_r0", "concentrated_A1"):
        packets = Packets(PACK, condition)
        names = [i["name"] for i in packets.task["items"]]
        outputs = [{"ranking": names, "explanation": "reason " * 350} for _ in range(3)]
        outputs += [{"text": "discussion " * 350} for _ in range(6)]
        outputs += [{"ranking": names, "explanation": "Final fixture answer"}]
        with tempfile.TemporaryDirectory(prefix="coreta-discussion-payload-") as temp:
            journal, seen = Journal(Path(temp)), []
            def transport(payload, timeout):
                seen.append({"stage": journal.call_context["stage"], "estimated_input": gateway.client.size(payload)})
                return local_reply(outputs.pop(0))
            gateway = Gateway(config, defaults, HandoffContracts(DESIGN / "message.schema.json"),
                              HandoffPrompts(DESIGN / "PROMPTS.md"), journal, transport=transport, token_counter=COUNTER)
            with patch("urllib.request.urlopen", side_effect=AssertionError("Network forbidden")):
                result = Runner(packets, gateway, journal).run("ordinary_discussion")
            reports.append({"condition": condition, "system": "ordinary_discussion", "words_per_turn": 350,
                            "completed_attempts": len(seen), "status": result["status"], "stop_reason": result["stop_reason"],
                            "peak_dispatched_input_estimate": max(r["estimated_input"] for r in seen),
                            "configured_limit": config["generation"]["max_input_tokens"],
                            "count_mode": gateway.client.count_mode, "calls": seen, "real_model_calls": 0})
    document = {"kind": "offline_payload_sizing_not_capability_results", "real_model_calls": 0,
                "tokenizer_sha256": hashlib.sha256(DEFAULT_TOKENIZER.read_bytes()).hexdigest(),
                "profiles": reports, "note": "Representative sizes are fixtures, not measured model output distributions. Stress failures must remain visible."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2)
    print(json.dumps([{k: v for k, v in r.items() if k not in {"calls"}} for r in reports], ensure_ascii=False))


if __name__ == "__main__":
    main()
