"""Independent v2 prepare/run/score entry; no API request without explicit --live."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from ..handoff.__main__ import configure, load_counter, DEFAULT_TOKENIZER, DEFAULT_PACK, DESIGN, PROJECT
from ..handoff.gateway import Gateway, Journal, write_json
from .inputs import Packets, read_json
from ..schemas import ProtocolError
from .contracts import ApplicationContracts
from .prompts import ApplicationPrompts
from .runtime import ApplicationRunner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run"):
        command = commands.add_parser(name)
        command.add_argument("--pack", type=Path, default=DEFAULT_PACK)
        command.add_argument("--condition", default="distributed_r0")
        command.add_argument("--task-ordinal", type=int, default=1)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--live", action="store_true")
        command.add_argument("--system", choices=("coreta", "ordinary_discussion", "independent"), default="coreta")
        command.add_argument("--member", help="Only this member answers in independent calibration")
    scoring = commands.add_parser("score")
    scoring.add_argument("--run", type=Path, required=True)
    scoring.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    scoring.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            parser.error("Output already exists")
        if args.command == "score":
            from .ranking import score_run
            result = read_json(args.run / "result.json")
            if result["protocol"] not in {"coreta/application-v2", "coreta/ranking-baseline-v2"}:
                parser.error("Expected a v2 result")
            report = score_run(args.pack, result)
            report["result_sha256"] = hashlib.sha256((args.run / "result.json").read_bytes()).hexdigest()
            report["evaluator_sha256"] = hashlib.sha256((args.pack / "offline/evaluator.json").read_bytes()).hexdigest()
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                json.dump(report, stream, ensure_ascii=False, indent=2)
            print(json.dumps({"score_file": str(args.output)}))
            return 0
        if args.command == "run" and (not args.live or not os.environ.get("DEEPSEEK_API_KEY")):
            parser.error("Real runs require --live and configured DEEPSEEK_API_KEY")
        if args.task_ordinal < 0:
            parser.error("Task ordinal must be nonnegative")
        config, defaults = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
        packets = Packets(args.pack, args.condition)
        if args.member and (args.system != "independent" or args.member not in packets.agents):
            parser.error("--member requires independent and a member of the task roster")
        if args.member:
            defaults["limits"]["max_network_attempts_total"] = 4
        counter = load_counter()
        contracts, prompts = ApplicationContracts(DESIGN / "message.schema.json"), ApplicationPrompts(DESIGN / "PROMPTS.md")
        args.output.mkdir(parents=True, exist_ok=False)
        paths = list(Path(__file__).parent.glob("*.py")) + list((PROJECT / "src/coreta/handoff").glob("*.py"))
        paths += [PROJECT / "src/coreta/model_client.py", DESIGN / "message.schema.json", DESIGN / "PROMPTS.md",
                  DESIGN / "runtime.defaults.json", PROJECT / "config/deepseek_flash_inspection.json", DEFAULT_TOKENIZER]
        write_json(args.output / "manifest.json", {
            "protocol": "coreta/application-v2" if args.system == "coreta" else "coreta/ranking-baseline-v2",
            "system": args.system, "selected_member": args.member, "item_count": len(packets.task["items"]),
            "mode": args.command, "started_at": datetime.now(timezone.utc).isoformat(),
            "condition": args.condition, "task_id": packets.task["task_id"], "task_ordinal": args.task_ordinal,
            "driver": packets.agents[args.task_ordinal % len(packets.agents)], "configuration": config,
            "limits": defaults, "member_packet_hashes": packets.hashes, "sampling_seed_sent": False,
            "source_hashes": {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            "input_count_mode": "local_tokenizer_estimate", "scoring_feedback": False})
        if args.command == "prepare":
            stage = "CONTRIBUTE" if args.system == "coreta" else "INDEPENDENT"
            for agent in ([args.member] if args.member else packets.agents):
                packet = packets.member(agent)
                schema = contracts.schema(stage, {r["ref"] for r in packet["REFERENCE_INDEX"]}, packets.agents, [],
                                          ranking_items=[i["name"] for i in packets.task["items"]])
                write_json(args.output / f"{agent}.input.json", packet)
                write_json(args.output / f"{agent}.schema.json", schema)
                (args.output / f"{agent}.prompt.txt").write_text(prompts.render(stage, packet, schema), encoding="utf-8")
            write_json(args.output / "PREPARATION_ONLY.json", {"network_requests": 0, "initial_stage_only": True, "initial_stage": stage})
            print(json.dumps({"prepared": str(args.output), "network_requests": 0}))
            return 0
        journal = Journal(args.output)
        gateway = Gateway(config, defaults, contracts, prompts, journal, token_counter=counter)
        runner = ApplicationRunner(packets, gateway, journal, task_ordinal=args.task_ordinal)
        runner.selected_member = args.member
        try:
            result = runner.run(args.system)
        except BaseException as exc:
            runner.save_state()
            write_json(args.output / "implementation_or_interruption.json", {"type": type(exc).__name__})
            raise
        print(json.dumps({k: result[k] for k in ("protocol", "status", "stop_reason", "http_attempts")}))
        return 2 if result["status"] in {"protocol_failure", "budget_exhausted"} else 0
    except (ValueError, OSError, ProtocolError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
