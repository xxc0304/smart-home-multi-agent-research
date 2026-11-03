"""Run only the twelve predeclared independent calibration cells, stop on trouble."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT / "runs/student-president-v2-prepared-20261021"


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
    matrix = json.loads((PREPARED / "matrix.json").read_text(encoding="utf-8"))
    cells = [c for c in matrix["cells"] if c["phase"] == "calibration"]
    if len(cells) != 12 or sum(c["max_http_attempts"] for c in cells) != 48:
        parser.error("Expected fixed twelve cells with 48 total maximum attempts")
    # Validate every fixed code/input snapshot before the first paid call.
    for cell in cells:
        folder = Path(cell["prepared_directory"])
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        for filename, digest in manifest["source_hashes"].items():
            if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != digest:
                parser.error("Prepared source changed: " + filename)
        pack = ROOT / "data/task-packs/student-president-dev-v1"
        for filename, digest in manifest["member_packet_hashes"].items():
            if hashlib.sha256((pack / filename).read_bytes()).hexdigest() != digest:
                parser.error("Prepared input changed: " + filename)
        expected = [sys.executable, "-m", "coreta.application_v2", "run", "--pack", str(pack),
                    "--condition", cell["condition"], "--system", "independent", "--task-ordinal", "1",
                    "--member", cell["member"], "--output", str((PREPARED / "future-runs" / cell["cell"]).resolve()), "--live"]
        if cell["future_run_argv"] != expected:
            parser.error("Unexpected prepared arguments")
        target = Path(expected[-2])
        if target.exists():
            parser.error("Refuse to repeat an existing cell: " + cell["cell"])
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"kind": "real_independent_information_calibration_not_team_comparison", "status": "running",
              "started_at": now(), "planned_cells": 12, "max_http_attempts": 48, "cells": [],
              "team_runs_started": False, "scoring_feedback": False, "active_cell": None}
    batch_path = args.output / "batch.json"
    write(batch_path, report)
    try:
        for cell in cells:
            report["active_cell"] = cell["cell"]
            write(batch_path, report)
            print(json.dumps({"starting": cell["cell"]}), flush=True)
            process = subprocess.run(cell["future_run_argv"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
            (args.output / f"{cell['cell']}.stdout.txt").write_text(process.stdout, encoding="utf-8")
            (args.output / f"{cell['cell']}.stderr.txt").write_text(process.stderr, encoding="utf-8")
            target = Path(cell["future_run_argv"][-2])
            result = json.loads((target / "result.json").read_text(encoding="utf-8")) if (target / "result.json").exists() else {}
            row = {"cell": cell["cell"], "condition": cell["condition"], "member": cell["member"],
                   "repetition": cell["repetition"], "run_directory": str(target), "returncode": process.returncode,
                   "status": result.get("status"), "http_attempts": result.get("http_attempts"),
                   "format_repairs": result.get("format_repairs"), "usage_complete": result.get("usage_complete"),
                   "uncertain_usage_attempts": result.get("uncertain_usage_attempts")}
            report["cells"].append(row)
            report["active_cell"] = None
            clean = (process.returncode == 0 and row["status"] == "independent_collected"
                     and row["format_repairs"] == 0 and row["usage_complete"] is True
                     and row["uncertain_usage_attempts"] == 0 and row["http_attempts"] == 1
                     and set(result.get("independent_answers", {})) == {cell["member"]})
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
