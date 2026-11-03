"""Offline protocol fixtures only. Scripted success is not agent capability evidence."""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from coreta.handoff.__main__ import configure, load_counter, DEFAULT_TOKENIZER
from coreta.handoff.contracts import HandoffContracts
from coreta.handoff.gateway import Gateway, Journal
from coreta.handoff.inputs import Packets, read_json
from coreta.handoff.prompts import HandoffPrompts
from coreta.handoff.ranking import parse_ranking, render_ranking, score_artifact, score_run
from coreta.handoff.runtime import Runner
from coreta.schemas import ProtocolError

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "data/task-packs/moon-survival-v1"
DESIGN = ROOT / "design/expertise-handoff/protocol-v1"
NAMES = [i["name"] for i in read_json(PACK / "public/task.json")["items"]]
ARTIFACT = "MY RANKING:\n" + "\n".join(f"{i}. {name}" for i, name in enumerate(NAMES, 1))


def contribution(content="Scripted local observation", refs=("T",)):
    return {"items": [{"content": content, "support": "Offline fixture, not model evidence",
                       "support_refs": list(refs), "conditions": [], "needs": []}], "note": ""}


def application(artifact=ARTIFACT, refs=("C1", "C2", "C3"), request=None, unresolved=()):
    if isinstance(artifact, str):
        parsed, error = parse_ranking(artifact, set(NAMES))
        if error:
            raise ValueError("Use an invalid raw dict explicitly when testing schema rejection")
        artifact = sorted(parsed, key=parsed.get)
    return {"artifact": artifact,
            "applications": [{"refs": list(refs), "result": "Scripted application for control-flow validation"}],
            "excluded": [], "unresolved": list(unresolved), "request": request}


def request(kind="ask", recipient="A1", question="Explain the missing operation", targets=("C1",)):
    return {"kind": kind, "recipient": recipient, "target_refs": list(targets),
            "question": question, "impact": "May change the ranking decision"}


def review(verdict="no_defect_found", target="W1", suggestion=None):
    return {"verdict": verdict, "finding": "Scripted inspection for program validation, not a correctness claim",
            "target_refs": [target], "check_suggestion": suggestion}


def response(value):
    raw = value if isinstance(value, str) else json.dumps(value)
    return {"status": "completed", "output": [{"type": "message", "content": [
        {"type": "output_text", "text": raw}]}], "usage": {"input_tokens": 1, "output_tokens": 1}}


def answer(explanation="Scripted complete answer", ranking=None):
    return {"explanation": explanation, "ranking": list(NAMES if ranking is None else ranking)}


