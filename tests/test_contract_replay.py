from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from everyinfra_contract_replay.compare import compare_contracts, replay_check
from everyinfra_contract_replay.cli import main as cli_main
from everyinfra_contract_replay.contract import build_contract, path_template
from everyinfra_contract_replay.io import ContractReplayError, load_captures, write_json_exclusive
from everyinfra_contract_replay.redact import redact_url, sanitize_capture

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def baseline_captures():
    return load_captures(sorted((PROJECT_ROOT / "examples" / "baseline").glob("*.json")))


def current_captures():
    return load_captures(sorted((PROJECT_ROOT / "examples" / "current").glob("*.json")))


class RedactionTests(unittest.TestCase):
    def test_recursive_redaction_does_not_mutate_input(self):
        original = baseline_captures()[0]
        unchanged = copy.deepcopy(original)
        sanitized = sanitize_capture(original)
        rendered = json.dumps(sanitized, sort_keys=True)
        self.assertEqual(original, unchanged)
        self.assertNotIn("synthetic-secret", rendered)
        self.assertNotIn("operator@example.test", rendered)
        self.assertIn("[REDACTED]", rendered)
        self.assertIn("[REDACTED_CONTACT]", rendered)

    def test_query_values_are_masked(self):
        masked = redact_url("https://api.example.test/items?q=public&token=secret")
        self.assertIn("q=%5BVALUE%5D", masked)
        self.assertIn("token=%5BREDACTED%5D", masked)
        self.assertNotIn("public", masked)
        self.assertNotIn("secret", masked)

    def test_url_userinfo_is_rejected(self):
        with self.assertRaises(ContractReplayError):
            redact_url("https://user:pass@api.example.test/v1")


class ContractTests(unittest.TestCase):
    def test_path_template_normalizes_common_identifiers(self):
        self.assertEqual(
            path_template("/v1/jobs/job_123456/550e8400-e29b-41d4-a716-446655440000/42"),
            "/v1/jobs/{id}/{uuid}/{int}",
        )

    def test_contract_is_deterministic_across_input_order(self):
        captures = baseline_captures()
        self.assertEqual(build_contract(captures), build_contract(list(reversed(captures))))

    def test_contract_contains_no_fixture_secrets(self):
        rendered = json.dumps(build_contract(baseline_captures()), sort_keys=True)
        self.assertNotIn("synthetic-secret", rendered)
        self.assertNotIn("operator@example.test", rendered)
        self.assertIn("GET https://api.example.test/v1/jobs/{id}", rendered)


class DiffAndReplayTests(unittest.TestCase):
    def test_diff_classifies_breaking_and_additive_changes(self):
        diff = compare_contracts(
            build_contract(baseline_captures()), build_contract(current_captures())
        )
        self.assertGreaterEqual(diff["summary"]["breaking_candidates"], 2)
        self.assertGreaterEqual(diff["summary"]["additive"], 1)
        paths = {change["path"] for change in diff["changes"]}
        self.assertIn("responses.200.body.status", paths)
        self.assertIn("responses.200.body.result.source", paths)

    def test_replay_passes_same_evidence(self):
        captures = baseline_captures()
        result = replay_check(build_contract(captures), list(reversed(captures)))
        self.assertTrue(result["passed"])
        self.assertEqual(result["diff"]["summary"]["total_changes"], 0)

    def test_replay_fails_on_structural_drift(self):
        result = replay_check(build_contract(baseline_captures()), current_captures())
        self.assertFalse(result["passed"])
        self.assertGreater(result["diff"]["summary"]["total_changes"], 0)


class IOAndCLITests(unittest.TestCase):
    def test_redact_cli_writes_a_sanitized_list(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sanitized.json"
            code = cli_main(
                [
                    "redact",
                    "--output",
                    str(output),
                    str(PROJECT_ROOT / "examples" / "baseline" / "get-job.json"),
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(output.read_text())
            self.assertEqual(len(payload), 1)
            self.assertNotIn("synthetic-secret", json.dumps(payload))

    def test_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "report.json"
            write_json_exclusive(target, {"first": True})
            with self.assertRaises(FileExistsError):
                write_json_exclusive(target, {"second": True})
            self.assertEqual(json.loads(target.read_text()), {"first": True})

    def test_capture_count_limit(self):
        sample = baseline_captures()[0]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "too-many.json"
            source.write_text(json.dumps([sample] * 1001), encoding="utf-8")
            with self.assertRaises(ContractReplayError):
                load_captures([source])

    def test_demo_outputs_redacted_evidence_and_expected_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "demo"
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "scripts" / "demo.py"), "--output", str(output)],
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads((output / "demo-receipt.json").read_text())
            self.assertEqual(receipt["network_requests"], 0)
            self.assertEqual(receipt["raw_secret_leaks"], 0)
            self.assertFalse(receipt["replay_passed"])


if __name__ == "__main__":
    unittest.main()
