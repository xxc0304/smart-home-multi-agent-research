"""Offline stage replay only. Scripted fixtures never count as model experiments."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

from ..application_v2.inputs import Packets
from ..handoff.__main__ import PROJECT, DESIGN, configure, load_counter
from ..handoff.gateway import Journal, write_json
from ..schemas import ProtocolError
from ..workboard.artifacts import RankingAdapter, ChoiceAdapter
from ..workboard.choice_inputs import ChoicePackets
from ..workboard.gateway import Gateway, defaults
from .contracts import Contracts
from .prompts import Prompts
from .runtime import Runner


class ReplayTransport:
    def __init__(self, rows):
        self.rows, self.cursor = rows, 0

    def __call__(self, payload, timeout):
        packet = json.loads(payload["instructions"].split("\nPACKET=", 1)[1].split("\nOUTPUT_SCHEMA=", 1)[0])
        if self.cursor >= len(self.rows):
            raise ProtocolError("REPLAY_MISMATCH", "Script has no response for this stage")
        row = self.rows[self.cursor]
        self.cursor += 1
        if (row["stage"], row["member"]) != (packet["STAGE"], packet["SELF"]["agent_id"]):
            raise ProtocolError("REPLAY_MISMATCH", "Script stage/member differs from actual invocation")
        value = row["output"]
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        return {"status": "completed", "usage": {"input_tokens": 1, "output_tokens": 1},
                "fixture_only": True,
                "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}


def replay(pack, condition, task_type, script, output, ordinal=1):
    rows = json.loads(Path(script).read_text(encoding="utf-8"))
    packets = (ChoicePackets if task_type == "choice" else Packets)(Path(pack), condition)
    adapter = ChoiceAdapter(packets.task) if task_type == "choice" else RankingAdapter(packets.task)
    config, legacy = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    journal = Journal(output)
    transport = ReplayTransport(rows)
    gateway = Gateway(config, defaults(len(packets.agents), legacy), Contracts(adapter), Prompts(), journal,
                      transport=transport, token_counter=load_counter())
    runner = Runner(packets, gateway, journal, adapter, task_ordinal=ordinal)
    with patch("urllib.request.urlopen", side_effect=AssertionError("Offline D0 replay forbids network")):
        result = runner.run()
    mismatch = result["error"] or ({"code": "REPLAY_UNUSED", "detail": "Script contains unused responses"}
                                    if transport.cursor != len(rows) else None)
    replay_meta = {"execution_mode": "scripted_engineering_only", "actual_http_attempts": 0,
                   "scripted_transport_attempts": result["http_attempts"], "fixture_usage_not_billable": True,
                   "consumed_responses": transport.cursor, "provided_responses": len(rows),
                   "error": mismatch, "replay_complete": mismatch is None and result["status"] == "completed"}
    result.update(execution_mode=replay_meta["execution_mode"], http_attempts=0,
                  scripted_transport_attempts=replay_meta["scripted_transport_attempts"],
                  fixture_usage_not_billable=True, replay_complete=replay_meta["replay_complete"],
                  replay_error=mismatch)
    write_json(output / "result.json", result)
    write_json(output / "replay.json", replay_meta)
    return replay_meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--condition", default="distributed")
    parser.add_argument("--task-type", choices=["ranking", "choice"], required=True)
    parser.add_argument("--script", type=Path, required=True,
                        help="JSON array of {stage, member, output} engineering fixture rows")
    parser.add_argument("--output", type=Path, required=True, help="New directory only")
    parser.add_argument("--ordinal", type=int, default=1)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output directory must be new")
    report = replay(args.pack, args.condition, args.task_type, args.script, args.output, args.ordinal)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["replay_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
