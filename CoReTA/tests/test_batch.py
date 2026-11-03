import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coreta.batch import build_plan, run_batch, sha, verify_plan
from coreta.state import write_json

ROOT = Path(__file__).resolve().parents[1]


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / "bundle"
        (self.bundle / "public").mkdir(parents=True)
        public = self.bundle / "public/task.json"
        write_json(public, {"task_id": "fixture", "task_type": "math", "prompt": "1+1?", "entry_point": None})
        write_json(self.bundle / "tasks.json", [{"task_id": "fixture", "family": "gsm8k", "path": "public/task.json",
                   "sha256": sha(public), "engineering": True, "pilot": True}])
        write_json(self.bundle / "manifest.json", {"task_index_sha256": sha(self.bundle / "tasks.json")})
        self.plan = build_plan(self.bundle, ROOT / "config/deepseek_flash.json", ROOT / "design/v0.3")
        self.plan_path = self.root / "plan.json"
        write_json(self.plan_path, self.plan)

    def test_plan_is_bounded_and_contains_no_gold(self):
        self.assertEqual(self.plan["job_count"], 3)
        self.assertEqual(self.plan["normal_call_upper_bound"], 26)
        self.assertEqual(self.plan["model_calls_executed"], 0)
        self.assertNotIn("evaluation", json.dumps(self.plan))

    def test_changed_public_task_refuses_run(self):
        (self.bundle / "public/task.json").write_text("{}")
        with self.assertRaises(ValueError):
            verify_plan(self.plan)

    def test_no_live_never_executes(self):
        with self.assertRaises(ValueError):
            run_batch(self.plan_path, self.root / "runs", max_jobs=1)
        self.assertFalse((self.root / "runs").exists())

    def test_missing_credential_refuses_before_run_directory(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            run_batch(self.plan_path, self.root / "runs", max_jobs=1, live=True)
        self.assertFalse((self.root / "runs").exists())

    def test_bound_and_resume_use_complete_results_not_scores(self):
        calls = []
        def execute(command, **kwargs):
            calls.append(command)
            output = Path(command[command.index("--output") + 1])
            output.mkdir()
            write_json(output / "result.json", {"task_id": "fixture", "system": command[command.index("--system") + 1],
                                               "seed": 17, "status": "degraded", "artifact": ""})
            return subprocess.CompletedProcess(command, 0, stdout="fixture only", stderr="")
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "FAKE_TEST_KEY"}):
            first = run_batch(self.plan_path, self.root / "runs", max_jobs=1, live=True, execute=execute)
            second = run_batch(self.plan_path, self.root / "runs", max_jobs=1, live=True, execute=execute)
        self.assertEqual(first["jobs_started"], 1)
        self.assertEqual(second["jobs_skipped_complete"], 1)
        self.assertEqual(second["jobs_started"], 1)
        self.assertEqual(len(calls), 2)
        self.assertIn("--draft-bank", calls[0])

    def test_failed_entry_stops_batch_and_preserves_next_attempt(self):
        calls = []
        def execute(command, **kwargs):
            calls.append(command)
            output = Path(command[command.index("--output") + 1])
            output.mkdir()
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="fixture implementation error")
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "FAKE_TEST_KEY"}):
            first = run_batch(self.plan_path, self.root / "runs", max_jobs=3, live=True, execute=execute)
            run_batch(self.plan_path, self.root / "runs", max_jobs=1, live=True, execute=execute)
        self.assertEqual(first["jobs_started"], 1)
        self.assertNotEqual(calls[0][calls[0].index("--output") + 1], calls[1][calls[1].index("--output") + 1])

    def test_infrastructure_error_stops_even_with_zero_exit(self):
        def execute(command, **kwargs):
            output = Path(command[command.index("--output") + 1])
            output.mkdir()
            write_json(output / "result.json", {"task_id": "fixture", "system": command[command.index("--system") + 1],
                       "seed": 17, "status": "failed", "errors": [{"code": "MODEL_UNAVAILABLE", "detail": "HTTP 401"}]})
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "FAKE_TEST_KEY"}):
            report = run_batch(self.plan_path, self.root / "runs", max_jobs=3, live=True, execute=execute)
        self.assertEqual(report["jobs_started"], 1)
        self.assertEqual(report["stop_reason"], "model_infrastructure_failure")

    def test_tokenizer_is_pinned_and_forwarded(self):
        tokenizer = self.root / "tokenizer.json"
        tokenizer.write_text("fixture")
        plan = build_plan(self.bundle, ROOT / "config/deepseek_flash.json", ROOT / "design/v0.3", tokenizer=tokenizer)
        write_json(self.plan_path, plan)
        def execute(command, **kwargs):
            self.assertEqual(command[command.index("--tokenizer") + 1], str(tokenizer.resolve()))
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="fixture")
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "FAKE_TEST_KEY"}):
            run_batch(self.plan_path, self.root / "runs", max_jobs=1, live=True, execute=execute)
        tokenizer.write_text("changed")
        with self.assertRaises(ValueError):
            verify_plan(plan)

    def test_analysis_rejects_wholly_missing_task(self):
        from coreta.analyze import paired_summary
        rows = [{"task_id": "present", "system": system, "seed": seed, "score": 1}
                for system in ("coreta", "static_debate") for seed in (17,29,43)]
        with self.assertRaises(ValueError):
            paired_summary(rows, expected_tasks=["present", "missing"])


if __name__ == "__main__":
    unittest.main()
