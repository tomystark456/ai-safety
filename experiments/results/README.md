# Published experimental evidence

Metrics from the local course experiment on 27 October 2026. Original model
completions stay in `experiments/logs/`, which is excluded from Git. Exporting
does not rerun the model or change the measured scores.

- `historical_model_summary.json`: supplied Midterm aggregates, separate from the new run.
- `assignment3/model_results.jsonl`: 120 selected-response records, timings,
  refusal-proxy scores, votes, completion fingerprints and candidate counts.
  Response text and candidate text are omitted.
- `assignment3/ollama_summary.json`: aggregate scores and timing for three configurations.
- `assignment3/judge_labels.jsonl`: 90 automatic labels; free-text reasons are omitted.
- `assignment3/judge_summary.json`: judge instructions, counts and limitations.
- `assignment3/benign_review.json`: original and audited task scores with the post-run rubric.
- `assignment3/boundary_results.jsonl`: 96 HTTP outcomes with a stub upstream.
- `assignment3/boundary_summary.json` and `test_cases.json`: boundary metrics and harmless inputs.
- `assignment3/environment.json`: relevant model digests and runtime metadata.
- `assignment3/integration_smoke.json`: a live guarded+smoothing API smoke check.
- `provenance.json`: SHA-256 fingerprints of the private source files.

Exact model evaluation inputs are in `../data/gcg_evaluation_cases.json`.
The lexical detector and local judge have the limitations documented in the report.

Verify counts without Ollama:

```bash
python experiments/check_public_results.py
python experiments/evaluate_smoothllm.py --summary
```

The second command recomputes aggregates from local raw results if available,
otherwise from published per-case metrics. It writes to the ignored local log
directory. Actual model evaluation is needed to regenerate completions. The judge
and rubric review scripts require those local raw answers.

Refresh public exports after a new local run:

```bash
python experiments/export_public_results.py
python experiments/check_public_results.py
```

The PDF and slides cite private log paths as their original sources. This directory
provides the public metrics counterparts; raw answers are absent from the repository.
