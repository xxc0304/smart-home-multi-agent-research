"""Offline source-citation counterfactual; never repairs or resumes a live run."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from coreta.schemas import ProtocolError
from coreta.workboard.artifacts import RankingAdapter
from coreta.workboard.contracts import Contracts
from coreta.workboard.provenance import describe_sources


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diagnose(unit, output):
    if output.exists() or unit.resolve() in output.resolve().parents:
        raise ValueError("Output must be new and outside the historical unit")
    paths = [unit / name for name in ("responses.jsonl", "result.json", "state.json")]
    before = {str(p): sha(p) for p in paths}
    row = json.loads(paths[0].read_text(encoding="utf-8").splitlines()[-1])
    response = row["response"]
    packet = json.loads(response["instructions"].split("\nPACKET=", 1)[1].split("\nOUTPUT_SCHEMA=", 1)[0])
    packet = describe_sources(packet)
    raw = "".join(c["text"] for m in response["output"] if m["type"] == "message"
                  for c in m["content"] if c["type"] == "output_text")
    value = json.loads(raw)
    stage = row["call_context"]["stage"]
    contracts = Contracts(RankingAdapter(packet["TASK"]))
    schema = contracts.schema(stage, packet)
    try:
        contracts.decode(raw, schema)
    except ProtocolError as error:
        rejected = error.code == "SCHEMA_ERROR"
    else:
        rejected = False
    if not rejected:
        raise ValueError("Expected original inaccessible citations to remain rejected")
    allowed = {r["ref"] for r in packet["REFERENCE_INDEX"]}
    invalid = [r for r in value["declared_sources"] if r not in allowed]
    already_cited = set(value["declared_sources"]) & allowed
    links = {r["reported_ref"]: sorted(set(r["via_public_refs"]) & already_cited)
             for r in packet["SOURCE_ACCESS"]["reported_originals"] if r["reported_ref"] in invalid}
    if not invalid or any(not links.get(r) for r in invalid):
        raise ValueError("Counterfactual requires every removed ID to have an already-cited public carrier")
    corrected = copy.deepcopy(value)
    corrected["declared_sources"] = [r for r in value["declared_sources"] if r in allowed]
    contracts.decode(json.dumps(corrected), schema)
    contracts.validate_action(stage, corrected)
    assert {k:v for k,v in value.items() if k != "declared_sources"} == {
        k:v for k,v in corrected.items() if k != "declared_sources"}
    assert before == {str(p): sha(p) for p in paths}
    report = {"kind": "offline_source_citation_counterfactual_not_model_evidence", "network_attempts": 0,
              "original_response_still_rejected": True, "removed_in_diagnostic_copy_only": invalid,
              "already_cited_public_carriers_from_unverified_metadata": links,
              "diagnostic_copy_accepted": True, "non_source_fields_unchanged": True,
              "historical_files_unchanged": True, "historical_file_hashes": before,
              "historical_status": json.loads(paths[1].read_text(encoding="utf-8"))["status"],
              "source_access": packet["SOURCE_ACCESS"], "diagnostic_output": corrected,
              "scope": "Shows correct citation form; does not prove semantic support or natural generation reliability."}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = diagnose(args.unit, args.output)
    print(json.dumps({k:report[k] for k in ("original_response_still_rejected", "diagnostic_copy_accepted",
                                            "historical_files_unchanged", "network_attempts")}))
