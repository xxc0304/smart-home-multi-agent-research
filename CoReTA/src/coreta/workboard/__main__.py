"""Explicit prepare/run entry; no evaluator or automatic live invocation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from . import PROTOCOL
from .artifacts import RankingAdapter
from .contracts import Contracts
from .gateway import Gateway, defaults
from .prompts import Prompts
from .runtime import Runner
from ..application_v2.inputs import Packets
from ..handoff.__main__ import PROJECT, DESIGN, DEFAULT_TOKENIZER, configure, load_counter
from ..handoff.gateway import Journal, write_json
from ..schemas import ProtocolError


def main():
    parser = argparse.ArgumentParser(description="Workboard v3 prototype; preparation does not run a task")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run"):
        command = commands.add_parser(name)
        command.add_argument("--pack", type=Path, required=True)
        command.add_argument("--condition", required=True)
        command.add_argument("--output", type=Path, required=True, help="New nonexistent directory")
        command.add_argument("--task-ordinal", type=int, default=1)
        command.add_argument("--config", type=Path, default=PROJECT / "config/deepseek_flash_inspection.json")
        command.add_argument("--tokenizer", type=Path, default=DEFAULT_TOKENIZER)
        if name == "run":
            command.add_argument("--live", action="store_true")
    args = parser.parse_args()
    try:
        if args.output.exists():
            parser.error("Output directory already exists")
        if args.task_ordinal < 0:
            parser.error("Task ordinal must be nonnegative")
        if args.command == "run" and (not args.live or not os.environ.get("DEEPSEEK_API_KEY")):
            parser.error("Live runs require --live and DEEPSEEK_API_KEY; no requests sent")
        packets = Packets(args.pack, args.condition)
        if len(packets.agents) < 3:
            parser.error("Main prototype requires at least three members; N=2 variant is not implemented")
        config, legacy = configure(args.config, DESIGN / "runtime.defaults.json")
        settings = defaults(len(packets.agents), legacy)
        adapter, counter = RankingAdapter(packets.task), load_counter(args.tokenizer)
        contracts, prompts = Contracts(adapter), Prompts()
        args.output.mkdir(parents=True, exist_ok=False)
        paths = list(Path(__file__).parent.glob("*.py")) + [
            PROJECT / "src/coreta/model_client.py", PROJECT / "src/coreta/schemas.py",
            PROJECT / "src/coreta/handoff/gateway.py", PROJECT / "src/coreta/handoff/contracts.py",
            PROJECT / "src/coreta/handoff/inputs.py", PROJECT / "src/coreta/handoff/__main__.py",
            PROJECT / "src/coreta/application_v2/inputs.py", args.config, args.tokenizer,
            DESIGN / "runtime.defaults.json"]
        write_json(args.output / "manifest.json", {
            "protocol": PROTOCOL, "mode": args.command, "task_id": packets.task["task_id"],
            "condition": args.condition, "member_packet_hashes": packets.hashes,
            "task_ordinal": args.task_ordinal, "editor": packets.agents[args.task_ordinal % len(packets.agents)],
            "started_at": datetime.now(timezone.utc).isoformat(), "configuration": config,
            "defaults": settings, "scoring_feedback": False, "baseline_comparison_ready": False,
            "input_count_mode": "local_tokenizer_estimate", "sampling_seed_sent": False,
            "model_revision_pinnable": False,
            "source_hashes": {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}})
        journal = Journal(args.output)
        gateway = Gateway(config, settings, contracts, prompts, journal, token_counter=counter)
        runner = Runner(packets, gateway, journal, adapter, task_ordinal=args.task_ordinal)
        if args.command == "prepare":
            for member in packets.agents:
                packet = runner.packet(member, "INITIAL")
                schema = contracts.schema("INITIAL", packet)
                prompt = prompts.render("INITIAL", packet, schema)
                payload = gateway.client.payload(prompt, schema, settings["max_output_tokens"]["initial"])
                size = gateway.client.size(payload)
                if size > config["generation"]["max_input_tokens"]:
                    raise ProtocolError("CONTEXT_OVERFLOW", "Initial request exceeds local context estimate")
                write_json(args.output / f"{member}.initial.input.json", packet)
                write_json(args.output / f"{member}.initial.schema.json", schema)
                write_json(args.output / f"{member}.initial.request.json", payload)
            write_json(args.output / "PREPARATION_ONLY.json", {"network_requests": 0, "solved": False,
                       "scope": "initial_packets_only_not_whole_protocol", "verified_service_compatibility": False})
            print(json.dumps({"prepared": str(args.output), "network_requests": 0}))
            return 0
        try:
            result = runner.run()
        except Exception as exc:
            runner.save_state()
            write_json(args.output / "implementation_error.json", {"type": type(exc).__name__, "message": str(exc)})
            raise
        print(json.dumps({key: result[key] for key in ("status", "stop_reason", "logical_calls", "http_attempts")}))
        return 0 if result["status"] == "completed" else 2
    except (ProtocolError, ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
