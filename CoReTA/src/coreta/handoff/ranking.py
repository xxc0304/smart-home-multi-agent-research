"""Explicit offline ranking scoring; never used to guide the live protocol."""
from __future__ import annotations

import re

from .inputs import read_json


def render_ranking(ranking):
    """Format the model's validated order; no gold access or content correction."""
    if not isinstance(ranking, list) or len(ranking) != 15 or not all(isinstance(x, str) for x in ranking) or len(set(ranking)) != 15:
        raise ValueError("Expected a validated complete ranking array")
    return "MY RANKING:\n" + "\n".join(f"{index}. {name}" for index, name in enumerate(ranking, 1))


def parse_ranking(artifact, names):
    if not isinstance(artifact, str) or not artifact.strip():
        return None, "artifact_missing"
    lines = artifact.splitlines()
    markers = [i for i, line in enumerate(lines) if line.strip() == "MY RANKING:"]
    if len(markers) != 1:
        return None, "expected_one_ranking_marker"
    ranked_lines = [line.strip() for line in lines[markers[0] + 1:] if line.strip()]
    if len(ranked_lines) != len(names):
        return None, "ranking_line_count"
    ranking, positions = {}, set()
    for line in ranked_lines:
        match = re.fullmatch(r"([0-9]+)\.\s+(.+)", line)
        if not match:
            return None, "invalid_numbered_line"
        rank, name = int(match.group(1)), match.group(2).strip()
        if rank not in range(1, len(names) + 1) or rank in positions:
            return None, "duplicate_or_out_of_range_rank"
        if name not in names or name in ranking:
            return None, "unknown_or_duplicate_item_name"
        ranking[name] = rank
        positions.add(rank)
    if set(ranking) != set(names):
        return None, "incomplete_permutation"
    if [int(re.match(r"[0-9]+", line).group()) for line in ranked_lines] != list(range(1, len(names) + 1)):
        return None, "rank_lines_not_in_ascending_order"
    return ranking, None


def score_artifact(artifact, reference):
    ranking, error = parse_ranking(artifact, set(reference))
    n = len(reference)
    worst = n * n // 2
    if error:
        return {"L1_error": worst, "complete_ranking_correct": False,
                "delivery_failure": True, "failure_reason": error, "predicted_ranks": None}
    distance = sum(abs(ranking[name] - reference[name]) for name in reference)
    return {"L1_error": distance, "complete_ranking_correct": distance == 0,
            "delivery_failure": False, "failure_reason": None, "predicted_ranks": ranking}


def score_run(pack_root, result):
    # Only this explicitly offline entry reads evaluator data.
    evaluator = read_json(pack_root / "offline/evaluator.json")
    if evaluator["task_id"] != result["task_id"] or evaluator["runtime_visible"] is not False:
        raise ValueError("Run task and offline evaluator do not match")
    reference = evaluator["reference_ranks_by_exact_name"]
    public = read_json(pack_root / "public/task.json")
    if (set(reference) != {item["name"] for item in public["items"]}
            or sorted(reference.values()) != list(range(1, 16))):
        raise ValueError("Invalid reference ranking")
    answers = {agent: score_artifact(artifact, reference)
               for agent, artifact in result.get("independent_answers", {}).items()}
    final = None if result["system"] == "independent" else score_artifact(result.get("artifact"), reference)
    return {
        "task_id": result["task_id"], "condition": result["condition"], "system": result["system"],
        "protocol_status": result["status"], "final": final, "independent": answers,
        "independent_expected_members": result.get("agents", []),
        "independent_missing_members": [a for a in result.get("agents", []) if a not in answers],
        "reference_policy": "upstream exercise ranking, not universal physical optimality",
        "feedback_sent_to_model": False,
        "initial_all_wrong_recovery": None,
        "initial_any_correct_degradation": None,
        "stratification_note": "Pair a separately collected independent run by exact member-packet/model hashes; absent pairing is unknown, never assumed all wrong.",
    }
