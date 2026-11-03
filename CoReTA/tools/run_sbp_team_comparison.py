"""Execute the eight fixed team cells after calibration, without score feedback."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from coreta.handoff.ranking import parse_ranking

ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT / "runs/student-president-v2-prepared-20261021"
PACK = ROOT / "data/task-packs/student-president-dev-v1"


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.live or not os.environ.get("DEEPSEEK_API_KEY"):
        parser.error("Requires --live and configured DEEPSEEK_API_KEY")
    calibration = json.loads((ROOT / "runs/student-president-v2-calibration-20261021/batch.json").read_text(encoding="utf-8"))
    if calibration["status"] != "completed" or len(calibration["cells"]) != 12:
        parser.error("Calibration must be completed and reviewed first")
    matrix = json.loads((PREPARED / "matrix.json").read_text(encoding="utf-8"))
    cells = [c for c in matrix["cells"] if c["phase"] == "team"]
    if len(cells) != 8 or any(c["max_http_attempts"] != 20 for c in cells):
        parser.error("Expected fixed eight team cells, each at most 20 attempts")
    for cell in cells:
        manifest = json.loads((Path(cell["prepared_directory"]) / "manifest.json").read_text(encoding="utf-8"))
        for filename, digest in manifest["source_hashes"].items():
            if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != digest:
                parser.error("Prepared source changed: " + filename)
        for filename, digest in manifest["member_packet_hashes"].items():
            if hashlib.sha256((PACK / filename).read_bytes()).hexdigest() != digest:
                parser.error("Prepared input changed: " + filename)
        expected = [sys.executable, "-m", "coreta.application_v2", "run", "--pack", str(PACK),
                    "--condition", cell["condition"], "--system", cell["system"], "--task-ordinal", "1",
                    "--output", str((PREPARED / "future-runs" / cell["cell"]).resolve()), "--live"]
        if cell["future_run_argv"] != expected or Path(expected[-2]).exists():
            parser.error("Unexpected arguments or existing team run: " + cell["cell"])
    names = {item["name"] for item in json.loads((PACK / "public/task.json").read_text(encoding="utf-8"))["items"]}
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"kind": "real_fixed_team_development_comparison", "status": "running", "started_at": now(),
              "planned_cells": 8, "max_http_attempts": 160, "cells": [], "active_cell": None,
              "scoring_feedback": False, "calibration_review": "SBP_CALIBRATION_RESULTS_20261021.md and user authorization"}
    batch_path = args.output / "batch.json"
    write(batch_path, report)
    try:
        for cell in cells:
            report["active_cell"] = cell["cell"]
            write(batch_path, report)
            print(json.dumps({"starting": cell["cell"]}), flush=True)
            process = subprocess.run(cell["future_run_argv"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
            for name, value in (("stdout", process.stdout), ("stderr", process.stderr)):
                (args.output / f"{cell['cell']}.{name}.txt").write_text(value, encoding="utf-8")
            target = Path(cell["future_run_argv"][-2])
            result = json.loads((target / "result.json").read_text(encoding="utf-8")) if (target / "result.json").exists() else {}
            _, delivery_error = parse_ranking(result.get("artifact"), names)
            row = {"cell": cell["cell"], "condition": cell["condition"], "system": cell["system"],
                   "repetition": cell["repetition"], "run_directory": str(target), "returncode": process.returncode,
                   "status": result.get("status"), "stop_reason": result.get("stop_reason"),
                   "http_attempts": result.get("http_attempts"), "logical_calls": result.get("logical_calls"),
                   "format_repairs": result.get("format_repairs"), "usage_complete": result.get("usage_complete"),
                   "uncertain_usage_attempts": result.get("uncertain_usage_attempts"), "delivery_error": delivery_error}
            report["cells"].append(row)
            report["active_cell"] = None
            clean = (process.returncode == 0 and row["status"] in {"reviewed_no_defect", "best_effort_unreviewed", "best_effort_unresolved"}
                     and delivery_error is None and row["format_repairs"] == 0 and row["usage_complete"] is True
                     and row["uncertain_usage_attempts"] == 0 and row["http_attempts"] == row["logical_calls"])
            print(json.dumps(row), flush=True)
            if not clean:
                report["status"] = "stopped_for_diagnosis"
                break
        else:
            report["status"] = "completed"
    except BaseException as exc:
        report["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "runner_error"
        report["exception_type"] = type(exc).__name__
        raise
    finally:
        report["ended_at"] = now()
        report["recorded_completed_cell_attempts"] = sum(c["http_attempts"] or 0 for c in report["cells"])
        write(batch_path, report)
    return 0 if report["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
