"""Task-sized ranking rendering and offline-only scoring for v2 systems."""
from ..handoff.inputs import read_json
from ..handoff.ranking import parse_ranking, score_artifact


def render_ranking(ranking):
    if (not isinstance(ranking, list) or len(ranking) not in {4, 15}
            or not all(isinstance(x, str) for x in ranking) or len(set(ranking)) != len(ranking)):
        raise ValueError("Expected a validated 4 or 15 item ranking")
    return "MY RANKING:\n" + "\n".join(f"{i}. {name}" for i, name in enumerate(ranking, 1))


def score_run(pack_root, result):
    evaluator = read_json(pack_root / "offline/evaluator.json")
    public = read_json(pack_root / "public/task.json")
    reference = evaluator["reference_ranks_by_exact_name"]
    n = len(public["items"])
    if (evaluator["task_id"] != result["task_id"] or evaluator["runtime_visible"] is not False
            or n not in {4, 15} or set(reference) != {i["name"] for i in public["items"]}
            or any(type(v) is not int for v in reference.values()) or sorted(reference.values()) != list(range(1, n+1))):
        raise ValueError("Task and offline evaluator mismatch")
    expected = (result.get("independent_requested_members", result.get("agents", []))
                if result["system"] in {"independent", "ordinary_discussion"} else [])
    independent = {a: score_artifact(value, reference) for a, value in result.get("independent_answers", {}).items()}
    return {"task_id": result["task_id"], "condition": result["condition"], "system": result["system"],
            "protocol_status": result["status"], "item_count": n,
            "stop_reason": result.get("stop_reason"), "protocol_error": result.get("error"),
            "artifact_role": (None if result["system"] == "independent" else
                              "final_submission" if result["system"] == "ordinary_discussion" and result.get("stop_reason") == "discussion_finished" else
                              "driver_initial_fallback_or_interrupted_candidate" if result["system"] == "ordinary_discussion" else "current_candidate"),
            "final": None if result["system"] == "independent" else score_artifact(result.get("artifact"), reference),
            "independent": independent, "independent_expected_members": expected,
            "independent_missing_members": [a for a in expected if a not in independent],
            "unresolved": result.get("unresolved", []), "application_blockers": result.get("application_blockers", []),
            "http_attempts": result.get("http_attempts"), "usage_complete": result.get("usage_complete"),
            "usage_records": result.get("usage_records", []), "feedback_sent_to_model": False,
            "initial_all_wrong_recovery": None, "initial_any_correct_degradation": None,
            "stratification_note": "Separate calibration is not this team's actual initial answer event."}
