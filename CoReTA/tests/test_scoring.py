import copy
import json
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coreta.analyze import paired_summary
from coreta.scoring import (docker_command, evalplus_scores, launch_job, math_process,
                            preflight_math, score_math_results, score_mbpp, score_humaneval, subset_problems,
                            docker_math_records)
from coreta.tasks import export_evalplus, mbpp_signature, public_task, select_ids
from coreta.scoring_worker import final_boxed, main as worker_main
from math_verify.errors import TimeoutException


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_math_equivalent_and_wrong_and_unparseable(self):
        for answer, prediction, expected, status in [
            (r"\frac{1}{2}", r"\boxed{0.5}", 1, "scored"),
            ("2", r"\boxed{3}", 0, "scored"),
            ("2", "no answer", 0, "prediction_unparseable"),
            ("2", r"Earlier \boxed{3}, final \boxed{2}", 1, "scored"),
        ]:
            with self.subTest(prediction=prediction):
                row = math_process({"task_id": "fixture", "answer": answer, "artifact": prediction}, diagnostic=True)
                self.assertEqual(row["status"], status, row)
                self.assertEqual(row["score"], expected, row)
                self.assertTrue(row["diagnostic_only"])

    def test_math_preflight_then_prefinal_and_final_scoring(self):
        gold = self.root / "gold.json"
        gold.write_text(json.dumps([{"task_id": "a", "answer": "2"}]))
        report = preflight_math(gold, diagnostic=True)
        self.assertTrue(report["ready"], report)
        saved = self.root / "preflight.json"
        saved.write_text(json.dumps(report))
        rows = score_math_results(gold, saved, [{"task_id": "a", "system": "coreta", "seed": 17,
            "status": "completed", "artifact": r"\boxed{2}", "prefinal_artifact": r"\boxed{3}"}], diagnostic=True)
        self.assertEqual([row["score"] for row in rows], [0, 1])
        gold.write_text(json.dumps([{"task_id": "a", "answer": "9"}]))
        with self.assertRaises(ValueError):
            score_math_results(gold, saved, [], diagnostic=True)

    def test_final_boxed_balances_nested_and_escaped_braces(self):
        self.assertEqual(final_boxed(r"old \boxed{9} final \boxed{\frac{1}{2}}."), r"\boxed{\frac{1}{2}}")
        self.assertEqual(final_boxed(r"\boxed{\{1,2\}}"), r"\boxed{\{1,2\}}")
        with self.assertRaises(ValueError):
            final_boxed(r"\boxed{2} then \boxed{3")

    def test_math_library_base_exception_timeout_is_recorded_and_retried(self):
        request = {"records": [{"task_id": "fixture", "answer": "2"}], "preflight": True}
        output = io.StringIO()
        with patch("sys.argv", ["worker", "math-batch"]), patch("sys.stdin", io.StringIO(json.dumps(request))), \
             patch("sys.stdout", output), patch("coreta.scoring_worker.math_record", side_effect=TimeoutException("fixture timeout")) as call:
            worker_main()
        row = json.loads(output.getvalue())[0]
        self.assertEqual(call.call_count, 2)
        self.assertEqual(row["status"], "scoring_error")
        self.assertIsNone(row["score"])
        self.assertEqual(row["attempts"], 2)

    def test_math_process_fixed_retry_keeps_scoring_error(self):
        with patch("coreta.scoring.subprocess.run", side_effect=subprocess.TimeoutExpired("fixture", 1)) as run:
            row = math_process({"task_id": "a", "answer": "2", "artifact": "2"}, diagnostic=True)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(row["status"], "scoring_error")
        self.assertIsNone(row["score"])

    def test_nonlinux_formal_math_refuses_diagnostic_substitution(self):
        with patch("coreta.scoring.sys.platform", "win32"), self.assertRaises(RuntimeError):
            math_process({"task_id": "a", "answer": "2", "artifact": "2"})

    def test_docker_isolated_command_and_immutable_image(self):
        image = "sha256:" + "a" * 64
        command = docker_command(image, self.root, name="coreta-fixture")
        for flag in ("--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pull=never"):
            self.assertIn(flag, command)
        self.assertEqual(command[command.index("--user") + 1], "65532:65532")
        self.assertTrue(any("target=/input,readonly" in arg for arg in command))
        with self.assertRaises(ValueError):
            docker_command("ganler/evalplus:latest", self.root, name="fixture")

    def test_docker_timeout_removes_only_owned_container(self):
        seen = []
        def run(command, **kwargs):
            seen.append(command)
            if len(seen) == 1:
                raise subprocess.TimeoutExpired(command, 1)
            return subprocess.CompletedProcess(command, 0)
        command = docker_command("sha256:" + "a" * 64, self.root, name="coreta-fixture")
        result = launch_job(command, timeout=1, run=run)
        self.assertEqual(result["status"], "scoring_error")
        self.assertEqual(seen[1], ["docker", "rm", "-f", "coreta-fixture"])

    def test_linux_math_container_timeout_retries_once_and_preserves_null_score(self):
        seen = []
        def run(command, **kwargs):
            seen.append(command)
            if command[1] == "rm":
                return subprocess.CompletedProcess(command, 0)
            raise subprocess.TimeoutExpired(command, 1)
        with patch("coreta.scoring.subprocess.run", side_effect=run):
            rows = docker_math_records([{"task_id": "fixture", "answer": "2"}], "sha256:" + "a" * 64, timeout=1)
        self.assertEqual(len([c for c in seen if c[1] == "run"]), 2)
        self.assertEqual(len([c for c in seen if c[1] == "rm"]), 2)
        self.assertEqual(rows[0]["attempts"], 2)
        self.assertIsNone(rows[0]["score"])

    def test_no_docker_refuses_code_scoring_without_reading_candidate(self):
        with patch("coreta.scoring.shutil.which", return_value=None):
            with self.assertRaises(RuntimeError):
                score_humaneval(self.root / "missing", self.root / "missing", self.root / "job", "image")
            with self.assertRaises(RuntimeError):
                score_mbpp({}, self.root / "job", "image")

    def test_diagnostic_scores_cannot_enter_formal_analysis(self):
        with self.assertRaises(ValueError):
            paired_summary([{"task_id": "a", "system": "coreta", "seed": 17, "score": 1, "diagnostic_only": True}])

    def test_subset_preserves_original_test_data(self):
        path = self.root / "mother.jsonl"
        source = [{"task_id": "HumanEval/0", "plus_input": [[1]], "canonical_solution": "hidden"},
                  {"task_id": "HumanEval/1", "plus_input": [[2]], "canonical_solution": "hidden2"}]
        path.write_text("\n".join(json.dumps(row) for row in source))
        samples = [{"task_id": "HumanEval/1", "solution": ""}]
        self.assertEqual(subset_problems(path, samples), [source[1]])
        with self.assertRaises(ValueError):
            subset_problems(path, samples * 2)

    def test_evalplus_plus_requires_base_and_extra_pass(self):
        path = self.root / "eval.json"
        path.write_text(json.dumps({"eval": {"HumanEval/0": [{"base_status": "fail", "plus_status": "pass"}]}}))
        rows = evalplus_scores(path, ["HumanEval/0"], system="coreta", seed=17)
        self.assertEqual(rows[0]["plus_score"], 0)
        with self.assertRaises(ValueError):
            evalplus_scores(path, ["HumanEval/1"], system="coreta", seed=17)

    def test_evalplus_unknown_status_not_counted_wrong(self):
        path = self.root / "eval.json"
        path.write_text(json.dumps({"eval": {"HumanEval/0": [{"base_status": "pass", "plus_status": None}]}}))
        row = evalplus_scores(path, ["HumanEval/0"], system="coreta", seed=17)[0]
        self.assertEqual(row["status"], "scoring_error")
        self.assertIsNone(row["plus_score"])

    def test_task_adapter_filters_gold(self):
        rows = [("math500", {"unique_id": "a", "problem": "p", "answer": "SECRET", "solution": "SECRET"}),
                ("humaneval", {"task_id": "HumanEval/0", "prompt": "p", "entry_point": "f", "test": "SECRET"})]
        for dataset, row in rows:
            public = public_task(dataset, row)
            self.assertEqual(set(public), {"task_id", "task_type", "prompt", "entry_point"})
            self.assertNotIn("SECRET", json.dumps(public))

    def test_mbpp_signature_extracts_no_test_values(self):
        row = {"task_id": 7, "prompt": "Add inputs", "test_imports": ["import math"],
               "test_list": ["assert add(123, 456) == 579", "assert add(3, 4) == 7"]}
        self.assertEqual(mbpp_signature(row), ("add", 2))
        public = public_task("mbpp", row)
        for secret in ("123", "456", "579", "assert"):
            self.assertNotIn(secret, public["prompt"])
        bad = copy.deepcopy(row)
        bad["test_list"].append("assert add(1) == 1")
        with self.assertRaises(ValueError):
            mbpp_signature(bad)

    def test_export_empty_answer_retains_task_and_rejects_duplicate(self):
        result = {"task_id": "HumanEval/0", "artifact": "", "prefinal_artifact": ""}
        out = self.root / "samples.jsonl"
        export_evalplus([result], out)
        self.assertEqual(json.loads(out.read_text()), {"task_id": "HumanEval/0", "solution": ""})
        with self.assertRaises(ValueError):
            export_evalplus([result, result], self.root / "other.jsonl")

    def test_selection_is_order_independent(self):
        self.assertEqual(select_ids(["a", "b", "c"], "fixture", 2), select_ids(["c", "b", "a"], "fixture", 2))

    def test_task_unit_paired_bootstrap_and_repetition_coverage(self):
        rows = [{"task_id": task, "system": system, "seed": seed, "score": score}
                for task in ("a", "b") for seed in (17, 29, 43)
                for system, score in (("coreta", 1), ("static_debate", 0))]
        result = paired_summary(rows, resamples=100)
        self.assertEqual(result["tasks"], 2)
        self.assertEqual(result["paired_bootstrap_ci95"], [1.0, 1.0])
        with self.assertRaises(ValueError):
            paired_summary(rows[:-2], resamples=100)


if __name__ == "__main__":
    unittest.main()
