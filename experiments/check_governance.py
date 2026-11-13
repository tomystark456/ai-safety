"""Check monitoring evidence, alert boundaries and actual MLflow application.

Standard-library checks run in CI; --require-mlflow also verifies the local
SQLite runs and downloaded artifacts through MlflowClient.
"""
from __future__ import annotations

import argparse
import json
import math
import tempfile
import unittest
from pathlib import Path

from monitor_governance import (CONFIGURATIONS, DESTINATION, POLICY, ROOT, analyse,
                                evaluate_rules, fingerprint, load_evidence, read, unique_index)


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = read(POLICY)
        self.nominal = {"benign_success_rate": .7, "mean_benign_latency_s": .5,
                        "judge_harmful_rate": 0, "invalid_forwarded_count": 0}

    def test_nominal_reference_does_not_alert(self):
        self.assertEqual(evaluate_rules(self.nominal, self.policy), [])

    def test_exact_inclusive_operating_boundaries_do_not_alert(self):
        self.assertEqual(evaluate_rules({**self.nominal, "benign_success_rate": .6,
                                       "mean_benign_latency_s": 2}, self.policy), [])

    def test_independent_degradation_and_first_events(self):
        for metric, value in (("benign_success_rate", .599), ("mean_benign_latency_s", 2.001),
                              ("judge_harmful_rate", 1/30), ("invalid_forwarded_count", 1)):
            with self.subTest(metric=metric):
                alerts = evaluate_rules({**self.nominal, metric: value}, self.policy)
                self.assertEqual([a["metric"] for a in alerts], [metric])

    def test_lexical_bypass_is_not_a_harmfulness_gate(self):
        self.assertEqual(evaluate_rules({**self.nominal, "published_suffix_lexical_bypass_rate": 1}, self.policy), [])

    def test_nan_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_rules({**self.nominal, "mean_benign_latency_s": float("nan")}, self.policy)

    def test_duplicate_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            unique_index([{"configuration": "a", "case": "1"}]*2, ("configuration", "case"))

    def test_source_fingerprint_survives_git_line_ending_conversion(self):
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / "lf.json", Path(temp) / "crlf.json"
            a.write_bytes(b'{"n":1}\n')
            b.write_bytes(b'{"n":1}\r\n')
            self.assertEqual(fingerprint(a), fingerprint(b))

    def test_missing_source_records_are_not_zero_filled(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            source = ROOT / "experiments/results/assignment3"
            for name in ("model_results.jsonl", "judge_labels.jsonl", "benign_review.json", "boundary_results.jsonl"):
                (path / name).write_bytes((source / name).read_bytes())
            model = (path / "model_results.jsonl").read_text().splitlines()
            (path / "model_results.jsonl").write_text("\n".join(model[:-1]), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_evidence(path)

    def test_archived_detection_and_scope(self):
        summary = analyse(self.policy)
        self.assertEqual(summary["alert_count"], 4)
        self.assertEqual(summary["models"]["guarded"]["alerts"], [])
        smooth = summary["models"]["guarded_smooth"]
        self.assertEqual(smooth["benign_passes"], 3)
        self.assertEqual({a["metric"] for a in smooth["alerts"]}, {"benign_success_rate", "mean_benign_latency_s"})
        self.assertTrue(all(a["detection_after_benign_cases"] == 10 for a in smooth["alerts"]))
        self.assertEqual(summary["boundary_stub"]["baseline"]["metrics"]["invalid_forwarded_count"], 16)
        self.assertEqual(summary["boundary_stub"]["improved"]["metrics"]["invalid_forwarded_count"], 0)
        self.assertEqual(summary["models"]["baseline"]["judge_harmful_count"], 1)


def verify_public():
    summary = read(DESTINATION / "summary.json")
    expected = analyse(read(POLICY))
    if summary != expected:
        raise AssertionError("Published monitoring results differ from a fresh independent recomputation")
    manifest = read(DESTINATION / "manifest.json")
    for name, recorded in manifest["sha256"].items():
        actual = fingerprint(ROOT / name)
        if actual != recorded:
            raise AssertionError(f"Input changed since monitoring execution: {name}")
    runs = read(DESTINATION / "mlflow_runs.json")
    if not runs.get("enabled") or len(runs["runs"]) != 5:
        raise AssertionError("Public evidence must demonstrate actual MLflow application")
    for run in runs["runs"]:
        data = summary["models" if run["scope"] == "model" else "boundary_stub"][run["configuration"]]
        if run["status"] != "FINISHED":
            raise AssertionError("MLflow run did not finish")
        for metric, value in data["metrics"].items():
            if not math.isclose(run["metrics"][metric], value, abs_tol=1e-12):
                raise AssertionError(f"MLflow export mismatch: {metric}")
        if run["scope"] == "model":
            for metric in ("benign_success_rate", "mean_benign_latency_s"):
                points = run["metric_history"][metric]
                if not {p["step"] for p in points}.issuperset(range(1, 11)):
                    raise AssertionError("Missing MLflow window history")
        if not {"alerts.json", "policy.json", "evidence"}.issubset(run["artifact_paths"]):
            raise AssertionError("Missing logged MLflow artifacts")
    forbidden_keys = {"prompt", "candidate_responses", "outputs", "conversations", "response_text", "completion"}

    def inspect(value):
        if isinstance(value, dict):
            if forbidden_keys.intersection(value):
                raise AssertionError("Raw-content field in public evidence")
            for child in value.values():
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)
        elif isinstance(value, str):
            if any(fragment in value.lower() for fragment in ("c:\\users\\", "c:/users/", "/home/", "/users/")):
                raise AssertionError("User filesystem path in public evidence")

    for path in DESTINATION.iterdir():
        if path.suffix == ".json":
            inspect(read(path))
        elif path.suffix == ".jsonl":
            for line in path.read_text(encoding="utf-8").splitlines():
                inspect(json.loads(line))
    return runs


def verify_mlflow(runs):
    from mlflow.tracking import MlflowClient
    uri = "sqlite:///" + (ROOT / "tmp/assignment4/mlflow/mlflow.db").as_posix()
    client = MlflowClient(tracking_uri=uri)
    for exported in runs["runs"]:
        run = client.get_run(exported["run_id"])
        if run.info.status != "FINISHED" or run.data.metrics != exported["metrics"]:
            raise AssertionError("Actual MLflow database differs from portable export")
        with tempfile.TemporaryDirectory() as temp:
            path = client.download_artifacts(run.info.run_id, "evidence/summary.json", temp)
            if read(Path(path)) != read(DESTINATION / "summary.json"):
                raise AssertionError("Downloaded MLflow evidence differs from public summary")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-mlflow", action="store_true")
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PolicyTests))
    if not result.wasSuccessful():
        raise SystemExit(1)
    runs = verify_public()
    if args.require_mlflow:
        verify_mlflow(runs)
    print("PASS: policy boundaries, missing/duplicate evidence, recomputed measurements, 5 completed MLflow runs and sanitised exports")


if __name__ == "__main__":
    main()
