# Checking What Models Say About Their Answers

Materials for the Apart Research AI x Epistemics sprint entry (Track 1):
*Checking What Models Say About Their Answers: Confidence, Pushback and Action on Rules with Exact Answers*.

The study measures, on the same exactly-scored items, five signals people use to judge a model's answer: its stated confidence
(asked four ways), its answer probabilities, how it responds to true and false pushback, which rule it cites, and what it does
when given a tool. It also splits the accuracy score into the separate errors it combines. The items are one-way permission
rules, where every answer is exactly right or wrong and no model grades another. The rulebooks are invented and short, so the
results are for this task and the nine models tested. Every experiment was specified in writing, with hashes, before its data
was collected.

| Part | What it covers | Plan | Folder |
|---|---|---|---|
| Decisions and plain confidence | six kinds of request, quick and step-by-step answers, confidence, double-check, each step alone | `benchmark_v2/PLAN.md` | `benchmark_v2/` |
| Internal signal and wording | answer-word probabilities; each part of the stricter sentence | `followups/stage2/PLAN_B.md` | `followups/stage2/`, `followups/open_model/` |
| Causes, fixes, re-asking and acting | word choice, rulebook size, hidden reasoning, acting with a tool, asking again, stating the rule first, re-run on fresh names | `followups/stage3/PLAN_C.md` | `followups/stage3/` |
| Confidence, pushback and citation | confidence under a Brier rule and a word scale; a penalty for wrong answers; authority and true-or-false claims about the list; three turns of doubt; the cited rule; the requester's opinion; 150-token replies | `followups/stage4/PLAN_D.md` | `followups/stage4/` |

## What is here

- `paper/Checking_What_Models_Say.pdf` is the report (`.docx` is a copy for pasting into the sprint template).
  `paper/ABSTRACT.txt` is the title and abstract for the submission form.
- `paper/` also holds the sources: `build_data.py` (measurement numbers), `figs.py`, `figs2.py` and `figs3.py` (figures),
  `build_paper.py` and `render.js` (PDF).
- `slides/Checking_What_Models_Say_slides.pdf` is the five-slide deck and `slides/SCRIPT.md` the speaker script
  (rebuild with `build_slides.py` and `node render_slides.js slides.pdf` from `slides/`).
- `benchmark_v2/` holds the base generator (`gen.py`), runner (`run.py`), analysis (`analyze.py`), the plan with its dated
  amendments, results tables, the public-dataset audit and every raw response (`raw_responses.zip`).
- `followups/stage2/`, `followups/stage3/` and `followups/stage4/` hold the later experiments: each plan, item generator, runner,
  analysis, results (`results_b.json`, `results_c.json`, `results_d.json`) and raw responses. The generators import the base
  `gen.py` and never edit it. `stage4/long_format.py` is the 150-token re-run described in `PLAN_D.md` (Amendments D-1, D-2).
- `followups/open_model/` holds the scripts for the planned probe and steering test in an open-weight model, and the decisions of
  the two small models that were tried. Both answered the task at chance, so the test was stopped at its preset gate and no probe
  result is claimed (`PLAN_B.md`, Amendment B-2). `steer.py` was never run.

## Rebuilding

The scripts expect this layout: `v2/` (contents of `benchmark_v2/` with `raw_responses.zip` unzipped), `v3/` (contents of
`followups/stage2/` and `followups/stage3/` with both raw-response zips unzipped), `v4/` (contents of `followups/stage4/` with its zip unzipped), `paper/` and `slides/` side by side. Then, from
`v3/`: `python3 analyze_b.py` and `python3 analyze_c.py`; from `v4/`: `python3 analyze_d.py`; from `paper/`: `python3 build_data.py`, `python3 figs.py`,
`python3 figs2.py`, `python3 figs3.py`, `python3 build_paper.py`, `node render.js paper.pdf`. Running the hosted experiments needs an OpenRouter key in
`OPENROUTER_API_KEY`; the raw-response archives contain model outputs and provider metadata only.
