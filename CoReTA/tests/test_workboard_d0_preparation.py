"""Offline preparation checks only; do not validate model behavior or scientific claims."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coreta.handoff.__main__ import PROJECT
from coreta.workboard_d0.preparation import (prepare_compatibility, prepare_snapshots,
                                           run_compatibility, read, lines, packet_from_request)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="coreta-d0-preparation-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        guard = patch("urllib.request.urlopen", side_effect=AssertionError("Offline checks forbid network"))
        guard.start()
        self.addCleanup(guard.stop)

    def prepare_copy(self):
        output = self.root / "copy"
        manifest = prepare_compatibility(output, PROJECT / "runs/workboard-d0-engineering-20261022-r1")
        return output, manifest

    @staticmethod
    def copy_response(payload, timeout):
        value = json.loads(payload["instructions"].rsplit("\n", 1)[1])
        return {"status": "completed", "usage": {"input_tokens": 1, "output_tokens": 1},
                "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(value)}]}]}

    def test_copy_cases_and_scripted_pass_never_claim_live_compatibility(self):
        prepared, manifest = self.prepare_copy()
        self.assertEqual(manifest["max_http_attempts"], 8)
        self.assertEqual(manifest["max_output_tokens"], 7168)
        result = run_compatibility(prepared, self.root / "scripted", self.copy_response)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(result["service_compatibility_verified"])
        self.assertEqual(result["actual_http_attempts"], 0)
        self.assertEqual(result["transport_attempts"], 8)

    def test_copy_stops_on_first_mismatch_without_retry(self):
        prepared, _ = self.prepare_copy()
        def bad(payload, timeout):
            response = self.copy_response(payload, timeout)
            value = json.loads(response["output"][0]["content"][0]["text"])
            value["offer"]["knowledge"] = "different fixture"
            response["output"][0]["content"][0]["text"] = json.dumps(value)
            return response
        result = run_compatibility(prepared, self.root / "mismatch", bad)
        self.assertEqual(result["status"], "stopped_on_first_error")
        self.assertEqual(result["transport_attempts"], 1)
        self.assertEqual(result["error"]["code"], "COPY_MISMATCH")

    def test_copy_changed_prepared_request_is_rejected_before_transport(self):
        prepared, manifest = self.prepare_copy()
        request = prepared / (manifest["cases"][0]["id"] + ".request.json")
        request.write_text(request.read_text(encoding="utf-8") + " ", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Prepared copy requests changed"):
            run_compatibility(prepared, self.root / "changed", self.copy_response)

    def test_incomplete_usage_stops_copy_check(self):
        prepared, _ = self.prepare_copy()
        def incomplete(payload, timeout):
            value = self.copy_response(payload, timeout)
            value["usage"].pop("output_tokens")
            return value
        result = run_compatibility(prepared, self.root / "unknown", incomplete)
        self.assertEqual(result["error"]["code"], "USAGE_UNKNOWN")
        self.assertEqual(result["transport_attempts"], 1)
        self.assertEqual(result["incomplete_or_unknown_usage_attempts"], 1)

    def test_all_checkpoints_use_only_past_requests_and_no_gold(self):
        source = PROJECT / "runs/hiddenbench-development-live-20261022-r1"
        dataset = PROJECT / "data/task-packs/hiddenbench-workboard-dev-v1"
        output = self.root / "repair"
        manifest = prepare_snapshots(output, source, dataset)
        self.assertEqual(len(manifest["snapshots"]), 18)
        self.assertEqual(manifest["max_http_attempts"], 264)
        self.assertEqual(manifest["max_output_tokens"], 577536)
        self.assertFalse(manifest["gold_read"])
        self.assertTrue(all("offline" not in p and not p.endswith(("state.json", "result.json"))
                            for p in manifest["source_hashes"]))
        for row in manifest["snapshots"]:
            folder = output / row["id"]
            snapshot = read(folder / "snapshot.json")
            requests = lines(source / row["pair"] / "coreta_workboard/requests.jsonl")
            request = next(r for r in requests if r["call_context"]["logical_call"] == row["source_choose_call"])
            packet = packet_from_request(request)
            prior = [packet_from_request(r) for r in requests
                     if r["call_context"]["logical_call"] < row["source_choose_call"]]
            last_use = next(p for p in reversed(prior) if p["STAGE"] == "CHECK_USE")
            self.assertEqual(snapshot["visible_works"], last_use["CANDIDATES"])
            self.assertEqual(snapshot["before"], packet["BEFORE"])
            self.assertEqual(snapshot["after"], packet["AFTER"])
            self.assertEqual(snapshot["checks"], packet["CHECKS"])
            before_ids = {w["id"] for w in snapshot["visible_works"]}
            self.assertTrue(set(snapshot["choices"]) <= before_ids)
            for method in manifest["methods"]:
                first = packet_from_request({"payload": read(folder / f"{method}.first.request.json")})
                self.assertEqual(first["SELF"]["agent_id"], snapshot["editor"])
                self.assertEqual(first["SELF_MATERIALS"], read(folder / f"{snapshot['editor']}.packet.json")["SELF_MATERIALS"])
                self.assertEqual(first["CHECKS"], snapshot["checks"])
                self.assertNotIn("correct_option_id", json.dumps(first))
            self.assertEqual(row["per_method_calls"], row["members"] + 4)


if __name__ == "__main__":
    unittest.main()
