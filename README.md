# One Score, Three Failures

Materials for the Apart Research AI x Epistemics sprint entry (Track 1):
*One Score, Three Failures: What Accuracy on One-Way Authorization Rules Hides*.

The study shows that one accuracy score on one-way permission rules hides three failures, and for each failure it measures the
size, finds what drives it and tests a fix. Every experiment was specified in writing, with hashes, before its data was collected.

| Part | What it covers | Plan | Folder |
|---|---|---|---|
| Measuring the failures | six kinds of request, quick and step-by-step answers, confidence, double-check, each step alone | `benchmark_v2/PLAN.md` | `benchmark_v2/` |
| Causes and fixes: signal and wording | answer-word probabilities; each part of the stricter sentence | `followups/stage2/PLAN_B.md` | `followups/stage2/`, `followups/open_model/` |
| Causes and fixes: seven experiments | word choice, rulebook size, hidden reasoning, acting with a tool, asking again, stating the rule first, re-run on fresh names | `followups/stage3/PLAN_C.md` | `followups/stage3/` |

## What is here

- `paper/One_Score_Three_Failures.pdf` is the report. `paper/ABSTRACT.txt` is the abstract for the submission form.
- `paper/` also holds the sources: `build_data.py` (measurement numbers), `figs.py` and `figs2.py` (figures), `build_paper.py` and
  `render.js` (PDF).
- `slides/One_Score_Three_Failures_slides.pdf` is the five-slide deck and `slides/SCRIPT.md` the speaker script
  (rebuild with `build_slides.py` and `node render_slides.js slides.pdf` from `slides/`).
- `benchmark_v2/` holds the base generator (`gen.py`), runner (`run.py`), analysis (`analyze.py`), the plan with its dated
  amendments, results tables, the public-dataset audit and every raw response (`raw_responses.zip`).
- `followups/stage2/` and `followups/stage3/` hold the cause-and-fix experiments: each plan, item generator, runner, analysis, results
  (`results_b.json`, `results_c.json`) and raw responses. The generators import the base `gen.py` and never edit it.
- `followups/open_model/` holds the scripts for the planned probe and steering test in an open-weight model, and the decisions of
  the two small models that were tried. Both answered the task at chance, so the test was stopped at its preset gate and no probe
  result is claimed (`PLAN_B.md`, Amendment B-2). `steer.py` was never run.

## Rebuilding

The scripts expect this layout: `v2/` (contents of `benchmark_v2/` with `raw_responses.zip` unzipped), `v3/` (contents of
`followups/stage2/` and `followups/stage3/` with both raw-response zips unzipped), `paper/` and `slides/` side by side. Then, from
`v3/`: `python3 analyze_b.py` and `python3 analyze_c.py`; from `paper/`: `python3 build_data.py`, `python3 figs.py`,
`python3 figs2.py`, `python3 build_paper.py`, `node render.js paper.pdf`. Running the hosted experiments needs an OpenRouter key in
`OPENROUTER_API_KEY`; the raw-response archives contain model outputs and provider metadata only.
