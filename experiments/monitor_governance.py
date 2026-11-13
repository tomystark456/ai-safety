"""Replay Assignment 3 evidence through a versioned monitoring policy and MLflow.

No inference, external API calls or live application instrumentation. Raw prompts,
answers and judge free-text are never loaded or exported by this script.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib.metadata
import json
import math
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/results/assignment3"
POLICY = ROOT / "experiments/monitoring_policy.json"
DESTINATION = ROOT / "experiments/results/assignment4"
CONFIGURATIONS = ("baseline", "guarded", "guarded_smooth")
GROUPS = ("direct", "published_suffix", "cached_gcg", "benign")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fingerprint(path):
    """Git may normalise text line endings; the benchmark is explicitly -text."""
    content = path.read_bytes()
    if path != ROOT / "experiments/data/gcg_evaluation_cases.json":
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def unique_index(rows, keys):
    index = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        if key in index:
            raise ValueError(f"Duplicate evidence key: {key}")
        index[key] = row
    return index


def load_evidence(source=SOURCE):
    rows = lines(source / "model_results.jsonl")
    judges = lines(source / "judge_labels.jsonl")
    audited = read(source / "benign_review.json")["cases"]
    boundary = lines(source / "boundary_results.jsonl")
    unique_index(rows, ("configuration", "case"))
    unique_index(judges, ("configuration", "case"))
    unique_index(audited, ("configuration", "case"))
    unique_index(boundary, ("configuration", "case"))
    expected_model_keys = set()
    for config in CONFIGURATIONS:
        for group in GROUPS:
            selected = [r for r in rows if r["configuration"] == config and r["group"] == group]
            if len(selected) != 10:
                raise ValueError(f"Expected exactly 10 {config}/{group} records")
            if any(type(r["latency_s"]) not in (int, float) or not math.isfinite(r["latency_s"]) or r["latency_s"] < 0 for r in selected):
                raise ValueError("Invalid response latency")
            keys = {(r["configuration"], r["case"]) for r in selected}
            expected_model_keys |= keys
            if group == "benign":
                actual = {(r["configuration"], r["case"]) for r in audited if r["configuration"] == config}
            else:
                actual = {(r["configuration"], r["case"]) for r in judges if r["configuration"] == config and r["group"] == group}
            if actual != keys:
                raise ValueError("Model, judge and rubric evidence cannot be joined")
    if len(rows) != 120 or len(judges) != 90 or len(audited) != 30:
        raise ValueError("Unexpected evidence size")
    if any(r["label"] not in ("harmful", "refusal", "other") for r in judges):
        raise ValueError("Unknown judge label")
    if any(type(r["audited_task_pass"]) is not bool for r in audited):
        raise ValueError("Invalid task score")
    for config in ("baseline", "improved"):
        for group, n in (("forged_system", 8), ("oversized_message", 8), ("invalid_schema", 8), ("legitimate", 24)):
            subset = [r for r in boundary if r["configuration"] == config and r["group"] == group]
            if len(subset) != n or any(type(r["forwarded"]) is not bool for r in subset):
                raise ValueError("Incomplete or invalid boundary evidence")
    if len(boundary) != 96:
        raise ValueError("Unexpected boundary evidence size")
    return rows, judges, audited, boundary


def validate_policy(policy):
    if policy["window_size"] != 10:
        raise ValueError("This archived experiment requires a 10-case benign window")
    expected = {"benign_success_rate", "mean_benign_latency_s", "judge_harmful_rate", "invalid_forwarded_count"}
    if {r["metric"] for r in policy["indicators"]} != expected or len(policy["indicators"]) != 4:
        raise ValueError("Policy must define exactly four supported indicators")
    for rule in policy["indicators"]:
        if rule["operator"] not in ("lt", "gt") or not math.isfinite(rule["threshold"]):
            raise ValueError("Invalid threshold rule")


def evaluate_rules(metrics, policy):
    """A missing metric is not interpreted as a passing zero measurement."""
    result = []
    for rule in policy["indicators"]:
        if rule["metric"] not in metrics:
            continue  # Rules have separate model and boundary scopes.
        value = metrics[rule["metric"]]
        if not math.isfinite(value):
            raise ValueError("Non-finite monitoring measurement")
        exceeded = value < rule["threshold"] if rule["operator"] == "lt" else value > rule["threshold"]
        if exceeded:
            result.append({"metric": rule["metric"], "value": value, "operator": rule["operator"],
                           "threshold": rule["threshold"], "severity": rule["severity"],
                           "response": rule["response"]})
    return result


def analyse(policy, source=SOURCE):
    validate_policy(policy)
    rows, judges, audited, boundary = load_evidence(source)
    review = unique_index(audited, ("configuration", "case"))
    models, boundaries, all_alerts = {}, {}, []
    for config in CONFIGURATIONS:
        benign = sorted((r for r in rows if r["configuration"] == config and r["group"] == "benign"), key=lambda r: r["case"])
        labelled = [r for r in judges if r["configuration"] == config]
        suffix = [r for r in rows if r["configuration"] == config and r["group"] == "published_suffix"]
        passed = sum(review[config, r["case"]]["audited_task_pass"] for r in benign)
        harmful = [r["case"] for r in labelled if r["label"] == "harmful"]
        metrics = {"benign_success_rate": passed / len(benign),
                   "mean_benign_latency_s": statistics.mean(r["latency_s"] for r in benign),
                   "judge_harmful_rate": len(harmful) / len(labelled),
                   "published_suffix_lexical_bypass_rate": sum(r["lexicon_bypass"] for r in suffix) / len(suffix)}
        history = [{"step": i, "case": r["case"],
                    "benign_success_rate": sum(review[config, x["case"]]["audited_task_pass"] for x in benign[:i]) / i,
                    "mean_benign_latency_s": statistics.mean(x["latency_s"] for x in benign[:i])}
                   for i, r in enumerate(benign, 1)]
        alerts = evaluate_rules(metrics, policy)
        for alert in alerts:
            alert.update({"scope": "model", "configuration": config, "status": "pending_operator_review",
                          "control_status": "offline_flag_only_no_live_action"})
            if alert["metric"] == "judge_harmful_rate":
                first = next(i for i, r in enumerate(labelled, 1) if r["label"] == "harmful")
                alert.update({"detection_after_labelled_attack_cases": first, "evidence_case_ids": harmful})
            else:
                alert.update({"detection_after_benign_cases": len(benign),
                              "archived_inference_seconds_for_window": sum(r["latency_s"] for r in benign),
                              "evidence_case_ids": [r["case"] for r in benign]})
                if alert["metric"] == "benign_success_rate":
                    alert["evidence_case_ids"] = [r["case"] for r in benign if not review[config, r["case"]]["audited_task_pass"]]
        models[config] = {"metrics": metrics, "benign_passes": passed, "benign_n": len(benign),
                          "attack_n": len(labelled), "judge_harmful_count": len(harmful), "suffix_n": len(suffix),
                          "history": history, "alerts": alerts}
        all_alerts.extend(alerts)
    for config in ("baseline", "improved"):
        selected = [r for r in boundary if r["configuration"] == config]
        invalid = [r for r in selected if r["group"] != "legitimate"]
        valid = [r for r in selected if r["group"] == "legitimate"]
        metrics = {"invalid_forwarded_count": sum(r["forwarded"] for r in invalid),
                   "legitimate_forwarded_rate": sum(r["forwarded"] for r in valid) / len(valid)}
        alerts = evaluate_rules(metrics, policy)
        for alert in alerts:
            alert.update({"scope": "http_boundary_stub", "configuration": config,
                          "status": "pending_operator_review", "control_status": "offline_flag_only_no_live_action",
                          "evidence_case_ids": [r["case"] for r in invalid if r["forwarded"]],
                          "detection_after_invalid_cases": next(i for i, r in enumerate(invalid, 1) if r["forwarded"])})
        boundaries[config] = {"metrics": metrics, "invalid_n": len(invalid), "legitimate_n": len(valid), "alerts": alerts}
        all_alerts.extend(alerts)
    return {"mode": "retrospective_offline_replay", "policy_id": policy["policy_id"],
            "models": models, "boundary_stub": boundaries,
            "alerts": all_alerts, "alert_count": len(all_alerts),
            "deployment_decision": "NO-GO for public or unattended deployment; authorised local research may continue",
            "interpretation": "Guarded is a relative reference, not a certified safe operating state. Batch alarms evaluate at benign case 10. Harmful and boundary events flag on first occurrence. Replay is not a chronological production incident or an independent replication."}


def export_tables(destination, policy, summary):
    with (destination / "indicators.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = list(policy["indicators"][0])
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(policy["indicators"])
    with (destination / "comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = ["configuration", "benign_passes", "benign_n", *summary["models"]["baseline"]["metrics"], "alert_count"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for config, data in summary["models"].items():
            writer.writerow({"configuration": config, "benign_passes": data["benign_passes"], "benign_n": data["benign_n"],
                             **data["metrics"], "alert_count": len(data["alerts"])})
    (destination / "alerts.jsonl").write_text("".join(json.dumps(a, ensure_ascii=False) + "\n" for a in summary["alerts"]), encoding="utf-8")


def dashboard(destination, summary):
    escape = html.escape
    rows = []
    for config, data in summary["models"].items():
        m = data["metrics"]
        rows.append(f"<tr><td>{escape(config)}</td><td>{data['benign_passes']}/10</td><td>{m['mean_benign_latency_s']:.3f} s</td><td>{data['judge_harmful_count']}/30</td><td>{m['published_suffix_lexical_bypass_rate']:.0%}</td><td>{len(data['alerts'])}</td></tr>")
    alerts = "".join(f"<tr><td>{escape(a['scope'])}</td><td>{escape(a['configuration'])}</td><td>{escape(a['metric'])}</td><td>{a['value']:.4g}</td><td>{escape(a['severity'])}</td><td>{escape(a['response'])}</td></tr>" for a in summary["alerts"])
    document = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Assignment 4 Monitoring Evidence</title>
<style>body{font:16px/1.5 system-ui,sans-serif;color:#182b3a;background:#edf2f6;margin:0}main{max-width:1200px;margin:32px auto;background:white;padding:36px;border-radius:12px}h1,h2{color:#123f5b}table{width:100%;border-collapse:collapse;font-size:14px;margin:20px 0}td,th{padding:10px;text-align:left;border-bottom:1px solid #dbe3e9;vertical-align:top}th{background:#eaf2f6}.note{background:#fff3da;padding:16px;border-left:4px solid #b86c00}.decision{font-size:22px;font-weight:700;color:#9d2a2a}code{font-size:13px}a{color:#125b84}</style><main>
<h1>Local LLM Monitoring and Governance</h1><p>Assignment 4 | AISRA1301 | QAIRU</p>
<p class="note">Retrospective offline replay of archived measurements. Alerts are generated by the policy script and logged in MLflow. No live interception, automatic shutdown or independent model replication is claimed.</p>
<p class="decision">NO-GO for public or unattended deployment</p><h2>Model comparison</h2>
<table><thead><tr><th>Configuration</th><th>Audited benign success</th><th>Mean benign latency</th><th>Judge harmful</th><th>Suffix lexical bypass</th><th>Alerts</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table>
<p>Judge labels are uncalibrated screening. Lexical bypass is diagnostic only. Zero judge flags do not establish safety. Guarded is the relative reference. The original and audited benign scores differ; this experiment uses the audited rubric.</p>
<h2>Generated alerts</h2><table><thead><tr><th>Scope</th><th>Configuration</th><th>Indicator</th><th>Value</th><th>Severity</th><th>Required response</th></tr></thead><tbody>""" + alerts + """</tbody></table>
<h2>API boundary replay</h2><p>Historical proxy: 16/24 invalid requests forwarded. Improved proxy: 0/24. Both accepted 24/24 legitimate requests. These are archived stub HTTP tests, not model inference.</p>
<h2>Detection and oversight</h2><p>Quality and latency decisions occur at benign case 10. For Guarded + SmoothLLM that window contains 26.547 seconds of archived inference time, not a measured online alert delivery time. An operator must inspect alerts and approve configuration changes; no automatic fallback to the base model is permitted.</p>
<p><a href="summary.json">Full measurements</a> | <a href="indicators.csv">Indicators and thresholds</a> | <a href="alerts.jsonl">Alert evidence</a> | <a href="mlflow_runs.json">MLflow run export</a> | <a href="manifest.json">Input fingerprints</a></p></main></html>"""
    (destination / "dashboard.html").write_text(document, encoding="utf-8")


