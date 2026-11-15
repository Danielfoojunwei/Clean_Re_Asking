# When the Speaker Beats the Page

Materials for the Apart Research AI x Epistemics sprint entry (Track 1):
*When the Speaker Beats the Page: An Open-Book Test of AI Epistemics*.

When a model gives way to "you are wrong", did it not know, or did it defer? The study puts the answer on the page. In an
open-book task the right answer can be read off a four-line list in the prompt, and the pushback is a statement about that
list, true or false by construction and worded the same both ways. No model grades another.

**Findings**

1. **Checkable pushback.** Six of eight models gave up 57–99% of right answers on permission rules to a false claim about a list
   they could read. This extends the two-sided scoring of Basta et al. (2026), whose objections the model cannot verify.
2. **The rule a model cites.** Two models, asked for the rule behind a wrong refusal, quoted the rule that permits the request.
3. **It is not about permissions.** On two unrelated tasks (a stock list, room bookings) every model read the list correctly
   100% of the time, and the same models then gave way; the ordering of models matched the permission task (rank correlation
   0.73 and 0.62). Asked to re-read the list while being contradicted, six models reported listed lines as missing.
4. **Where it fails.** When a fact computed outside the model was attached, most models held; asking the model to re-read helped
   less.

**What the paper proposes**

- A principle, stated as a claim to test: *access is not use*. That a model can read a fact does not predict that it will use
  or keep it.
- A method, the *open-book control*: put the deciding fact on the page, confirm the model reads it, apply the manipulation with
  its truth set by construction, and report each step on the same items.

Known results on stated confidence, penalties, answer probabilities and tool calls are replicated on the same items and
credited. The lists are invented and short and each pushback has one wording, so results are for these tasks and the nine
models tested. Every experiment was specified in writing, with hashes, before its data was collected.

| Part | What it covers | Plan | Folder |
|---|---|---|---|
| Decisions and plain confidence | six kinds of request, quick and step-by-step answers, confidence, double-check, each step alone | `benchmark_v2/PLAN.md` | `benchmark_v2/` |
| Internal signal and wording | answer-word probabilities; each part of the stricter sentence | `followups/stage2/PLAN_B.md` | `followups/stage2/`, `followups/open_model/` |
| Causes, fixes, re-asking and acting | word choice, rulebook size, hidden reasoning, acting with a tool, asking again, stating the rule first, re-run on fresh names | `followups/stage3/PLAN_C.md` | `followups/stage3/` |
| Confidence, pushback and citation | confidence under a Brier rule and a word scale; a penalty for wrong answers; authority and true-or-false claims about the list; three turns of doubt; the cited rule; the requester's opinion; 150-token replies | `followups/stage4/PLAN_D.md` | `followups/stage4/` |
| Harness-side fixes | the model checks the claim first; the harness checks it and attaches the result; cite-and-compare and a probability gate evaluated on stored responses | `followups/stage5/PLAN_E.md` | `followups/stage5/` |
| Cross-task test | the same claim on a stock list and room bookings; re-reading under contradiction | `followups/stage6/PLAN_F.md` | `followups/stage6/` |

## What is here

- `paper/Epistemics_Sprint_Paper.pdf` is the report (`.docx` is a copy for pasting into the sprint template).
  `paper/ABSTRACT.txt` is the title and abstract for the submission form.
- `paper/` also holds the sources: `build_data.py` (measurement numbers), `figs.py` and `figs2.py` to `figs5.py` (figures),
  `build_paper.py` and `render.js` (PDF).
- `slides/Epistemics_Sprint_Slides.pdf` is the five-slide deck and `slides/SCRIPT.md` the speaker script
  (rebuild with `build_slides.py` and `node render_slides.js slides.pdf` from `slides/`).
- `benchmark_v2/` holds the base generator (`gen.py`), runner (`run.py`), analysis (`analyze.py`), the plan with its dated
  amendments, results tables, the public-dataset audit and every raw response (`raw_responses.zip`).
- `followups/stage2/` to `followups/stage6/` hold the later experiments: each plan, item generator, runner,
  analysis, results (`results_b.json` to `results_f.json`, `results_checks.json`, `results_ladder.json`) and raw responses. The generators import the base
  `gen.py` and never edit it. `stage4/long_format.py` is the 150-token re-run described in `PLAN_D.md` (Amendments D-1, D-2).
- `followups/open_model/` holds the scripts for the planned probe and steering test in an open-weight model, and the decisions of
  the two small models that were tried. Both answered the task at chance, so the test was stopped at its preset gate and no probe
  result is claimed (`PLAN_B.md`, Amendment B-2). `steer.py` was never run.

## Rebuilding

The scripts expect this layout: `v2/` (contents of `benchmark_v2/` with `raw_responses.zip` unzipped), `v3/` (contents of
`followups/stage2/` and `followups/stage3/` with both raw-response zips unzipped), `v4/` (contents of `followups/stage4/` and `followups/stage5/` with their zips unzipped), `v5/` (contents of `followups/stage6/` with its zip unzipped), `paper/` and `slides/` side by side. Then, from
`v3/`: `python3 analyze_b.py` and `python3 analyze_c.py`; from `v4/`: `python3 analyze_d.py`, `python3 analyze_e.py`, `python3 offline_checks.py`; from `v5/`: `python3 analyze_f.py`, `python3 ladder.py`; from `paper/`: `python3 build_data.py`, `python3 figs.py`,
`python3 figs2.py`, `python3 figs3.py`, `python3 figs4.py`, `python3 figs5.py`, `python3 build_paper.py`, `node render.js paper.pdf`. Running the hosted experiments needs an OpenRouter key in
`OPENROUTER_API_KEY`; the raw-response archives contain model outputs and provider metadata only.
