"""Prepare fixed calibration/team inputs without network calls or score access."""
import argparse
import contextlib
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

from coreta.application_v2.__main__ import main as prepare_main

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "data/task-packs/student-president-dev-v1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cells = []
    views = [("shared", "none", "A1"), ("all", "full", "A1")] + [(f"local_{a}", "distributed", a) for a in ("A1", "A2", "A3", "A4")]
    for repetition in (1, 2):
        for view, condition, member in views:
            cells.append({"cell": f"A-{view}-r{repetition}", "phase": "calibration", "condition": condition,
                          "system": "independent", "member": member, "repetition": repetition, "max_http_attempts": 4})
    for repetition in (1, 2):
        for condition in ("concentrated_A1", "distributed"):
            for system in ("ordinary_discussion", "coreta"):
                cells.append({"cell": f"B-{condition}-{system}-r{repetition}", "phase": "team",
                              "condition": condition, "system": system, "member": None,
                              "repetition": repetition, "max_http_attempts": 20})
    for row in cells:
        options = ["--pack", str(PACK), "--condition", row["condition"], "--system", row["system"], "--task-ordinal", "1"]
        if row["member"]:
            options += ["--member", row["member"]]
        out = args.output / row["cell"]
        with patch.object(sys, "argv", ["application_v2", "prepare", *options, "--output", str(out)]), contextlib.redirect_stdout(io.StringIO()):
            if prepare_main() != 0:
                raise RuntimeError("Preparation failed")
        row["prepared_directory"] = str(out.resolve())
        row["future_run_argv"] = [sys.executable, "-m", "coreta.application_v2", "run", *options,
                                  "--output", str((args.output / "future-runs" / row["cell"]).resolve()), "--live"]
    report = {"kind": "fixed_development_preparation_not_results", "model_calls": 0, "cells": cells,
              "calibration_logical_calls": 12, "team_runs": 8, "max_http_attempts_if_all_authorized": 208,
              "phase_B_requires_phase_A_review": True, "four_item_live_schema_check_completed": False,
              "initial_stage_only": True, "sampling_seed_sent": False,
              "not_a_test_split": True}
    (args.output / "matrix.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"prepared_cells": len(cells), "model_calls": 0, "phase_B": "pending calibration review"}))


if __name__ == "__main__":
    main()
