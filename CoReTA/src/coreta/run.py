"""Explicit single-task entry point. Imports and --help perform no network calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .model_client import DeepSeekClient
from .prompts import Prompts
from .protocol import Runner, SYSTEM_CAPS
from .schemas import Contracts
from .state import State, write_json


PROJECT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description="Run one public CoReTA task; no automatic scoring or code execution")
    parser.add_argument("--task", type=Path, required=True, help="PublicTask JSON, with no evaluator fields")
    parser.add_argument("--config", type=Path, default=PROJECT / "config/deepseek_flash.json")
    parser.add_argument("--design-root", type=Path, default=PROJECT / "design/v0.3")
    parser.add_argument("--system", choices=tuple(SYSTEM_CAPS), default="coreta")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--output", type=Path, required=True, help="New, nonexistent single-run directory")
    parser.add_argument("--live", action="store_true", help="Actually send requests to the configured DeepSeek endpoint")
    parser.add_argument("--tokenizer", type=Path, help="Local tokenizer.json for serialized-request token estimates; not server chat-template counts")
    parser.add_argument("--draft-bank", type=Path, help="Shared independent drafts for sequential paired-system runs")
    args = parser.parse_args()
    if not args.live:
        parser.error("No requests sent. A real model run requires explicit --live.")
    if not os.environ.get("DEEPSEEK_API_KEY"):
        parser.error("DEEPSEEK_API_KEY is not configured; no requests sent or run directory created.")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if config["model"] != "deepseek-flash" or config["base_url"] != "https://api.deepseek.com":
        parser.error("This prototype currently targets the approved official deepseek-flash endpoint")
    if config["protocol"]["max_work_turns"] != 2:
        parser.error("v0.3 caps assume exactly two work turns")
    contracts = Contracts(args.design_root / "coreta.schema.json")
    task = json.loads(args.task.read_text(encoding="utf-8"))
    contracts.validate("PublicTask", task)
    prompts = Prompts(args.design_root / "PROMPTS.md")
    token_counter = None
    if args.tokenizer:
        from tokenizers import Tokenizer
        tokenizer = Tokenizer.from_file(str(args.tokenizer))
        token_counter = lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids)
    args.output.mkdir(parents=True, exist_ok=False)
    run_id = "coreta-" + uuid.uuid4().hex[:12]
    state = State(task, run_id, args.output, contracts)
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in
              (args.design_root / "coreta.schema.json", args.design_root / "PROMPTS.md", args.config)}
    write_json(args.output / "manifest.json", {"run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat(),
               "system": args.system, "logical_seed": args.seed, "config": config, "source_hashes": hashes,
               "tokenizer_path": str(args.tokenizer) if args.tokenizer else None,
               "tokenizer_sha256": hashlib.sha256(args.tokenizer.read_bytes()).hexdigest() if args.tokenizer else None,
               "input_count_mode": "local_tokenizer_estimate" if token_counter else "conservative_utf8_bytes",
               "seed_supported": False, "revision_pinnable": False})
    write_json(args.output / "public_task.json", task)
    client = DeepSeekClient(config, state.log, token_counter=token_counter)
    try:
        result = Runner(state, client, prompts, config, system=args.system, seed=args.seed,
                        draft_bank=args.draft_bank).run()
    except Exception as exc:
        # Distinguish implementation failures from model/protocol degradation; do not fabricate an answer.
        write_json(args.output / "implementation_error.json", {"type": type(exc).__name__, "message": str(exc)})
        raise
    print(json.dumps({key: result[key] for key in ("run_id", "status", "normal_calls", "format_repairs", "http_attempts")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
