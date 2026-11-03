"""Write a local interface example from historical inputs; no client or API.

The legacy knowledge is copied wholesale as one illustrative claim. This is NOT
autonomous decomposition and is not an experimental request or model response.
"""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

from coreta.workboard.grounded import GroundRunner, GroundContracts, GroundPrompts
from coreta.workboard.artifacts import ChoiceAdapter
from coreta.handoff.gateway import Journal, write_json

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "refine-logs/evidence-before-application-20261024/interface-preview"
    output.mkdir(exist_ok=False)
    for task in ("hb-dev-004-r1-c1", "hb-dev-034-r1-c2"):
        source = ROOT / "runs/workboard-d0-natural-live-20261022-r2" / task / "d0_continuation/requests.jsonl"
        packets = []
        for line in source.read_text(encoding="utf-8").splitlines():
            instructions = json.loads(line).get("payload", {}).get("instructions", "")
            if "PACKET=" in instructions:
                p = json.JSONDecoder().raw_decode(instructions.split("PACKET=", 1)[1])[0]
                if p.get("STAGE") == "TRY":
                    packets.append(p)
        historical = packets[0]
        member_dir = ROOT / "data/task-packs/hiddenbench-workboard-dev-v1" / task[:10] / "packets/distributed"
        members = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in member_dir.glob("A*.json")}
        access = SimpleNamespace(agents=list(historical["SELF"]["team"]),
            member=lambda member: copy.deepcopy(members[member]))
        adapter = ChoiceAdapter(historical["TASK"])
        contracts, prompts = GroundContracts(adapter), GroundPrompts()
        gateway = SimpleNamespace(contracts=contracts, prompts=prompts, outputs={"ground": 2048}, remaining=20)
        folder = output / task[:10]
        folder.mkdir()
        runner = GroundRunner(access, gateway, Journal(folder), adapter)
        runner.editor = historical["SELF"]["agent_id"]
        runner.board._works = {w["id"]: copy.deepcopy(w) for w in historical["CANDIDATES"]}
        runner.board.current = historical["CURRENT_WORK"]["id"]
        runner.published = copy.deepcopy(historical["PUBLIC_EVIDENCE"])
        offer = copy.deepcopy(historical["TARGET_OFFER"])
        offer["claims"] = [{"statement": offer["knowledge"],
                            "premises": "Legacy interface illustration; decomposition not generated.",
                            "source_refs": [offer["ref"]]}]
        packet = runner.ground_packet(offer)
        schema = contracts.schema("GROUND", packet)
        write_json(folder / "ground.input.json", packet)
        write_json(folder / "ground.output_schema.json", schema)
        (folder / "ground.prompt.txt").write_text(prompts.render("GROUND", packet, schema), encoding="utf-8")
        observe = runner.packet(offer["author"], "OBSERVE")
        write_json(folder / "observe.output_schema.json", contracts.schema("OBSERVE", observe))
    write_json(output / "README.json", {"purpose": "interface_preview_only", "model_calls": 0,
        "claim_origin": "legacy knowledge copied wholesale; not autonomous extraction",
        "visibility": "full public offers and candidates, own private originals only",
        "not_validated": ["end_to_end_execution", "autonomous_claim_coverage", "quality", "cost"]})
    print(output)


if __name__ == "__main__":
    main()
