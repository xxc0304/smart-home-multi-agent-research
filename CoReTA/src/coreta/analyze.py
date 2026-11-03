"""Summaries of external task scores; never imported by runtime orchestration."""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def paired_summary(rows, left="coreta", right="static_debate", resamples=10000, seed=17, expected_seeds=(17, 29, 43), expected_tasks=None):
    """One task family and metric at a time; average repetitions before task bootstrap."""
    grouped = defaultdict(dict)
    if left == right or resamples < 100:
        raise ValueError("Distinct conditions and at least 100 resamples required")
    for row in rows:
        if row["system"] not in {left, right}:
            continue
        if row.get("diagnostic_only"):
            raise ValueError("Diagnostic scorer outputs are not formal research scores")
        score = row["score"]
        if score not in (0, 1):
            raise ValueError("Explicit binary scores required; unresolved scorer failures must remain unresolved")
        key = (row["task_id"], row["seed"])
        if row["system"] in grouped[key]:
            raise ValueError("Duplicate task/system/repetition score")
        grouped[key][row["system"]] = score
    per_task = defaultdict(list)
    task_seeds = defaultdict(set)
    for (task_id, repeat_seed), values in grouped.items():
        if set(values) != {left, right}:
            raise ValueError("Incomplete pair; explicitly resolve failures before primary analysis")
        per_task[task_id].append(values[left] - values[right])
        task_seeds[task_id].add(repeat_seed)
    if not per_task:
        raise ValueError("No paired task scores")
    if expected_tasks is not None and set(per_task) != set(expected_tasks):
        raise ValueError("Observed tasks differ from the predeclared task universe")
    if any(seeds != set(expected_seeds) for seeds in task_seeds.values()):
        raise ValueError("Each task must contain every predeclared repetition, including explicit failed scores")
    means = [sum(values) / len(values) for _, values in sorted(per_task.items())]
    rng = random.Random(seed)
    draws = sorted(sum(rng.choice(means) for _ in means) / len(means) for _ in range(resamples))
    return {"tasks": len(means), "task_mean_difference": sum(means) / len(means),
            "paired_bootstrap_ci95": [draws[int(.025 * (resamples - 1))], draws[int(.975 * (resamples - 1))]],
            "resamples": resamples, "replications_per_task": {key: len(value) for key, value in per_task.items()}}


def main():
    parser = argparse.ArgumentParser(description="Analyze binary external scores for one metric/task family")
    parser.add_argument("scores", type=Path, help="JSON list: task_id, seed, system, score")
    parser.add_argument("--left", default="coreta")
    parser.add_argument("--right", default="static_debate")
    parser.add_argument("--seeds", type=int, nargs="+", default=[17, 29, 43])
    parser.add_argument("--expected-tasks", type=Path, required=True, help="Frozen JSON list of task IDs for this metric/family")
    args = parser.parse_args()
    print(json.dumps(paired_summary(json.loads(args.scores.read_text(encoding="utf-8")), args.left, args.right,
                                  expected_seeds=args.seeds, expected_tasks=json.loads(args.expected_tasks.read_text(encoding="utf-8"))), indent=2))


if __name__ == "__main__":
    main()
