"""Scripted engineering checks only; outputs are fixtures, not solving evidence."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coreta.application_v2.inputs import Packets
from coreta.handoff.__main__ import configure, load_counter, PROJECT, DESIGN
from coreta.handoff.gateway import Journal
from coreta.schemas import ProtocolError
from coreta.workboard.artifacts import RankingAdapter, TextAdapter, Board
from coreta.workboard.contracts import Contracts
from coreta.workboard.gateway import Gateway, defaults
from coreta.workboard.prompts import Prompts
from coreta.workboard.runtime import Runner


class Script:
    def __init__(self, journal, handler):
        self.journal, self.handler, self.calls = journal, handler, []

    def __call__(self, payload, timeout):
        packet = json.loads(payload["instructions"].split("\nPACKET=", 1)[1].split("\nOUTPUT_SCHEMA=", 1)[0])
        self.calls.append(copy.deepcopy(packet))
        value = self.handler(packet)
        text = value if isinstance(value, str) else json.dumps(value)
        return {"status": "completed", "usage": {"input_tokens": 1, "output_tokens": 1},
                "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}


class WorkboardTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="coreta-workboard-")
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        guard = patch("urllib.request.urlopen", side_effect=AssertionError("Offline checks must not access network"))
        guard.start()
        self.addCleanup(guard.stop)
        self.packets = Packets(PROJECT / "data/task-packs/student-president-dev-v1", "distributed")
        self.names = [row["name"] for row in self.packets.task["items"]]
        self.adapter = RankingAdapter(self.packets.task)
        self.config, self.legacy = configure(PROJECT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")

    def work(self, artifact="full"):
        return {"artifact": list(self.names) if artifact == "full" else artifact,
                "work_text": "SCRIPTED native work\nA second line", "open_points": []}

    def change(self, action="reuse", candidate=None, work=None, sources=()):
        return {"action": action, "candidate_id": candidate, "work": work,
                "use_record": None if action == "unable" else "SCRIPTED use description",
                "reason": "SCRIPTED unable reason" if action == "unable" else None,
                "declared_sources": list(sources)}

    def respond(self, p):
        stage = p["STAGE"]
        if stage == "INITIAL":
            return self.work()
        if stage == "OBSERVE":
            return {"action": "pass", "offer": None}
        if stage == "FINALIZE":
            return self.change(candidate=p["CURRENT_WORK"]["id"])
        if "CHECK" in stage:
            return {"finding": "no_issue_found", "observation": "SCRIPTED limited observation", "scope": "fixture only"}
        if stage in {"CHOOSE", "FINAL_CHOOSE"}:
            return {"candidate_id": p["CHOICES"][0], "reason": "SCRIPTED selection"}
        if stage == "TRY":
            return self.change("new", work=self.work(), sources=[p["TARGET_OFFER"]["ref"]])
        raise AssertionError(stage)

    def offer(self, p):
        return {"action": "offer", "offer": {"target": p["CURRENT_WORK"]["id"],
                "knowledge": "SCRIPTED knowledge", "support": [{"ref": "T", "excerpt": "SCRIPTED excerpt"}],
                "proposed_use": "SCRIPTED trial"}}

    def engine(self, handler=None, members=None, budget=None, counter=None):
        packets = copy.deepcopy(self.packets)
        if members:
            packets.agents = packets.agents[:members]
            for member in packets.members.values():
                member["SELF"]["team"] = packets.agents
        journal = Journal(self.folder)
        script = Script(journal, handler or self.respond)
        settings = defaults(len(packets.agents), self.legacy)
        if budget is not None:
            settings["limits"]["max_network_attempts_total"] = budget
        gateway = Gateway(self.config, settings, Contracts(self.adapter), Prompts(), journal,
                          transport=script, token_counter=counter or load_counter())
        return Runner(packets, gateway, journal, self.adapter), script

    def test_all_pass_closes_without_fake_provider(self):
        runner, script = self.engine()
        result = runner.run()
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["closure_complete"])
        self.assertEqual(result["truth_status"], "not_certified")
        self.assertEqual(result["http_attempts"], 11)
        self.assertEqual(len(runner.offers), 0)
        self.assertEqual(result["artifact"], self.adapter.render(result["selected_work"]["artifact"]))

    def test_full_four_member_cycles_fit_budget_and_rotate(self):
        runner, script = self.engine(lambda p: self.offer(p) if p["STAGE"] == "OBSERVE" else self.respond(p))
        result = runner.run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["http_attempts"], 29)
        self.assertEqual(sorted(runner.counts.values()), [0, 1, 1, 1])
        self.assertEqual(len(runner.offers), 9)

    def test_three_member_cycles_fit_budget(self):
        runner, _ = self.engine(lambda p: self.offer(p) if p["STAGE"] == "OBSERVE" else self.respond(p), members=3)
        self.assertEqual(runner.run()["http_attempts"], 19)

    def test_initial_and_current_round_offer_isolation(self):
        runner, script = self.engine(lambda p: self.offer(p) if p["STAGE"] == "OBSERVE" else self.respond(p))
        runner.run()
        for p in script.calls:
            if p["STAGE"] == "INITIAL":
                self.assertNotIn("CANDIDATES", p)
                self.assertNotIn("CURRENT_WORK", p)
                self.assertNotIn("PUBLIC_EVIDENCE", p)
            if p["STAGE"] == "OBSERVE" and p["BUDGET"]["cycle"] == 1:
                self.assertEqual(p["PUBLIC_EVIDENCE"], [])
            original = self.packets.member(p["SELF"]["agent_id"])
            self.assertEqual(p["SELF_MATERIALS"], original["SELF_MATERIALS"])
        checks = [p for p in script.calls if "CHECK" in p["STAGE"]]
        for p in checks:
            self.assertTrue(p["CANDIDATES"])
            self.assertIn("APPLICATION_SOURCE_REFS", p)
            self.assertNotIn("CHECKS", p)
            if "EFFECT" in p["STAGE"]:
                self.assertNotIn("USE_RECORD", p)

    def test_unable_skips_trial_checks_and_delivers_reason(self):
        def handler(p):
            if p["STAGE"] == "OBSERVE":
                return self.offer(p)
            if p["STAGE"] == "TRY":
                return self.change("unable")
            return self.respond(p)
        runner, script = self.engine(handler)
        result = runner.run()
        self.assertEqual(result["status"], "completed")
        self.assertNotIn("CHECK_USE", [p["STAGE"] for p in script.calls])
        self.assertNotIn("CHOOSE", [p["STAGE"] for p in script.calls])
        self.assertTrue(runner.feedback[0]["reason_delivered_to_provider"])
        self.assertFalse(runner.feedback[-1]["reason_delivered_to_provider"])

    def test_mid_check_failure_returns_deliverable_fallback(self):
        def handler(p):
            if p["STAGE"] == "OBSERVE":
                return self.offer(p)
            if p["STAGE"] == "CHECK_EFFECT":
                return "NOT JSON"
            return self.respond(p)
        runner, _ = self.engine(handler)
        result = runner.run()
        self.assertEqual(result["status"], "interrupted")
        self.assertFalse(result["closure_complete"])
        self.assertEqual(result["error"]["code"], "SCHEMA_ERROR")
        self.assertEqual(result["selected_work_id"], runner.board.fallback)

    def test_all_initial_failures_produce_delivery_failure(self):
        runner, _ = self.engine(lambda p: "NOT JSON")
        result = runner.run()
        self.assertEqual(result["status"], "delivery_failure")
        self.assertIsNone(result["artifact"])

    def test_context_overflow_prevents_http(self):
        runner, _ = self.engine(counter=lambda _: 10**9)
        result = runner.run()
        self.assertEqual(result["http_attempts"], 0)
        self.assertEqual(result["stop_reason"], "CONTEXT_OVERFLOW")

    def test_budget_reserves_closure(self):
        runner, script = self.engine(budget=8)
        result = runner.run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["http_attempts"], 8)
        self.assertNotIn("OBSERVE", [p["STAGE"] for p in script.calls])

    def test_no_deliverable_is_not_success(self):
        def handler(p):
            if p["STAGE"] == "INITIAL":
                return self.work(None)
            if p["STAGE"] == "FINALIZE":
                return self.change("new", work=self.work(None))
            return self.respond(p)
        runner, _ = self.engine(handler)
        self.assertEqual(runner.run()["status"], "delivery_failure")

    def test_partial_reuse_at_closure_rejected(self):
        runner, _ = self.engine()
        runner.initialize()
        ref = runner.board.add(self.work(None), runner.editor)
        p = runner.packet(runner.editor, "FINALIZE")
        schema = runner.gateway.contracts.schema("FINALIZE", p)
        with self.assertRaises(ProtocolError):
            Contracts.decode(json.dumps(self.change(candidate=ref)), schema)

    def test_reuse_current_not_counted_as_adoption(self):
        def handler(p):
            if p["STAGE"] == "OBSERVE":
                return self.offer(p)
            if p["STAGE"] == "TRY":
                return self.change(candidate=p["CURRENT_WORK"]["id"])
            return self.respond(p)
        runner, _ = self.engine(handler)
        runner.run()
        events = [json.loads(line)["kind"] for line in (self.folder / "events.jsonl").read_text().splitlines()]
        self.assertIn("selection_unchanged", events)
        self.assertNotIn("offer_adopted", events)

    def test_untried_and_original_work_sources_select_author(self):
        runner, _ = self.engine()
        runner.initialize()
        outsider = runner.next_peer({runner.editor})
        row = {"ref": "O1", "author": outsider}
        runner.published.append(row)
        ref = runner.board.initials[runner.editor]
        self.assertEqual(runner.closing_checker(ref, ["O1"]), outsider)
        self.assertEqual(runner.closing_checker(ref, [runner.board.initials[outsider]]), outsider)

    def test_same_source_multiple_support_excerpts_allowed(self):
        runner, _ = self.engine()
        runner.initialize()
        p = runner.packet(runner.editor, "OBSERVE")
        value = self.offer(p)
        value["offer"]["support"] *= 30
        Contracts.decode(json.dumps(value), runner.gateway.contracts.schema("OBSERVE", p))

    def test_illegal_private_reference_rejected(self):
        runner, _ = self.engine()
        runner.initialize()
        p = runner.packet(runner.editor, "OBSERVE")
        value = self.offer(p)
        value["offer"]["support"][0]["ref"] = "UNREAD_SOURCE"
        with self.assertRaises(ProtocolError):
            Contracts.decode(json.dumps(value), runner.gateway.contracts.schema("OBSERVE", p))

    def test_impossible_action_rejected(self):
        with self.assertRaises(ProtocolError):
            Contracts.validate_action("TRY", self.change("new", candidate="W1", work=self.work()))

    def test_board_snapshots_are_copies(self):
        board = Board(TextAdapter())
        ref = board.add({"artifact": "answer", "work_text": "reason", "open_points": []}, "A1")
        value = board.get(ref)
        value["artifact"] = "mutated"
        self.assertEqual(board.get(ref)["artifact"], "answer")

    def test_unknown_tool_version_rejected(self):
        runner, _ = self.engine()
        with self.assertRaises(ProtocolError):
            runner.record_observation("W404", "fixture", {}, "text", 0)


if __name__ == "__main__":
    unittest.main()
