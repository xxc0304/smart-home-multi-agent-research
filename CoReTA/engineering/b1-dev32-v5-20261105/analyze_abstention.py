"""Post-hoc D32 readout diagnostic; never changes original scores or responses."""
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from b0_answers import answer_text
from metrics.answer import normalize_answer

source = Path(sys.argv[1]).resolve()
scores = json.loads(source.read_text(encoding="utf-8"))
output = {"scope": "POST_HOC_DEVELOPMENT_DIAGNOSTIC_NOT_CONFIRMATION",
          "rule": "Exclude normalized exact Unknown from voting; empty vote scores zero; uniform tied-class expectation.",
          "no_generation": True, "original_scores_unchanged": True,
          "source": str(source), "arms": {}}
for arm in "ABCD":
    rows = []
    for report in scores["reports"]:
        r = report["arms"][arm]
        groups = defaultdict(list)
        for actor, member in r["members"].items():
            key = normalize_answer(answer_text(member["answer"]))
            if key:
                groups[key].append(member["em"])
        def expectation(g):
            if not g:
                return 0.0
            highest = max(map(len, g.values()))
            winners = [v for v in g.values() if len(v) == highest]
            assert all(len(set(v)) == 1 for v in g.values())
            return sum(v[0] for v in winners) / len(winners)
        original = expectation(groups)
        assert abs(original - r["expected_em"]) < 1e-12
        alternative = expectation({k: v for k, v in groups.items() if k != "unknown"})
        rows.append({"id": report["id"], "original": original,
                     "unknown_as_abstention": alternative,
                     "difference": alternative - original})
    n = len(rows)
    output["arms"][arm] = {
        "n": n, "original_expected_em": sum(x["original"] for x in rows) / n,
        "alternative_expected_em": sum(x["unknown_as_abstention"] for x in rows) / n,
        "improved_items": sum(x["difference"] > 0 for x in rows),
        "worsened_items": sum(x["difference"] < 0 for x in rows),
        "changed": [x for x in rows if x["difference"] != 0]}
target = HERE / "READOUT_ABSTENTION_DIAGNOSTIC.json"
target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({a: {k: v for k, v in r.items() if k != "changed"}
                  for a, r in output["arms"].items()}, ensure_ascii=False, indent=2))
