"""Explicit opt-in entry for the constructive revision; no automatic experiments."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from pathlib import Path

from .closure import ClosureContracts as RevisionContracts
from .closure_format import FormatClosureClient as DeepSeekClient
from .closure_format import FormatClosureRunner as RevisionRunner
from .revision import REVISION_SYSTEMS
from .state import write_json


PROJECT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description="Run one public task with the opt-in constructive revision")
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=PROJECT / "config/deepseek_flash_closure.json")
    parser.add_argument("--tokenizer", type=Path)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--system", choices=tuple(REVISION_SYSTEMS), default="coreta_revision")
    parser.add_argument("--draft-bank", type=Path)
    parser.add_argument("--draft-only", action="store_true", help="Generate three independent drafts only")
    args = parser.parse_args()
    if not args.live:
        parser.error("No requests sent. Explicit --live is required for a real model run.")
    if not os.environ.get("DEEPSEEK_API_KEY"):
        parser.error("DEEPSEEK_API_KEY is not configured.")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if config["model"] != "deepseek-flash" or config["base_url"] != "https://api.deepseek.com":
        parser.error("This entry targets the approved official deepseek-flash endpoint")
    if config["protocol"]["max_work_turns"] != 2:
        parser.error("Revision budget assumes two work turns")
    # Map new phases explicitly; leave the old config file unchanged.
    legacy = PROJECT / "design/v0.3/coreta.schema.json"
    prompt_path = PROJECT / "design/closure_prompts.json"
    contracts = RevisionContracts(legacy)
    task = json.loads(args.task.read_text(encoding="utf-8"))
    contracts.validate("PublicTask", task)
    prompts = json.loads(prompt_path.read_text(encoding="utf-8"))
    token_counter = None
    if args.tokenizer:
        from tokenizers import Tokenizer
        tokenizer = Tokenizer.from_file(str(args.tokenizer))
        token_counter = lambda value: len(tokenizer.encode(value, add_special_tokens=False).ids)
    args.output.mkdir(parents=True, exist_ok=False)
    run_id = "coreta-closure-format-" + uuid.uuid4().hex[:12]
    runner = RevisionRunner(task, args.output, run_id, contracts, None, config, prompts, args.seed,
                            system=args.system, draft_bank=args.draft_bank)
    runner.client = DeepSeekClient(config, runner.log, token_counter=token_counter)
    sources = [legacy, prompt_path, args.config, Path(__file__), Path(__file__).with_name("revision.py"), Path(__file__).with_name("closure.py"), Path(__file__).with_name("closure_feedback.py"), Path(__file__).with_name("closure_diff.py"), Path(__file__).with_name("closure_format.py"),
               Path(__file__).with_name("model_client.py"), Path(__file__).with_name("schemas.py"),
               Path(__file__).with_name("state.py")]
    write_json(args.output / "manifest.json", {"run_id": run_id, "system": args.system, "config": config,
        "normal_call_cap": 3 if args.draft_only else runner.CAP,
        "phase": "draft_screen" if args.draft_only else "comparison",
        "protocol_variant": "inspection_format_v1",
        "draft_bank": str(args.draft_bank) if args.draft_bank else None,
        "logical_seed": args.seed, "seed_supported": False,
        "input_count_mode": runner.client.count_mode, "revision_pinnable": False,
        "source_hashes": {str(p.relative_to(PROJECT)) if p.is_relative_to(PROJECT) else str(p):
                          hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "tokenizer_sha256": hashlib.sha256(args.tokenizer.read_bytes()).hexdigest() if args.tokenizer else None})
    write_json(args.output / "contract_snapshot.json", contracts.document)
    write_json(args.output / "public_task.json", task)
    try:
        result = runner.run_drafts() if args.draft_only else runner.run()
    except Exception as exc:
        write_json(args.output / "implementation_error.json", {"type": type(exc).__name__, "message": str(exc)})
        raise
    print(json.dumps({k: result[k] for k in ("run_id", "status", "phase", "stop_reason", "normal_calls",
                                            "format_repairs", "http_attempts") if k in result}))


if __name__ == "__main__":
    main()
