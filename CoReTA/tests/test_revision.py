"""Offline protocol checks using scripted outputs, never capability evidence."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from coreta.model_client import DeepSeekClient
from coreta.revision import RevisionContracts, RevisionRunner
from coreta.schemas import ProtocolError


ROOT = Path(__file__).resolve().parents[1]
TASK = {"task_id": "revision-fixture", "task_type": "math", "prompt": "Compute 1+1.", "entry_point": None}


def candidate():
    return {"artifact": r"\boxed{2}", "summary": "Add.", "steps": [
        {"id": "s1", "text": "1+1=2", "basis_refs": [], "status": "candidate"}], "open_issues": []}


def decision(action="FINISH_COMPLETE", ids=None, marker="first"):
    return {"action": action, "recipient": "none" if action.startswith("FINISH") else
            "A0" if action == "CONTINUE_SELF" else "A1", "goal": marker,
            "deliverable": "Compute the missing addition", "check_plan": "Recompute independently",
            "issue_ids": ids or [], "reason": "Fixture decision"}


def update(action="FINISH_COMPLETE"):
    return {"candidate": candidate(), "resolutions": [], "issues": [],
            "application": "Fixture application", "next": decision(action)}


class Script:
    def __init__(self, actions=None, issue=False, cannot=False, corrupt_stage=None):
        self.actions = list(actions or ["FINISH_COMPLETE"])
        self.issue, self.cannot, self.corrupt_stage = issue, cannot, corrupt_stage
        self.updates, self.corruptions = 0, 0
        self.seen = []

    def __call__(self, payload, timeout):
        instructions = payload["instructions"]
        start = instructions.index('\n{"ACTOR"') + 1
        context = json.JSONDecoder().raw_decode(instructions[start:])[0]
        material = context["MATERIAL"]
        props = payload["text"]["format"]["schema"]["properties"]
        if "steps" in props:
            stage, value = "refine_draft" if "previous_candidates" in material else "draft", candidate()
        elif "next" in props:
            stage = "apply"
            action = self.actions[min(self.updates, len(self.actions) - 1)]
            value = update(action)
            ids = [i["issue_id"] for i in material["issues"]]
            value["next"] = decision(action, ids, f"work-{self.updates}")
            self.updates += 1
        elif "candidate" in props:
            stage, value = "synthesize", {"candidate": candidate(), "issues": []}
            if self.issue:
                value["issues"] = [{"description": "Missing justified addition", "blocking": True, "existing_issue_id": None,
                                    "target_refs": [context["REFERENCE_INDEX"][0]]}]
        elif "checks" in props:
            stage = "inspect"
            value = {"checks": [{"target_refs": [context["REFERENCE_INDEX"][0]], "method": "manual addition",
                                 "observation": "One plus one equals two", "conclusion": "supported",
                                 "scope": "Only this calculation"}], "issues": []}
        elif "body" in props:
            stage = "work" if "request" in material else "build"
            value = {"status": "cannot_help" if self.cannot else "provided",
                     "body": "Recomputed 1+1=2; use at s1 under integer addition", "basis_refs": [],
                     "attempted_issue_ids": [i["issue_id"] for i in material["issues"]], "issues": []}
        else:
            stage, value = "final", {"artifact": r"\boxed{2}", "basis_refs": []}
        self.seen.append((stage, context["ACTOR"], copy.deepcopy(material)))
        if stage == self.corrupt_stage and not self.corruptions:
            self.corruptions += 1
            raw = "not json"
        else:
            raw = json.dumps(value)
        return {"status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": raw}]}], "usage": {"input_tokens": 1, "output_tokens": 1}}


class RevisionChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.contracts = RevisionContracts(ROOT / "design/v0.3/coreta.schema.json")
        self.config = json.loads((ROOT / "config/deepseek_flash.json").read_text(encoding="utf-8"))
        self.config["generation"]["max_input_tokens"] = 1000000
        self.config["generation"]["max_output_tokens"].update(
            synthesize=3072, build=2048, inspect=2048, apply=4096, work=2048, refine_draft=2048)
        self.prompts = json.loads((ROOT / "design/revision_prompts.json").read_text(encoding="utf-8"))

    def runner(self, script=None, **kwargs):
        runner = RevisionRunner(TASK, self.directory, "fixture", self.contracts, None,
                                self.config, self.prompts, **kwargs)
        runner.client = DeepSeekClient(self.config, runner.log, transport=script or Script())
        return runner

    def issue(self, runner, status="open"):
        runner.issues["i0001"] = {"issue_id": "i0001", "blocking": True, "status": status,
                                  "description": "missing result", "handling_events": []}

    def test_all_stage_schemas_load(self):
        Draft202012Validator.check_schema(self.contracts.document)
        for name in ("Candidate", "Synthesis", "Constructive", "Inspection", "RevisionUpdate", "Event", "Final"):
            Draft202012Validator.check_schema(self.contracts.schema(name))

    def test_all_comparison_conditions_and_caps(self):
        for system, calls in (("independent_aggregate", 4), ("static_debate", 10), ("independent_refine", 10)):
            with self.subTest(system=system):
                result = self.runner(Script(), system=system).run()
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["normal_calls"], calls)
                self.assertEqual(result["system"], system)

    def test_shared_drafts_reuse_identical_payloads(self):
        bank = self.directory / "bank"
        first = self.runner(Script(), system="independent_aggregate", draft_bank=bank)
        first.run()
        second = self.runner(Script(), draft_bank=bank)
        result = second.run()
        self.assertEqual([e["payload"] for e in first.drafts], [e["payload"] for e in second.drafts])
        self.assertEqual(result["normal_calls"], 8)
        self.assertEqual(result["http_attempts"], 5)

    def test_independent_refine_never_sees_peer_trajectory(self):
        script = Script()
        self.runner(script, system="independent_refine").run()
        for stage, actor, material in script.seen:
            if stage == "refine_draft":
                self.assertEqual([e["sent_from"] for e in material["previous_candidates"]], [actor])
                self.assertNotIn("drafts", material)

    def test_static_round_uses_frozen_previous_outputs(self):
        script = Script()
        self.runner(script, system="static_debate").run()
        rounds = [row[2]["previous_candidates"] for row in script.seen if row[0] == "refine_draft"]
        self.assertEqual(rounds[0], rounds[1])
        self.assertEqual(rounds[1], rounds[2])
        self.assertEqual(rounds[3], rounds[4])

    def test_draft_cache_changes_with_prompt(self):
        bank = self.directory / "bank"
        self.runner(Script(), system="independent_aggregate", draft_bank=bank).run()
        self.prompts["draft"] += " Changed operation."
        result = self.runner(Script(), system="independent_aggregate", draft_bank=bank).run()
        self.assertEqual(result["http_attempts"], 4)
        self.assertEqual(len(list(bank.glob("*.json"))), 6)

    def test_fixed_constructive_flow_even_when_answers_agree(self):
        script = Script()
        result = self.runner(script).run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["stop_reason"], "complete")
        self.assertEqual(result["normal_calls"], 8)
        self.assertEqual([r[0] for r in script.seen],
                         ["draft"] * 3 + ["synthesize", "build", "inspect", "apply", "final"])
        self.assertTrue(all("drafts" not in r[2] for r in script.seen[:3]))

    def test_two_full_rounds_reserve_final_and_cap14(self):
        script = Script(["REQUEST_HELP", "REQUEST_ALTERNATIVE", "CONTINUE_SELF"])
        result = self.runner(script).run()
        self.assertEqual(result["normal_calls"], 14)
        self.assertEqual(result["stop_reason"], "budget_exhausted")
        self.assertEqual(script.seen[-1][0], "final")

    def test_cannot_help_does_not_close_issue(self):
        script = Script(["REQUEST_HELP", "FINISH_STALLED"], issue=True, cannot=True)
        result = self.runner(script).run()
        self.assertEqual(result["stop_reason"], "stalled")
        self.assertEqual(result["issues"]["i0001"]["status"], "open")
        self.assertEqual([s[0] for s in script.seen].count("inspect"), 1)

    def test_check_only_branch(self):
        script = Script(["REQUEST_CHECK", "FINISH_COMPLETE"])
        result = self.runner(script).run()
        self.assertEqual(result["normal_calls"], 10)
        self.assertNotIn("work", [s[0] for s in script.seen])

    def test_self_work_is_checked_by_peer(self):
        script = Script(["CONTINUE_SELF", "FINISH_COMPLETE"])
        result = self.runner(script).run()
        self.assertEqual(result["normal_calls"], 11)
        self.assertIn(("work", "A0"), [(s[0], s[1]) for s in script.seen])
        self.assertEqual([s[1] for s in script.seen if s[0] == "inspect"][-1], "A2")

    def test_open_blocker_prevents_complete_without_mutation(self):
        runner = self.runner()
        self.issue(runner)
        before = copy.deepcopy(runner.issues)
        with self.assertRaises(ProtocolError):
            runner.validate_update(update())
        self.assertEqual(before, runner.issues)

    def test_new_blocker_in_same_update_prevents_complete(self):
        value = update()
        value["issues"] = [{"description": "new missing bridge", "blocking": True, "target_refs": [], "existing_issue_id": None}]
        with self.assertRaises(ProtocolError):
            self.runner().validate_update(value)

    def test_stalled_requires_attempt_on_each_blocker(self):
        runner = self.runner()
        self.issue(runner)
        with self.assertRaises(ProtocolError):
            runner.validate_update(update("FINISH_STALLED"))
        runner.attempts.append({"issue_ids": ["i0001"], "fingerprint": "fixture"})
        runner.validate_update(update("FINISH_STALLED"))

    def test_close_requires_evidence_or_output_step(self):
        runner = self.runner()
        self.issue(runner)
        value = update()
        value["resolutions"] = [{"issue_id": "i0001", "status": "addressed", "reason": "Resolved",
                                  "evidence_refs": [], "changed_step_ids": []}]
        with self.assertRaises(ProtocolError):
            runner.validate_update(value)
        value["resolutions"][0]["changed_step_ids"] = ["s1"]
        runner.validate_update(value)

    def test_unknown_or_duplicate_resolution_rejected(self):
        runner = self.runner()
        self.issue(runner)
        value = update()
        row = {"issue_id": "unknown", "status": "addressed", "reason": "fixture",
               "evidence_refs": [], "changed_step_ids": ["s1"]}
        value["resolutions"] = [row]
        with self.assertRaises(ProtocolError):
            runner.validate_update(value)
        row["issue_id"] = "i0001"
        value["resolutions"] = [row, row]
        with self.assertRaises(ProtocolError):
            runner.validate_update(value)

    def test_reviewer_can_be_rebutted_and_issue_reopened(self):
        runner = self.runner()
        self.issue(runner)
        value = update()
        value["resolutions"] = [{"issue_id": "i0001", "status": "dismissed", "reason": "Explicit recomputation",
                                  "evidence_refs": [], "changed_step_ids": ["s1"]}]
        runner.validate_update(value)
        runner.issues = runner.update_registry(value)
        value["resolutions"][0]["status"] = "open"
        value["next"] = decision("REQUEST_CHECK", ["i0001"])
        runner.validate_update(value)
        self.assertEqual(runner.update_registry(value)["i0001"]["status"], "open")

    def test_repeat_request_rejected(self):
        runner = self.runner()
        value = update("REQUEST_HELP")
        runner.attempts.append({"issue_ids": [], "fingerprint": runner.fingerprint(value["next"])})
        with self.assertRaises(ProtocolError):
            runner.validate_update(value)

    def test_invalid_recipient_rejected(self):
        value = update("CONTINUE_SELF")
        value["next"]["recipient"] = "A1"
        with self.assertRaises(ProtocolError):
            self.runner().validate_update(value)

    def test_unknown_attempted_issue_rejected(self):
        with self.assertRaises(ProtocolError):
            self.runner().validate_work({"attempted_issue_ids": ["i9999"]})

    def test_invisible_targets_rejected(self):
        with self.assertRaises(ProtocolError):
            self.runner().check_targets({"target_refs": ["secret"]}, set())

    def test_format_repair_preserves_fixed_stage(self):
        script = Script(corrupt_stage="build")
        result = self.runner(script).run()
        self.assertEqual(result["format_repairs"], 1)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["normal_calls"], 8)
        self.assertEqual(result["http_attempts"], 9)

    def test_diff_records_actual_explanation_change(self):
        runner = self.runner()
        value = {"candidate": candidate(), "issues": []}
        runner.candidate_commit("synthesize", value, {})
        value["candidate"]["steps"][0]["text"] = "A different explanation"
        runner.candidate_commit("synthesize", value, {})
        rows = [json.loads(line) for line in (self.directory / "commits.jsonl").read_text().splitlines()]
        self.assertFalse(rows[-1]["artifact_changed"])
        self.assertEqual(rows[-1]["changed_steps"], ["s1"])

    def test_input_overflow_is_degraded_not_fake_success(self):
        runner = self.runner()
        runner.config["generation"]["max_input_tokens"] = 1
        result = runner.run()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["errors"][0]["code"], "CONTEXT_OVERFLOW")

    def test_unchanged_step_cannot_be_claimed_as_change(self):
        runner = self.runner()
        self.issue(runner)
        runner.current = {"candidate": candidate()}
        value = update()
        value["resolutions"] = [{"issue_id": "i0001", "status": "addressed", "reason": "claimed repair",
                                  "evidence_refs": [], "changed_step_ids": ["s1"]}]
        with self.assertRaises(ProtocolError):
            runner.validate_update(value)

    def test_repeated_issue_uses_original_id_and_attempt(self):
        runner = self.runner()
        self.issue(runner)
        runner.issues["i0001"]["related_events"] = []
        runner.attempts = [{"issue_ids": ["i0001"], "fingerprint": "fixture"}]
        proposal = {"description": "same unresolved dependency", "blocking": True,
                    "target_refs": [], "existing_issue_id": "i0001"}
        runner.proposed_issues([proposal], "fixture:e0010", runner.issues)
        self.assertEqual(len(runner.issues), 1)
        runner.validate_update(update("FINISH_STALLED"))

    def test_prompt_projection_does_not_delete_audit_history(self):
        runner = self.runner()
        self.issue(runner)
        runner.issues["i0001"]["handling_events"] = [{"reason": str(i)} for i in range(20)]
        self.assertEqual(len(runner.view()["issues"][0]["handling_events"]), 1)
        self.assertEqual(len(runner.issues["i0001"]["handling_events"]), 20)

    def test_duplicate_candidate_steps_repaired_before_commit(self):
        script = Script()
        original = script.__call__
        corrupted = [False]
        def transport(payload, timeout):
            response = original(payload, timeout)
            props = payload["text"]["format"]["schema"]["properties"]
            if "candidate" in props and "next" not in props and not corrupted[0]:
                corrupted[0] = True
                data = json.loads(response["output"][0]["content"][0]["text"])
                data["candidate"]["steps"].append(copy.deepcopy(data["candidate"]["steps"][0]))
                response["output"][0]["content"][0]["text"] = json.dumps(data)
            return response
        result = self.runner(transport).run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["format_repairs"], 1)

    def test_invalid_update_never_committed_and_final_still_runs(self):
        script = Script(issue=True)
        runner = self.runner(script)
        result = runner.run()
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["stop_reason"], "runtime_error")
        self.assertFalse(any(e["stage"] == "apply" for e in runner.events))
        self.assertEqual(runner.current["version"], 1)
        self.assertEqual(runner.events[-1]["stage"], "final")

    def test_final_failure_preserves_prefinal_and_stop(self):
        script = Script()
        def transport(payload, timeout):
            props = payload["text"]["format"]["schema"]["properties"]
            if set(props) == {"artifact", "basis_refs"}:
                raise ProtocolError("MODEL_TIMEOUT", "Fixture final timeout")
            return script(payload, timeout)
        result = self.runner(transport).run()
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["stop_reason"], "complete")
        self.assertEqual(result["artifact"], result["prefinal_artifact"])

    def test_empty_check_targets_cannot_be_committed(self):
        script = Script()
        def transport(payload, timeout):
            response = script(payload, timeout)
            if "checks" in payload["text"]["format"]["schema"]["properties"]:
                value = json.loads(response["output"][0]["content"][0]["text"])
                value["checks"][0]["target_refs"] = []
                response["output"][0]["content"][0]["text"] = json.dumps(value)
            return response
        runner = self.runner(transport)
        result = runner.run()
        self.assertEqual(result["status"], "degraded")
        self.assertFalse(any(e["stage"] == "inspect" for e in runner.events))


if __name__ == "__main__":
    unittest.main()
