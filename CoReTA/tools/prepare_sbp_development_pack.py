"""Extract published SBP facts as data; never execute downloaded Python."""
from __future__ import annotations

import ast
import hashlib
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/task-source-audit-20261021/student_body_president_task.py"
OUT = ROOT / "data/task-packs/student-president-dev-v1"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if OUT.exists():
        raise ValueError("Refuse to overwrite task pack")
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "StudentBodyPresidentTask")
    assignments = {}
    for node in cls.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            assignments[node.targets[0].id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assignments[node.target.id] = node.value
    names = ast.literal_eval(assignments["ITEMS"])
    shared = ast.literal_eval(assignments["SHARED_INFORMATION"])
    ground = ast.literal_eval(assignments["GROUND_TRUTH_RANKING"])
    unique = []
    mapping = assignments["PER_AGENT_UNIQUE_INFORMATION"]
    for group in mapping.values:
        for call in group.elts:
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != "UniqueInformationPiece":
                raise ValueError("Unexpected source structure")
            fields = {kw.arg: ast.literal_eval(kw.value) for kw in call.keywords}
            if set(fields) != {"trait", "valence", "candidate"}:
                raise ValueError("Unexpected fact fields")
            unique.append(fields)
    assert len(names) == 4 and len(unique) == 16
    values = {"positive": 1, "neutral": 0, "negative": -1}
    shared_scores = {}
    for label, block in re.findall(r"CANDIDATE ([A-D]):(.*?)(?=CANDIDATE [A-D]:|$)", shared, re.S):
        shared_scores[label] = sum(values[x.lower()] for x in re.findall(r": (Positive|Neutral|Negative)", block))
    total = {k: shared_scores[k] + sum(values[f["valence"]] for f in unique if f["candidate"] == k) for k in shared_scores}
    ranks = {f"Candidate {k}": i+1 for i, k in enumerate(sorted(total, key=lambda k: -total[k]))}
    assert len(set(total.values())) == 4 and [ranks[n] for n in names] == ground
    rng = random.Random(20261021)
    rng.shuffle(unique)
    rng.shuffle(names)
    materials = [{"ref": f"S{i+1:02d}", "item_id": f"I{f['candidate']}", "item_name": f"Candidate {f['candidate']}",
                  "content": f"Candidate {f['candidate']}: {f['trait']} (valence: {f['valence']})"}
                 for i, f in enumerate(unique)]
    task = {"task_id": "student-president/dev-001", "task_type": "ranking", "title": "Student Committee Selection",
            "scenario": "A committee ranks four student body president candidates. Some committee members may hold additional evidence.\n\n" + shared,
            "instruction": "Rank all four candidates from best to worst by total valence across all available facts: positive=+1, neutral=0, negative=-1. Do not count the same fact twice. Do not assume unseen evidence is absent.",
            "items": [{"item_id": "I"+n[-1], "name": n} for n in names],
            "output_contract": "Return all four exact candidate names once in a ranking array. No reference ranking is available during solving."}
    write(OUT / "public/task.json", task)
    write(OUT / "offline/evaluator.json", {"task_id": task["task_id"], "runtime_visible": False,
          "reference_ranks_by_exact_name": ranks, "shared_scores": shared_scores, "total_scores": total,
          "rule": values, "source_private_facts": unique})
    agents = ["A1", "A2", "A3", "A4"]
    audit = []
    for condition in ("concentrated_A1", "distributed", "full", "none"):
        allocation = {a: list(materials) if condition == "full" or (condition == "concentrated_A1" and a == "A1") else
                      [m for m in materials if m["item_name"] == f"Candidate {chr(65+i)}"] if condition == "distributed" else []
                      for i, a in enumerate(agents)}
        directory = [{"agent_id": a, "accessible_materials": [{k: v for k, v in m.items() if k != "content"} for m in allocation[a]]} for a in agents]
        for a in agents:
            packet = {"TASK": task, "SELF": {"agent_id": a, "team": agents}, "SELF_MATERIALS": allocation[a],
                      "DIRECTORY": directory, "REFERENCE_INDEX": [{"ref": "T", "kind": "task"}] +
                      [{"ref": m["ref"], "kind": "private_material"} for m in allocation[a]]}
            assert not any(key in json.dumps(packet) for key in ("correct_answer", "GROUND_TRUTH", "reference_ranks", "total_scores"))
            write(OUT / f"packets/{condition}/{a}.json", packet)
        counts = {a: len(allocation[a]) for a in agents}
        assert len({m["ref"] for ms in allocation.values() for m in ms}) == (0 if condition == "none" else 16)
        if condition == "distributed":
            assert list(counts.values()) == [4]*4
        audit.append({"condition": condition, "private_fact_counts": counts})
    write(OUT / "provenance.json", {"source": str(SOURCE.relative_to(ROOT)), "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          "seed": 20261021, "extraction": "AST literals only; downloaded code not executed", "changes": ["neutral handles and seeded display order", "our JSON packet format", "explicit deduplication/unseen-evidence instruction"],
          "not_original_paper_replication": True})
    write(OUT / "PREPARATION_CHECKS.json", {"kind": "task_data_audit_not_model_results", "facts_preserved": 16, "agents": 4, "candidates": 4,
          "arithmetic_matches_upstream_reference": True, "allocation": audit, "model_calls": 0,
          "empirical_expertise_advantage_established": False, "runtime_adapter_ready": False,
          "blocking_adapter": "Existing inputs/contracts/render/scoring/prompts require exactly 15 ranked items"})
    print(json.dumps({"prepared_data": str(OUT), "packets": 16, "runtime_adapter_ready": False}))


if __name__ == "__main__":
    main()
