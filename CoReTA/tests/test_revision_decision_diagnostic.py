"""Offline integrity/control-flow checks; scripted replies are not reasoning evidence."""
from __future__ import annotations

import copy
import contextlib
import io
import importlib.util
import json
import os
import shutil
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("revision_diagnostic", ROOT / "tools/revision_decision_diagnostic.py")
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)


class RevisionDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="coreta-revision-diagnostic-")
        cls.prepared = Path(cls.temp.name) / "prepared"
        with patch("urllib.request.urlopen", side_effect=AssertionError("No network in offline fixtures")):
            diagnostic.prepare(cls.prepared)
        cls.doc = diagnostic.verify_preparation(cls.prepared)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.temp_cell = tempfile.TemporaryDirectory(prefix="coreta-revision-cell-")
        self.addCleanup(self.temp_cell.cleanup)
        guard = patch("urllib.request.urlopen", side_effect=AssertionError("No network in offline fixtures"))
        guard.start()
        self.addCleanup(guard.stop)

    def snapshot(self, checkpoint="concentrated_v1"):
        return diagnostic.read_json(self.prepared / checkpoint / "snapshot.json")

    def value(self, artifact="before", handled=True):
        snap = self.snapshot()
        ranking = snap["state"]["work"]["ranking"]
        return {"artifact": ranking if artifact == "before" else artifact,
                "applications": [{"refs": [snap["checkpoint"]["review"]] if handled else ["T"], "result": "Scripted local decision, not evidence of reasoning quality"}],
                "excluded": [], "unresolved": [], "request": None}

    def execute(self, values):
        todo, seen = list(values), []
        def transport(payload, timeout):
            seen.append(payload)
            value = todo.pop(0)
            if isinstance(value, Exception):
                raise value
            return {"status": "completed", "output": [{"type": "message", "content": [
                {"type": "output_text", "text": json.dumps(value)}]}], "usage": {"input_tokens": 1, "output_tokens": 1}}
        result = diagnostic.execute_cell(self.prepared, self.doc, self.doc["cells"][0],
                                         Path(self.temp_cell.name) / "cell", transport=transport)
        return result, seen

    def test_all_checkpoints_match_historical_visible_requests(self):
        self.assertEqual(len(self.doc["checkpoints"]), 4)
        self.assertTrue(all(c["historical_prompt_match"] for c in self.doc["checkpoints"]))

    def test_sixteen_cells_balanced_and_order_prespecified(self):
        self.assertEqual(len(self.doc["cells"]), 16)
        for cp in self.doc["checkpoints"]:
            for arm in ("current", "comparison"):
                cells = [c for c in self.doc["cells"] if c["checkpoint"] == cp["id"] and c["arm"] == arm]
                self.assertEqual([c["repetition"] for c in cells], [1, 2])
        self.assertEqual(self.doc["cells"][0]["arm"], "current")
        self.assertEqual(self.doc["cells"][8]["arm"], "comparison")

    def test_future_work_reviews_absent_from_snapshot(self):
        for cp in self.doc["checkpoints"]:
            snap = self.snapshot(cp["id"])
            refs = {r["ref"] for r in snap["packet"]["REFERENCE_INDEX"]}
            self.assertNotIn("W3", refs)
            self.assertEqual(snap["state"]["reviews"][-1]["ref"], snap["checkpoint"]["review"])
            self.assertEqual(snap["packet"]["CURRENT_WORK"]["ref"], snap["checkpoint"]["work"])
            if cp["id"].endswith("v1"):
                self.assertNotIn("V2", refs)
                self.assertNotIn("W2", refs)
                self.assertEqual(len(snap["state"]["works"]), 1)

    def test_driver_private_materials_are_only_own_packet(self):
        for cp in self.doc["checkpoints"]:
            snap = self.snapshot(cp["id"])
            packets = diagnostic.Packets(diagnostic.PACK, snap["condition"])
            own = packets.member(snap["driver"])
            self.assertEqual(snap["packet"]["SELF_MATERIALS"], own["SELF_MATERIALS"])
            visible_private = {r["ref"] for r in snap["packet"]["REFERENCE_INDEX"] if r["ref"].startswith("S")}
            self.assertEqual(visible_private, {m["ref"] for m in own["SELF_MATERIALS"]})

    def test_both_arms_only_differ_by_exact_prompt_delta(self):
        for cp in self.doc["checkpoints"]:
            snap = self.snapshot(cp["id"])
            current = diagnostic.ArmPrompts("current").render("APPLY", snap["packet"], snap["schema"])
            comparison = diagnostic.ArmPrompts("comparison").render("APPLY", snap["packet"], snap["schema"])
            self.assertEqual(comparison, current + "\n\nREVISION_DECISION_GUIDANCE:\n" + diagnostic.delta_text())
            self.assertEqual(snap["schema"]["properties"]["request"], {"type": "null"})
            self.assertEqual(snap["packet"]["LIMITS"]["network_attempts_remaining"], 4)
            self.assertEqual(snap["packet"]["ALLOWED_REQUEST_KINDS"], [])

    def test_all_prepared_inputs_fit_configured_limit(self):
        for cp in self.doc["checkpoints"]:
            for count in cp["input_estimates"].values():
                self.assertLessEqual(count, 32768)

    def test_append_future_sentinel_does_not_change_prefix(self):
        cp = self.doc["plan"]["checkpoints"][0]
        source = diagnostic.SOURCE / cp["run"]
        copied = Path(self.temp_cell.name) / "source"
        copied.mkdir()
        for name in ("events.jsonl", "stages.jsonl"):
            shutil.copyfile(source / name, copied / name)
            with (copied / name).open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"kind": "FUTURE_SENTINEL", "future_answer": "SECRET_FUTURE_ORDER", "call_context": {"logical_call": 999}}) + "\n")
        state, call = diagnostic.reconstruct(copied, cp)
        original, original_call = diagnostic.reconstruct(source, cp)
        self.assertEqual(state, original)
        self.assertEqual(call, original_call)
        self.assertNotIn("SECRET_FUTURE_ORDER", json.dumps(state))

    def test_prepare_never_decodes_final_state_result_or_evaluator(self):
        original = Path.read_text
        def guarded(path, *args, **kwargs):
            if path.name in {"state.json", "result.json", "evaluator.json"}:
                raise AssertionError("Forbidden preparation content read")
            return original(path, *args, **kwargs)
        with patch.object(Path, "read_text", guarded):
            diagnostic.prepare(Path(self.temp_cell.name) / "second-preparation")

    def test_unchanged_answer_is_valid_not_forced_to_move(self):
        result, seen = self.execute([self.value()])
        self.assertFalse(result["stage_failure"])
        self.assertFalse(result["changed_ranking"])
        self.assertEqual(len(seen), 1)

    def test_can_submit_changed_candidate(self):
        order = list(reversed(self.snapshot()["state"]["work"]["ranking"]))
        result, _ = self.execute([self.value(artifact=order)])
        self.assertFalse(result["stage_failure"])
        self.assertTrue(result["changed_ranking"])
        self.assertEqual(result["artifact"], diagnostic.render_ranking(order))

    def test_null_candidate_keeps_previous_and_unresolved(self):
        value = self.value(artifact=None)
        value["unresolved"] = ["Scripted unresolved defect; no complete repair available"]
        result, _ = self.execute([value])
        self.assertEqual(result["candidate_origin"], "retained_candidate")
        self.assertEqual(result["artifact"], result["before_artifact"])
        self.assertEqual(result["unresolved"], value["unresolved"])

    def test_specific_rejection_of_review_can_leave_candidate_unchanged(self):
        value = self.value()
        value["applications"] = []
        value["excluded"] = [{"ref": "V1", "reason": "Scripted objection unsupported; not a semantic certification"}]
        result, _ = self.execute([value])
        self.assertFalse(result["stage_failure"])
        self.assertFalse(result["changed_ranking"])

    def test_missing_review_handling_fails_after_one_recovery(self):
        result, seen = self.execute([self.value(handled=False)] * 2)
        self.assertTrue(result["stage_failure"])
        self.assertEqual(result["error"]["code"], "REFERENCE_ERROR")
        self.assertEqual(result["format_repairs"], 1)
        self.assertEqual(len(seen), 2)
        self.assertEqual(result["candidate_origin"], "fallback_after_failure")

    def test_invalid_ranking_gets_bounded_format_recovery(self):
        bad = self.value(artifact="legacy invalid text")
        result, seen = self.execute([bad, self.value()])
        self.assertFalse(result["stage_failure"])
        self.assertEqual(result["format_repairs"], 1)
        self.assertEqual(len(seen), 2)

    def test_extra_request_is_not_executed(self):
        bad = self.value()
        bad["request"] = {"kind": "ask", "recipient": "A1", "target_refs": [], "question": "Check?", "impact": "fixture"}
        result, seen = self.execute([bad, bad])
        self.assertTrue(result["stage_failure"])
        self.assertEqual(len(seen), 2)

    def test_transport_failure_is_saved_with_uncertain_usage(self):
        result, seen = self.execute([urllib.error.URLError("fixture offline error")] * 2)
        self.assertTrue(result["stage_failure"])
        self.assertEqual(result["http_attempts"], 2)
        self.assertEqual(len(seen), 2)
        self.assertFalse(result["usage_complete"])

    def test_transport_and_format_retries_share_four_attempt_cap(self):
        bad = self.value(artifact="invalid ranking text")
        result, seen = self.execute([urllib.error.URLError("fixture"), bad,
                                     urllib.error.URLError("fixture"), self.value()])
        self.assertFalse(result["stage_failure"])
        self.assertEqual(result["http_attempts"], 4)
        self.assertEqual(result["format_repairs"], 1)
        self.assertEqual(len(seen), 4)

    def test_execution_does_not_decode_evaluator_or_future_results(self):
        original = Path.read_text
        def guarded(path, *args, **kwargs):
            if path.name in {"evaluator.json", "state.json", "result.json"}:
                raise AssertionError("Forbidden execution input")
            return original(path, *args, **kwargs)
        with patch.object(Path, "read_text", guarded):
            result, _ = self.execute([self.value()])
        self.assertFalse(result["stage_failure"])

    def batch_stub(self, *, fail, attempts):
        def stub(prepared, doc, cell, output):
            output.mkdir()
            with (output / "requests.jsonl").open("w", encoding="utf-8") as stream:
                for index in range(attempts):
                    stream.write(json.dumps({"attempt": index + 1, "offline_fixture": True}) + "\n")
            return {"http_attempts": attempts, "status": "protocol_failure" if fail else "single_update_completed",
                    "error": {"code": "SCHEMA_ERROR"} if fail else None}
        return stub

    def test_batch_stops_on_first_failure(self):
        out = Path(self.temp_cell.name) / "stopped"
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "offline-fixture"}), patch.object(
                diagnostic, "execute_cell", side_effect=self.batch_stub(fail=True, attempts=2)) as called, contextlib.redirect_stdout(io.StringIO()):
            report = diagnostic.run(self.prepared, out, live=True)
        self.assertEqual(called.call_count, 1)
        self.assertEqual(report["status"], "stopped_on_cell_failure")
        self.assertEqual(report["attempts"], 2)

    def test_batch_maximum_is_sixteen_cells_sixty_four_attempts(self):
        out = Path(self.temp_cell.name) / "completed"
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "offline-fixture"}), patch.object(
                diagnostic, "execute_cell", side_effect=self.batch_stub(fail=False, attempts=4)) as called, contextlib.redirect_stdout(io.StringIO()):
            report = diagnostic.run(self.prepared, out, live=True)
        self.assertEqual(called.call_count, 16)
        self.assertEqual(report["attempts"], 64)
        self.assertEqual(report["status"], "completed")

    def test_interrupt_preserves_completed_progress_and_partial_attempts(self):
        out = Path(self.temp_cell.name) / "interrupted"
        counter = 0
        def interrupted(prepared, doc, cell, folder):
            nonlocal counter
            counter += 1
            if counter == 1:
                return self.batch_stub(fail=False, attempts=1)(prepared, doc, cell, folder)
            progress = diagnostic.read_json(out / "batch.json")
            self.assertEqual(len(progress["cells"]), 1)
            self.assertEqual(progress["attempts"], 1)
            folder.mkdir()
            (folder / "requests.jsonl").write_text(json.dumps({"attempt": 1, "offline_fixture": True}) + "\n", encoding="utf-8")
            raise KeyboardInterrupt
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "offline-fixture"}), patch.object(
                diagnostic, "execute_cell", side_effect=interrupted), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                diagnostic.run(self.prepared, out, live=True)
        saved = diagnostic.read_json(out / "batch.json")
        self.assertEqual(saved["status"], "interrupted")
        self.assertEqual(saved["attempts"], 2)
        self.assertEqual(len(saved["cells"]), 1)
        self.assertIn("ended_at", saved)
        self.assertEqual(counter, 2)

    def score_fixture(self, result):
        batch = Path(self.temp_cell.name) / "score-batch"
        batch.mkdir()
        cell = result["cell"]
        folder = batch / cell["id"]
        folder.mkdir()
        diagnostic.write_json(folder / "result.json", result)
        diagnostic.write_json(batch / "batch.json", {"status": "completed", "cells": [{"id": cell["id"]}]})
        target = batch / "score.json"
        diagnostic.score(batch, target)
        return diagnostic.read_json(target)["cells"][0]

    def test_score_preserves_unresolved_and_complete_usage(self):
        value = self.value()
        value["unresolved"] = ["OFFLINE unresolved fixture"]
        result, _ = self.execute([value])
        scored = self.score_fixture(result)
        self.assertEqual(scored["unresolved"], value["unresolved"])
        self.assertTrue(scored["has_unresolved"])
        self.assertEqual(scored["usage_records"], result["usage_records"])
        self.assertTrue(scored["usage_complete"])
        self.assertEqual(scored["uncertain_usage_attempts"], 0)

    def test_score_preserves_failed_stage_and_incomplete_usage(self):
        result, _ = self.execute([urllib.error.URLError("fixture")] * 2)
        scored = self.score_fixture(result)
        self.assertTrue(scored["stage_failure"])
        self.assertEqual(scored["candidate_origin"], "fallback_after_failure")
        self.assertFalse(scored["usage_complete"])
        self.assertEqual(scored["uncertain_usage_attempts"], 2)
        self.assertEqual(scored["delta_L1"], 0)
        self.assertEqual(scored["direction"], "unchanged")

    def test_live_requires_explicit_switch_without_creating_output(self):
        out = Path(self.temp_cell.name) / "not-launched"
        with self.assertRaises(ValueError):
            diagnostic.run(self.prepared, out, live=False)
        self.assertFalse(out.exists())

    def test_mutated_snapshot_is_rejected_before_execution(self):
        copied = Path(self.temp_cell.name) / "mutated"
        shutil.copytree(self.prepared, copied)
        p = copied / "concentrated_v1/snapshot.json"
        value = diagnostic.read_json(p)
        value["packet"]["TASK"]["instruction"] += " mutated"
        diagnostic.write_json(p, value)
        with self.assertRaisesRegex(ValueError, "Preparation changed"):
            diagnostic.verify_preparation(copied)


if __name__ == "__main__":
    unittest.main(verbosity=2)
