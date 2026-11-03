"""Read-only post-hoc process audit; no model requests or runtime changes."""
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
ROOTS = [
    ("r2", "workboard-pilot-live-20261022-r2", ["distributed-r1", "concentrated-r1"]),
    ("r3", "workboard-pilot-live-20261022-r3", ["distributed-r1", "concentrated-r1", "distributed-r2", "concentrated-r2"]),
    ("historical", "workboard-historical-live-20261022-r1", ["historical-r1", "historical-r2"]),
]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]


def main():
    gold_path = PROJECT / "data/task-packs/student-president-dev-v1/offline/evaluator.json"
    ranks = read(gold_path)["reference_ranks_by_exact_name"]
    def distance(artifact):
        if not isinstance(artifact, list) or len(artifact) != len(ranks) or set(artifact) != set(ranks):
            return 8
        return sum(abs(i-ranks[n]) for i,n in enumerate(artifact, 1))
    report = {"kind": "posthoc_process_comparison_not_independent_tasks", "network_requests": 0,
              "gold_sha256": hashlib.sha256(gold_path.read_bytes()).hexdigest(), "pairs": []}
    for version, run, pairs in ROOTS:
        for pair in pairs:
            pair_report = {"version": version, "pair": pair, "methods": {}}
            initial_sets = []
            for method in ("ordinary_discussion", "coreta_workboard"):
                folder = PROJECT / "runs" / run / pair / method
                result, state = read(folder / "result.json"), read(folder / "state.json")
                assert result["status"] == "completed"
                initial_sets.append([w for w in state["works"] if w["initial"]])
                works = {w["id"]: w for w in state["works"]}
                stages = lines(folder / "stages.jsonl")
                pending = iter(w for w in state["works"] if not w["initial"])
                creations = []
                for call, row in enumerate(stages, 1):
                    value, stage = row["output"], row["stage"]
                    native = value if stage == "DISCUSS" else value["work"] if (
                        stage in {"TRY", "FINALIZE"} and value["action"] == "new") else None
                    if native is not None:
                        work = next(pending)
                        assert work["artifact"] == native["artifact"] and work["work_text"] == native["work_text"]
                        assert work["author"] == row["member"]
                        creations.append({"call": call, "stage": stage, "id": work["id"], "author": work["author"],
                                          "l1": distance(work["artifact"])})
                assert next(pending, None) is None
                exact_initial = any(distance(w["artifact"]) == 0 for w in initial_sets[-1])
                good = [c for c in creations if c["l1"] == 0]
                editor_good = [c for c in good if c["author"] == result["editor"]]
                events = lines(folder / "events.jsonl")
                trials = []
                for e in events:
                    if e["kind"] != "trial_created": continue
                    related = [c for c in state["checks"] if c["before"] == e["before"] and c["after"] == e["after"]]
                    trials.append({"before": e["before"], "after": e["after"], "offer_ref": e["offer_ref"],
                                   "before_l1": distance(works[e["before"]]["artifact"]),
                                   "after_l1": distance(works[e["after"]]["artifact"]),
                                   "use_record": e["use_record"],
                                   "checks": [{k:c[k] for k in ("stage", "member", "finding", "observation")} for c in related]})
                pair_report["methods"][method] = {
                    "folder": str(folder.relative_to(PROJECT)), "editor": result["editor"],
                    "final_l1": distance(result["selected_work"]["artifact"]), "final_work": result["selected_work_id"],
                    "any_correct_initial": exact_initial,
                    "first_correct_creation_call": 0 if exact_initial else good[0]["call"] if good else None,
                    "first_editor_correct_creation_call": editor_good[0]["call"] if editor_good else None,
                    "correct_candidate_available_but_final_wrong": bool(good and distance(result["selected_work"]["artifact"]) != 0),
                    "creations": creations, "trials": trials,
                    "input_tokens": sum(u["input_tokens"] for u in result["usage"]),
                    "output_tokens": sum(u["output_tokens"] for u in result["usage"]),
                    "http": result["http_attempts"],
                }
            assert initial_sets[0] == initial_sets[1]
            report["pairs"].append(pair_report)
    out = Path(__file__).with_name("PROCESS_AUDIT_DATA.json")
    if out.exists(): raise ValueError("Do not overwrite an audit export")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for pair in report["pairs"]:
        print(pair["version"], pair["pair"], {m:{k:v[k] for k in (
            "final_l1", "first_correct_creation_call", "first_editor_correct_creation_call",
            "correct_candidate_available_but_final_wrong")} for m,v in pair["methods"].items()})


if __name__ == "__main__":
    main()
