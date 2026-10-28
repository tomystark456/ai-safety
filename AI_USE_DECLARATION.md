# AI Use Declaration

Course: AISRA1301 - AI Security and Risk Analysis, QAIRU.
Project: Assignment 3 - Safety Improvement of a Local LLM Assistant.

## Supplied Midterm provenance

The original declaration attributes React/Vite scaffolding, proxy/SPA serving and
initial documentation drafts to Claude via Claude Code. It attributes the original
model measurements to the student. This provenance is retained as supplied,
rather than a claim that Codex observed those historical runs.

## Assistance in this revision

OpenAI Codex assisted with reading the assignment, researching SmoothLLM in its
original paper and repository, implementing an independent Ollama adaptation,
server role/schema/size validation, human-AI safety notices, experimental scripts,
the report, presentation, Russian speaker notes, README and this declaration.

Codex executed actual local Ollama requests comparing vicuna:7b, vicuna-guarded and
vicuna-guarded with randomized smoothing. The test inputs reuse published AdvBench
and GCG fixtures. No attack suffix was generated, optimised or strengthened.
The implemented defence is an adaptation, not an exact reproduction or a formal
certification of the published algorithm. Its refusal voting detector differs
from the reference implementation.

Codex also ran paired HTTP tests with a recording stub upstream. Those tests
measure API enforcement and compatibility, not model safety. The model experiment
is kept separate, including per-case completions, configuration, input hashes,
refusal-proxy scores, simple benign-task checks and measured latency. A supplementary
Qwen model judge provides fallible automatic labels, not human-validated ground truth.

## Verification and limitations

The supplied historical model results remain distinct from the new Ollama runs.
Model answers may be truncated at the 96-token cap, affecting safety assessment.
The small fixed test suite cannot establish general robustness or statistical
significance. The report states these limitations and the safety/usability trade-offs.

Codex rendered the report and slides, checked the PPTX structure and built the
updated React front-end. These checks do not imply independent student review.
The student remains responsible for reviewing the materials and academic claims.

## Storage

The proxy does not persist chat messages. The full-page React chat stores browser
history in localStorage. Historical garak logs and new model evaluation logs contain
prompts and responses and should be access-controlled. The earlier blanket claim
that no text is stored is inaccurate across the whole project. New HTTP boundary
test cases contain harmless synthetic strings.

Ollama is the evaluated local runtime, not an authoring assistant.

The benign rubric was audited after the run to correct overly permissive initial
patterns; both scores are retained. The judge prompt was revised to separate
fragments from refusals, but some fragment mislabels remain. No attack or defence
parameters were tuned on the final results, and model answers were not regenerated.

For the GitHub preparation, Codex added the model selector, CI checks, a public
metrics exporter and validation of exported counts. Raw completions, candidate
texts, free-text judge reasons, temporary files and local credentials are excluded
from Git. Public metrics retain the recorded scores without regenerating answers.
