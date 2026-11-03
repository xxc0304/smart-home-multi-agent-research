"""Audit archived CoReTA pilot events and request contracts; no generation or execution of candidates."""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re

from coreta.protocol import ACTIONS
from coreta.schemas import Contracts, check_update
from coreta.state import write_json


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def code_structure(text):
    """Parse only; normalize docstrings without executing candidate source."""
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                node.body.pop(0)
    return ast.dump(tree, include_attributes=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    p = args.project.resolve()
    plan = read(p / "engineering/DEVELOPMENT_PILOT_TOKENIZER_PLAN_20261019.json")
    contracts = Contracts(p / "design/v0.3/coreta.schema.json")
    rows = []
    for job in plan["jobs"]:
        if job["system"] != "coreta":
            continue
        directory = p / "runs/development-pilot-20261019" / job["job_id"] / "attempt_0001"
        events = jsonl(directory / "events.jsonl")
        requests = jsonl(directory / "requests.jsonl")
        result = read(directory / "result.json")
        event_ids = set()
        for index, event in enumerate(events):
            contracts.validate("Event", event)
            if event["sequence"] != index or not set(event["parent_ids"]) <= event_ids:
                raise ValueError("Event sequence or parent ordering failed")
            event_ids.add(event["event_id"])
        drafts = {e["sent_from"]: e for e in events if e["kind"] == "draft"}
        review = next(e for e in events if e["kind"] == "review")
        lead_requests = [r for r in requests if "candidate" in r["payload"]["text"]["format"]["schema"].get("properties", {})]
        lead = next((e for e in events if e["kind"] == "lead_update"), None)
        review_requests = [r for r in requests if "subject_id" in r["payload"]["text"]["format"]["schema"].get("properties", {})]
        row = {"task_id": job["task_id"], "directory": str(directory), "status": result["status"],
               "family": job["family"],
               "event_schema_and_parent_checks": True,
               "three_drafts_and_a0_initial": set(drafts) == {"A0", "A1", "A2"} and events[0]["sent_from"] == "A0",
               "bootstrap_reviewer_a2_on_a0": review["sent_from"] == "A2" and review["payload"]["subject_id"] == drafts["A0"]["event_id"],
               "a1_draft_not_exposed_to_bootstrap_review": all(drafts["A1"]["event_id"] not in r["payload"]["instructions"] for r in review_requests),
               "two_turns_and_all_actions_supplied": all("REMAINING_WORK_TURNS = 2" in r["payload"]["instructions"] and
                   all(a in r["payload"]["instructions"].split("LEGAL_ACTIONS = ")[-1].split("\n")[0] for a in ACTIONS) for r in lead_requests),
               "request_event_count": sum(e["kind"] == "request" for e in events),
               "contribution_event_count": sum(e["kind"] == "contribution" for e in events),
               "final_event_present": any(e["kind"] == "final" for e in events),
               "version_transition_coherent": review["base_version"] == 0 and
                   (lead is None or lead["base_version"] == 0) and
                   next(e for e in events if e["kind"] == "final")["base_version"] == (1 if lead else 0),
               "committed_lead_contract": None, "initial_issues": drafts["A0"]["payload"]["open_issues"]}
        if lead:
            refs = json.loads(re.findall(r"(?:^|\n)REFERENCE_INDEX=(\[[^\n]*\])", lead_requests[-1]["payload"]["instructions"])[-1])
            contracts.validate("LeadUpdate", lead["payload"])
            check_update(lead["payload"], set(refs), ACTIONS, [review], False)
            row["committed_lead_contract"] = True
            before = drafts["A0"]["payload"]
            after = lead["payload"]["candidate"]
            old_steps = {s["id"]: s for s in before["steps"]}
            actual = [s["id"] for s in after["steps"] if s["id"] not in old_steps or old_steps[s["id"]]["text"] != s["text"]]
            declared = lead["payload"]["application"]["changed_step_ids"]
            candidate_refs = [ref for step in after["steps"] for ref in step["basis_refs"]]
            row.update({"action": lead["payload"]["next"]["action"], "reason": lead["payload"]["next"]["reason"],
                        "application_disposition": lead["payload"]["application"]["disposition"],
                        "application_outcome_self_reported": lead["payload"]["application"]["application_outcome"],
                        "peer_initial_refs_present": any(ref == drafts[a]["event_id"] or ref.startswith(drafts[a]["event_id"] + "#") for ref in candidate_refs for a in ("A1", "A2")),
                        "candidate_artifact_changed": before["artifact"] != after["artifact"],
                        "step_text_changes": actual, "declared_changes": declared,
                        "text_changes_missing_from_application": sorted(set(actual) - set(declared)),
                        "open_issues_after": after["open_issues"],
                        "step_status_after": dict(Counter(s["status"] for s in after["steps"]))})
        else:
            row.update({"action": None, "errors": result["errors"],
                        "fallback_prefinal_is_last_valid_a0": result["prefinal_artifact"] == drafts["A0"]["payload"]["artifact"]})
        if job["family"] == "mbpp":
            final_ast = code_structure(result["artifact"])
            row["finalizer_code_audit"] = {"text_changed": result["artifact"] != result["prefinal_artifact"],
                "ast_excluding_docstrings_changed": final_ast != code_structure(result["prefinal_artifact"]),
                "same_ast_as_initial_actors": [a for a, event in drafts.items() if final_ast == code_structure(event["payload"]["artifact"])]}
        rows.append(row)
    report = {"scope": "archived-event and request audit, not a new intervention or model experiment",
              "review_independence": "none", "new_model_calls": 0, "cases": rows,
              "formal_checks_passed": all(all(r[k] for k in ("event_schema_and_parent_checks", "three_drafts_and_a0_initial",
                       "bootstrap_reviewer_a2_on_a0", "a1_draft_not_exposed_to_bootstrap_review", "two_turns_and_all_actions_supplied", "final_event_present", "version_transition_coherent")) for r in rows),
              "valid_committed_leads": sum(r["committed_lead_contract"] is True for r in rows),
              "step_text_change_cases": sum(bool(r.get("step_text_changes")) for r in rows),
              "missing_declared_text_change_cases": [r["task_id"] for r in rows if r.get("text_changes_missing_from_application")]}
    valid = [r for r in rows if r["committed_lead_contract"]]
    report["chain_metrics"] = {"valid_first_updates": len(valid),
        "artifact_unchanged_at_first_update": sum(not r["candidate_artifact_changed"] for r in valid),
        "valid_code_first_updates": sum(r["family"] == "mbpp" for r in valid),
        "code_unchanged_at_first_update": sum(r["family"] == "mbpp" and not r["candidate_artifact_changed"] for r in valid),
        "peer_initial_refs_present_tasks": [r["task_id"] for r in valid if r["peer_initial_refs_present"]],
        "application_dispositions": dict(Counter(r["application_disposition"] for r in valid)),
        "application_outcomes_self_reported": dict(Counter(r["application_outcome_self_reported"] for r in valid)),
        "finalizer_code_ast_changes": [r["task_id"] for r in rows if r.get("finalizer_code_audit", {}).get("ast_excluding_docstrings_changed")],
        "interpretation": "Text identity, AST identity and citations are descriptive; none alone establishes absence of reasoning or causal use."}
    # Independent integer arithmetic, not execution of a generated candidate function.
    report["rotate_review_arithmetic_witness"] = {"task_id": "mbpp/train/799", "input_hex": "0x80000001", "d": 1,
              "left_shift": hex(0x80000001 << 1), "wrapped_high_bit": hex(0x80000001 >> 31),
              "correct_masked_result": hex(((0x80000001 << 1) | (0x80000001 >> 31)) & 0xFFFFFFFF),
              "review_and_updated_step_claimed": "0x40000000", "candidate_code_changed": False}
    write_json(args.output, report)
    print(json.dumps({k: report[k] for k in ("formal_checks_passed", "valid_committed_leads", "step_text_change_cases", "missing_declared_text_change_cases", "rotate_review_arithmetic_witness")}))


if __name__ == "__main__":
    main()
