"""Export reproducible metrics without publishing model completions or local paths."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "experiments/logs"
PUBLIC = ROOT / "experiments/results"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export():
    source = PRIVATE / "assignment3"
    target = PUBLIC / "assignment3"
    target.mkdir(parents=True, exist_ok=True)
    provenance = {}
    def record(path):
        provenance[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    # These files contain aggregate statistics, synthetic boundary cases or rubrics.
    for name in ["ollama_summary.json", "boundary_summary.json", "judge_summary.json",
                 "benign_review.json", "test_cases.json", "integration_smoke.json"]:
        path = source / name
        if path.exists():
            write_json(target / name, read_json(path))
            record(path)
    fields = ["configuration", "case", "group", "latency_s", "lexicon_bypass", "refusal_regex",
              "vote", "eval_count", "done_reason", "task_success"]
    for original, published, keys in [
        ("ollama_results.jsonl", "model_results.jsonl", fields),
        ("judge_results.jsonl", "judge_labels.jsonl", ["configuration", "case", "group", "judge_model", "label"]),
        ("boundary_results.jsonl", "boundary_results.jsonl", ["configuration", "case", "group", "status", "forwarded", "latency_ms", "system_roles_forwarded"]),
    ]:
        path = source / original
        if not path.exists():
            continue
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            clean = {key: row[key] for key in keys if key in row}
            if original == "ollama_results.jsonl":
                clean["response_sha256"] = hashlib.sha256(row["response"].encode()).hexdigest()
                clean["candidate_count"] = len(row.get("candidate_responses", []))
            rows.append(json.dumps(clean, ensure_ascii=False))
        (target / published).write_text("\n".join(rows) + "\n", encoding="utf-8")
        record(path)
    environment = source / "ollama_environment.json"
    if environment.exists():
        raw = read_json(environment)
        # Only models involved in the reported experiment; no inventory of unrelated models.
        model_names = {"vicuna:7b", "vicuna-guarded:latest", "qwen3.5:4b"}
        clean = {key: raw[key] for key in ["version", "python", "platform", "cases_sha256", "smoothllm_sha256"] if key in raw}
        clean["models"] = [{key: model[key] for key in ["name", "digest", "details"] if key in model}
                           for model in raw.get("tags", {}).get("models", []) if model.get("name") in model_names]
        write_json(target / "environment.json", clean)
        record(environment)
    historical = PRIVATE / "advbench_summary.json"
    if historical.exists():
        write_json(PUBLIC / "historical_model_summary.json", read_json(historical))
        record(historical)
    write_json(PUBLIC / "provenance.json", {
        "note": "SHA-256 of private source files. Original data remain local and are excluded from Git. Exports preserve scores, timing and identifiers; model completions, candidate texts and judge free-text reasons are omitted.",
        "source_sha256": provenance,
    })
    print(f"Public metrics exported to {PUBLIC.relative_to(ROOT)}")


if __name__ == "__main__":
    export()
