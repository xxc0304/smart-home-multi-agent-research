"""Paired pilot preparation and full-path checks. Real network is blocked."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import test_workboard as fixtures
from coreta.handoff.__main__ import PROJECT, load_counter
from coreta.schemas import ProtocolError
from coreta.workboard.baseline import DiscussionRunner
from coreta.workboard.contracts import Contracts

spec = importlib.util.spec_from_file_location("workboard_pilot", PROJECT / "tools/workboard_pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class PilotTests(unittest.TestCase):
    setUp = fixtures.WorkboardTests.setUp
    work = fixtures.WorkboardTests.work
    change = fixtures.WorkboardTests.change
    offer = fixtures.WorkboardTests.offer
    respond = fixtures.WorkboardTests.respond

    def cache(self):
        return {"origin": "SCRIPTED_OFFLINE_NOT_MODEL", "member_packet_hashes": self.packets.hashes,
                "candidates": {m: self.work() for m in self.packets.agents}}

    def engine(self, system, handler=None, cache=None):
        journal_proxy = type("Context", (), {})()
        script = fixtures.Script(journal_proxy, handler or self.respond)
        runner = pilot.engine(self.folder, self.packets, self.config, self.legacy, system, 1,
                              load_counter(), cache=self.cache() if cache is None else cache, transport=script)
        return runner, script

    def test_cached_initials_make_no_http(self):
        runner, script = self.engine("coreta_workboard")
        runner.initialize()
        self.assertEqual(script.calls, [])
        self.assertEqual(len(runner.board.initials), 4)
        self.assertEqual(runner.board.get("W1")["artifact"], self.names)

    def test_invalid_cache_rejected(self):
        cache = self.cache()
        cache["member_packet_hashes"] = {}
        runner, script = self.engine("coreta_workboard", cache=cache)
        self.assertEqual(runner.run()["stop_reason"], "INPUT_ERROR")
        self.assertEqual(script.calls, [])

    def test_cache_schema_still_validated(self):
        cache = self.cache()
        cache["candidates"]["A1"]["unexpected"] = True
        runner, _ = self.engine("coreta_workboard", cache=cache)
        self.assertEqual(runner.run()["stop_reason"], "SCHEMA_ERROR")

    def test_equal_call_and_output_ceilings(self):
        ours, baseline = (pilot.settings(self.legacy, s) for s in ("coreta_workboard", "ordinary_discussion"))
        self.assertEqual(ours["limits"], baseline["limits"])
        self.assertEqual(ours["limits"]["max_network_attempts_total"], 25)
        caps = ours["max_output_tokens"]
        actual_ours = 3 * (3 * caps["observe"] + caps["try"] + caps["check_use"] + caps["check_effect"] + caps["choose"])
        actual_ours += caps["finalize"] + caps["final_check_use"] + caps["final_check_effect"] + caps["final_choose"]
        actual_base = 24 * baseline["max_output_tokens"]["discuss"] + baseline["max_output_tokens"]["finalize"]
        self.assertEqual(actual_ours, actual_base)
        self.assertEqual(actual_ours, 61440)

    def test_baseline_25_calls_and_synchronous_rounds(self):
        def handler(p):
            if p["STAGE"] == "DISCUSS":
                return self.work()
            return self.respond(p)
        runner, script = self.engine("ordinary_discussion", handler)
        result = runner.run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["http_attempts"], 25)
        self.assertEqual(result["system"], "ordinary_discussion")
        first_round = [p for p in script.calls if p["STAGE"] == "DISCUSS"][:4]
        for p in first_round:
            self.assertEqual(p["DISCUSSION"], [])
            self.assertEqual(len(p["CANDIDATES"]), 4)
            self.assertNotIn("work_text", p["CURRENT_WORK"])
            self.assertTrue(all("locations" not in w for w in p["CANDIDATES"]))
            self.assertEqual(p["BUDGET"]["reserved_closure_calls"], 1)
        self.assertNotIn("CHECK_USE", [p["STAGE"] for p in script.calls])
        self.assertEqual(result["artifact"], self.adapter.render(result["selected_work"]["artifact"]))

    def test_workboard_uses_same_cached_initials_with_25_post_calls(self):
        runner, _ = self.engine("coreta_workboard", lambda p: self.offer(p) if p["STAGE"] == "OBSERVE" else self.respond(p))
        self.assertEqual(runner.run()["http_attempts"], 25)

    def test_output_budget_stops_before_http(self):
        runner, script = self.engine("coreta_workboard")
        runner.gateway.limits["max_output_tokens_total"] = 1
        runner.initialize()
        with self.assertRaises(ProtocolError) as exc:
            runner.gateway.call("OBSERVE", "A1", runner.packet("A1", "OBSERVE"))
        self.assertEqual(exc.exception.code, "OUTPUT_BUDGET")
        self.assertEqual(script.calls, [])

    def test_baseline_finalizer_allows_new_native_work(self):
        def handler(p):
            if p["STAGE"] == "DISCUSS":
                return self.work()
            if p["STAGE"] == "FINALIZE":
                return self.change("new", work=self.work(), sources=["T"])
            return self.respond(p)
        runner, _ = self.engine("ordinary_discussion", handler)
        self.assertEqual(runner.run()["status"], "completed")
        self.assertEqual(len(runner.board.snapshot()), 29)

    def test_optional_reason_on_successful_actions(self):
        runner, _ = self.engine("coreta_workboard")
        runner.initialize()
        for stage in ("TRY", "FINALIZE"):
            packet = runner.packet("A2", stage)
            schema = runner.gateway.contracts.schema(stage, packet)
            for action in ("reuse", "new"):
                for reason in (None, "This candidate preserves the supported result."):
                    with self.subTest(stage=stage, action=action, reason=reason):
                        value = self.change(action, candidate="W1" if action == "reuse" else None,
                                            work=self.work() if action == "new" else None)
                        value["reason"] = reason
                        Contracts.decode(json.dumps(value), schema)
                        Contracts.validate_action(stage, value)

    def test_meaningful_action_constraints_still_reject(self):
        runner, _ = self.engine("coreta_workboard")
        runner.initialize()
        invalid = [
            ("TRY", self.change("reuse", candidate="W1", work=self.work())),
            ("TRY", self.change("reuse")),
            ("TRY", self.change("new", candidate="W1", work=self.work())),
            ("TRY", self.change("new")),
            ("TRY", {**self.change("reuse", candidate="W1"), "use_record": None}),
            ("TRY", {**self.change("unable"), "reason": None}),
            ("TRY", {**self.change("unable"), "use_record": "I applied it"}),
            ("TRY", self.change("unable", sources=["T"])),
            ("FINALIZE", self.change("unable")),
            ("FINALIZE", self.change("reuse", candidate="W999")),
            ("FINALIZE", {**self.change("reuse", candidate="W1"), "reason": ""}),
            ("FINALIZE", {**self.change("reuse", candidate="W1"), "reason": 7}),
            ("FINALIZE", self.change("reuse", candidate="W1", sources=["UNSEEN"])),
        ]
        for stage, value in invalid:
            with self.subTest(stage=stage, value=value):
                with self.assertRaises(ProtocolError):
                    Contracts.decode(json.dumps(value), runner.gateway.contracts.schema(stage, runner.packet("A2", stage)))
                    Contracts.validate_action(stage, value)

    def test_both_full_paths_allow_explanations_without_rewriting(self):
        scenarios = [("ordinary_discussion", final, None) for final in ("reuse", "new")]
        scenarios += [("coreta_workboard", final, trial) for final in ("reuse", "new")
                      for trial in ("reuse", "new")]
        for system, final_action, trial_action in scenarios:
            with self.subTest(system=system, final=final_action, trial=trial_action):
                # Separate journals: the two paths must not reuse earlier calls or work.
                self.setUp()
                def handler(p):
                    if p["STAGE"] == "DISCUSS":
                        return self.work()
                    if p["STAGE"] == "OBSERVE":
                        return self.offer(p)
                    value = self.respond(p)
                    if p["STAGE"] == "FINALIZE" and final_action == "new":
                        value = self.change("new", work=self.work(), sources=["T"])
                    if p["STAGE"] == "TRY" and trial_action == "reuse":
                        value = self.change("reuse", candidate=p["CURRENT_WORK"]["id"], sources=["T"])
                    if p["STAGE"] in {"TRY", "FINALIZE"}:
                        value["reason"] = "An optional explanation accompanies the actual action."
                    return value
                runner, script = self.engine(system, handler)
                result = runner.run()
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["http_attempts"], 25)
                self.assertEqual(result["artifact"], self.adapter.render(self.work()["artifact"]))
                self.assertTrue(all(w["artifact"] == self.work()["artifact"] for w in runner.board.snapshot()))

    def test_action_guidance_shared_by_both_methods(self):
        from coreta.workboard.contracts import ACTION_GUIDANCE
        for system in ("ordinary_discussion", "coreta_workboard"):
            runner, _ = self.engine(system)
            runner.initialize()
            packet = runner.packet("A2", "FINALIZE")
            text = runner.gateway.prompts.render("FINALIZE", packet, runner.gateway.contracts.schema("FINALIZE", packet))
            self.assertIn(ACTION_GUIDANCE, text)
            self.assertNotIn("Unused fields must be null", text)

    def test_no_gold_or_source_data_in_prepare(self):
        manifest = pilot.prepare(self.folder / "prepared")
        self.assertEqual(manifest["method_units"], 8)
        self.assertEqual(len(manifest["initial_context_estimates"]), 16)
        for path in (self.folder / "prepared").glob("*/*.request.json"):
            text = path.read_text(encoding="utf-8")
            for field in ("reference_ranks_by_exact_name", "total_scores", "correct_answer", "evaluator.json"):
                self.assertNotIn(field, text)

    def test_matrix_balances_order_without_expert_editor(self):
        matrix = pilot.pairs()
        self.assertEqual(len(matrix), 4)
        self.assertEqual({p["ordinal"] for p in matrix}, {1, 2})
        self.assertEqual(sum(p["methods"][0] == "coreta_workboard" for p in matrix), 2)

    def test_entire_eight_unit_batch_uses_216_requests_and_paired_cache(self):
        prepared, output = self.folder / "prepared", self.folder / "batch"
        pilot.prepare(prepared)
        original_engine = pilot.engine
        def factory(*args, **kwargs):
            def handler(p):
                if p["STAGE"] == "DISCUSS":
                    return self.work()
                if p["STAGE"] == "OBSERVE":
                    return self.offer(p)
                return self.respond(p)
            kwargs["transport"] = fixtures.Script(None, handler)
            return original_engine(*args, **kwargs)
        with patch.object(pilot, "engine", side_effect=factory):
            result = pilot.run(prepared, output)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["http_attempts"], 216)
        self.assertEqual(len(result["units"]), 8)
        for pair in pilot.pairs():
            states = [json.loads((output / pair["id"] / m / "state.json").read_text()) for m in pair["methods"]]
            self.assertEqual([w for w in states[0]["works"] if w["initial"]],
                             [w for w in states[1]["works"] if w["initial"]])

    def test_batch_stops_on_first_initial_format_error(self):
        prepared, output = self.folder / "prepared", self.folder / "stopped"
        pilot.prepare(prepared)
        original_engine = pilot.engine
        def factory(*args, **kwargs):
            kwargs["transport"] = fixtures.Script(None, lambda p: "NOT JSON")
            return original_engine(*args, **kwargs)
        with patch.object(pilot, "engine", side_effect=factory):
            with self.assertRaises(ProtocolError):
                pilot.run(prepared, output)
        result = json.loads((output / "progress.json").read_text())
        self.assertEqual(result["status"], "stopped_on_first_technical_error")
        self.assertEqual(result["http_attempts"], 1)
        self.assertTrue(all(u["status"] == "not_started" for u in result["units"]))


if __name__ == "__main__":
    unittest.main()
