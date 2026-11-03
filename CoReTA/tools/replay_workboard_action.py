"""Offline validation of an unchanged historical action, never a live result repair."""
import argparse
import hashlib
import json
from pathlib import Path

from coreta.handoff.__main__ import PROJECT
from coreta.workboard.artifacts import RankingAdapter
from coreta.workboard.contracts import Contracts


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(unit, output):
    if output.exists():
        raise ValueError("Output must be new; historical files are never overwritten")
    if unit.resolve() == output.resolve() or unit.resolve() in output.resolve().parents:
        raise ValueError("Write diagnostic output outside the historical unit")
    files = [unit / name for name in ("responses.jsonl", "result.json", "state.json")]
    before = {str(p): digest(p) for p in files}
    last = json.loads(files[0].read_text(encoding="utf-8").splitlines()[-1])
    response = last["response"]
    packet = json.loads(response["instructions"].split("\nPACKET=", 1)[1].split("\nOUTPUT_SCHEMA=", 1)[0])
    raw = "".join(c["text"] for message in response["output"] if message["type"] == "message"
                  for c in message["content"] if c["type"] == "output_text")
    stage = last["call_context"]["stage"]
    contracts = Contracts(RankingAdapter(packet["TASK"]))
    value = contracts.decode(raw, contracts.schema(stage, packet))
    contracts.validate_action(stage, value)
    result = json.loads(files[1].read_text(encoding="utf-8"))
    state = json.loads(files[2].read_text(encoding="utf-8"))
    chosen = next(w for w in state["works"] if w["id"] == value["candidate_id"])
    after = {str(p): digest(p) for p in files}
    if before != after:
        raise ValueError("Historical input changed during replay")
    report = {
        "kind": "offline_historical_action_validation_only", "network_attempts": 0,
        "natural_model_run": False, "historical_unit": str(unit), "stage": stage,
        "raw_action_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "historical_file_hashes": before, "historical_files_unchanged": True,
        "accepted_by_current_contract": True, "action": value["action"],
        "candidate_id": value["candidate_id"], "reason": value["reason"],
        "candidate_artifact": chosen["artifact"], "historical_status": result["status"],
        "historical_error": result.get("error"),
        "source_hashes": {str(p.relative_to(PROJECT)): digest(p) for p in
                          [PROJECT / "src/coreta/workboard/contracts.py", Path(__file__)]},
        "scope": "Contract accepts original response; not a completed rerun or a new method comparison.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = replay(args.unit, args.output)
    print(json.dumps({k: report[k] for k in ("kind", "accepted_by_current_contract", "candidate_id",
                                            "historical_status", "network_attempts")}))
