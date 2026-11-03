"""Freeze a manually reviewed, untried challenge slice from local train sources."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq

from coreta.schemas import Contracts
from coreta.state import write_json
from coreta.tasks import canonical_prompt, public_task

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/complementarity-challenge-20261019"
GSM_ROWS = (310, 3750, 7446, 5129)
MBPP_IDS = (721, 751, 622)


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read_jsonl(path: Path, compressed=False):
    opener = gzip.open if compressed else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def prepare():
    if OUT.exists():
        raise ValueError("Frozen challenge bundle already exists; refusing overwrite")
    src = ROOT / "data/source"
    gsm_path, mbpp_path = src / "gsm8k-train.parquet", src / "mbpp-sanitized-train.parquet"
    gsm_rows = pq.read_table(gsm_path).to_pylist()
    mbpp_rows = pq.read_table(mbpp_path).to_pylist()
    mbpp_by_id = {row["task_id"]: row for row in mbpp_rows}
    if len(gsm_rows) != 7473 or len(mbpp_rows) != 120:
        raise ValueError("Frozen source row counts changed")

    dev = ROOT / "data/development-20261019"
    prior_index = json.loads((dev / "tasks.json").read_text(encoding="utf-8"))
    prior_ids = {row["task_id"] for row in prior_index}
    prior_prompts = set()
    for row in prior_index:
        public = json.loads((dev / row["path"]).read_text(encoding="utf-8"))
        prior_prompts.add(canonical_prompt(public["prompt"].split("\nImplement Python function ")[0]))

    math_eval = read_jsonl(src / "math500-test.jsonl")
    human_eval = read_jsonl(src / "HumanEvalPlus-v0.1.10.jsonl.gz", compressed=True)
    heldout_prompts = {canonical_prompt(row["problem"]) for row in math_eval}
    heldout_prompts.update(canonical_prompt(row["prompt"]) for row in human_eval)
    contracts = Contracts(ROOT / "design/v0.3/coreta.schema.json")

    selected = []
    for index in GSM_ROWS:
        source = gsm_rows[index]
        task_id = f"gsm8k/train/{index}"
        if task_id in prior_ids or canonical_prompt(source["question"]) in prior_prompts | heldout_prompts:
            raise ValueError("GSM task is previously used or duplicates a protected prompt: " + task_id)
        public = public_task("gsm8k", source, row_number=index)
        contracts.validate("PublicTask", public)
        selected.append({"public": public, "family": "gsm8k", "source_id": task_id,
                         "source_row_sha256": json_sha(source), "evaluation": {
                             "task_id": task_id,
                             "answer": source["answer"].rsplit("####", 1)[1].strip().replace(",", "")}})
    for source_id in MBPP_IDS:
        source = mbpp_by_id[source_id]
        task_id = f"mbpp/train/{source_id}"
        if task_id in prior_ids or canonical_prompt(source["prompt"]) in prior_prompts | heldout_prompts:
            raise ValueError("MBPP task is previously used or duplicates a protected prompt: " + task_id)
        public = public_task("mbpp", source)
        contracts.validate("PublicTask", public)
        selected.append({"public": public, "family": "mbpp", "source_id": task_id,
                         "source_row_sha256": json_sha(source), "evaluation": {
                             "task_id": task_id, "test_imports": source["test_imports"],
                             "test_list": source["test_list"]}})

    OUT.mkdir(parents=True)
    (OUT / "public").mkdir()
    (OUT / "evaluation").mkdir()
    task_index, math_gold, mbpp_tests = [], [], []
    for row in selected:
        public = row["public"]
        filename = hashlib.sha256(public["task_id"].encode()).hexdigest()[:16] + ".json"
        destination = OUT / "public" / filename
        write_json(destination, public)
        task_index.append({"task_id": public["task_id"], "family": row["family"],
                           "path": "public/" + filename, "sha256": sha(destination),
                           "source_row_sha256": row["source_row_sha256"], "pilot": False})
        if row["family"] == "gsm8k":
            math_gold.append(row["evaluation"])
        else:
            mbpp_tests.append(row["evaluation"])
    write_json(OUT / "tasks.json", task_index)
    write_json(OUT / "evaluation/math_gold.json", math_gold)
    write_json(OUT / "evaluation/mbpp_tests.json", mbpp_tests)
    source_meta = {str(path.relative_to(ROOT)): sha(path) for path in (
        gsm_path, mbpp_path, src / "math500-test.jsonl", src / "HumanEvalPlus-v0.1.10.jsonl.gz",
        dev / "tasks.json", ROOT / "engineering/DEVELOPMENT_POOL_QUALITY_AUDIT_20261019.json")}
    manifest = {
        "version": "complementarity-challenge/1",
        "selection": "preselected untried train tasks by multi-step reference solution or nontrivial algorithm/test count; manual contract review before any new model output",
        "task_count": len(task_index), "family_counts": {"gsm8k": len(math_gold), "mbpp": len(mbpp_tests)},
        "tasks_sha256": sha(OUT / "tasks.json"),
        "evaluation_sha256": {name: sha(OUT / "evaluation" / name) for name in ("math_gold.json", "mbpp_tests.json")},
        "source_sha256": source_meta, "model_calls": 0,
        "quality_limit": "manual review of seven selected records; not formal proof of benchmark validity",
    }
    write_json(OUT / "manifest.json", manifest)
    print(json.dumps({"bundle": str(OUT), "tasks": [row["task_id"] for row in task_index],
                      "counts": manifest["family_counts"], "model_calls": 0}, ensure_ascii=False))


if __name__ == "__main__":
    prepare()
