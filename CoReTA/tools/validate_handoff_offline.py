"""Persist focused offline test evidence. Never launch a model experiment."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Run only handoff offline fixtures and save validation evidence")
    parser.add_argument("--output", type=Path, required=True, help="New nonexistent report directory")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    stream = io.StringIO()
    started = time.monotonic()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_handoff.py")
    with patch("urllib.request.urlopen", side_effect=AssertionError("Real network forbidden in offline validation")):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    paths = sorted((ROOT / "src/coreta/handoff").glob("*.py")) + [
        ROOT / "src/coreta/model_client.py", ROOT / "src/coreta/schemas.py",
        ROOT / "tests/test_handoff.py", ROOT / "tools/validate_handoff_offline.py",
        ROOT / "design/expertise-handoff/protocol-v1/PROMPTS.md",
        ROOT / "design/expertise-handoff/protocol-v1/message.schema.json",
        ROOT / "design/expertise-handoff/protocol-v1/runtime.defaults.json",
        ROOT / "config/deepseek_flash_inspection.json",
        ROOT / "tools/check_handoff_payloads.py", ROOT / "tools/check_handoff_live_compatibility.py",
        ROOT / "data/tokenizer-v4.1-flash-1017/tokenizer.json",
    ]
    paths += sorted((ROOT / "data/task-packs/moon-survival-v1/packets").glob("*/*.json"))
    paths += [ROOT / "data/task-packs/moon-survival-v1/offline/evaluator.json",
              ROOT / "data/task-packs/moon-survival-v1/public/task.json"]
    report = {
        "kind": "offline_engineering_validation_not_model_results",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "passed": result.wasSuccessful(),
        "duration_seconds": time.monotonic() - started,
        "real_model_calls": 0,
        "transport": "Scripted responses/exceptions, never a remote model",
        "network_guard": "In-process urllib requests blocked; child CLI commands cover only help/prepare/score and explicit refusal paths",
        "scope": ["packet permissions", "dynamic references", "all six packet allocations",
                  "normal and ask/check/probe flows", "empty replies", "format recovery",
                  "shared attempt cap", "timeout and context overflow", "candidate retention",
                  "work-version review binding", "baseline and independent branches",
                  "strict ranking parser and offline CLI scoring", "structured ranking permutations",
                  "deterministic rendering with explanation separated", "local tokenizer availability"],
        "not_established": ["Live API compatibility", "Real-model format compliance",
                            "Expertise advantage", "CoReTA capability gain", "Mechanism efficacy",
                            "Cross-run independent-answer pairing"],
        "source_hashes": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
    }
    (args.output / "unittest.log").write_text(stream.getvalue(), encoding="utf-8")
    (args.output / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("tests_run", "failures", "errors", "passed", "real_model_calls")}))
    print(str(args.output / "validation.json"))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
