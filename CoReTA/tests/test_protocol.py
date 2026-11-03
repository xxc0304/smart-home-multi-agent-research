"""Deterministic E0 tests. Responses are fixtures, not model or capability evidence."""
import copy
import json
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path

from coreta.model_client import DeepSeekClient
from coreta.prompts import Prompts
from coreta.protocol import Runner, SYSTEM_CAPS
from coreta.schemas import Contracts, ProtocolError, check_update
from coreta.state import State, reference_index

ROOT = Path(__file__).resolve().parents[1]
TASK = {"task_id": "fixture-math", "task_type": "math", "prompt": "Compute 1+1.", "entry_point": None}


def candidate(step="s1"):
    return {"artifact": r"\boxed{2}", "summary": "Add one and one.", "steps": [
        {"id": step, "text": "1+1=2", "basis_refs": [], "status": "candidate"}], "open_issues": []}


def label(text, name):
    marker = name + " = "
    start = text.index(marker) + len(marker)
    return json.JSONDecoder().raw_decode(text[start:])[0]


class ScriptedModel:
    def __init__(self, actions=None, cannot_help=False, corrupt=0):
        self.actions = list(actions or ["REQUEST_HELP", "REQUEST_ALTERNATIVE", "FINISH"])
        self.cannot_help, self.corrupt = cannot_help, corrupt
        self.payloads = []
        self.updates = 0

    def __call__(self, payload, timeout):
        self.payloads.append(copy.deepcopy(payload))
        text = payload["instructions"]
        props = payload["text"]["format"]["schema"]["properties"]
        if self.corrupt:
            self.corrupt -= 1
            output = "not JSON"
        elif "steps" in props:
            output = candidate()
        elif "verdict" in props:
            output = {"subject_id": label(text, "SUBJECT_ID"), "verdict": "supported", "findings": [], "scope_limit": "Fixture only"}
        elif "body" in props:
            output = {"request_id": label(text, "REQUEST_ID"), "status": "cannot_help" if self.cannot_help else "provided",
                      "body": "fixture contribution", "basis_refs": [], "check_suggestion": "Check addition"}
        elif "next" in props:
            evidence = label(text, "NEW_EVIDENCE")
            no_app = props["application"] == {"type": "null"}
            application = None
            if evidence and not no_app:
                application = {"request_id": None, "contribution_id": None, "review_id": None,
                               "disposition": "accepted", "before_refs": [], "changed_step_ids": [],
                               "application_outcome": "unknown", "reason": "Fixture inspection"}
                for event in evidence:
                    data = event["payload"]
                    key = "review_id" if "verdict" in data else "contribution_id" if "body" in data else "request_id"
                    application[key] = event["event_id"]
            action = self.actions[min(self.updates, len(self.actions) - 1)]
            self.updates += 1
            kind = {"REQUEST_HELP": "complete", "REQUEST_ALTERNATIVE": "alternative", "REQUEST_CHECK": "verify"}
            request = None if action not in kind else {"kind": kind[action], "goal": "TARGETED_SECRET_FIXTURE",
                "target_step_ids": ["s1"], "current_attempt": "1+1", "deliverable": "a calculation",
                "check_plan": "substitution", "reason_for_recipient": "visible draft"}
            output = {"candidate": candidate(), "application": application,
                      "next": {"action": action, "recipient": "A1" if request else None, "request": request, "reason": "fixture"}}
        else:
            output = {"artifact": r"\boxed{2}", "basis_refs": []}
        return {"status": "completed", "model": "fixture-not-deepseek", "usage": {"input_tokens": 1, "output_tokens": 1},
                "output": [{"type": "message", "content": [{"type": "output_text", "text": output if isinstance(output, str) else json.dumps(output)}]}]}


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.contracts = Contracts(ROOT / "design/v0.3/coreta.schema.json")
        self.prompts = Prompts(ROOT / "design/v0.3/PROMPTS.md")
        self.config = json.loads((ROOT / "config/deepseek_flash.json").read_text())

    def runner(self, system="coreta", model=None, config=None, bank=None, folder="run"):
        directory = self.directory / folder
        directory.mkdir()
        state = State(copy.deepcopy(TASK), folder, directory, self.contracts)
        client = DeepSeekClient(config or self.config, state.log, transport=model or ScriptedModel(),
                                token_counter=lambda text: len(text.encode()) // 4)
        return Runner(state, client, self.prompts, config or self.config, system=system, draft_bank=bank)

    def test_all_seven_conditions_and_call_caps(self):
        for system, cap in SYSTEM_CAPS.items():
            with self.subTest(system=system):
                runner = self.runner(system, folder=system)
                result = runner.run()
                self.assertEqual(result["status"], "completed", result["errors"])
                self.assertEqual(result["normal_calls"], cap)
                self.assertEqual(result["http_attempts"], cap)
                self.assertEqual(result["format_repairs"], 0)
                self.assertEqual(result["artifact"], r"\boxed{2}")
                if system in {"coreta", "generic_help", "no_application_record"}:
                    self.assertEqual(runner.state.version, 3)
                    reqs = [e for e in runner.state.events if e["kind"] == "request"]
                    self.assertEqual([r["base_version"] for r in reqs], [1, 2])

    def test_continue_and_early_finish(self):
        for actions, calls in [(["FINISH"], 6), (["CONTINUE_SELF", "CONTINUE_SELF", "FINISH"], 8)]:
            runner = self.runner(model=ScriptedModel(actions), folder=str(calls))
            self.assertEqual(runner.run()["normal_calls"], calls)
            self.assertFalse([e for e in runner.state.events if e["kind"] == "request"])

    def test_check_path(self):
        runner = self.runner(model=ScriptedModel(["REQUEST_CHECK", "FINISH"]))
        result = runner.run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["normal_calls"], 8)
        self.assertFalse([e for e in runner.state.events if e["kind"] == "contribution"])

    def test_cannot_help_skips_peer_check(self):
        runner = self.runner(model=ScriptedModel(cannot_help=True))
        result = runner.run()
        self.assertEqual(result["normal_calls"], 10)
        self.assertEqual(len([e for e in runner.state.events if e["kind"] == "review"]), 1)

    def test_generic_targeted_fields_do_not_leak(self):
        model = ScriptedModel()
        runner = self.runner("generic_help", model)
        self.assertEqual(runner.run()["status"], "completed")
        for payload in model.payloads:
            self.assertNotIn("TARGETED_SECRET_FIXTURE", payload["instructions"])
        for event in runner.state.events:
            if event["kind"] == "request":
                self.assertEqual(event["payload"]["target_step_ids"], [])

    def test_no_application_history_or_schema_leaks(self):
        model = ScriptedModel()
        runner = self.runner("no_application_record", model)
        self.assertEqual(runner.run()["status"], "completed")
        self.assertEqual(runner.state.applications, [])
        for payload in model.payloads:
            self.assertNotIn("APPLICATION_HISTORY", payload["instructions"])
            self.assertNotIn('"application_outcome"', payload["instructions"])
            props = payload["text"]["format"]["schema"]["properties"]
            if "next" in props:
                self.assertEqual(props["application"], {"type": "null"})

    def test_static_round_is_synchronous(self):
        model = ScriptedModel()
        runner = self.runner("static_debate", model)
        runner.run()
        rounds = model.payloads[3:9]
        for group in (rounds[:3], rounds[3:]):
            material = [json.loads(p["instructions"].split("\n")[-1])["MATERIAL"] for p in group]
            self.assertEqual(material[0], material[1])
            self.assertEqual(material[1], material[2])

    def test_one_format_repair(self):
        runner = self.runner("single_finalized", ScriptedModel(corrupt=1))
        result = runner.run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["normal_calls"], 2)
        self.assertEqual(result["format_repairs"], 1)
        self.assertEqual(result["http_attempts"], 3)

    def test_unrepairable_initial_fails_without_answer(self):
        runner = self.runner(model=ScriptedModel(corrupt=99))
        result = runner.run()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["artifact"], "")
        self.assertEqual(result["format_repairs"], 1)

    def test_finalizer_failure_returns_last_valid_candidate(self):
        model = ScriptedModel()
        def transport(payload, timeout):
            if "Produce the best final answer" in payload["instructions"]:
                raise TimeoutError("fixture")
            return model(payload, timeout)
        runner = self.runner("single_finalized", transport)
        result = runner.run()
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["artifact"], result["prefinal_artifact"])
        self.assertEqual(result["http_attempts"], 4)

    def test_task_deadline_stops_before_transport(self):
        model = ScriptedModel()
        runner = self.runner(model=model)
        runner.deadline = time.monotonic() - 1
        self.assertEqual(runner.run()["status"], "failed")
        self.assertEqual(model.payloads, [])

    def test_context_overflow_stops_without_network(self):
        config = copy.deepcopy(self.config)
        config["generation"]["max_input_tokens"] = 1
        model = ScriptedModel()
        runner = self.runner(model=model, config=config)
        result = runner.run()
        self.assertEqual(result["errors"][0]["code"], "CONTEXT_OVERFLOW")
        self.assertEqual(model.payloads, [])

    def test_shared_draft_bank_reuses_physical_calls(self):
        bank = self.directory / "bank"
        first = self.runner("independent_aggregate", bank=bank, folder="first")
        second = self.runner("coreta", bank=bank, folder="second")
        self.assertEqual(first.run()["http_attempts"], 4)
        result = second.run()
        self.assertEqual(result["normal_calls"], 12)
        self.assertEqual(result["http_attempts"], 9)

    def test_schema_rejects_evaluator_fields(self):
        for field in ("answer", "gold", "solution", "test", "canonical_solution"):
            with self.subTest(field=field), self.assertRaises(ProtocolError):
                self.contracts.validate("PublicTask", {**TASK, field: "HIDDEN"})

    def test_duplicate_steps_are_rejected(self):
        value = candidate()
        value["steps"] *= 2
        with self.assertRaises(ProtocolError):
            self.contracts.validate("Candidate", value)

    def test_reference_index_does_not_follow_citations(self):
        self.assertEqual(reference_index({"basis_refs": ["secret"], "before_refs": ["v9:s1"]}), [])

    def test_invalid_update_is_not_committed(self):
        runner = self.runner()
        draft = runner.draft("A0")
        value = {"candidate": candidate(), "application": None,
                 "next": {"action": "REQUEST_HELP", "recipient": "A0", "request": None, "reason": "bad"}}
        with self.assertRaises(ProtocolError):
            check_update(value, set(), ["REQUEST_HELP"], [], False)
        self.assertEqual(runner.state.version, 0)
        self.assertEqual(runner.state.current["source_event_id"], draft["event_id"])

    def test_http_400_not_retried_429_retried(self):
        for status, expected in [(400, 1), (401, 1), (429, 3), (500, 3)]:
            runner = self.runner(folder=str(status))
            def transport(payload, timeout):
                raise urllib.error.HTTPError("fixture", status, "fixture", {}, None)
            runner.client.transport = transport
            result = runner.run()
            self.assertEqual(result["http_attempts"], expected)

    def test_two_repairs_per_task_not_unbounded(self):
        model = ScriptedModel()
        failed_actors = 0
        on_repair = False
        def transport(payload, timeout):
            nonlocal failed_actors, on_repair
            props = payload["text"]["format"]["schema"]["properties"]
            if "steps" in props and not on_repair:
                failed_actors += 1
                on_repair = True
                return {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "bad"}]}]}
            on_repair = False
            return model(payload, timeout)
        runner = self.runner(model=transport)
        result = runner.run()
        self.assertEqual(result["format_repairs"], 2)
        self.assertEqual(failed_actors, 3)
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["artifact"], r"\boxed{2}")

    def test_new_candidate_targets_validated_against_output(self):
        value = {"candidate": candidate("s2"), "application": None,
                 "next": {"action": "REQUEST_HELP", "recipient": "A1", "request": {
                     "kind": "complete", "goal": "g", "target_step_ids": ["s2"], "current_attempt": "a",
                     "deliverable": "d", "check_plan": "c", "reason_for_recipient": "r"}, "reason": "r"}}
        check_update(value, set(), ["REQUEST_HELP"], [], False)
        value["next"]["request"]["target_step_ids"] = ["s1"]
        with self.assertRaises(ProtocolError):
            check_update(value, set(), ["REQUEST_HELP"], [], False)

    def test_bootstrap_does_not_read_A1(self):
        model = ScriptedModel(["FINISH"])
        runner = self.runner(model=model)
        runner.run()
        text = model.payloads[3]["instructions"]
        self.assertNotIn(runner.state.drafts["A1"]["event_id"], text)
        self.assertIn(runner.state.drafts["A2"]["event_id"], text)

    def test_stale_request_is_rejected_before_model_call(self):
        runner = self.runner()
        draft = runner.draft("A0")
        with self.assertRaises(ProtocolError) as caught:
            runner.review("A0", draft, {"base_version": 99})
        self.assertEqual(caught.exception.code, "STALE_VERSION")

    def test_malformed_transport_response_is_not_an_implementation_crash(self):
        def transport(payload, timeout):
            raise json.JSONDecodeError("fixture", "", 0)
        result = self.runner(model=transport).run()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["http_attempts"], 3)

    def test_normal_cap_reserves_finalizer(self):
        runner = self.runner("single_finalized")
        runner.draft("A0")
        with self.assertRaises(ProtocolError) as caught:
            runner.draft("A1")
        self.assertEqual(caught.exception.code, "CALL_LIMIT")


if __name__ == "__main__":
    unittest.main()
