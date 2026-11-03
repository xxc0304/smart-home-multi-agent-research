"""Prepare or execute a separately frozen, bounded local continuation batch."""
import argparse
import json
from pathlib import Path
from coreta.workboard_d0.continuation import prepare_run, run_batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "run"])
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoints", nargs="+")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output must be new; no resume")
    if args.action == "prepare":
        result = prepare_run(args.input, args.output, args.checkpoints or ["hb-dev-034-r1-c2", "hb-dev-004-r1-c1"])
        fields = ("kind", "max_http_attempts", "max_output_tokens")
    else:
        result = run_batch(args.input, args.output)
        fields = ("kind", "status", "actual_http_attempts")
    print(json.dumps({k: result[k] for k in fields}, ensure_ascii=False))
    return 2 if result.get("status") == "stopped_on_first_error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
