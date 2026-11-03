"""Prepare D0 diagnostics or run only the explicitly bounded schema-copy checks."""
import argparse
import json
from pathlib import Path

from coreta.workboard_d0.preparation import prepare_compatibility, prepare_snapshots, run_compatibility


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare-copy", "run-copy", "prepare-repair"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--dataset", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output must be a new directory")
    if args.action == "prepare-copy":
        result = prepare_compatibility(args.output, args.input)
        fields = ("kind", "max_http_attempts", "max_output_tokens")
    elif args.action == "run-copy":
        result = run_compatibility(args.input, args.output)
        fields = ("kind", "status", "actual_http_attempts", "service_compatibility_verified")
    else:
        if args.dataset is None:
            parser.error("prepare-repair requires --dataset")
        result = prepare_snapshots(args.output, args.input, args.dataset)
        fields = ("kind", "max_http_attempts", "max_output_tokens", "live_calls")
    print(json.dumps({k: result[k] for k in fields}, ensure_ascii=False))
    return 2 if result.get("status") == "stopped_on_first_error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
