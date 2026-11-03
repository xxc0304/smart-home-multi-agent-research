"""Offline source-access checks, not evidence of improved model collaboration."""
import copy
import json
import unittest

import test_workboard as fixtures
import test_workboard_pilot as pilot_fixtures
from coreta.schemas import ProtocolError
from coreta.workboard.contracts import Contracts
from coreta.workboard.provenance import SOURCE_GUIDANCE, describe_sources


class SourceAccessTests(unittest.TestCase):
    setUp = fixtures.WorkboardTests.setUp
    work = fixtures.WorkboardTests.work
    change = fixtures.WorkboardTests.change
    offer = fixtures.WorkboardTests.offer
    respond = fixtures.WorkboardTests.respond
    cache = pilot_fixtures.PilotTests.cache
    engine = pilot_fixtures.PilotTests.engine

    def publish(self, runner):
        offer = {"ref": "O1", "author": "A2", "base_version": "W2", "target": "whole_goal",
                 "knowledge": "Peer claims B has negative communication evidence.",
                 "support": [{"ref": "S03", "excerpt": "SCRIPTED peer claim"}],
                 "proposed_use": "Use the report with its provenance limits."}
        runner.published.append(offer)
        return offer

    def test_recipient_has_carrier_not_original_access(self):
        runner, _ = self.engine("coreta_workboard")
        runner.initialize()
        offer = self.publish(runner)
        packet = runner.packet("A3", "TRY")
        access = packet["SOURCE_ACCESS"]
        self.assertEqual(set(access["direct_original_refs"]), {"T", "S06", "S07", "S11", "S15"})
        self.assertIn("O1", access["public_report_refs"])
        self.assertIn({"reported_ref": "S03", "via_public_refs": ["O1"],
                       "status": "peer_metadata_not_verified"}, access["reported_originals"])
        self.assertNotIn("S03", {r["ref"] for r in packet["REFERENCE_INDEX"]})
        self.assertEqual(packet["PUBLIC_EVIDENCE"][0], offer)
        self.assertEqual(packet["SELF_MATERIALS"], self.packets.member("A3")["SELF_MATERIALS"])
        schema = runner.gateway.contracts.schema("TRY", packet)
        Contracts.decode(json.dumps(self.change("new", work=self.work(), sources=["O1", "S06"])), schema)
        with self.assertRaises(ProtocolError):
            Contracts.decode(json.dumps(self.change("new", work=self.work(), sources=["O1", "S03"])), schema)

    def test_original_holder_can_still_cite_and_check_own_material(self):
        runner, _ = self.engine("coreta_workboard")
        runner.initialize()
        self.publish(runner)
        packet = runner.packet("A2", "TRY")
        self.assertIn("S03", packet["SOURCE_ACCESS"]["direct_original_refs"])
        Contracts.decode(json.dumps(self.change("new", work=self.work(), sources=["S03"])),
                         runner.gateway.contracts.schema("TRY", packet))

    def test_work_metadata_does_not_grant_original_access(self):
        runner, _ = self.engine("ordinary_discussion")
        runner.initialize()
        wid = runner.board.add(self.work(), "A2", sources=["S03"])
        for stage in ("DISCUSS", "FINALIZE"):
            packet = runner.packet("A3", stage)
            self.assertIn({"reported_ref": "S03", "via_public_refs": [wid],
                           "status": "peer_metadata_not_verified"}, packet["SOURCE_ACCESS"]["reported_originals"])
            self.assertIn(wid, packet["SOURCE_ACCESS"]["public_report_refs"])
            self.assertNotIn("S03", {r["ref"] for r in packet["REFERENCE_INDEX"]})

    def test_offer_support_uses_same_access_boundary(self):
        runner, _ = self.engine("coreta_workboard")
        runner.initialize(); self.publish(runner)
        packet = runner.packet("A3", "OBSERVE")
        value = self.offer(packet)
        value["offer"]["support"] = [{"ref": "O1", "excerpt": "SCRIPTED reported evidence"}]
        schema = runner.gateway.contracts.schema("OBSERVE", packet)
        Contracts.decode(json.dumps(value), schema)
        value["offer"]["support"][0]["ref"] = "S03"
        with self.assertRaises(ProtocolError):
            Contracts.decode(json.dumps(value), schema)

    def test_no_source_guessed_from_free_text_or_hidden_directory(self):
        runner, _ = self.engine("coreta_workboard")
        runner.initialize()
        w = self.work(); w["work_text"] = "Mentions S99 and S03 but has no provenance metadata."
        runner.board.add(w, "A2")
        packet = runner.packet("A3", "TRY")
        self.assertEqual(packet["SOURCE_ACCESS"]["reported_originals"], [])
        self.assertNotIn("S99", {r["ref"] for r in packet["REFERENCE_INDEX"]})

    def test_description_idempotent_and_does_not_mutate_work(self):
        runner, _ = self.engine("coreta_workboard")
        runner.initialize()
        self.publish(runner)
        before = runner.board.snapshot()
        packet = runner.packet("A3", "TRY")
        first = copy.deepcopy(packet)
        describe_sources(packet)
        self.assertEqual(packet, first)
        self.assertEqual(runner.board.snapshot(), before)

    def test_both_methods_have_same_source_policy_and_legal_ids(self):
        packets = []
        for system in ("ordinary_discussion", "coreta_workboard"):
            self.setUp()
            runner, _ = self.engine(system)
            runner.initialize(); self.publish(runner)
            packet = runner.packet("A3", "FINALIZE")
            packets.append(packet)
            schema = runner.gateway.contracts.schema("FINALIZE", packet)
            prompt = runner.gateway.prompts.render("FINALIZE", packet, schema)
            self.assertIn(SOURCE_GUIDANCE, prompt)
            self.assertEqual({r["ref"] for r in packet["REFERENCE_INDEX"]},
                             set(packet["SOURCE_ACCESS"]["direct_original_refs"])
                             | set(packet["SOURCE_ACCESS"]["public_report_refs"]))
            with self.assertRaises(ProtocolError):
                Contracts.decode(json.dumps(self.change(candidate="W1", sources=["UNKNOWN"])), schema)
        self.assertEqual(packets[0]["SOURCE_ACCESS"], packets[1]["SOURCE_ACCESS"])

    def test_both_full_paths_accept_public_carrier_citations(self):
        for system in ("ordinary_discussion", "coreta_workboard"):
            self.setUp()
            def handler(p):
                if p["STAGE"] == "DISCUSS": return self.work()
                if p["STAGE"] == "OBSERVE": return self.offer(p)
                value = self.respond(p)
                if p["STAGE"] in {"TRY", "FINALIZE"}:
                    ref = next(r["ref"] for r in p["REFERENCE_INDEX"] if r["access"] == "public_report")
                    value["declared_sources"] = [ref]
                return value
            runner, _ = self.engine(system, handler)
            self.assertEqual(runner.run()["status"], "completed")


if __name__ == "__main__":
    unittest.main()
