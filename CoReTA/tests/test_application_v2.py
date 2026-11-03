"""Offline control-flow acceptance. Scripted answers are NOT model evidence."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from coreta.application_v2.contracts import ApplicationContracts
from coreta.application_v2.prompts import ApplicationPrompts
from coreta.application_v2.runtime import ApplicationRunner
from coreta.application_v2.state import Applications
from coreta.handoff.__main__ import configure, load_counter
from coreta.handoff.gateway import Gateway, Journal
from coreta.handoff.inputs import Packets, read_json
from coreta.schemas import ProtocolError
from test_handoff import Script, contribution, request, review, NAMES, ROOT, PACK, DESIGN


def unit(target=None, refs=("T",), result="Scripted local result", missing=None):
    return {"target": target, "task_step": "Scripted concrete use for program validation",
            "bindings": [{"ref": ref, "use": "Scripted input binding"} for ref in refs],
            "result": result, "missing": missing}


def apply_output(app=None, uses=(), artifact=True, ask=None, excluded=(), retired=(), unresolved=()):
    return {"artifact": list(NAMES) if artifact is True else artifact,
            "applications": [] if app is None else [app], "artifact_uses": list(uses),
            "retire_applications": [{"ref": r, "reason": "Scripted path retirement"} for r in retired],
            "excluded": [{"ref": r, "reason": "Scripted explicit rejection"} for r in excluded],
            "unresolved": list(unresolved), "request": ask}


def pending_reply(ref="U1"):
    return {"kind": "reply", "request": {"application_ref": ref}, "required_handling_refs": ["C4"]}


def normal_update_chain(detail="Scripted concrete intermediate operation"):
    """Legal chronological fixture, including one explicitly unhelpful reply."""
    def app(target=None, refs=("T",)):
        return unit(target=target, refs=refs, result=detail)
    return [contribution(f"Scripted initial {i}") for i in range(3)] + [
        apply_output(app()),
        review("issue", target="W1"),
        apply_output(app(refs=("U1", "V1")), uses=("U1",), ask=request(question="Check downstream operation")),
        contribution("Scripted unhelpful observation, to be explicitly rejected"),
        apply_output(app(refs=("U2",)), uses=("U1", "U2"), excluded=("C4",),
                     ask=request(targets=("U1",), question="Check original input assignment")),
        contribution("Scripted correction of original input assignment"),
        apply_output(app(target="U1", refs=("C5",)), uses=("U1", "U2", "U3")),
        apply_output(app(target="U2", refs=("U4",)), uses=("U2", "U3", "U4")),
        apply_output(app(target="U3", refs=("U5",)), uses=("U3", "U4", "U5")),
        review(target="W6"),
    ]


class ApplicationV2Tests(unittest.TestCase):
    def setUp(self):
        evidence = os.environ.get("CORETA_V2_TEST_ARTIFACTS")
        if evidence:
            self.directory = Path(evidence) / self._testMethodName
            self.directory.mkdir(parents=True, exist_ok=False)
        else:
            tmp = tempfile.TemporaryDirectory(prefix="coreta-v2-offline-")
            self.addCleanup(tmp.cleanup)
            self.directory = Path(tmp.name)
        guard = patch("urllib.request.urlopen", side_effect=AssertionError("Real network forbidden in offline acceptance"))
        guard.start()
        self.addCleanup(guard.stop)
        self.config, self.defaults = configure(ROOT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
        self.contracts = ApplicationContracts(DESIGN / "message.schema.json")
        self.prompts = ApplicationPrompts(DESIGN / "PROMPTS.md")
        self.packets = Packets(PACK, "distributed_r0")

    def engine(self, outputs=(), cap=None):
        out = self.directory / "scripted_fixture_not_model_results"
        out.mkdir()
        defaults = copy.deepcopy(self.defaults)
        if cap is not None:
            defaults["limits"]["max_network_attempts_total"] = cap
        journal = Journal(out)
        script = Script(journal, outputs)
        gateway = Gateway(self.config, defaults, self.contracts, self.prompts, journal,
                          transport=script, token_counter=load_counter())
        runner = ApplicationRunner(self.packets, gateway, journal)
        return runner, script

    def initial(self):
        return [contribution(f"Scripted initial {i}") for i in range(3)]

    def state_with_two_units(self):
        state = Applications()
        state.update(apply_output(unit()))
        state.update(apply_output(unit(refs=("U1",)), uses=("U1",)))
        return state

    def validate(self, value, refs=("T",), allowed=("ask",)):
        schema = self.contracts.schema("APPLY", set(refs), self.packets.agents, allowed, NAMES)
        Draft202012Validator.check_schema(schema)
        return self.contracts.decode(json.dumps(value), schema)

    def test_empty_registry_schema_and_no_application(self):
        self.validate(apply_output())

    def test_application_schema_accepts_new_unit(self):
        self.validate(apply_output(unit()))

    def test_invisible_and_future_refs_rejected(self):
        for value in (apply_output(unit(target="U1")), apply_output(unit(refs=("C99",))),
                      apply_output(uses=("U1",))):
            with self.subTest(value=value), self.assertRaises(ProtocolError):
                self.validate(value)

    def test_old_application_shape_rejected(self):
        value = apply_output()
        value["applications"] = [{"refs": ["T"], "result": "Old shape"}]
        with self.assertRaises(ProtocolError):
            self.validate(value)

    def test_no_request_when_budget_disallows(self):
        with self.assertRaises(ProtocolError):
            self.validate(apply_output(unit(), ask=request(targets=("T",))), allowed=())

    def test_all_stage_schemas_valid(self):
        for stage in ("CONTRIBUTE", "REPLY", "APPLY", "REVIEW"):
            schema = self.contracts.schema(stage, {"T", "C1", "U1", "W1", "V1", "Q1"}, self.packets.agents, ["ask"], NAMES)
            Draft202012Validator.check_schema(schema)

    def test_waiting_and_partial_result_states(self):
        state = Applications()
        state.update(apply_output(unit(result=None, missing="Need input")))
        self.assertEqual(state.units["U1"]["status"], "waiting")
        state.update(apply_output(unit(target="U1", missing="Need residual input"), uses=("U1",)))
        self.assertEqual(state.units["U1"]["status"], "superseded")
        self.assertEqual(state.units["U2"]["status"], "provisional")

    def test_empty_result_and_missing_rejected(self):
        with self.assertRaises(ProtocolError):
            Applications().update(apply_output(unit(result=None)))

    def test_second_explicit_missing_rejected(self):
        state = Applications()
        state.update(apply_output(unit(missing="First")))
        with self.assertRaises(ProtocolError):
            copy.deepcopy(state).update(apply_output(unit(missing="Second"), uses=("U1",)))

    def test_provisional_upstream_propagates(self):
        state = Applications()
        state.update(apply_output(unit(missing="Need input")))
        state.update(apply_output(unit(refs=("U1",)), uses=("U1",)))
        self.assertEqual(state.units["U2"]["status"], "provisional")
        self.assertEqual({r["ref"] for r in state.blocked()}, {"U1", "U2"})

    def test_silent_candidate_drop_rejected(self):
        state = self.state_with_two_units()
        with self.assertRaises(ProtocolError):
            state.update(apply_output(uses=("U1",)))

    def test_explicit_exclusion_preserves_unit_history(self):
        state = self.state_with_two_units()
        state.update(apply_output(uses=("U2",), excluded=("U1",)))
        self.assertEqual(state.candidate_refs, ["U2"])
        self.assertIn("U1", state.units)

    def test_replace_invalidates_declared_descendant(self):
        state = self.state_with_two_units()
        state.update(apply_output(unit(target="U1"), uses=("U1", "U2")))
        self.assertEqual(state.units["U2"]["status"], "stale")
        self.assertEqual(state.candidate_refs, ["U2", "U3"])
        self.assertEqual(state.units["U1"]["result"], "Scripted local result")

    def test_retire_invalidates_descendant(self):
        state = self.state_with_two_units()
        state.update(apply_output(uses=("U2",), retired=("U1",)))
        self.assertEqual(state.units["U1"]["status"], "retired")
        self.assertEqual(state.units["U2"]["status"], "stale")

    def test_replaced_self_or_descendant_cannot_support_revision(self):
        state = self.state_with_two_units()
        for ref in ("U1", "U2"):
            with self.subTest(ref=ref), self.assertRaises(ProtocolError):
                copy.deepcopy(state).update(apply_output(unit(target="U1", refs=(ref,)), uses=("U1", "U2")))

    def test_cannot_bind_stale_unit(self):
        state = self.state_with_two_units()
        state.update(apply_output(unit(target="U1"), uses=("U1", "U2")))
        with self.assertRaises(ProtocolError):
            state.update(apply_output(unit(refs=("U2",)), uses=("U2", "U3")))

    def test_reply_accepted_on_unrelated_unit_rejected(self):
        state = self.state_with_two_units()
        with self.assertRaises(ProtocolError):
            state.update(apply_output(unit(target="U2", refs=("C4",)), uses=("U1", "U2")), pending_reply())

    def test_reply_must_be_handled(self):
        state = Applications()
        state.update(apply_output(unit(missing="Need input")))
        with self.assertRaises(ProtocolError):
            state.update(apply_output(unit(target="U1"), uses=("U1",)), pending_reply())

    def test_retiring_requested_path_alone_handles_reply(self):
        state = Applications()
        state.update(apply_output(unit(missing="Need input")))
        state.update(apply_output(retired=("U1",)), pending_reply())
        self.assertEqual(state.units["U1"]["status"], "retired")
        self.assertFalse(state.blocked())

    def test_binding_and_excluding_reply_cannot_bypass_original_target(self):
        state = self.state_with_two_units()
        with self.assertRaises(ProtocolError):
            state.update(apply_output(unit(target="U2", refs=("C4",)), uses=("U1", "U2"),
                                      excluded=("C4",)), pending_reply())

    def test_accepted_review_of_one_unit_must_address_that_unit(self):
        state = self.state_with_two_units()
        pending = {"kind": "review", "review": {"target_refs": ["U1"]}, "required_handling_refs": ["V1"]}
        with self.assertRaises(ProtocolError):
            state.update(apply_output(unit(target="U2", refs=("V1",)), uses=("U1", "U2")), pending)

    def test_explicit_review_rejection_keeps_application(self):
        state = self.state_with_two_units()
        pending = {"kind": "review", "review": {"target_refs": ["U1"]}, "required_handling_refs": ["V1"]}
        state.update(apply_output(uses=("U1", "U2"), excluded=("V1",)), pending)
        self.assertEqual(state.units["U1"]["status"], "applied_declared")

    def test_accepted_review_revises_original_unit_in_runner(self):
        runner, _ = self.engine(self.initial() + [apply_output(unit()), review("issue", target="U1"),
            apply_output(unit(target="U1", refs=("V1",)), uses=("U1",)), review(target="W2")])
        self.assertEqual(runner.run()["status"], "reviewed_no_defect")
        self.assertEqual(runner.application_state.units["U1"]["status"], "superseded")

    def test_retiring_reviewed_path_alone_handles_review(self):
        runner, _ = self.engine(self.initial() + [apply_output(unit()), review("issue", target="U1"),
            apply_output(retired=("U1",)), review(target="W2")])
        self.assertEqual(runner.run()["status"], "reviewed_no_defect")
        self.assertEqual(runner.application_state.units["U1"]["status"], "retired")

    def test_retired_requested_path_alone_is_accepted_in_runner(self):
        runner, _ = self.engine(self.initial() + [apply_output(unit(missing="Need input"), ask=request()), contribution(),
            apply_output(retired=("U1",)), review(target="W2")])
        self.assertEqual(runner.run()["status"], "reviewed_no_defect")
        self.assertEqual(len(runner.contributions), 4)

    def test_exclusion_does_not_free_global_missing_slot(self):
        state = Applications()
        state.update(apply_output(unit(missing="First input")))
        state.update(apply_output(excluded=("U1",)))
        with self.assertRaises(ProtocolError):
            copy.deepcopy(state).update(apply_output(unit(missing="Second input")))
        state.update(apply_output(unit(missing="Second input"), retired=("U1",)))
        self.assertEqual(state.units["U2"]["missing"], "Second input")

    def test_request_target_remapped_to_new_version(self):
        state = Applications()
        state.update(apply_output(unit()))
        delta = state.update(apply_output(unit(target="U1"), uses=("U1",), ask=request(targets=("U1",))))
        self.assertEqual(delta["request_target"], "U2")

    def test_explicit_request_target_overrides_recent_unit(self):
        state = self.state_with_two_units()
        delta = state.update(apply_output(unit(), uses=("U1", "U2"), ask=request(targets=("U1",))))
        self.assertEqual(delta["request_target"], "U1")

    def test_request_without_application_rejected(self):
        with self.assertRaises(ProtocolError):
            Applications().update(apply_output(ask=request(targets=("T",))))

    def test_request_two_applications_rejected(self):
        state = self.state_with_two_units()
        with self.assertRaises(ProtocolError):
            state.update(apply_output(uses=("U1", "U2"), ask=request(targets=("U1", "U2"))))

    def test_spine_receive_then_reapply_original_unit(self):
        runner, script = self.engine(self.initial() + [
            apply_output(unit(refs=("C1",), missing="Need operation"), ask=request()),
            contribution("Scripted supplemental operation"),
            apply_output(unit(target="U1", refs=("C1", "C4")), uses=("U1",)), review(target="W2")])
        result = runner.run()
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(result["protocol"], "coreta/application-v2")
        self.assertEqual(result["http_attempts"], 7)
        self.assertEqual(runner.requests[0]["application_ref"], "U1")
        self.assertEqual(runner.application_state.units["U1"]["missing"], "Need operation")
        self.assertEqual(runner.application_state.units["U2"]["status"], "applied_declared")
        self.assertFalse(script.outputs)
        self.assertTrue(result["usage_complete"])

    def test_reply_receipt_does_not_resolve_missing(self):
        runner, _ = self.engine(self.initial() + [apply_output(unit(missing="Need input"), ask=request()), contribution()])
        for agent in runner.agents:
            runner.contribute(agent)
        ask = runner.apply()
        runner.intervene(ask)
        self.assertEqual(runner.application_state.units["U1"]["missing"], "Need input")
        self.assertEqual(runner.application_state.units["U1"]["status"], "provisional")
        self.assertEqual(runner.pending["request"]["application_ref"], "U1")

    def test_partial_reply_cannot_claim_completed(self):
        runner, _ = self.engine(self.initial() + [apply_output(unit(missing="Need input"), ask=request()), contribution(),
            apply_output(unit(target="U1", refs=("C4",), missing="Residual input"), uses=("U1",)), review(target="W2")])
        result = runner.run()
        self.assertEqual(result["status"], "best_effort_unresolved")
        self.assertEqual(result["application_blockers"][0]["missing"], "Residual input")

    def test_rejected_reply_retains_original_gap(self):
        runner, _ = self.engine(self.initial() + [apply_output(unit(missing="Need input"), ask=request()), contribution(),
            apply_output(uses=("U1",), artifact=None, excluded=("C4",)), review()])
        result = runner.run()
        self.assertEqual(result["status"], "best_effort_unresolved")
        self.assertEqual(len(runner.application_state.units), 1)
        self.assertIsNone(runner.pending.get("request"))

    def test_unable_reply_note_can_be_rejected_via_q(self):
        runner, _ = self.engine(self.initial() + [apply_output(unit(missing="Need input"), ask=request()),
            {"items": [], "note": "Scripted inability to supply input"},
            apply_output(uses=("U1",), excluded=("Q1",)), review(target="W2")])
        self.assertEqual(runner.run()["status"], "best_effort_unresolved")

    def test_retire_requested_path_and_use_reply_in_new_path(self):
        runner, _ = self.engine(self.initial() + [apply_output(unit(missing="Need input"), ask=request()), contribution(),
            apply_output(unit(refs=("C4",)), retired=("U1",)), review(target="W2")])
        result = runner.run()
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(runner.application_state.units["U1"]["status"], "retired")
        self.assertEqual(len(runner.contributions), 4)

    def test_no_request_or_application_required(self):
        runner, _ = self.engine(self.initial() + [apply_output(), review()])
        result = runner.run()
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(result["interventions"], 0)
        self.assertFalse(runner.application_state.units)

    def test_no_request_needed_with_complete_application(self):
        runner, _ = self.engine(self.initial() + [apply_output(unit(refs=("C1", "C2"))), review()])
        self.assertEqual(runner.run()["status"], "reviewed_no_defect")
        self.assertEqual(runner.interventions, 0)

    def test_model_unresolved_prevents_completed_status(self):
        runner, _ = self.engine(self.initial() + [apply_output(unresolved=("Scripted consequential unknown",)), review()])
        self.assertEqual(runner.run()["status"], "best_effort_unresolved")

    def test_retained_artifact_creates_new_work_for_changed_basis(self):
        runner, _ = self.engine([apply_output(unit()), apply_output(unit(target="U1"), uses=("U1",), artifact=None)])
        runner.apply()
        old = runner.work["artifact"]
        runner.apply()
        self.assertEqual(runner.work["ref"], "W2")
        self.assertEqual(runner.work["artifact"], old)
        self.assertTrue(runner.work["retained_text"])

    def seed_and_invalidate(self, tail, cap=None):
        outputs = [apply_output(unit()), apply_output(unit(refs=("U1",)), uses=("U1",))]
        outputs += self.initial() + [apply_output(unit(target="U1"), uses=("U1", "U2"), artifact=None)] + tail
        runner, script = self.engine(outputs, cap=cap)
        runner.apply()
        runner.apply()
        return runner, script

    def test_stale_application_recomputed_before_review(self):
        runner, script = self.seed_and_invalidate([
            apply_output(unit(target="U2", refs=("U3",)), uses=("U2", "U3")), review(target="W4")])
        result = runner.run()
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(runner.application_state.units["U2"]["status"], "superseded")
        focus_call = script.seen[-2]
        self.assertEqual(focus_call["context"]["stage"], "APPLY")
        self.assertIn('"APPLICATION_FOCUS": {"ref": "U2"', focus_call["payload"]["instructions"])
        self.assertEqual([e["kind"] for e in runner.events][-3:], ["application_update_required", "apply", "review"])

    def test_explicitly_excluding_stale_leaf_allows_new_candidate(self):
        runner, _ = self.seed_and_invalidate([apply_output(uses=("U3",), excluded=("U2",)),
                                             review(target="W4")])
        # Here U2 itself is excluded; no dependent candidate remains.
        self.assertEqual(runner.run()["status"], "reviewed_no_defect")

    def test_excluding_stale_ancestor_does_not_repair_descendant(self):
        runner, _ = self.engine([
            apply_output(unit()),
            apply_output(unit(refs=("U1",)), uses=("U1",)),
            apply_output(unit(refs=("U2",)), uses=("U1", "U2")),
            *self.initial(),
            apply_output(unit(target="U1"), uses=("U1", "U2", "U3")),
            apply_output(uses=("U3", "U4"), excluded=("U2",)),
        ])
        for _ in range(3):
            runner.apply()
        result = runner.run()
        self.assertEqual(result["status"], "best_effort_unresolved")
        self.assertEqual(result["stop_reason"], "application_update_unresolved")
        self.assertEqual(result["final_reviews"], 0)
        self.assertEqual({r["ref"] for r in result["application_blockers"]}, {"U1", "U2", "U3"})

    def test_multiple_stale_levels_updated_upstream_first(self):
        runner, script = self.engine([
            apply_output(unit()),
            apply_output(unit(refs=("U1",)), uses=("U1",)),
            apply_output(unit(refs=("U2",)), uses=("U1", "U2")),
            *self.initial(),
            apply_output(unit(target="U1"), uses=("U1", "U2", "U3")),
            apply_output(unit(target="U2", refs=("U4",)), uses=("U2", "U3", "U4")),
            apply_output(unit(target="U3", refs=("U5",)), uses=("U3", "U4", "U5")),
            review(target="W6"),
        ])
        for _ in range(3):
            runner.apply()
        result = runner.run()
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual([e["focus"]["ref"] for e in runner.events if e["kind"] == "application_update_required"], ["U2", "U3"])
        self.assertFalse(script.outputs)

    def test_normal_run_builds_chain_and_repairs_two_levels(self):
        runner, script = self.engine(normal_update_chain())
        result = runner.run()
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(result["http_attempts"], 13)
        self.assertEqual([e["focus"]["ref"] for e in runner.events if e["kind"] == "application_update_required"], ["U2", "U3"])
        self.assertEqual([c["context"]["stage"] for c in script.seen],
                         ["CONTRIBUTE"] * 3 + ["APPLY", "REVIEW", "APPLY", "REPLY", "APPLY", "REPLY", "APPLY", "APPLY", "APPLY", "REVIEW"])
        self.assertFalse(result["application_blockers"])
        self.assertFalse(script.outputs)

    def pressure(self, repetitions):
        detail = "A concrete intermediate calculation uses the corrected input and retains the stated relation. " * repetitions
        outputs = normal_update_chain(detail)
        runner, script = self.engine(outputs)
        output_sizes = []
        for output in outputs:
            if "applications" in output:
                limit = self.defaults["max_output_tokens"]["apply"]
                size = runner.gateway.client.token_counter(json.dumps(output, ensure_ascii=False))
                output_sizes.append(size)
                self.assertLessEqual(size, limit)
        prepared_sizes = []
        original_payload = runner.gateway.client.payload
        def prepare(*args, **kwargs):
            payload = original_payload(*args, **kwargs)
            prepared_sizes.append(runner.gateway.client.size(payload))
            return payload
        with patch.object(runner.gateway.client, "payload", side_effect=prepare):
            result = runner.run()
        (self.directory / "pressure.json").write_text(json.dumps({
            "kind": "synthetic_length_profile_not_model_evidence", "repetitions": repetitions,
            "max_apply_output_token_estimate": max(output_sizes), "prepared_input_estimates": prepared_sizes,
            "input_limit": self.config["generation"]["max_input_tokens"],
            "status": result["status"], "error": result["error"], "simulated_attempts": result["http_attempts"],
        }, indent=2), encoding="utf-8")
        self.assertLessEqual(result["http_attempts"], 20)
        requests = [json.loads(line) for line in (runner.journal.root / "requests.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertTrue(all(r["estimated_input_count"] <= self.config["generation"]["max_input_tokens"] for r in requests))
        return result, script

    def test_normal_long_input_profile(self):
        result, script = self.pressure(80)
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertFalse(script.outputs)

    def test_upper_long_input_profile(self):
        result, _ = self.pressure(250)
        self.assertEqual(result["status"], "reviewed_no_defect")

    def test_output_legal_but_accumulated_input_overflows(self):
        result, _ = self.pressure(345)
        self.assertEqual(result["error"]["code"], "CONTEXT_OVERFLOW")
        self.assertIsNotNone(result["artifact"])
        self.assertEqual(result["format_repairs"], 0)

    def test_overflow_stops_before_transport(self):
        runner, script = self.engine(normal_update_chain())
        runner.gateway.client.config["generation"]["max_input_tokens"] = 1
        result = runner.run()
        self.assertEqual(result["error"]["code"], "CONTEXT_OVERFLOW")
        self.assertFalse(script.seen)

    def test_inspection_exports_evidence_without_semantic_scoring(self):
        from coreta.application_v2.inspect import export
        runner, _ = self.engine(normal_update_chain())
        runner.run()
        before = {p.name: p.read_bytes() for p in runner.journal.root.iterdir()}
        report = export(runner.journal.root, self.directory / "inspection")
        self.assertEqual(len(report["records"]), 4)
        self.assertIsNone(report["automatic_semantic_success"])
        self.assertTrue(all(all(v is None for v in r["content_judgment"].values()) for r in report["records"]))
        q1 = next(r for r in report["records"] if r["message_ref"] == "Q1")
        self.assertIsNone(q1["replacement_application"])
        self.assertEqual(q1["following_application"]["ref"], "U3")
        q2 = next(r for r in report["records"] if r["message_ref"] == "Q2")
        self.assertEqual(q2["replacement_application"]["ref"], "U4")
        self.assertEqual(q2["original_application"]["ref"], "U1")
        self.assertEqual(before, {p.name: p.read_bytes() for p in runner.journal.root.iterdir()})

    def test_inspection_keeps_unanswered_request_unjudged(self):
        from coreta.application_v2.inspect import collect
        runner, _ = self.engine(self.initial() + [apply_output(unit(missing="Need input"), ask=request())])
        for member in runner.agents:
            runner.contribute(member)
        ask = runner.apply()
        runner.gateway.deadline = time.monotonic() - 1
        with self.assertRaises(ProtocolError):
            runner.intervene(ask)
        row = collect(runner.journal.root)["records"][0]
        self.assertFalse(row["reply_received"])
        self.assertIsNone(row["following_apply_event"])

    def test_inspection_rejects_output_inside_source_run(self):
        from coreta.application_v2.inspect import export
        runner, _ = self.engine(self.initial() + [apply_output(), review()])
        runner.run()
        with self.assertRaises(ValueError):
            export(runner.journal.root, runner.journal.root / "inspection")

    def test_inspection_cli_entry(self):
        from coreta.application_v2.inspect import main
        runner, _ = self.engine(self.initial() + [apply_output(), review()])
        runner.run()
        output = self.directory / "inspection"
        with patch.object(sys, "argv", ["inspect", "--run", str(runner.journal.root), "--output", str(output)]):
            self.assertEqual(main(), 0)
        self.assertTrue((output / "REVIEW.md").exists())

    def test_stale_budget_stop_retains_unresolved(self):
        runner, _ = self.seed_and_invalidate([], cap=7)
        result = runner.run()
        self.assertEqual(result["stop_reason"], "application_update_budget")
        self.assertEqual(result["status"], "best_effort_unresolved")
        self.assertEqual(result["final_reviews"], 0)

    def test_focus_ignoring_output_repaired_without_partial_commit(self):
        runner, _ = self.seed_and_invalidate([
            apply_output(unit(), uses=("U2", "U3")),
            apply_output(unit(target="U2", refs=("U3",)), uses=("U2", "U3")), review(target="W4")])
        result = runner.run()
        self.assertEqual(result["format_repairs"], 1)
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(len(runner.application_state.units), 4)

    def test_invalid_action_rolls_back_then_recovers(self):
        invalid = apply_output(unit(), ask=request(targets=("U1", "U2")), uses=("U1", "U2"))
        runner, _ = self.engine([apply_output(unit()), apply_output(unit(), uses=("U1",)), invalid,
                                 apply_output(uses=("U1", "U2"))])
        runner.apply()
        runner.apply()
        before = runner.application_state.record()
        runner.apply()
        self.assertEqual(runner.application_state.record(), before)
        self.assertEqual(runner.journal.repairs, 1)

    def test_schema_failure_preserves_pending_reply_and_work(self):
        runner, script = self.engine([apply_output(unit(missing="Need input")), "not JSON", "still not JSON"])
        runner.apply()
        runner.pending = pending_reply()
        before = (runner.application_state.record(), copy.deepcopy(runner.work), copy.deepcopy(runner.pending))
        with self.assertRaises(ProtocolError):
            runner.apply()
        self.assertEqual((runner.application_state.record(), runner.work, runner.pending), before)
        self.assertFalse(script.outputs)

    def test_total_attempt_cap_includes_format_recovery(self):
        runner, _ = self.engine(self.initial() + ["bad JSON", "bad JSON"], cap=4)
        result = runner.run()
        self.assertEqual(result["status"], "budget_exhausted")
        self.assertEqual(result["http_attempts"], 4)

    def test_deadline_stops_before_transport(self):
        runner, script = self.engine()
        runner.gateway.deadline = time.monotonic() - 1
        self.assertEqual(runner.run()["status"], "budget_exhausted")
        self.assertFalse(script.seen)

    def test_repeated_request_is_bounded(self):
        runner, script = self.engine(self.initial() + [apply_output(unit(missing="Need input"), ask=request()), contribution(),
            apply_output(uses=("U1",), excluded=("C4",), ask=request()), review(target="W2")])
        result = runner.run()
        self.assertEqual(result["interventions"], 1)
        self.assertEqual(result["status"], "best_effort_unresolved")
        self.assertFalse(script.outputs)

    def test_three_interventions_and_two_reviews_remain_bounded(self):
        outputs = self.initial() + [apply_output(unit(missing="Need input"), ask=request())]
        for i in range(1, 4):
            outputs.append(contribution(f"Scripted supplement {i}"))
            ask = request(question=f"Need residual input {i}", targets=(f"U{i}",)) if i < 3 else None
            outputs.append(apply_output(unit(target=f"U{i}", refs=(f"C{i+3}",),
                                                  missing="Residual input" if i < 3 else None),
                                        uses=(f"U{i}",), ask=ask))
        outputs += [review("issue", target="W4"),
                    apply_output(unit(target="U4", refs=("V1",)), uses=("U4",)),
                    review("issue", target="W5"),
                    apply_output(unit(target="U5", refs=("V2",)), uses=("U5",))]
        runner, script = self.engine(outputs)
        result = runner.run()
        self.assertEqual(result["interventions"], 3)
        self.assertEqual(result["final_reviews"], 2)
        self.assertEqual(result["stop_reason"], "review_limit")
        self.assertEqual(result["status"], "best_effort_unreviewed")
        self.assertEqual(result["http_attempts"], 14)
        self.assertFalse(script.outputs)

    def test_private_source_binding_cannot_be_cited_by_other_member(self):
        own = {r["ref"] for r in self.packets.member("A2")["REFERENCE_INDEX"]}
        foreign = next(m["ref"] for m in self.packets.member("A1")["SELF_MATERIALS"] if m["ref"] not in own)
        with self.assertRaises(ProtocolError):
            self.validate(apply_output(unit(refs=(foreign,))), refs=own)

    def test_source_coverage_traces_application_to_contribution(self):
        source = self.packets.member("A1")["SELF_MATERIALS"][0]["ref"]
        runner, _ = self.engine([contribution(refs=(source,)), contribution(), contribution(),
                                apply_output(unit(refs=("C1",))), review()])
        result = runner.run()
        self.assertIn(source, runner.source_refs())
        self.assertEqual(result["latest_review"]["author"], "A1")

    def test_prepare_entry_and_live_guard(self):
        from coreta.application_v2.__main__ import main
        out = self.directory / "prepared_initial_inputs"
        with patch.object(sys, "argv", ["application_v2", "prepare", "--output", str(out)]):
            self.assertEqual(main(), 0)
        self.assertTrue(read_json(out / "PREPARATION_ONLY.json")["initial_stage_only"])
        denied = self.directory / "must_not_exist"
        with patch.object(sys, "argv", ["application_v2", "run", "--output", str(denied)]), self.assertRaises(SystemExit):
            main()
        self.assertFalse(denied.exists())

    def test_score_entry_reads_scripted_result_separately(self):
        from coreta.application_v2.__main__ import main
        runner, _ = self.engine(self.initial() + [apply_output(), review()])
        runner.run()
        out = self.directory / "SCRIPTED_OFFLINE_SCORE_NOT_MODEL_EVIDENCE.json"
        with patch.object(sys, "argv", ["application_v2", "score", "--run", str(runner.journal.root), "--output", str(out)]):
            self.assertEqual(main(), 0)
        self.assertTrue(out.exists())

    def test_module_entry_help_in_subprocess(self):
        result = subprocess.run([sys.executable, "-m", "coreta.application_v2", "--help"],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("prepare", result.stdout)

    def test_run_entry_with_scripted_transport_and_separate_score(self):
        from coreta.application_v2.__main__ import main
        out = self.directory / "cli_scripted_not_model_results"
        def gateway_factory(config, defaults, contracts, prompts, journal, **kwargs):
            script = Script(journal, self.initial() + [apply_output(unit()), review()])
            return Gateway(config, defaults, contracts, prompts, journal, transport=script, **kwargs)
        with patch.object(sys, "argv", ["application_v2", "run", "--live", "--output", str(out)]), \
                patch.dict(os.environ, {"DEEPSEEK_API_KEY": "offline-fixture-not-a-real-key"}), \
                patch("coreta.application_v2.__main__.Gateway", side_effect=gateway_factory):
            self.assertEqual(main(), 0)
        result = read_json(out / "result.json")
        manifest = read_json(out / "manifest.json")
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertFalse(manifest["scoring_feedback"])
        self.assertEqual(result["http_attempts"], 5)
        self.assertFalse(result["externally_scored"])

    def test_run_entry_interruption_saves_state(self):
        from coreta.application_v2.__main__ import main
        out = self.directory / "interrupted_scripted_fixture"
        def interrupt(payload, timeout):
            raise KeyboardInterrupt()
        def gateway_factory(config, defaults, contracts, prompts, journal, **kwargs):
            return Gateway(config, defaults, contracts, prompts, journal, transport=interrupt, **kwargs)
        with patch.object(sys, "argv", ["application_v2", "run", "--live", "--output", str(out)]), \
                patch.dict(os.environ, {"DEEPSEEK_API_KEY": "offline-fixture-not-a-real-key"}), \
                patch("coreta.application_v2.__main__.Gateway", side_effect=gateway_factory), \
                self.assertRaises(KeyboardInterrupt):
            main()
        self.assertEqual(read_json(out / "implementation_or_interruption.json")["type"], "KeyboardInterrupt")
        self.assertEqual(read_json(out / "state.json")["protocol"], "coreta/application-v2")


if __name__ == "__main__":
    unittest.main()
