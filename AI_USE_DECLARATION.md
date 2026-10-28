# AI Use Declaration

**Course:** AISRA1301 — AI Security and Risk Analysis, QAIRU
**Project:** Assignment 3 — Improvement and Experimental Validation

## AI tools used
- **Claude (Anthropic) via Claude Code** — code scaffolding and documentation drafting.
- **Ollama** is a runtime for the evaluated models, not an authoring assistant.

## Purpose of use
- Convert the earlier static news mock-up into a modern **React (Vite)** front-end
  (components, streaming chat hook, CSS).
- Wire the local server to serve the React build and proxy chat requests to Ollama.
- Draft the README, the technical report and this declaration.

## Substantive generated contributions
- `site/web/` React application: `App.jsx`, components (`Header`, `Card`, `Reader`,
  `Chat`), the `useChat` streaming hook, and `index.css`.
- SPA-serving and fallback logic added to `site/server.py`.
- First drafts of `README.md`, `report/` documents and this file.

## What the author did NOT delegate to AI
- The security experiment itself (garak runs, `Modelfile.guarded`, the AdvBench and
  suffix measurements in `experiments/logs/`) was designed and executed by the student.
- Generation or application of jailbreak suffixes to harmful prompts was **performed by
  the student**, not by the AI assistant; the assistant declined to produce attack
  payloads.

## Verification and testing performed by the student
- Ran `npm run build` — the React app compiles with no errors.
- Started `server.py` and verified: index served (`200`), static images served (`200`),
  SPA fallback returns `index.html` for unknown routes, `/api/chat` proxied to Ollama.
- Captured a headless-Chrome screenshot to confirm the layout renders correctly.
- Confirmed the reported experimental numbers against
  `experiments/logs/advbench_summary.json` and the garak report files; no figure in the
  report is invented — all trace back to the logs.

## Note on correctness and security review
- The chat proxy stores no prompts or responses and forwards only sanitized, length-capped
  message history. The front-end treats model output as text (no HTML injection from the
  stream). These properties were checked by reading the code and exercising the endpoints.
