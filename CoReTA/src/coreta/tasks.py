"""Public input adapters. This module never executes candidate code."""
from __future__ import annotations

import ast
import builtins
import hashlib
import json
import unicodedata
from pathlib import Path


def canonical_prompt(prompt):
    return " ".join(unicodedata.normalize("NFKC", prompt).split())


def select_ids(ids, prefix, n):
    return sorted(ids, key=lambda task_id: (hashlib.sha256((prefix + "|" + task_id).encode()).hexdigest(), task_id))[:n]


def public_task(dataset: str, row: dict, *, row_number: int | None = None):
    if dataset == "math500":
        return {"task_id": row["unique_id"], "task_type": "math", "prompt": row["problem"], "entry_point": None}
    if dataset == "gsm8k":
        if row_number is None:
            raise ValueError("GSM8K needs the frozen zero-based source row number")
        return {"task_id": f"gsm8k/train/{row_number}", "task_type": "math", "prompt": row["question"], "entry_point": None}
    if dataset == "humaneval":
        return {"task_id": row["task_id"], "task_type": "code", "prompt": row["prompt"], "entry_point": row["entry_point"]}
    if dataset == "mbpp":
        name, arity = mbpp_signature(row)
        return {"task_id": f"mbpp/train/{row['task_id']}", "task_type": "code",
                "prompt": row["prompt"] + f"\nImplement Python function {name} with {arity} positional arguments.", "entry_point": name}
    raise ValueError("Unknown dataset adapter")


def mbpp_signature(row):
    imported = set()
    for line in row.get("test_imports", []):
        for node in ast.walk(ast.parse(line)):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imported.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
    candidates = []
    all_calls = []
    for assertion in row["test_list"]:
        tree = ast.parse(assertion)
        if not any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
            raise ValueError("MBPP test item has no assertion")
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id not in imported and node.func.id not in vars(builtins)]
        candidates.append({call.func.id for call in calls})
        all_calls.extend(calls)
    common = set.intersection(*candidates) if candidates else set()
    if len(common) != 1:
        raise ValueError("Cannot infer one public MBPP entry point")
    name = next(iter(common))
    calls = [call for call in all_calls if call.func.id == name]
    if any(call.keywords or any(isinstance(arg, ast.Starred) for arg in call.args) for call in calls):
        raise ValueError("Unsupported MBPP call signature")
    arities = {len(call.args) for call in calls}
    if len(arities) != 1:
        raise ValueError("Inconsistent MBPP positional arity")
    return name, next(iter(arities))


def export_evalplus(results: list[dict], path: Path, *, prefinal=False):
    ids = [row["task_id"] for row in results]
    if len(set(ids)) != len(ids):
        raise ValueError("One repetition/system per file; duplicate task ids are not allowed")
    if not all(task_id.startswith("HumanEval/") for task_id in ids):
        raise ValueError("EvalPlus export expects HumanEval task ids")
    field = "prefinal_artifact" if prefinal else "artifact"
    with path.open("x", encoding="utf-8") as stream:
        for row in results:
            stream.write(json.dumps({"task_id": row["task_id"], "solution": row[field]}, ensure_ascii=False) + "\n")