class Script:
    def __init__(self, journal, outputs):
        self.journal, self.outputs, self.seen = journal, list(outputs), []

    def __call__(self, payload, timeout):
        self.seen.append({"context": copy.deepcopy(self.journal.call_context),
                          "payload": copy.deepcopy(payload), "timeout": timeout})
        if not self.outputs:
            raise AssertionError("Unexpected additional scripted call")
        value = self.outputs.pop(0)
        if isinstance(value, Exception):
            raise value
        if callable(value):
            value = value(payload)
        return response(value)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="coreta-handoff-fixture-")
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        # Accidental networking must fail, even if a real key is present in the environment.
        self.network_guard = patch("urllib.request.urlopen", side_effect=AssertionError("No real networking in fixtures"))
        self.network_guard.start()
        self.addCleanup(self.network_guard.stop)
        self.config, self.defaults = configure(ROOT / "config/deepseek_flash_inspection.json", DESIGN / "runtime.defaults.json")
        self.contracts = HandoffContracts(DESIGN / "message.schema.json")
        self.prompts = HandoffPrompts(DESIGN / "PROMPTS.md")
        self.packets = Packets(PACK, "distributed_r0")

    def engine(self, outputs=(), *, packets=None, cap=None, retries=None, folder="fixture"):
        out = self.directory / folder
        out.mkdir()
        defaults = copy.deepcopy(self.defaults)
        if cap is not None:
            defaults["limits"]["max_network_attempts_total"] = cap
        if retries is not None:
            defaults["limits"]["transport_retries_per_request"] = retries
        journal = Journal(out)
        script = Script(journal, outputs)
        gateway = Gateway(self.config, defaults, self.contracts, self.prompts, journal, transport=script)
        runner = Runner(packets or self.packets, gateway, journal, task_ordinal=1)
        return runner, script

    def copy_packets(self, modify):
        root = self.directory / "copy"
        folder = root / "packets/distributed_r0"
        folder.mkdir(parents=True)
        for agent in self.packets.agents:
            packet = self.packets.member(agent)
            modify(agent, packet)
            (folder / f"{agent}.json").write_text(json.dumps(packet), encoding="utf-8")
        return root

    def first_three(self):
        return [contribution(f"Scripted item {i}") for i in range(3)]

    def test_load_all_six_conditions(self):
        folders = list((PACK / "packets").iterdir())
        self.assertEqual(len(folders), 6)
        for folder in folders:
            packets = Packets(PACK, folder.name)
            self.assertEqual(sum(len(packets.member(a)["SELF_MATERIALS"]) for a in packets.agents), 15)

    def test_material_ids_with_leading_zero_are_valid(self):
        refs = {m["ref"] for a in self.packets.agents for m in self.packets.member(a)["SELF_MATERIALS"]}
        self.assertIn("S01", refs)

    def test_input_unknown_answer_field_is_rejected(self):
        def change(agent, packet):
            if agent == "A1":
                packet["correct_answer"] = "not for runtime"
        with self.assertRaises(ProtocolError):
            Packets(self.copy_packets(change), "distributed_r0")

    def test_input_foreign_source_in_reference_index_is_rejected(self):
        foreign = self.packets.member("A2")["SELF_MATERIALS"][0]["ref"]
        def change(agent, packet):
            if agent == "A1":
                packet["REFERENCE_INDEX"].append({"ref": foreign, "kind": "private_material"})
        with self.assertRaises(ProtocolError):
            Packets(self.copy_packets(change), "distributed_r0")

    def test_directory_body_injection_rejected(self):
        def change(agent, packet):
            packet["DIRECTORY"][0]["accessible_materials"][0]["content"] = "unauthorized正文"
        with self.assertRaises(ProtocolError):
            Packets(self.copy_packets(change), "distributed_r0")

    def test_runtime_loads_no_offline_data(self):
        from coreta.handoff import inputs
        original = inputs.read_json
        def guarded(path):
            self.assertNotIn("offline", path.parts)
            return original(path)
        with patch.object(inputs, "read_json", guarded):
            Packets(PACK, "concentrated_A1")

    def test_member_snapshot_is_deep_copy(self):
        p = self.packets.member("A1")
        p["SELF_MATERIALS"][0]["content"] = "changed"
        self.assertNotEqual(p, self.packets.member("A1"))

    def test_no_other_private_text_in_initial_prompt(self):
        def change(agent, packet):
            for index, material in enumerate(packet["SELF_MATERIALS"]):
                material["content"] = f"PRIVATE_{agent}_{index}_SENTINEL"
        packets = Packets(self.copy_packets(change), "distributed_r0")
        runner, script = self.engine(self.first_three() + [application(), review()], packets=packets)
        self.assertEqual(runner.run("coreta")["status"], "reviewed_no_defect")
        for call in script.seen[:3]:
            agent = call["context"]["member"]
            prompt = call["payload"]["instructions"]
            self.assertIn(f"PRIVATE_{agent}_0_SENTINEL", prompt)
            for other in packets.agents:
                if other != agent:
                    self.assertNotIn(f"PRIVATE_{other}_0_SENTINEL", prompt)

    def test_schema_extracts_only_required_definitions(self):
        schema = self.contracts.schema("CONTRIBUTE", {"T"}, self.packets.agents, [])
        Draft202012Validator.check_schema(schema)
        self.assertNotIn("ApplyOutput", schema["$defs"])
        self.assertNotIn("Request", schema["$defs"])

    def test_invisible_reference_rejected(self):
        schema = self.contracts.schema("CONTRIBUTE", {"T"}, self.packets.agents, [])
        with self.assertRaises(ProtocolError):
            self.contracts.decode(json.dumps(contribution(refs=("S99",))), schema)

    def test_future_work_reference_rejected(self):
        schema = self.contracts.schema("APPLY", {"T", "C1"}, self.packets.agents, ["ask"], ranking_items=NAMES)
        with self.assertRaises(ProtocolError):
            self.contracts.decode(json.dumps(application(refs=("W1",))), schema)

    def test_unknown_recipient_rejected(self):
        schema = self.contracts.schema("APPLY", {"T", "C1"}, self.packets.agents, ["ask"], ranking_items=NAMES)
        with self.assertRaises(ProtocolError):
            self.contracts.decode(json.dumps(application(refs=("C1",), request=request(recipient="A4"))), schema)

    def test_no_request_when_no_budget(self):
        schema = self.contracts.schema("APPLY", {"T", "C1"}, self.packets.agents, [], ranking_items=NAMES)
        with self.assertRaises(ProtocolError):
            self.contracts.decode(json.dumps(application(refs=("C1",), request=request())), schema)

    def test_duplicate_json_key_is_rejected(self):
        schema = self.contracts.schema("INDEPENDENT", {"T"}, self.packets.agents, [], ranking_items=NAMES)
        with self.assertRaises(ProtocolError):
            self.contracts.decode('{"text":"first","text":"second"}', schema)

    def test_nan_json_is_rejected(self):
        schema = self.contracts.schema("INDEPENDENT", {"T"}, self.packets.agents, [], ranking_items=NAMES)
        with self.assertRaises(ProtocolError):
            self.contracts.decode('{"text":NaN}', schema)

    def test_prompt_ranking_override_and_no_code_only_requirement(self):
        runner, _ = self.engine()
        p = runner.packet("A2", "APPLY", ["ask"])
        schema = self.contracts.schema("APPLY", {"T"}, self.packets.agents, ["ask"], ranking_items=NAMES)
        prompt = self.prompts.render("APPLY", p, schema)
        self.assertIn("ordered array", prompt)
        self.assertNotIn("full requested Python function(s)", prompt)

    def test_single_pass_template_does_not_expand_material_text(self):
        packet = self.packets.member("A1")
        packet["SELF_MATERIALS"][0]["content"] = "Literal {{task}} marker"
        schema = self.contracts.schema("CONTRIBUTE", {"T"}, self.packets.agents, [])
        self.assertIn("Literal {{task}} marker", self.prompts.render("CONTRIBUTE", packet, schema))

    def test_normal_path_five_calls(self):
        runner, script = self.engine(self.first_three() + [application(), review()])
        result = runner.run("coreta")
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(result["http_attempts"], 5)
        self.assertFalse(result["externally_scored"])
        self.assertEqual([x["context"]["stage"] for x in script.seen], ["CONTRIBUTE"] * 3 + ["APPLY", "REVIEW"])
        self.assertFalse(script.outputs)

    def test_ask_reply_apply_path(self):
        runner, script = self.engine(self.first_three() + [application(None, request=request()),
            contribution("Scripted help"), application(refs=("C4",)), review()])
        result = runner.run("coreta")
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(result["interventions"], 1)
        self.assertEqual(result["http_attempts"], 7)
        self.assertFalse(script.outputs)

    def test_check_and_probe_are_supported(self):
        for kind in ("check", "probe"):
            with self.subTest(kind=kind):
                runner, script = self.engine(self.first_three() + [application(None, request=request(kind)),
                    contribution("Scripted discriminating check"), application(refs=("C4",)), review()], folder=kind)
                self.assertEqual(runner.run("coreta")["interventions"], 1)
                self.assertFalse(script.outputs)

    def test_empty_reply_is_legal_and_handled_via_q(self):
        runner, _ = self.engine(self.first_three() + [application(None, request=request()),
            {"items": [], "note": "No relevant material is accessible"},
            application(refs=("Q1",)), review()])
        result = runner.run("coreta")
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(result["format_repairs"], 0)

    def test_empty_items_need_inability_note(self):
        runner, _ = self.engine([{"items": [], "note": ""}, contribution()] + self.first_three()[1:] + [application(), review()])
        result = runner.run("coreta")
        self.assertEqual(result["format_repairs"], 1)

    def test_reply_must_be_addressed(self):
        runner, _ = self.engine(self.first_three() + [application(None, request=request()), contribution(),
            application(), application(refs=("C4",)), review()])
        result = runner.run("coreta")
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(result["format_repairs"], 1)

    def test_review_must_be_addressed(self):
        runner, _ = self.engine(self.first_three() + [application(), review("issue"),
            application(), application(refs=("V1",)), review(target="W2")])
        result = runner.run("coreta")
        self.assertEqual(result["format_repairs"], 1)
        self.assertEqual(result["work_ref"], "W2")

    def test_null_artifact_keeps_previous_complete_candidate(self):
        runner, _ = self.engine(self.first_three() + [application(request=request()), contribution(),
            application(None, refs=("C4",)), review()])
        result = runner.run("coreta")
        self.assertEqual(result["artifact"], ARTIFACT)
        self.assertEqual(result["work_ref"], "W1")

    def test_no_artifact_no_request_stops_without_review(self):
        runner, script = self.engine(self.first_three() + [application(None)])
        result = runner.run("coreta")
        self.assertEqual(result["stop_reason"], "artifact_missing")
        self.assertEqual(result["status"], "protocol_failure")
        self.assertIsNone(result["artifact"])
        self.assertEqual(len(script.seen), 4)

    def test_unresolved_survives_no_defect_verdict(self):
        runner, _ = self.engine(self.first_three() + [application(unresolved=("Missing applicable scope",)), review()])
        self.assertEqual(runner.run("coreta")["status"], "best_effort_unresolved")

    def test_undetermined_stops_without_evidence(self):
        runner, _ = self.engine(self.first_three() + [application(), review("undetermined")])
        self.assertEqual(runner.run("coreta")["status"], "best_effort_unresolved")

    def test_last_review_does_not_certify_new_version(self):
        runner, _ = self.engine(self.first_three() + [application(), review("issue"),
            application(refs=("V1",)), review("issue", "W2"), application(refs=("V2",))])
        result = runner.run("coreta")
        self.assertEqual(result["work_ref"], "W3")
        self.assertEqual(result["status"], "best_effort_unreviewed")
        self.assertFalse(result["latest_review_applies_to_current_work"])

    def test_immutable_earlier_work_and_contribution(self):
        runner, _ = self.engine(self.first_three() + [application(), review("issue"),
            application(ARTIFACT + "\n", refs=("V1",)), review(target="W2")])
        runner.run("coreta")
        self.assertEqual(runner.works[0]["artifact"], ARTIFACT)
        self.assertEqual(runner.contributions[0]["content"], "Scripted item 0")

    def test_request_deduplication_is_bounded(self):
        req = request()
        runner, _ = self.engine(self.first_three() + [application(request=req), contribution(),
            application(refs=("C4",), request=req), review(target="W2")])
        result = runner.run("coreta")
        self.assertEqual(result["interventions"], 1)
        self.assertEqual(result["status"], "best_effort_unresolved")

    def test_three_intervention_cap(self):
        outputs = self.first_three() + [application(None, request=request(question="q1"))]
        for index in range(3):
            outputs.append(contribution())
            outputs.append(application(refs=(f"C{index+4}",), request=request(question=f"q{index+2}") if index < 2 else None))
        outputs.append(review(target="W3"))
        runner, script = self.engine(outputs)
        result = runner.run("coreta")
        self.assertEqual(result["interventions"], 3)
        self.assertFalse(script.outputs)
        self.assertEqual(runner.allowed(), [])

    def test_route_null_uses_target_author(self):
        runner, _ = self.engine(self.first_three())
        for agent in runner.agents:
            runner.contribute(agent)
        self.assertEqual(runner.route(request(recipient=None, targets=("C3",)))[0], "A3")

    def test_reviewer_prefers_source_owner(self):
        source = self.packets.member("A3")["SELF_MATERIALS"][0]["ref"]
        runner, _ = self.engine([contribution(refs=(source,))])
        runner.contribute("A3")
        runner.gateway.client.transport = Script(runner.journal, [application(refs=("C1",)), review()])
        runner.apply()
        self.assertEqual(runner.review()["author"], "A3")

    def test_single_format_recovery(self):
        runner, _ = self.engine(["not-json"] + self.first_three() + [application(), review()])
        result = runner.run("coreta")
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(result["http_attempts"], 6)
        self.assertEqual(result["format_repairs"], 1)

    def test_second_bad_format_stops(self):
        runner, script = self.engine(["bad", "still bad"])
        result = runner.run("coreta")
        self.assertEqual(result["status"], "protocol_failure")
        self.assertEqual(len(script.seen), 2)

    def test_transport_retry_counts_toward_attempt_cap(self):
        runner, _ = self.engine([urllib.error.URLError("fixture transient")] + self.first_three() + [application(), review()])
        result = runner.run("coreta")
        self.assertEqual(result["http_attempts"], 6)
        self.assertEqual(result["logical_calls"], 5)
        self.assertEqual(result["uncertain_usage_attempts"], 1)
        self.assertFalse(result["usage_complete"])

    def test_total_cap_one_never_dispatches_two_attempts(self):
        runner, script = self.engine([urllib.error.URLError("fixture")], cap=1)
        result = runner.run("coreta")
        self.assertEqual(result["http_attempts"], 1)
        self.assertEqual(len(script.seen), 1)

    def test_format_recovery_cannot_exceed_attempt_cap(self):
        runner, script = self.engine(["bad"], cap=1)
        result = runner.run("coreta")
        self.assertEqual(result["status"], "budget_exhausted")
        self.assertEqual(result["http_attempts"], 1)
        self.assertEqual(len(script.seen), 1)

    def test_budget_failure_retains_complete_candidate(self):
        runner, _ = self.engine(self.first_three() + [application()], cap=4)
        result = runner.run("coreta")
        self.assertEqual(result["status"], "budget_exhausted")
        self.assertEqual(result["artifact"], ARTIFACT)
        self.assertEqual(result["http_attempts"], 4)

    def test_task_timeout_before_network(self):
        runner, script = self.engine()
        runner.gateway.deadline = time.monotonic() - 1
        result = runner.run("coreta")
        self.assertEqual(result["stop_reason"], "MODEL_TIMEOUT")
        self.assertEqual(len(script.seen), 0)

    def test_context_overflow_before_dispatch(self):
        runner, script = self.engine()
        runner.gateway.config["generation"]["max_input_tokens"] = 1
        result = runner.run("coreta")
        self.assertEqual(result["stop_reason"], "CONTEXT_OVERFLOW")
        self.assertEqual(result["http_attempts"], 0)
        self.assertEqual(len(script.seen), 0)

    def test_timeout_passed_to_transport_is_bounded(self):
        runner, script = self.engine(self.first_three() + [application(), review()])
        runner.run("coreta")
        self.assertTrue(all(0 < call["timeout"] <= 120 for call in script.seen))

    def test_independent_three_calls_no_other_initial_answers(self):
        runner, script = self.engine([answer(f"UNIQUE_FULL_ANSWER_{i}") for i in range(3)])
        result = runner.run("independent")
        self.assertEqual(result["status"], "independent_collected")
        self.assertEqual(result["http_attempts"], 3)
        self.assertIsNone(result["artifact"])
        for call in script.seen:
            self.assertNotIn("UNIQUE_FULL_ANSWER", call["payload"]["instructions"])

    def test_ordinary_ten_calls_and_initial_visibility(self):
        outputs = [answer(f"FULL_INITIAL_{i}") for i in range(3)]
        outputs += [{"text": "Scripted discussion"}] * 6 + [answer()]
        runner, script = self.engine(outputs)
        result = runner.run("ordinary_discussion")
        self.assertEqual(result["http_attempts"], 10)
        self.assertEqual(result["artifact"], ARTIFACT)
        self.assertEqual(result["status"], "best_effort_unreviewed")
        for i in range(3):
            self.assertIn(f"FULL_INITIAL_{i}", script.seen[3]["payload"]["instructions"])
        self.assertFalse(script.outputs)

    def test_ordinary_failure_preserves_driver_initial_without_oracle(self):
        runner, _ = self.engine([answer(f"initial{i}") for i in range(3)] + [urllib.error.HTTPError(
            "https://fixture.invalid", 401, "fixture", {}, None)])
        result = runner.run("ordinary_discussion")
        self.assertEqual(result["status"], "protocol_failure")
        self.assertEqual(result["artifact"], ARTIFACT)
        self.assertEqual(runner.works[0]["explanation"], "initial1")

    def test_score_perfect_reverse_and_adjacent_swap(self):
        reference = {name: index for index, name in enumerate(NAMES, 1)}
        self.assertEqual(score_artifact(ARTIFACT, reference)["L1_error"], 0)
        reverse = "MY RANKING:\n" + "\n".join(f"{i}. {name}" for i, name in enumerate(reversed(NAMES), 1))
        self.assertEqual(score_artifact(reverse, reference)["L1_error"], 112)
        swapped = list(NAMES)
        swapped[:2] = swapped[1::-1]
        artifact = "MY RANKING:\n" + "\n".join(f"{i}. {name}" for i, name in enumerate(swapped, 1))
        self.assertEqual(score_artifact(artifact, reference)["L1_error"], 2)

    def test_invalid_rankings_are_delivery_failures(self):
        malformed = [None, "", "MY RANKING:\n1. nope", ARTIFACT + "\nMY RANKING:",
                     ARTIFACT.replace("2. ", "1. ", 1), ARTIFACT.replace(NAMES[1], NAMES[0]),
                     ARTIFACT.replace("1. ", "16. ", 1), ARTIFACT + "\nextra sentence",
                     ARTIFACT.replace("1. ", "1) ", 1)]
        reference = {name: index for index, name in enumerate(NAMES, 1)}
        for artifact in malformed:
            with self.subTest(artifact=repr(artifact)[:60]):
                score = score_artifact(artifact, reference)
                self.assertTrue(score["delivery_failure"])
                self.assertEqual(score["L1_error"], 112)

    def test_missing_independent_data_is_unknown_not_all_wrong(self):
        runner, _ = self.engine(self.first_three() + [application(), review()])
        result = runner.run("coreta")
        scored = score_run(PACK, result)
        self.assertIsNone(scored["initial_all_wrong_recovery"])
        self.assertEqual(scored["independent_missing_members"], ["A1", "A2", "A3"])

    def test_cli_help_prepare_and_refuse_live_without_flag(self):
        base = [sys.executable, "-m", "coreta.handoff"]
        result = subprocess.run(base + ["--help"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        out = self.directory / "prepared"
        result = subprocess.run(base + ["prepare", "--output", str(out)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((out / "result.json").exists())
        self.assertEqual(read_json(out / "PREPARATION_ONLY.json")["network_requests"], 0)
        refused = self.directory / "refused"
        result = subprocess.run(base + ["run", "--output", str(refused)], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(refused.exists())

    def test_cli_score_fixture_does_not_rewrite_result(self):
        runner, _ = self.engine(self.first_three() + [application(), review()])
        runner.run("coreta")
        before = (runner.journal.root / "result.json").read_bytes()
        output = self.directory / "fixture_score.json"
        completed = subprocess.run([sys.executable, "-m", "coreta.handoff", "score",
            "--run", str(runner.journal.root), "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(read_json(output)["feedback_sent_to_model"])
        self.assertEqual(before, (runner.journal.root / "result.json").read_bytes())

    def test_malformed_input_identifiers_fail_as_input_errors(self):
        cases = ("directory_item_id", "private_ref", "reference_index_ref")
        for case in cases:
            with self.subTest(case=case):
                root = self.directory / case
                folder = root / "packets/distributed_r0"
                folder.mkdir(parents=True)
                for agent in self.packets.agents:
                    packet = self.packets.member(agent)
                    if case == "directory_item_id":
                        packet["DIRECTORY"][0]["accessible_materials"][0]["item_id"] = []
                    elif agent == "A1" and case == "private_ref":
                        packet["SELF_MATERIALS"][0]["ref"] = []
                    elif agent == "A1" and case == "reference_index_ref":
                        packet["REFERENCE_INDEX"][0]["ref"] = []
                    (folder / f"{agent}.json").write_text(json.dumps(packet), encoding="utf-8")
                with self.assertRaises(ProtocolError):
                    Packets(root, "distributed_r0")

    def test_independent_and_contribute_never_see_previous_member_note(self):
        outputs = [contribution() for _ in range(3)] + [application(), review()]
        outputs[0]["note"] = "UNSHARED_INITIAL_NOTE_SENTINEL"
        runner, script = self.engine(outputs)
        runner.run("coreta")
        for call in script.seen[1:3]:
            self.assertNotIn("UNSHARED_INITIAL_NOTE_SENTINEL", call["payload"]["instructions"])
        self.assertIn("UNSHARED_INITIAL_NOTE_SENTINEL", script.seen[3]["payload"]["instructions"])

    def test_all_six_conditions_complete_scripted_normal_path(self):
        for folder in (PACK / "packets").iterdir():
            with self.subTest(condition=folder.name):
                packets = Packets(PACK, folder.name)
                runner, script = self.engine(self.first_three() + [application(), review()], packets=packets, folder=folder.name)
                self.assertEqual(runner.run("coreta")["http_attempts"], 5)
                self.assertFalse(script.outputs)

    def test_undetermined_with_suggestion_can_continue(self):
        runner, _ = self.engine(self.first_three() + [application(), review("undetermined", suggestion="Check scope"),
            application(refs=("V1",), request=request()), contribution(),
            application(refs=("C4",)), review(target="W3")])
        result = runner.run("coreta")
        self.assertEqual(result["status"], "reviewed_no_defect")
        self.assertEqual(result["interventions"], 1)

    def test_private_support_cannot_be_cited_directly_by_driver(self):
        foreign = self.packets.member("A1")["SELF_MATERIALS"][0]["ref"]
        bad = application(refs=(foreign,))
        runner, _ = self.engine([contribution(refs=(foreign,)), contribution(), contribution(),
            bad, application(refs=("C1",)), review()])
        result = runner.run("coreta")
        self.assertEqual(result["format_repairs"], 1)
        self.assertEqual(result["status"], "reviewed_no_defect")

    def test_failed_apply_does_not_destroy_previous_candidate(self):
        runner, _ = self.engine(self.first_three() + [application(), review("issue"), "bad", "bad"])
        result = runner.run("coreta")
        self.assertEqual(result["status"], "protocol_failure")
        self.assertEqual(result["artifact"], ARTIFACT)
        self.assertEqual(result["work_ref"], "W1")

    def test_combined_transport_and_format_retries_share_one_cap(self):
        runner, script = self.engine([urllib.error.URLError("fixture"), "bad", "bad"], cap=3)
        result = runner.run("coreta")
        self.assertEqual(result["http_attempts"], 3)
        self.assertEqual(len(script.seen), 3)
        self.assertEqual(result["format_repairs"], 1)
        self.assertEqual(result["status"], "protocol_failure")

    def test_live_guard_missing_key_creates_no_directory(self):
        import os
        env = dict(os.environ)
        env.pop("DEEPSEEK_API_KEY", None)
        output = self.directory / "no_key"
        completed = subprocess.run([sys.executable, "-m", "coreta.handoff", "run", "--live", "--output", str(output)],
                                   cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not configured", completed.stderr)
        self.assertFalse(output.exists())

    def test_ordinary_privacy_all_rounds(self):
        def change(agent, packet):
            for index, material in enumerate(packet["SELF_MATERIALS"]):
                material["content"] = f"RAW_PRIVATE_{agent}_{index}_SENTINEL"
        packets = Packets(self.copy_packets(change), "distributed_r0")
        outputs = [answer()] * 3 + [{"text": "Scripted public turn"}] * 6 + [answer()]
        runner, script = self.engine(outputs, packets=packets)
        runner.run("ordinary_discussion")
        for call in script.seen:
            agent = call["context"]["member"]
            prompt = call["payload"]["instructions"]
            for other in packets.agents:
                if other != agent:
                    self.assertNotIn(f"RAW_PRIVATE_{other}_0_SENTINEL", prompt)

    def test_review_does_not_include_unused_private_raw_text(self):
        def change(agent, packet):
            for index, material in enumerate(packet["SELF_MATERIALS"]):
                material["content"] = f"RAW_PRIVATE_{agent}_{index}_SENTINEL"
        packets = Packets(self.copy_packets(change), "distributed_r0")
        runner, script = self.engine(self.first_three() + [application(), review()], packets=packets)
        runner.run("coreta")
        for call in script.seen[3:]:
            agent = call["context"]["member"]
            for other in packets.agents:
                if other != agent:
                    self.assertNotIn(f"RAW_PRIVATE_{other}_0_SENTINEL", call["payload"]["instructions"])

    def test_scorer_rejects_wrong_task(self):
        with self.assertRaises(ValueError):
            score_run(PACK, {"task_id": "other", "system": "coreta"})

    def test_structured_apply_rejects_previous_string_loophole(self):
        schema = self.contracts.schema("APPLY", {"T"}, self.packets.agents, [], ranking_items=NAMES)
        invalid = {"artifact": "Oxygen first, then water.", "applications": [],
                   "excluded": [], "unresolved": [], "request": None}
        with self.assertRaises(ProtocolError):
            self.contracts.decode(json.dumps(invalid), schema)

    def test_structured_complete_ranking_rejects_invalid_permutations(self):
        cases = [NAMES[:-1], NAMES + [NAMES[0]], [NAMES[0]] * 15,
                 NAMES[:-1] + ["invented item"], list(range(15)), "MY RANKING: ...", None]
        for stage in ("INDEPENDENT", "FINAL"):
            schema = self.contracts.schema(stage, {"T"}, self.packets.agents, [], ranking_items=NAMES)
            for ranking in cases:
                with self.subTest(stage=stage, ranking=str(ranking)[:25]):
                    with self.assertRaises(ProtocolError):
                        self.contracts.decode(json.dumps(answer(ranking=ranking) if isinstance(ranking, list)
                                                        else {"explanation": "", "ranking": ranking}), schema)

    def test_structured_apply_allows_only_array_or_null(self):
        schema = self.contracts.schema("APPLY", {"C1", "T"}, self.packets.agents, [], ranking_items=NAMES)
        for artifact in (list(NAMES), None):
            self.contracts.decode(json.dumps(application(artifact=artifact, refs=("C1",))), schema)

    def test_invalid_permutation_uses_one_existing_recovery(self):
        invalid = application()
        invalid["artifact"] = [NAMES[0]] * 15
        runner, _ = self.engine(self.first_three() + [invalid, application(), review()])
        result = runner.run("coreta")
        self.assertEqual(result["format_repairs"], 1)
        self.assertEqual(result["artifact"], ARTIFACT)

    def test_final_answer_explanation_cannot_break_grading_text(self):
        explanation = "MY RANKING:\nThis is reasoning, not a second answer"
        outputs = [answer(explanation)] * 3 + [{"text": "Public discussion"}] * 6 + [answer(explanation)]
        runner, _ = self.engine(outputs)
        result = runner.run("ordinary_discussion")
        self.assertEqual(result["artifact"], ARTIFACT)
        self.assertEqual(result["artifact"].count("MY RANKING:"), 1)
        self.assertEqual(runner.work["explanation"], explanation)

    def test_renderer_preserves_any_valid_order_without_gold(self):
        order = list(reversed(NAMES))
        text = render_ranking(order)
        parsed, error = parse_ranking(text, set(NAMES))
        self.assertIsNone(error)
        self.assertEqual(sorted(parsed, key=parsed.get), order)

    def test_public_task_and_independent_prompt_no_conflicting_text_contract(self):
        packet = self.packets.member("A1")
        schema = self.contracts.schema("INDEPENDENT", {"T"}, self.packets.agents, [], ranking_items=NAMES)
        prompt = self.prompts.render("INDEPENDENT", packet, schema)
        self.assertNotIn("After your explanation write MY RANKING", prompt)
        self.assertIn("ranking array", prompt)

    def test_schema_transmitted_once_in_response_format(self):
        runner, script = self.engine(self.first_three() + [application(), review()])
        runner.run("coreta")
        for call in script.seen:
            schema = call["payload"]["text"]["format"]["schema"]
            self.assertNotIn(json.dumps(schema, ensure_ascii=False), call["payload"]["instructions"])

    def test_current_work_no_duplicate_rank_text_or_application_copy(self):
        runner, _ = self.engine(self.first_three() + [application()])
        for agent in runner.agents:
            runner.contribute(agent)
        runner.apply()
        packet = runner.packet("A1", "REVIEW")
        self.assertIn("ranking", packet["CURRENT_WORK"])
        self.assertNotIn("artifact", packet["CURRENT_WORK"])
        self.assertNotIn("applications", packet["CURRENT_WORK"])
        self.assertEqual(packet["CURRENT_WORK"]["application_history"], runner.work["application_history"])

    def test_answer_schema_without_public_items_fails_closed(self):
        for stage in ("APPLY", "INDEPENDENT", "FINAL"):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    self.contracts.schema(stage, {"T"}, self.packets.agents, [])

    def test_default_local_counter_is_available_and_not_byte_count(self):
        counter = load_counter()
        self.assertTrue(DEFAULT_TOKENIZER.is_file())
        text = "reason " * 350
        self.assertLess(counter(text), len(text.encode("utf-8")))
        self.assertEqual(counter(text), counter(text))

    def test_missing_tokenizer_does_not_silently_fall_back(self):
        with self.assertRaises(Exception):
            load_counter(self.directory / "missing-tokenizer.json")


if __name__ == "__main__":
    unittest.main(verbosity=2)
