"""Offline one-cycle reconstruction and stop-rule checks; no solving evidence."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coreta.handoff.__main__ import PROJECT, DESIGN, configure, load_counter
from coreta.schemas import ProtocolError
from coreta.workboard_d0.continuation import engine, run_unit, prepare_run, run_batch
from coreta.workboard_d0.preparation import read
import test_workboard as fixtures


INPUTS = PROJECT / "runs/workboard-d0-repair-prepared-20261022-r2"


def respond(p):
    stage = p["STAGE"]
    if stage == "CHOOSE":
        value = {"candidate_id": p["CHOICES"][-1], "reason": "SCRIPTED selection only"}
        if "FOCUS" in p:
            focus = p["FOCUS"]
            value["focus_disposition"] = ({"focus_id": focus["id"], "status": "pending",
                                           "reason": "SCRIPTED unresolved"} if focus else None)
            value["next_check"] = None if focus else {"target": p["AFTER"]["id"],
                "question": "SCRIPTED local condition?", "check": "SCRIPTED wording comparison", "refs": ["T"]}
        return value
    if stage == "OBSERVE":
        offer = {"target": p["CURRENT_WORK"]["id"], "knowledge": "SCRIPTED knowledge",
                 "support": [{"ref": "T", "excerpt": "SCRIPTED excerpt"}], "proposed_use": "SCRIPTED apply"}
        if "FOCUS" in p:
            offer["responds_to"] = (p["FOCUS"] or {}).get("id")
        return {"action": "offer", "offer": offer}
    if stage == "TRY":
        return {"action": "new", "candidate_id": None, "reason": None, "declared_sources": [p["TARGET_OFFER"]["ref"]],
                "use_record": "SCRIPTED actual fixture revision, not a solution",
                "work": {"artifact": p["TASK"]["choices"][0]["id"], "work_text": "SCRIPTED only", "open_points": []}}
    if stage in {"CHECK_USE", "CHECK_EFFECT"}:
        return {"finding": "no_issue_found", "observation": "SCRIPTED limited check", "scope": "fixture"}
    raise AssertionError(stage)


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="coreta-local-continuation-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        guard = patch("urllib.request.urlopen", side_effect=AssertionError("Offline checks forbid network"))
        guard.start()
        self.addCleanup(guard.stop)
        self.config, self.legacy = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
        self.counter = load_counter()

    def unit(self, system="d0_continuation", number="004", handler=respond, suffix="unit"):
        checkpoint = INPUTS / f"hb-dev-{number}-r1-c1"
        folder = self.root / suffix
        # Script parses actual outgoing instructions, not a separate schema mock.
        script = fixtures.Script(None, handler)
        result = run_unit(folder, checkpoint, system, self.config, self.legacy, self.counter, script)
        return result, script, folder

    def test_native_three_and_four_member_paths_match_frozen_first_requests(self):
        for number, count in (("004", 7), ("001", 8)):
            for system in ("v3_continuation", "d0_continuation"):
                with self.subTest(number=number, system=system):
                    result, script, _ = self.unit(system, number, suffix=number + system)
                    self.assertEqual(result["status"], "completed", result["error"])
                    self.assertEqual(result["transport_attempts"], count)
                    self.assertEqual(result["actual_http_attempts"], 0)
                    self.assertEqual(script.calls[0]["STAGE"], "CHOOSE")
                    self.assertEqual(script.calls[-1]["STAGE"], "CHOOSE")
                    self.assertFalse(any(p["STAGE"].startswith("FINAL") for p in script.calls))
                    remaining = [p["BUDGET"]["remaining_network_attempts"] for p in script.calls
                                 if p["STAGE"] == "OBSERVE"]
                    self.assertEqual(remaining, [count - 1] * len(remaining) if system == "d0_continuation"
                                     else list(range(count - 1, count - 1 - len(remaining), -1)))
                    if system == "d0_continuation":
                        self.assertEqual(result["focus_history"][0]["status"], "deferred")
                        trial = next(p for p in script.calls if p["STAGE"] == "TRY")
                        self.assertEqual(trial["FOCUS"]["id"], "Q1")
                        self.assertTrue(trial["APPLICATION_FEEDBACK"])

    def test_original_rotation_and_private_materials_are_preserved(self):
        result, script, _ = self.unit()
        snapshot = read(INPUTS / "hb-dev-004-r1-c1/snapshot.json")
        observers = [p for p in script.calls if p["STAGE"] == "OBSERVE"]
        self.assertTrue(all(p["FOCUS_HISTORY"] == observers[0]["FOCUS_HISTORY"] for p in observers))
        for p in script.calls:
            source = read(INPUTS / f"hb-dev-004-r1-c1/{p['SELF']['agent_id']}.packet.json")
            self.assertEqual(p["SELF_MATERIALS"], source["SELF_MATERIALS"])
        trial = next(p for p in script.calls if p["STAGE"] == "TRY")
        authors = [p["SELF"]["agent_id"] for p in observers]
        team = observers[0]["SELF"]["team"]
        selected = min(authors, key=lambda a: (snapshot["attempt_counts"][a],
                         (team.index(a) - snapshot["pointer"]) % len(team)))
        self.assertEqual(trial["TARGET_OFFER"]["author"], selected)

    def test_all_pass_and_unable_are_bounded_normal_ends(self):
        for mode in ("all_pass", "unable"):
            def handler(p):
                if mode == "all_pass" and p["STAGE"] == "OBSERVE":
                    return {"action": "pass", "offer": None}
                if mode == "unable" and p["STAGE"] == "TRY":
                    return {"action": "unable", "candidate_id": None, "work": None, "use_record": None,
                            "reason": "SCRIPTED obstacle", "declared_sources": []}
                return respond(p)
            result, script, _ = self.unit(handler=handler, suffix=mode)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["transport_attempts"], 3 if mode == "all_pass" else 4)
            self.assertFalse(any(p["STAGE"].startswith("CHECK") for p in script.calls))
            self.assertEqual(result["focus_history"][0]["status"], "deferred")

    def test_partial_trial_uses_explicit_complete_fallback(self):
        def handler(p):
            value = respond(p)
            if p["STAGE"] == "TRY":
                value["work"]["artifact"] = None
            return value
        result, _, _ = self.unit(handler=handler)
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["delivery_used_fallback"])
        self.assertTrue(result["selected_work"]["deliverable_shape"])

    def test_technical_error_stops_batch_leaving_rest_unstarted(self):
        prepared = self.root / "prepared"
        manifest = prepare_run(INPUTS, prepared, ["hb-dev-034-r1-c2", "hb-dev-004-r1-c1"])
        self.assertEqual(manifest["max_http_attempts"], 28)
        self.assertEqual(manifest["max_output_tokens"], 61440)
        def factory(row):
            return fixtures.Script(None, lambda p: "NOT JSON")
        result = run_batch(prepared, self.root / "batch", factory)
        self.assertEqual(result["status"], "stopped_on_first_error")
        self.assertEqual(result["units"][0]["error"]["code"], "SCHEMA_ERROR")
        self.assertTrue(all(row["status"] == "not_started" for row in result["units"][1:]))
        self.assertEqual(result["actual_http_attempts"], 0)

    def test_changed_first_payload_is_rejected_before_transport(self):
        checkpoint = INPUTS / "hb-dev-004-r1-c1"
        folder = self.root / "engine"
        folder.mkdir()
        script = fixtures.Script(None, respond)
        runner, snapshot, first = engine(folder, checkpoint, "d0_continuation", self.config, self.legacy, self.counter, script)
        first["instructions"] += " CHANGED"
        with self.assertRaisesRegex(ProtocolError, "differs from frozen"):
            runner.choose_local(snapshot["before"]["id"], snapshot["after"]["id"], snapshot["checks"], original=first)
        self.assertEqual(len(script.calls), 0)

    def test_all_18_checkpoint_first_requests_restore_exactly_for_both_methods(self):
        manifest = read(INPUTS / "manifest.json")
        for row in manifest["snapshots"]:
            for method in manifest["methods"]:
                with self.subTest(checkpoint=row["id"], method=method):
                    folder = self.root / (row["id"] + method)
                    folder.mkdir()
                    script = fixtures.Script(None, respond)
                    runner, snapshot, first = engine(folder, INPUTS / row["id"], method,
                                                     self.config, self.legacy, self.counter, script)
                    runner.choose_local(snapshot["before"]["id"], snapshot["after"]["id"],
                                        snapshot["checks"], original=first)
                    self.assertEqual(len(script.calls), 1)


if __name__ == "__main__":
    unittest.main()
