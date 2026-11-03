"""Freeze official source data and select development tasks before any model outcomes."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as parquet

from coreta.schemas import Contracts
from coreta.state import write_json
from coreta.tasks import canonical_prompt, public_task, select_ids


SOURCES = {
    "gsm8k": ("https://huggingface.co/datasets/openai/gsm8k/resolve/740312add88f781978c0658806c59bc2815b9866/main/train-00000-of-00001.parquet", "gsm8k-train.parquet"),
    "mbpp": ("https://huggingface.co/datasets/google-research-datasets/mbpp/resolve/4bb6404fdc6cacfda99d4ac4205087b89d32030c/sanitized/train-00000-of-00001.parquet", "mbpp-sanitized-train.parquet"),
    "math500": ("https://huggingface.co/datasets/HuggingFaceH4/MATH-500/resolve/6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be/test.jsonl", "math500-test.jsonl"),
    "humaneval": ("https://github.com/evalplus/humanevalplus_release/releases/download/v0.1.10/HumanEvalPlus.jsonl.gz", "HumanEvalPlus-v0.1.10.jsonl.gz"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_source(key, cache):
    url, filename = SOURCES[key]
    destination = cache / filename
    if not destination.exists():
        partial = destination.with_suffix(destination.suffix + ".partial")
        with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as stream:
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
        partial.replace(destination)
    if filename.endswith(".parquet"):
        rows = parquet.read_table(destination).to_pylist()
    else:
        opener = gzip.open if filename.endswith(".gz") else open
        with opener(destination, "rt", encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream if line.strip()]
    return rows, {"url": url, "file": str(destination.resolve()), "sha256": sha(destination), "rows": len(rows)}


def prepare(cache, output, design_root):
    if output.exists():
        raise ValueError("Frozen output already exists; choose a new bundle directory")
    cache.mkdir(parents=True, exist_ok=True)
    sources, metadata = {}, {}
    for key in SOURCES:
        sources[key], metadata[key] = load_source(key, cache)
        print(f"Loaded {key}: {len(sources[key])} rows", flush=True)
    if len(sources["math500"]) != 500 or len(sources["humaneval"]) != 164:
        raise ValueError("Official evaluation mother-data sizes do not match the design")
    contracts = Contracts(design_root / "coreta.schema.json")
    eval_prompts = {canonical_prompt(row["problem"]) for row in sources["math500"]}
    eval_prompts.update(canonical_prompt(row["prompt"]) for row in sources["humaneval"])
    selected, skipped = {}, []
    for family in ("gsm8k", "mbpp"):
        candidates = {}
        for index, row in enumerate(sources[family]):
            task_id = f"gsm8k/train/{index}" if family == "gsm8k" else f"mbpp/train/{row['task_id']}"
            if task_id in candidates:
                raise ValueError("Duplicate canonical source id")
            candidates[task_id] = (index, row)
        selected[family] = []
        seen = set(eval_prompts)
        for task_id in select_ids(candidates, "coreta-dev-v1", len(candidates)):
            index, row = candidates[task_id]
            source_prompt = row["question"] if family == "gsm8k" else row["prompt"]
            normalized = canonical_prompt(source_prompt)
            if normalized in seen:
                skipped.append({"task_id": task_id, "reason": "normalized_prompt_duplicate"})
                continue
            try:
                public = public_task(family, row, row_number=index)
            except (ValueError, SyntaxError) as exc:
                skipped.append({"task_id": task_id, "reason": type(exc).__name__, "detail": str(exc)})
                continue
            contracts.validate("PublicTask", public)
            seen.add(normalized)
            selected[family].append((public, row))
            if len(selected[family]) == 50:
                break
    output.mkdir(parents=True)
    (output / "public").mkdir()
    (output / "evaluation").mkdir()
    task_index, gold, mbpp_tests = [], [], []
    for family in ("gsm8k", "mbpp"):
        for position, (public, source) in enumerate(selected[family]):
            filename = hashlib.sha256(public["task_id"].encode()).hexdigest()[:16] + ".json"
            destination = output / "public" / filename
            write_json(destination, public)
            task_index.append({"task_id": public["task_id"], "family": family, "path": "public/" + filename,
                               "sha256": sha(destination), "engineering": position < 3, "pilot": position < 10})
            if family == "gsm8k":
                if "####" not in source["answer"]:
                    raise ValueError("GSM8K official answer delimiter missing")
                gold.append({"task_id": public["task_id"], "answer": source["answer"].rsplit("####", 1)[1].strip().replace(",", "")})
            else:
                mbpp_tests.append({"task_id": public["task_id"], "test_imports": source["test_imports"], "test_list": source["test_list"]})
    write_json(output / "tasks.json", task_index)
    write_json(output / "evaluation/math_gold.json", gold)
    write_json(output / "evaluation/mbpp_tests.json", mbpp_tests)
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "sources": metadata,
                "selection_prefix": "coreta-dev-v1", "counts": {family: len(rows) for family, rows in selected.items()},
                "pilot_counts": {family: min(10, len(rows)) for family, rows in selected.items()},
                "skipped": skipped, "task_index_sha256": sha(output / "tasks.json"),
                "evaluation_files": {name: sha(output / "evaluation" / name) for name in ("math_gold.json", "mbpp_tests.json")},
                "dedup": "NFKC plus whitespace; source public prompts checked against all MATH-500/HumanEval prompts",
                "model_calls": 0, "evaluation_scores": None}
    write_json(output / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--design-root", type=Path, default=Path(__file__).resolve().parents[1] / "design/v0.3")
    args = parser.parse_args()
    report = prepare(args.cache, args.output, args.design_root)
    print(json.dumps({"counts": report["counts"], "pilot_counts": report["pilot_counts"], "model_calls": 0}))


if __name__ == "__main__":
    main()
