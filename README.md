# Open-Book Epistemics

Materials for the Apart Research AI x Epistemics sprint entry (Track 1):
*Open-Book Epistemics: Checkable Pushback, Cited Evidence, and a Guard for Agent Harnesses*.

The study uses an open-book task (one-way permission rules, where the right answer can be read off a short list in the prompt
and no model grades another) to make two measurements we did not find in prior work:

1. **Checkable pushback.** The user's objection is a statement about the list, true or false by construction and worded the same
   both ways, so giving way can be scored as a correction or a mistake. This extends the two-sided scoring of Basta et al. (2026),
   whose objections the model cannot verify.
2. **The rule a model cites.** The line a model quotes for its decision is compared, by rule, with the decision itself.

It then tests what an agent harness can do about the first, and ends with six guidelines and a mock-up of a harness layer:

3. **Harness-side fix.** When the harness checks the claim against the list and attaches the result, right answers given up fall
   below 10% in six of eight models; asking the model to check for itself helps less. Two models still give way.
4. **Checks on stored responses.** Comparing the quoted line with the decision flags every wrong allow (266 of 266).

On the same items it replicates known results on stated confidence, stated penalties, answer probabilities and the mismatch
between written refusals and tool calls, and splits the accuracy score into the separate errors it combines. The rulebooks are
invented and short, so the results are for this task and the nine models tested. Every experiment was specified in writing, with
hashes, before its data was collected.

| Part | What it covers | Plan | Folder |
|---|---|---|---|
| Decisions and plain confidence | six kinds of request, quick and step-by-step answers, confidence, double-check, each step alone | `benchmark_v2/PLAN.md` | `benchmark_v2/` |
| Internal signal and wording | answer-word probabilities; each part of the stricter sentence | `followups/stage2/PLAN_B.md` | `followups/stage2/`, `followups/open_model/` |
| Causes, fixes, re-asking and acting | word choice, rulebook size, hidden reasoning, acting with a tool, asking again, stating the rule first, re-run on fresh names | `followups/stage3/PLAN_C.md` | `followups/stage3/` |
| Confidence, pushback and citation | confidence under a Brier rule and a word scale; a penalty for wrong answers; authority and true-or-false claims about the list; three turns of doubt; the cited rule; the requester's opinion; 150-token replies | `followups/stage4/PLAN_D.md` | `followups/stage4/` |
| Harness-side fixes | the model checks the claim first; the harness checks it and attaches the result; cite-and-compare and a probability gate evaluated on stored responses | `followups/stage5/PLAN_E.md` | `followups/stage5/` |

## What is here

- `paper/Epistemics_Sprint_Paper.pdf` is the report (`.docx` is a copy for pasting into the sprint template).
  `paper/ABSTRACT.txt` is the title and abstract for the submission form.
- `paper/` also holds the sources: `build_data.py` (measurement numbers), `figs.py`, `figs2.py`, `figs3.py` and `figs4.py` (figures),
  `build_paper.py` and `render.js` (PDF).
- `slides/Epistemics_Sprint_Slides.pdf` is the five-slide deck and `slides/SCRIPT.md` the speaker script
  (rebuild with `build_slides.py` and `node render_slides.js slides.pdf` from `slides/`).
- `benchmark_v2/` holds the base generator (`gen.py`), runner (`run.py`), analysis (`analyze.py`), the plan with its dated
  amendments, results tables, the public-dataset audit and every raw response (`raw_responses.zip`).
- `followups/stage2/` to `followups/stage5/` hold the later experiments: each plan, item generator, runner,
  analysis, results (`results_b.json` to `results_e.json`, `results_checks.json`) and raw responses. The generators import the base
  `gen.py` and never edit it. `stage4/long_format.py` is the 150-token re-run described in `PLAN_D.md` (Amendments D-1, D-2).
- `followups/open_model/` holds the scripts for the planned probe and steering test in an open-weight model, and the decisions of
  the two small models that were tried. Both answered the task at chance, so the test was stopped at its preset gate and no probe
  result is claimed (`PLAN_B.md`, Amendment B-2). `steer.py` was never run.

## Rebuilding

The scripts expect this layout: `v2/` (contents of `benchmark_v2/` with `raw_responses.zip` unzipped), `v3/` (contents of
`followups/stage2/` and `followups/stage3/` with both raw-response zips unzipped), `v4/` (contents of `followups/stage4/` and `followups/stage5/` with their zips unzipped), `paper/` and `slides/` side by side. Then, from
`v3/`: `python3 analyze_b.py` and `python3 analyze_c.py`; from `v4/`: `python3 analyze_d.py`, `python3 analyze_e.py`, `python3 offline_checks.py`; from `paper/`: `python3 build_data.py`, `python3 figs.py`,
`python3 figs2.py`, `python3 figs3.py`, `python3 figs4.py`, `python3 build_paper.py`, `node render.js paper.pdf`. Running the hosted experiments needs an OpenRouter key in
`OPENROUTER_API_KEY`; the raw-response archives contain model outputs and provider metadata only.
