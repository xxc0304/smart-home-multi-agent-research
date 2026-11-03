"""Independent CLI for local-contribution development runs and offline scoring."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..schemas import ProtocolError
from .contracts import HandoffContracts
from .gateway import Gateway, Journal, write_json
from .inputs import Packets, read_json
from .prompts import HandoffPrompts
from .runtime import Runner

PROJECT = Path(__file__).resolve().parents[3]
DEFAULT_PACK = PROJECT / "data/task-packs/moon-survival-v1"
DESIGN = PROJECT / "design/expertise-handoff/protocol-v1"
SYSTEMS = ("coreta", "ordinary_discussion", "independent")
DEFAULT_TOKENIZER = PROJECT / "data/tokenizer-v4.1-flash-1017/tokenizer.json"


def load_counter(path=DEFAULT_TOKENIZER):
    """Pinned local estimate, not a claim of exact server-side token accounting."""
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file(str(path))
    return lambda value: len(tokenizer.encode(value, add_special_tokens=False).ids)


def configure(config_path, defaults_path):
    config, defaults = read_json(config_path), read_json(defaults_path)
    if (config.get("provider") != "deepseek" or config.get("base_url") != "https://api.deepseek.com"
            or config.get("model") != "deepseek-flash" or config.get("api_key_env") != "DEEPSEEK_API_KEY"):
        raise ProtocolError("INPUT_ERROR", "Use the previously approved official DeepSeek model configuration")
    limits = defaults["limits"]
    required = {"max_interventions", "max_final_reviews", "max_network_attempts_total",
                "format_retries_per_stage", "transport_retries_per_request",
                "request_timeout_seconds", "task_timeout_seconds",
                "max_initial_items_per_agent", "max_reply_items"}
    if set(limits) != required or any(type(value) is not int or value < 0 for value in limits.values()):
        raise ProtocolError("INPUT_ERROR", "Invalid protocol limits")
    if (limits["max_network_attempts_total"] < 1 or limits["max_final_reviews"] < 1
            or limits["request_timeout_seconds"] < 1 or limits["task_timeout_seconds"] < 1
            or limits["format_retries_per_stage"] > 1 or limits["transport_retries_per_request"] > 1
            or limits["max_initial_items_per_agent"] != 3 or limits["max_reply_items"] != 3
            or defaults.get("runtime_tools") != []):
        raise ProtocolError("INPUT_ERROR", "Unsupported first-version limits/tools")
    if set(defaults["max_output_tokens"]) != {"contribute", "apply", "reply", "review"} or any(
            type(v) is not int or v <= 0 for v in defaults["max_output_tokens"].values()):
        raise ProtocolError("INPUT_ERROR", "Invalid stage output budgets")
    generation = config["generation"]
    if (type(generation["max_input_tokens"]) is not int or generation["max_input_tokens"] < 1
            or type(generation["temperature"]) not in (int, float)
            or not math.isfinite(generation["temperature"]) or not 0 <= generation["temperature"] <= 2
            or generation["reasoning_effort"] != "none"):
        raise ProtocolError("INPUT_ERROR", "Invalid generation limits")
    # Pass only recognized transport configuration to the client and manifest.
    safe = {key: config[key] for key in ("provider", "base_url", "model", "api_key_env")}
    safe["generation"] = {key: copy.deepcopy(generation[key]) for key in
                          ("reasoning_effort", "temperature", "max_input_tokens")}
    return safe, defaults


def main():
    parser = argparse.ArgumentParser(description="CoReTA local contributions: prepare inputs, explicit live run, separate offline score")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run"):
        command = commands.add_parser(name)
        command.add_argument("--pack", type=Path, default=DEFAULT_PACK)
        command.add_argument("--condition", default="distributed_r0")
        command.add_argument("--system", choices=SYSTEMS, default="coreta")
        command.add_argument("--config", type=Path, default=PROJECT / "config/deepseek_flash_inspection.json")
        command.add_argument("--defaults", type=Path, default=DESIGN / "runtime.defaults.json")
        command.add_argument("--task-ordinal", type=int, default=1)
        command.add_argument("--output", type=Path, required=True, help="A new nonexistent output directory")
        command.add_argument("--tokenizer", type=Path, default=DEFAULT_TOKENIZER,
                             help="Local tokenizer estimate; defaults to the project's pinned DeepSeek asset")
        if name == "run":
            command.add_argument("--live", action="store_true", help="Send real API requests")
            command.add_argument("--seed", type=int, default=17, help="Logical log identifier; not sent as sampling seed")
    score = commands.add_parser("score")
    score.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    score.add_argument("--run", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True, help="New separate score JSON file")
    args = parser.parse_args()
    try:
        if args.command == "score":
            from .ranking import score_run
            if args.output.exists():
                parser.error("Score output already exists")
            result = read_json(args.run / "result.json")
            report = score_run(args.pack.resolve(), result)
            report["result_sha256"] = hashlib.sha256((args.run / "result.json").read_bytes()).hexdigest()
            report["evaluator_sha256"] = hashlib.sha256((args.pack / "offline/evaluator.json").read_bytes()).hexdigest()
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            print(json.dumps({"score_file": str(args.output), "system": report["system"]}))
            return
        if args.command == "run" and not args.live:
            parser.error("No requests sent. Use prepare for static inputs, or explicit --live to run.")
        if args.command == "run" and not os.environ.get("DEEPSEEK_API_KEY"):
            parser.error("DEEPSEEK_API_KEY is not configured; no run directory created")
        if args.task_ordinal < 0:
            parser.error("Task ordinal must be nonnegative")
        if args.output.exists():
            parser.error("Output directory already exists")
        packets = Packets(args.pack, args.condition)
        config, defaults = configure(args.config, args.defaults)
        contracts = HandoffContracts(DESIGN / "message.schema.json")
        prompts = HandoffPrompts(DESIGN / "PROMPTS.md")
        token_counter = load_counter(args.tokenizer)
        args.output.mkdir(parents=True, exist_ok=False)
        source_paths = [DESIGN / "PROMPTS.md", DESIGN / "message.schema.json", args.config,
                        args.defaults, PROJECT / "data/task-packs/moon-survival-v1/PROMPT_ADAPTATION.md",
                        PROJECT / "src/coreta/model_client.py", PROJECT / "src/coreta/schemas.py"]
        source_paths += sorted(Path(__file__).parent.glob("*.py"))
        manifest = {
            "started_at": datetime.now(timezone.utc).isoformat(), "system": args.system,
            "condition": args.condition, "task_id": packets.task["task_id"],
            "task_ordinal": args.task_ordinal,
            "driver": packets.agents[args.task_ordinal % len(packets.agents)],
            "mode": args.command, "member_packet_hashes": packets.hashes,
            "configuration": config, "protocol_limits": defaults,
            "source_hashes": {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths},
            "scoring_feedback": False, "sampling_seed_sent": False,
            "logical_seed": getattr(args, "seed", None),
            "tokenizer_sha256": hashlib.sha256(args.tokenizer.read_bytes()).hexdigest() if getattr(args, "tokenizer", None) else None,
            "input_count_mode": "local_tokenizer_estimate" if token_counter else "conservative_utf8_bytes",
            "model_revision_pinnable": False,
        }
        write_json(args.output / "manifest.json", manifest)
        if args.command == "prepare":
            stage = "CONTRIBUTE" if args.system == "coreta" else "INDEPENDENT"
            for agent in packets.agents:
                packet = packets.member(agent)
                schema = contracts.schema(stage, {r["ref"] for r in packet["REFERENCE_INDEX"]}, packets.agents, [],
                                          ranking_items=[i["name"] for i in packet["TASK"]["items"]])
                write_json(args.output / f"{agent}.input.json", packet)
                write_json(args.output / f"{agent}.schema.json", schema)
                (args.output / f"{agent}.prompt.txt").write_text(prompts.render(stage, packet, schema), encoding="utf-8")
            write_json(args.output / "PREPARATION_ONLY.json", {"network_requests": 0, "solved": False,
                       "stage": stage, "note": "Only initial stage rendered; not an end-to-end run"})
            print(json.dumps({"prepared": str(args.output), "members": packets.agents, "network_requests": 0}))
            return
        journal = Journal(args.output)
        gateway = Gateway(config, defaults, contracts, prompts, journal,
                          token_counter=token_counter, seed=args.seed)
        runner = Runner(packets, gateway, journal, task_ordinal=args.task_ordinal)
        try:
            result = runner.run(args.system)
        except Exception as exc:
            runner.save_state()
            write_json(args.output / "implementation_error.json", {"type": type(exc).__name__, "message": str(exc)})
            raise
        print(json.dumps({key: result[key] for key in
                         ("system", "status", "stop_reason", "http_attempts", "logical_calls")}, ensure_ascii=False))
        if result["status"] in {"protocol_failure", "budget_exhausted"}:
            sys.exit(2)
    except (ProtocolError, ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
