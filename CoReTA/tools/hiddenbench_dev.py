"""Explicit preparation/run for the fixed four-task development batch."""
import argparse
import json
import os
from pathlib import Path
from coreta.workboard.choice_experiment import prepare,run


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["prepare","run"])
    parser.add_argument("--dataset",type=Path)
    parser.add_argument("--prepared",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--live",action="store_true")
    args=parser.parse_args()
    if args.command=="prepare" and args.dataset is None: parser.error("Preparation requires --dataset")
    if args.command=="run" and (args.prepared is None or not args.live or not os.environ.get("DEEPSEEK_API_KEY")):
        parser.error("Run requires --prepared, --live and configured API key")
    value=prepare(args.dataset,args.output) if args.command=="prepare" else run(args.prepared,args.output)
    print(json.dumps({"status":value.get("status","prepared"),"max_http_attempts":value["max_http_attempts"]}))
