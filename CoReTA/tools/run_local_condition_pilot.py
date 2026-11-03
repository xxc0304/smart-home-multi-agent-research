"""Run frozen requests once; never read offline labels. Stop on first failure."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from jsonschema import validate
from coreta.model_client import DeepSeekClient


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def run(prepared, output, transport=None):
    manifest = read(prepared/"manifest.json")
    root = Path(__file__).resolve().parents[1]
    for name, expected in manifest["code_sha256"].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError("frozen code changed")
    # Verify request/config files only. The live runner never opens offline labels.
    names = {s["request"] for s in manifest["schedule"]} | {"config.json"}
    for name in names:
        if hashlib.sha256((prepared/name).read_bytes()).hexdigest() != manifest["files"][name]:
            raise ValueError("frozen file changed")
    if len(manifest["schedule"]) != 24 or manifest["max_requests"] != 24:
        raise ValueError("unexpected schedule")
    if output.exists():
        raise ValueError("new output directory required; no resume")
    output.mkdir(parents=True)
    (output/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    state = dict(status="running", attempts=0, input_tokens=0, output_tokens=0, completed=[])
    def save():
        (output/"progress.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    def log(name, value):
        with (output/name).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(value, ensure_ascii=False) + "\n")
        if name == "responses.jsonl":
            usage = value.get("response", {}).get("usage", {})
            for key in ("input_tokens", "output_tokens"):
                if type(usage.get(key)) is not int or usage[key] < 0:
                    raise ValueError("unknown usage; batch stopped")
                state[key] += usage[key]
    config = read(prepared/"config.json")
    if config["base_url"] != "https://api.deepseek.com" or config["protocol"]["transport_retries_per_request"] != 0:
        raise ValueError("destination/retry policy differs")
    client = DeepSeekClient(config, log, transport=transport)
    save()
    try:
        for item in manifest["schedule"]:
            request = read(prepared/item["request"])
            cap = request["max_output_tokens"]
            if client.attempts >= 24 or state["output_tokens"] + cap > 36864:
                raise ValueError("budget exhausted")
            payload = client.payload(request["instructions"], request["schema"], cap)
            raw = client.complete(payload, deadline=time.monotonic()+180, logical_seed=item["repeat"])
            (output/(item["request"]+".raw.txt")).write_text(raw, encoding="utf-8")
            value = strict_json(raw)
            validate(value, request["schema"])
            state["completed"].append({**item, "answer": value})
            state["attempts"] = client.attempts
            save()
        state["status"] = "completed"
    except Exception as exc:
        state.update(status="stopped", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        state["attempts"] = client.attempts
        save()
    return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prepared", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run(args.prepared, args.output)
