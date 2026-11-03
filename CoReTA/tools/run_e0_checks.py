"""Run engineering checks and write their actual unittest outcome as a report."""
import argparse
import importlib.metadata
import json
import platform
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    suite = unittest.defaultTestLoader.discover(str(root / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"created_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
              "platform": platform.platform(), "python": sys.version,
              "packages": {name: importlib.metadata.version(name) for name in ("coreta", "jsonschema", "math-verify")},
              "tests_run": result.testsRun, "success": result.wasSuccessful(),
              "failures": [{"test": str(test), "traceback": text} for test, text in result.failures],
              "errors": [{"test": str(test), "traceback": text} for test, text in result.errors],
              "skipped": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
              "scope": "scripted model protocol tests and Windows math adapter diagnostics; not real experiments",
              "real_model_calls": 0, "linux_container_scoring_executed": False}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