def track_mlflow(destination, summary, policy, manifest, store):
    import mlflow
    from mlflow.tracking import MlflowClient

    store.mkdir(parents=True, exist_ok=True)
    uri = "sqlite:///" + (store / "mlflow.db").resolve().as_posix()
    mlflow.set_tracking_uri(uri)
    client = MlflowClient()
    name = "Assignment4_Local_LLM_Governance"
    experiment = client.get_experiment_by_name(name)
    experiment_id = experiment.experiment_id if experiment else client.create_experiment(name, artifact_location=(store / "artifacts").resolve().as_uri())
    exported = []
    for scope, configurations in (("model", summary["models"]), ("http_boundary_stub", summary["boundary_stub"])):
        for config, data in configurations.items():
            with mlflow.start_run(experiment_id=experiment_id, run_name=f"{scope}-{config}") as run:
                mlflow.set_tags({"evaluation_mode": summary["mode"], "scope": scope, "configuration": config,
                                 "policy_id": policy["policy_id"],
                                 "live_controls": "not_integrated", "review_state": "pending_operator_review" if data["alerts"] else "no_threshold_alert"})
                mlflow.log_params({"policy_id": policy["policy_id"], "benign_window": policy["window_size"],
                                   "source_model_records_sha256": manifest["sha256"]["experiments/results/assignment3/model_results.jsonl"],
                                   **{r["metric"] + "_threshold": r["threshold"] for r in policy["indicators"]}})
                for point in data.get("history", []):
                    mlflow.log_metrics({key: point[key] for key in ("benign_success_rate", "mean_benign_latency_s")}, step=point["step"])
                mlflow.log_metrics({**data["metrics"], "alert_count": len(data["alerts"])}, step=10 if scope == "model" else 48)
                mlflow.log_dict({"scope": scope, "configuration": config, "alerts": data["alerts"]}, "alerts.json")
                for filename in ("summary.json", "indicators.csv", "comparison.csv", "alerts.jsonl", "manifest.json", "dashboard.html"):
                    mlflow.log_artifact(str(destination / filename), artifact_path="evidence")
                mlflow.log_dict(policy, "policy.json")
                run_id = run.info.run_id
            saved = client.get_run(run_id)
            history = {metric: [{"step": item.step, "value": item.value} for item in client.get_metric_history(run_id, metric)]
                       for metric in data["metrics"]}
            exported.append({"run_id": run_id, "experiment_id": experiment_id, "scope": scope, "configuration": config,
                             "status": saved.info.status, "metrics": saved.data.metrics, "tags": {k: v for k, v in saved.data.tags.items() if not k.startswith("mlflow.")},
                             "metric_history": history,
                             "artifact_paths": [a.path for a in client.list_artifacts(run_id)]})
    export = {"enabled": True, "tool": "MLflow", "version": mlflow.__version__, "backend": "local SQLite; artifacts local; no external service",
              "experiment_name": name, "runs": exported}
    write_json(destination / "mlflow_runs.json", export)
    # Include the verified API export in each actual run as a portable evidence artifact.
    for run in exported:
        client.log_artifact(run["run_id"], str(destination / "mlflow_runs.json"), artifact_path="evidence")
    return export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DESTINATION)
    parser.add_argument("--store", type=Path, default=ROOT / "tmp/assignment4/mlflow")
    parser.add_argument("--without-mlflow", action="store_true", help="Verify deterministic metrics only; this does not satisfy the tool application deliverable")
    args = parser.parse_args()
    started = time.perf_counter()
    policy = read(POLICY)
    summary = analyse(policy)
    args.output.mkdir(parents=True, exist_ok=True)
    inputs = [SOURCE / name for name in ("model_results.jsonl", "judge_labels.jsonl", "benign_review.json", "boundary_results.jsonl", "environment.json", "ollama_summary.json", "judge_summary.json", "boundary_summary.json")]
    inputs += [POLICY, Path(__file__), ROOT / "experiments/data/gcg_evaluation_cases.json", ROOT / "experiments/results/historical_model_summary.json"]
    manifest = {"sha256": {p.relative_to(ROOT).as_posix(): fingerprint(p) for p in inputs},
                "hash_convention": "Text inputs: SHA-256 after CRLF-to-LF normalisation for cross-platform Git checkouts. Benchmark JSON: exact bytes, preserved by .gitattributes -text.",
                "scope": "Public evidence and monitoring code fingerprints; no raw completions or personal data exported",
                "case_hash_matches_assignment3_environment": hashlib.sha256((ROOT / "experiments/data/gcg_evaluation_cases.json").read_bytes()).hexdigest() == read(SOURCE / "environment.json")["cases_sha256"]}
    if not manifest["case_hash_matches_assignment3_environment"]:
        raise ValueError("Test cases differ from the recorded Assignment 3 dataset")
    write_json(args.output / "summary.json", summary)
    write_json(args.output / "manifest.json", manifest)
    export_tables(args.output, policy, summary)
    dashboard(args.output, summary)
    if args.without_mlflow:
        write_json(args.output / "mlflow_runs.json", {"enabled": False, "reason": "Explicit metrics-only verification; no MLflow application claimed"})
    else:
        track_mlflow(args.output, summary, policy, manifest, args.store)
    write_json(args.output / "execution.json", {"completed_utc": datetime.now(timezone.utc).isoformat(),
               "python": platform.python_version(), "replay_and_export_wall_seconds": time.perf_counter() - started,
               "new_model_generations": 0, "offline_only": True, "mlflow_enabled": not args.without_mlflow})
    print(f"PASS: 120 model records, 90 judge labels, 96 stub HTTP records; {summary['alert_count']} alerts; MLflow={not args.without_mlflow}")


if __name__ == "__main__":
    main()
