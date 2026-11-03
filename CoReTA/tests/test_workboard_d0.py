"""Scripted D0 engineering fixtures; never evidence of solving ability."""
import json
import subprocess
import sys
import unittest

import test_workboard as fixtures
from coreta.workboard_d0.runtime import Runner
from coreta.workboard_d0.contracts import Contracts
from coreta.workboard_d0.prompts import Prompts
from coreta.workboard_d0.__main__ import ReplayTransport, replay
from coreta.schemas import ProtocolError
from coreta.handoff.__main__ import PROJECT


class D0Tests(unittest.TestCase):
    setUp = fixtures.WorkboardTests.setUp
    work = fixtures.WorkboardTests.work
    change = fixtures.WorkboardTests.change
    def offer(self, p):
        value = fixtures.WorkboardTests.offer(self, p)
        value["offer"]["responds_to"] = (p.get("FOCUS") or {}).get("id")
        return value

    def respond(self, p):
        value = fixtures.WorkboardTests.respond(self, p)
        if p["STAGE"] in {"CHOOSE", "FINAL_CHOOSE"} and "FOCUS_HISTORY" in p:
            value["focus_disposition"] = None
            if p["STAGE"] == "CHOOSE":
                value["next_check"] = None
        return value

    def engine(self, handler=None, **kwargs):
        old, script = fixtures.WorkboardTests.engine(self, handler=handler, **kwargs)
        old.gateway.contracts = Contracts(old.board.adapter)
        old.gateway.prompts = Prompts()
        return Runner(old.packets, old.gateway, old.journal, old.board.adapter), script

    def test_spine(self):
        runner, _ = self.engine()
        result = runner.run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["protocol"], "coreta/workboard-d0")
        self.assertEqual(result["truth_status"], "not_certified")
        self.assertEqual(json.loads((self.folder / "result.json").read_text(encoding="utf-8")), result)

    def with_focus(self, p):
        if p["STAGE"] == "OBSERVE":
            return self.offer(p)
        value = self.respond(p)
        if p["STAGE"] == "CHOOSE":
            value["candidate_id"] = p["AFTER"]["id"]
            if p["BUDGET"]["cycle"] == 1:
                value["next_check"] = {"target": p["AFTER"]["id"], "question": "SCRIPTED condition?",
                                       "check": "SCRIPTED compare source wording", "refs": ["T"]}
            elif p["FOCUS"]:
                value["focus_disposition"] = {"focus_id": p["FOCUS"]["id"], "status": "addressed",
                                              "reason": "SCRIPTED revision explanation, not truth"}
        return value

    def test_focus_reaches_response_trial_checks_and_closure(self):
        runner, script = self.engine(self.with_focus, members=3)
        result = runner.run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["http_attempts"], 19)
        focus = result["focus_history"][0]
        self.assertEqual(focus["status"], "addressed")
        self.assertEqual(len(focus["responses"]), 2)
        self.assertEqual(len(focus["applications"]), 1)
        trial = next(p for p in script.calls if p["STAGE"] == "TRY" and p["BUDGET"]["cycle"] == 2)
        self.assertEqual(trial["FOCUS"]["id"], "Q1")
        self.assertTrue(trial["APPLICATION_FEEDBACK"])
        checks = [p for p in script.calls if p["STAGE"] in {"CHECK_USE", "CHECK_EFFECT"}
                  and p["BUDGET"]["cycle"] == 2]
        self.assertEqual(checks[0]["FOCUS_HISTORY"], checks[1]["FOCUS_HISTORY"])
        self.assertEqual(checks[0]["FOCUS_FEEDBACK"], checks[1]["FOCUS_FEEDBACK"])
        self.assertTrue(checks[0]["FOCUS_FEEDBACK"])
        self.assertEqual(checks[0]["FOCUS_FEEDBACK"][0]["after"], focus["origin_work"])
        self.assertTrue(all(row["after"] != checks[0]["AFTER"]["id"]
                            for row in checks[0]["FOCUS_FEEDBACK"]))
        self.assertNotIn("CHECKS", checks[1])
        self.assertEqual(result["truth_status"], "not_certified")

    def test_focus_response_never_auto_closes_and_all_pass_defers(self):
        def handler(p):
            if p["STAGE"] == "OBSERVE" and p["BUDGET"]["cycle"] == 2:
                return {"action": "pass", "offer": None}
            return self.with_focus(p)
        runner, script = self.engine(handler, members=3)
        result = runner.run()
        self.assertEqual(result["focus_history"][0]["status"], "deferred")
        self.assertEqual(result["focus_history"][0]["responses"], [])
        self.assertEqual(result["stop_reason"], "all_pass")
        closing = next(p for p in script.calls if p["STAGE"] == "FINALIZE")
        self.assertEqual(closing["FOCUS"]["id"], "Q1")
        self.assertEqual(closing["FOCUS"]["status"], "pending")

    def test_last_cycle_focus_gets_no_extra_cycle(self):
        def handler(p):
            if p["STAGE"] == "OBSERVE":
                return self.offer(p)
            value = self.respond(p)
            if p["STAGE"] == "CHOOSE" and p["BUDGET"]["cycle"] == 2:
                value["next_check"] = {"target": "whole_goal", "question": "SCRIPTED late question",
                                       "check": "SCRIPTED future check only", "refs": []}
            return value
        runner, script = self.engine(handler, members=3)
        result = runner.run()
        self.assertEqual(result["http_attempts"], 19)
        self.assertEqual(result["focus_history"][0]["status"], "deferred")
        self.assertFalse(any(p["BUDGET"]["cycle"] > 2 for p in script.calls))

    def test_unable_keeps_question_pending_and_records_obstacle(self):
        def handler(p):
            if p["STAGE"] == "TRY" and p["BUDGET"]["cycle"] == 2:
                return self.change("unable")
            return self.with_focus(p)
        runner, script = self.engine(handler, members=3)
        result = runner.run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["focus_history"][0]["status"], "deferred")
        self.assertEqual(runner.feedback[-1]["kind"], "unable_to_apply")
        self.assertEqual(runner.feedback[-1]["focus_id"], "Q1")

    def test_interrupted_check_defers_focus_without_forged_repair(self):
        def handler(p):
            if p["STAGE"] == "CHECK_EFFECT" and p["BUDGET"]["cycle"] == 2:
                return "NOT JSON"
            return self.with_focus(p)
        runner, _ = self.engine(handler, members=3)
        result = runner.run()
        self.assertEqual(result["status"], "interrupted")
        self.assertEqual(result["error"]["code"], "SCHEMA_ERROR")
        self.assertEqual(result["focus_history"][0]["status"], "deferred")
        self.assertFalse(result["closure_complete"])

    def test_source_permissions_and_response_ids_remain_member_specific(self):
        runner, script = self.engine(self.with_focus, members=3)
        runner.run()
        for p in script.calls:
            self.assertEqual(p["SELF_MATERIALS"], self.packets.member(p["SELF"]["agent_id"])["SELF_MATERIALS"])
            direct = {"T", *(m["ref"] for m in p["SELF_MATERIALS"])}
            self.assertEqual(set(p["SOURCE_ACCESS"]["direct_original_refs"]), direct)
        packet = next(p for p in script.calls if p["STAGE"] == "OBSERVE" and p["FOCUS"])
        bad = self.offer(packet)
        bad["offer"]["responds_to"] = "Q999"
        with self.assertRaises(ProtocolError):
            Contracts.decode(json.dumps(bad), runner.gateway.contracts.schema("OBSERVE", packet))
        private = next(m["ref"] for a in runner.agents for m in runner.packets.member(a)["SELF_MATERIALS"]
                       if m["ref"] not in packet["SOURCE_ACCESS"]["direct_original_refs"])
        bad = self.offer(packet)
        bad["offer"]["support"] = [{"ref": private, "excerpt": "SCRIPTED illegal private original"}]
        with self.assertRaises(ProtocolError):
            Contracts.decode(json.dumps(bad), runner.gateway.contracts.schema("OBSERVE", packet))

    def test_no_automatic_addressed_on_received_response(self):
        def handler(p):
            value = self.with_focus(p)
            if p["STAGE"] == "CHOOSE":
                value["focus_disposition"] = None
            return value
        runner, _ = self.engine(handler, members=3)
        focus = runner.run()["focus_history"][0]
        self.assertTrue(focus["responses"])
        self.assertTrue(focus["applications"])
        self.assertEqual(focus["status"], "deferred")

    def test_unrelated_offer_and_reuse_only_record_active_context(self):
        def handler(p):
            value = self.with_focus(p)
            if p["STAGE"] == "OBSERVE" and p["FOCUS"]:
                value["offer"]["responds_to"] = None
            if p["STAGE"] == "TRY" and p["FOCUS"]:
                return self.change(candidate=p["CURRENT_WORK"]["id"])
            if p["STAGE"] == "CHOOSE":
                value["focus_disposition"] = None
            return value
        runner, _ = self.engine(handler, members=3)
        focus = runner.run()["focus_history"][0]
        self.assertEqual(focus["responses"], [])
        self.assertEqual(focus["applications"][0]["relation"], "active_context_only")
        self.assertEqual(focus["applications"][0]["before"], focus["applications"][0]["after"])
        self.assertEqual(focus["status"], "deferred")

    def test_historical_focus_and_origin_work_retained_after_version_changes(self):
        def handler(p):
            value = self.with_focus(p)
            if p["STAGE"] == "CHOOSE" and p["BUDGET"]["cycle"] == 2:
                value["focus_disposition"] = None
                value["next_check"] = {"target": p["AFTER"]["id"], "question": "SCRIPTED second question",
                                       "check": "SCRIPTED independent check", "refs": ["T"]}
            return value
        runner, script = self.engine(handler)
        result = runner.run()
        self.assertEqual(len(result["focus_history"]), 2)
        third = next(p for p in script.calls if p["STAGE"] == "TRY" and p["BUDGET"]["cycle"] == 3)
        self.assertEqual(third["FOCUS"]["id"], "Q2")
        self.assertEqual(third["FOCUS_HISTORY"][0]["status"], "pending")
        origin = third["FOCUS_HISTORY"][0]["origin_work"]
        self.assertIn(origin, {w["id"] for w in third["CANDIDATES"]})
        self.assertEqual(result["focus_history"][0]["status"], "deferred")

    def test_focus_cited_base_work_stays_visible_to_later_selection(self):
        def handler(p):
            value = self.with_focus(p)
            if p["STAGE"] == "CHOOSE" and p["BUDGET"]["cycle"] == 1:
                value["next_check"]["target"] = "whole_goal"
                value["next_check"]["refs"] = [p["BEFORE"]["id"]]
            return value
        runner, script = self.engine(handler, members=3)
        result = runner.run()
        base = result["focus_history"][0]["base_work"]
        for p in script.calls:
            if p["STAGE"] in {"CHOOSE", "FINAL_CHOOSE"} and p["FOCUS_HISTORY"]:
                self.assertIn(base, {w["id"] for w in p["CANDIDATES"]})
                self.assertIn(base, {r["ref"] for r in p["REFERENCE_INDEX"]})

    def test_invalid_disposition_and_target_stop_first_error(self):
        runner, script = self.engine(self.with_focus, members=3)
        runner.run()
        packets = [p for p in script.calls if p["STAGE"] == "CHOOSE"]
        p = packets[1]
        for change in ("unknown_focus", "unknown_target", "private_source"):
            with self.subTest(change=change):
                value = self.with_focus(p)
                if change == "unknown_focus":
                    value["focus_disposition"]["focus_id"] = "Q999"
                else:
                    value["next_check"] = {"target": "W999" if change == "unknown_target" else "whole_goal",
                                           "question": "SCRIPTED", "check": "SCRIPTED",
                                           "refs": ["S999"] if change == "private_source" else []}
                with self.assertRaises(ProtocolError):
                    Contracts.decode(json.dumps(value), runner.gateway.contracts.schema("CHOOSE", p))

    def test_offline_replay_cli_and_no_overwrite(self):
        runner, script = self.engine(self.with_focus)
        runner.run()
        rows = [{"stage": p["STAGE"], "member": p["SELF"]["agent_id"], "output": self.with_focus(p)}
                for p in script.calls]
        fixture = self.folder / "SCRIPTED_stage_responses.json"
        fixture.write_text(json.dumps(rows), encoding="utf-8")
        output = self.folder / "replay"
        command = [sys.executable, "-m", "coreta.workboard_d0", "--pack",
                   str(PROJECT / "data/task-packs/student-president-dev-v1"), "--task-type", "ranking",
                   "--script", str(fixture), "--output", str(output)]
        process = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        report = json.loads(process.stdout)
        self.assertTrue(report["replay_complete"])
        self.assertEqual(report["actual_http_attempts"], 0)
        self.assertEqual(report["scripted_transport_attempts"], 29)
        saved = json.loads((output / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["execution_mode"], "scripted_engineering_only")
        self.assertEqual(saved["http_attempts"], 0)
        repeat = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(repeat.returncode, 0)
        rows.append({"stage": "INITIAL", "member": "A1", "output": {}})
        fixture.write_text(json.dumps(rows), encoding="utf-8")
        extra = self.folder / "unused-replay"
        report = replay(PROJECT / "data/task-packs/student-president-dev-v1", "distributed", "ranking",
                        fixture, extra)
        self.assertFalse(report["replay_complete"])
        saved = json.loads((extra / "result.json").read_text(encoding="utf-8"))
        self.assertFalse(saved["replay_complete"])
        self.assertEqual(saved["replay_error"]["code"], "REPLAY_UNUSED")

    def test_native_hiddenbench_three_and_four_member_choice_paths(self):
        import test_hiddenbench_workboard as choice_fixtures
        from coreta.handoff.gateway import Journal
        from coreta.workboard.artifacts import ChoiceAdapter
        from coreta.workboard.choice_inputs import ChoicePackets
        from coreta.workboard.gateway import Gateway, defaults
        from coreta.handoff.__main__ import load_counter

        def handler(p):
            value = choice_fixtures.respond(p)
            stage = p["STAGE"]
            if stage == "OBSERVE":
                value["offer"]["responds_to"] = (p["FOCUS"] or {}).get("id")
            if stage in {"CHOOSE", "FINAL_CHOOSE"}:
                value["focus_disposition"] = None
            if stage == "CHOOSE":
                value["next_check"] = ({"target": p["AFTER"]["id"], "question": "SCRIPTED private fact?",
                                         "check": "SCRIPTED compare wording", "refs": ["T"]}
                                        if p["BUDGET"]["cycle"] == 1 else None)
            return value

        for number, expected in ((1, 29), (4, 19)):
            with self.subTest(task=number):
                folder = self.folder / f"choice-{number}"
                folder.mkdir()
                packets = ChoicePackets(choice_fixtures.DATA / f"hb-dev-{number:03d}", "distributed")
                journal = Journal(folder)
                adapter = ChoiceAdapter(packets.task)
                script = fixtures.Script(journal, handler)
                gateway = Gateway(self.config, defaults(len(packets.agents), self.legacy), Contracts(adapter),
                                  Prompts(), journal, transport=script, token_counter=load_counter())
                result = Runner(packets, gateway, journal, adapter).run()
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["http_attempts"], expected)
                self.assertEqual(result["focus_history"][0]["status"], "deferred")
                self.assertEqual(result["truth_status"], "not_certified")

    def test_replay_rejects_stage_member_mismatch(self):
        transport = ReplayTransport([{"stage": "CHOOSE", "member": "A1", "output": {}}])
        payload = {"instructions": '\nPACKET={"STAGE":"INITIAL","SELF":{"agent_id":"A2"}}\nOUTPUT_SCHEMA={}'}
        with self.assertRaises(ProtocolError) as error:
            transport(payload, 1)
        self.assertEqual(error.exception.code, "REPLAY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
