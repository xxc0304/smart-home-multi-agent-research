"""Four-candidate adapter checks. Scripted output is not performance evidence."""
import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coreta.application_v2.contracts import ApplicationContracts
from coreta.application_v2.inputs import Packets
from coreta.application_v2.prompts import ApplicationPrompts
from coreta.application_v2.ranking import render_ranking, score_run
from coreta.application_v2.ranking_contracts import RankingContracts
from coreta.application_v2.runtime import ApplicationRunner
from coreta.handoff.contracts import HandoffContracts
from coreta.handoff.gateway import Gateway, Journal
from coreta.handoff.__main__ import configure, load_counter
from coreta.handoff.inputs import Packets as FrozenPackets, read_json
from coreta.handoff.prompts import HandoffPrompts
from coreta.schemas import ProtocolError
from test_handoff import Script, contribution, request, review, ROOT, DESIGN, PACK
from test_application_v2 import unit

SBP = ROOT / "data/task-packs/student-president-dev-v1"
NAMES = [i["name"] for i in read_json(SBP / "public/task.json")["items"]]


def answer():
    return {"ranking": list(NAMES), "explanation": "Scripted four-candidate answer"}


def application(target=None, refs=("T",), ask=None, uses=()):
    return {"artifact": list(NAMES), "applications": [unit(target=target, refs=refs)],
            "artifact_uses": list(uses), "retire_applications": [], "excluded": [], "unresolved": [], "request": ask}


class RankingAdapterTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="coreta-four-ranking-")
        self.addCleanup(tmp.cleanup)
        self.directory = Path(tmp.name)
        guard = patch("urllib.request.urlopen", side_effect=AssertionError("No real network in adapter checks"))
        guard.start()
        self.addCleanup(guard.stop)
        self.config, self.defaults = configure(ROOT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
        self.packets = Packets(SBP, "distributed")
        self.contracts = ApplicationContracts(DESIGN / "message.schema.json")
        self.prompts = ApplicationPrompts(DESIGN / "PROMPTS.md")

    def engine(self, outputs):
        journal = Journal(self.directory)
        script = Script(journal, outputs)
        gateway = Gateway(self.config, self.defaults, self.contracts, self.prompts, journal,
                          transport=script, token_counter=load_counter())
        return ApplicationRunner(self.packets, gateway, journal), script

    def test_all_four_allocations_load_without_gold(self):
        from coreta.handoff import inputs
        original = inputs.read_json
        def read(path):
            self.assertNotIn("offline", path.parts)
            return original(path)
        with patch.object(inputs, "read_json", side_effect=read):
            for name in ("distributed", "concentrated_A1", "full", "none"):
                p = Packets(SBP, name)
                self.assertEqual(len(p.agents), 4)
                self.assertEqual(len(p.task["items"]), 4)

    def test_original_packet_loader_stays_fifteen_only(self):
        with self.assertRaises(ProtocolError):
            FrozenPackets(SBP, "distributed")

    def test_fifteen_packet_views_unchanged(self):
        old, new = FrozenPackets(PACK, "distributed_r0"), Packets(PACK, "distributed_r0")
        for agent in old.agents:
            self.assertEqual(old.member(agent), new.member(agent))

    def test_duplicate_public_item_rejected(self):
        value = self.packets.member("A1")
        value["TASK"]["items"][0] = value["TASK"]["items"][1]
        with self.assertRaises(ProtocolError):
            Packets._validate(value)

    def test_unknown_task_field_rejected(self):
        value = self.packets.member("A1")
        value["TASK"]["correct_answer"] = "not runtime"
        with self.assertRaises(ProtocolError):
            Packets._validate(value)

    def test_foreign_private_handle_rejected(self):
        value = self.packets.member("A2")
        ref = self.packets.member("A1")["SELF_MATERIALS"][0]["ref"]
        value["REFERENCE_INDEX"].append({"ref": ref, "kind": "private_material"})
        with self.assertRaises(ProtocolError):
            Packets._validate(value)

    def test_four_item_schema_accepts_exact_permutation(self):
        for stage in ("INDEPENDENT", "FINAL", "APPLY"):
            value = application() if stage == "APPLY" else answer()
            schema = self.contracts.schema(stage, {"T"}, self.packets.agents, [], NAMES)
            self.assertEqual(self.contracts.decode(json.dumps(value), schema), value)

    def test_duplicate_omitted_and_unknown_candidates_rejected(self):
        schema = self.contracts.schema("INDEPENDENT", {"T"}, self.packets.agents, [], NAMES)
        for ranking in (NAMES[:3], [NAMES[0]]*4, NAMES[:3]+["Unknown"]):
            value = answer()
            value["ranking"] = ranking
            with self.subTest(ranking=ranking), self.assertRaises(ProtocolError):
                self.contracts.decode(json.dumps(value), schema)

    def test_fifteen_stage_schemas_equal_frozen_contracts(self):
        names = [i["name"] for i in read_json(PACK / "public/task.json")["items"]]
        old, new = HandoffContracts(DESIGN / "message.schema.json"), RankingContracts(DESIGN / "message.schema.json")
        for stage in ("INDEPENDENT", "FINAL", "APPLY", "CONTRIBUTE", "REPLY", "REVIEW", "DISCUSS"):
            self.assertEqual(old.schema(stage, {"T", "C1"}, self.packets.agents, ["ask"], names),
                             new.schema(stage, {"T", "C1"}, self.packets.agents, ["ask"], names))

    def test_four_prompts_use_task_count_and_do_not_rewrite_data(self):
        runner, _ = self.engine([])
        for stage in ("APPLY", "INDEPENDENT", "FINAL"):
            packet = runner.packet("A2", stage)
            packet["TASK"]["scenario"] += " Keep this data: all 15 exact public item names."
            prompt = self.prompts.render(stage, packet, {})
            self.assertIn("all 15 exact public item names.", prompt)
            self.assertIn("4 exact", prompt)
        prompt = self.prompts.render("INDEPENDENT", runner.packet("A2", "INDEPENDENT"), {})
        self.assertNotIn('"DIRECTORY"', prompt)

    def test_fifteen_baseline_prompts_unchanged(self):
        packet = FrozenPackets(PACK, "distributed_r0").member("A1")
        old = HandoffPrompts(DESIGN / "PROMPTS.md")
        for stage in ("INDEPENDENT", "FINAL", "DISCUSS"):
            self.assertEqual(self.prompts.render(stage, packet, {}), old.render(stage, packet, {}))

    def test_four_coreta_complete_path(self):
        runner, script = self.engine([contribution() for _ in range(4)] + [application(), review()])
        result = runner.run()
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(result["http_attempts"], 6)
        self.assertEqual(len(result["agents"]), 4)
        self.assertFalse(script.outputs)

    def test_four_coreta_request_and_original_application_update(self):
        runner, script = self.engine([contribution() for _ in range(4)] + [application(ask=request()),
            contribution(), application(target="U1", refs=("C5",), uses=("U1",)), review(target="W2")])
        self.assertEqual(runner.run()["status"], "reviewed_no_defect")
        self.assertFalse(script.outputs)

    def test_four_ordinary_discussion_complete_path(self):
        runner, script = self.engine([answer() for _ in range(4)] + [{"text": "Scripted discussion"} for _ in range(8)] + [answer()])
        result = runner.run("ordinary_discussion")
        self.assertEqual(result["protocol"], "coreta/ranking-baseline-v2")
        self.assertEqual(result["http_attempts"], 13)
        self.assertEqual(result["driver"], "A2")
        self.assertEqual(len(runner.discussion), 12)
        self.assertFalse(script.outputs)

    def test_four_independent_members(self):
        runner, script = self.engine([answer() for _ in range(4)])
        result = runner.run("independent")
        self.assertEqual(len(result["independent_answers"]), 4)
        self.assertEqual(result["http_attempts"], 4)
        self.assertFalse(script.outputs)

    def test_single_member_independent_has_no_spurious_missing_members(self):
        runner, script = self.engine([answer()])
        runner.selected_member = "A3"
        result = runner.run("independent")
        report = score_run(SBP, result)
        self.assertEqual(result["http_attempts"], 1)
        self.assertEqual(set(result["independent_answers"]), {"A3"})
        self.assertEqual(report["independent_expected_members"], ["A3"])
        self.assertEqual(report["independent_missing_members"], [])
        self.assertFalse(script.outputs)

    def test_selected_member_cannot_change_team_discussion(self):
        runner, _ = self.engine([])
        runner.selected_member = "A3"
        with self.assertRaises(ValueError):
            runner.run("ordinary_discussion")

    def test_offline_reference_and_failed_delivery(self):
        runner, _ = self.engine([contribution() for _ in range(4)] + [application(), review()])
        result = runner.run()
        gold = ["Candidate D", "Candidate C", "Candidate A", "Candidate B"]
        result["artifact"] = render_ranking(gold)
        self.assertEqual(score_run(SBP, result)["final"]["L1_error"], 0)
        result["artifact"] = "MY RANKING:\n1. Candidate A"
        self.assertTrue(score_run(SBP, result)["final"]["delivery_failure"])
        self.assertEqual(score_run(SBP, result)["final"]["L1_error"], 8)

    def test_coreta_does_not_claim_missing_independent_answers(self):
        runner, _ = self.engine([contribution() for _ in range(4)] + [application(), review()])
        report = score_run(SBP, runner.run())
        self.assertEqual(report["independent_expected_members"], [])
        self.assertEqual(report["independent_missing_members"], [])

    def test_interrupted_ordinary_scores_retained_candidate_with_failure_label(self):
        runner, _ = self.engine([answer() for _ in range(4)] + [ProtocolError("MODEL_UNAVAILABLE", "Scripted unavailable")])
        result = runner.run("ordinary_discussion")
        report = score_run(SBP, result)
        self.assertEqual(report["protocol_status"], "protocol_failure")
        self.assertEqual(report["protocol_error"]["code"], "MODEL_UNAVAILABLE")
        self.assertEqual(report["artifact_role"], "driver_initial_fallback_or_interrupted_candidate")
        self.assertFalse(report["final"]["delivery_failure"])

    def test_prepare_cli_single_member_four_candidates(self):
        from coreta.application_v2.__main__ import main
        out = self.directory / "prepared"
        with patch.object(sys, "argv", ["v2", "prepare", "--pack", str(SBP), "--condition", "distributed",
                                        "--system", "independent", "--member", "A3", "--output", str(out)]):
            self.assertEqual(main(), 0)
        self.assertEqual(len(list(out.glob('*.prompt.txt'))), 1)
        self.assertEqual(read_json(out/'manifest.json')["limits"]["limits"]["max_network_attempts_total"], 4)
        self.assertEqual(read_json(out/'PREPARATION_ONLY.json')["initial_stage"], "INDEPENDENT")

    def test_all_system_cli_paths_and_score_share_four_item_adapter(self):
        from coreta.application_v2.__main__ import main
        for system in ("coreta", "ordinary_discussion", "independent"):
            outputs = ([contribution() for _ in range(4)] + [application(), review()] if system == "coreta" else
                       [answer() for _ in range(4)] + [{"text": "Scripted discussion"} for _ in range(8)] + [answer()]
                       if system == "ordinary_discussion" else [answer()])
            def factory(config, defaults, contracts, prompts, journal, **kwargs):
                return Gateway(config, defaults, contracts, prompts, journal, transport=Script(journal, outputs), **kwargs)
            out = self.directory / system
            argv = ["v2", "run", "--pack", str(SBP), "--condition", "distributed", "--system", system,
                    "--output", str(out), "--live"]
            if system == "independent":
                argv += ["--member", "A3"]
            with self.subTest(system=system), patch.object(sys, "argv", argv), \
                    patch.dict(os.environ, {"DEEPSEEK_API_KEY": "scripted-not-real-key"}), \
                    patch("coreta.application_v2.__main__.Gateway", side_effect=factory):
                self.assertEqual(main(), 0)
            score = self.directory / f"{system}.score.json"
            with patch.object(sys, "argv", ["v2", "score", "--run", str(out), "--pack", str(SBP), "--output", str(score)]):
                self.assertEqual(main(), 0)
            self.assertEqual(read_json(score)["item_count"], 4)
            self.assertFalse(read_json(score)["feedback_sent_to_model"])

    def test_four_initial_prompts_keep_other_private_text_out(self):
        runner, script = self.engine([answer() for _ in range(4)])
        runner.run("independent")
        for call in script.seen:
            member = call["context"]["member"]
            prompt = call["payload"]["instructions"]
            for agent in self.packets.agents:
                for material in self.packets.member(agent)["SELF_MATERIALS"]:
                    if agent == member:
                        self.assertIn(material["content"], prompt)
                    else:
                        self.assertNotIn(material["content"], prompt)

    def test_four_initial_independent_calls_have_no_shared_discussion(self):
        runner, script = self.engine([answer() for _ in range(4)] + [{"text": "Scripted discussion"} for _ in range(8)] + [answer()])
        runner.run("ordinary_discussion")
        for call in script.seen[:4]:
            self.assertNotIn("PUBLIC_DISCUSSION", call["payload"]["instructions"])
        self.assertIn("Scripted four-candidate answer", script.seen[4]["payload"]["instructions"])


if __name__ == "__main__":
    unittest.main()
