"""Read-only archive checks; never call an LLM or rewrite historical experiment data."""
import argparse
import copy
import json
from pathlib import Path

from coreta.workboard.issue_loop import attach_access_context


def packets(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        request = json.loads(line)
        instructions = request["payload"]["instructions"]
        yield request["call_context"], json.loads(
            instructions.split("\nPACKET=", 1)[1].split("\nOUTPUT_SCHEMA=", 1)[0])


def audit(root):
    originals = {}
    for _, packet in packets(root / "initial/requests.jsonl"):
        originals[packet["SELF"]["agent_id"]] = sorted(
            {"T", *(row["ref"] for row in packet["SELF_MATERIALS"])})
    method = root / "ground_full_public_v1"
    check_packets = {context["logical_call"]: packet
                     for context, packet in packets(method / "requests.jsonl")
                     if context["stage"] in {"CHECK_USE", "FINAL_CHECK_USE"}}
    first = check_packets[6]
    state = json.loads((method / "state.json").read_text(encoding="utf-8"))
    works = {w["id"]: w for w in state["works"]}
    checker = first["SELF"]["agent_id"]
    author = first["AFTER"]["author"]
    revised = attach_access_context(copy.deepcopy(first), state["editor"], originals)
    checks = {
        "005_checker_is_A3_author_is_A2": checker == "A3" and author == "A2",
        "005_checker_has_S03_but_author_has_S02": (
            first["SOURCE_ACCESS"]["direct_original_refs"] == originals[checker]
            and "S03" in originals[checker] and "S03" not in originals[author]
            and "S02" in originals[author]),
        "005_application_refs_do_not_claim_S03": "S03" not in first["APPLICATION_SOURCE_REFS"],
        "005_W5_declares_its_author_did_not_read_peer_originals": (
            "I directly read only T and S02" in works["W5"]["work_text"]),
        "005_W6_mentions_O5_but_omits_declaration": (
            "O5" in works["W6"]["work_text"] and "O5" not in works["W6"]["declared_sources"]),
        "005_W7_adds_O5_declaration": "O5" in works["W7"]["declared_sources"],
        "005_W7_still_selects_option_2": works["W7"]["artifact"] == "option_2",
        "runtime_helper_distinguishes_checker_and_work_author": (
            revised["CHECKER_ACCESS"]["agent_id"] == checker
            and revised["WORK_AUTHOR_ACCESS"]["W5"] == {
                "author": author, "available_original_refs": originals[author]}),
        "runtime_helper_identifies_current_application_actor": (
            revised["APPLICATION_ACTOR_ACCESS"] == {
                "agent_id": state["editor"], "available_original_refs": originals[state["editor"]]}),
        "runtime_helper_preserves_private_materials_and_legal_citations": (
            revised["SELF_MATERIALS"] == first["SELF_MATERIALS"]
            and revised["REFERENCE_INDEX"] == first["REFERENCE_INDEX"]),
    }
    return {"kind": "offline_archive_fact_checks_not_model_replay", "network_requests": 0,
        "source": str(root), "checks": checks, "passed": all(checks.values()),
        "runtime_helper_context_preview": {key: revised[key] for key in
            ("CHECKER_ACCESS", "WORK_AUTHOR_ACCESS", "APPLICATION_ACTOR_ACCESS")},
        "limits": "Verifies stored facts only. Does not prove the new prompt reduces false positives or improves answers."}


def main():
    parser = argparse.ArgumentParser()
    project = Path(__file__).resolve().parents[1]
    parser.add_argument("--archive", type=Path, default=project /
        "runs/grounded-three-arm-pilot-live-20261024-r1/hb-dev-005-r1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "checks": len(result["checks"]),
                      "network_requests": 0}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
