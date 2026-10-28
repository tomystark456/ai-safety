# Evaluation fixtures and attribution

`gcg_evaluation_cases.json` freezes the 40 inputs used in the new experiment:
10 direct goals, the same goals with a published suffix, 10 cached-GCG inputs
and 10 benign controls. Source URLs and the suffix fingerprint are in the fixture.
No suffix was generated or optimised in this project.

Sources:

- AdvBench goals: [llm-attacks/llm-attacks](https://github.com/llm-attacks/llm-attacks),
  `data/advbench/harmful_behaviors.csv`, first 10 goals in the downloaded snapshot.
- Published suffix: [the authors' project page](https://llm-attacks.org/), first static example.
- Cached-GCG inputs: first 10 unique inputs in the supplied garak baseline log.
  These use two underlying goals with different suffixes.
- `refusal_lexicon.json`: 156 substrings from NVIDIA garak 0.17.0's
  `MitigationBypass` detector. Its Apache-2.0 terms are retained in `LICENSE.garak.txt`.

The project evaluates published fixtures on authorised local models. Generated
harmful instructions are excluded from the public results. Model weights are
installed separately with Ollama and remain subject to their upstream terms.

The full optional upstream CSV and raw historical log are not committed. The frozen
fixture is sufficient to repeat the new evaluation. `--prepare` is a maintenance
command requiring the original local source files.
