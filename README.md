# Certain Until Told Otherwise

Materials for the Apart Research AI x Epistemics sprint entry (Track 1):
*Certain Until Told Otherwise: Why Pushback Benchmarks Disagree*.

A model with good epistemics updates for reasons and holds against pressure. Published tests of this disagree: one reports
that current models almost never give up a well-anchored fact (Yang et al. 2026), another that models of the same generation
concede most correct answers (Basta et al. 2026). This study shows the tests measure two different things. It runs the
rebuttals of five published protocols, word for word, on three open-book tasks where the answer is on a four-line list in the
prompt, on 21 models, with the user wrong in half of the items and right in half. Scoring is by rule.
370,170 scored answers.

**The argument**

1. **The disagreement belongs to the tests.** On identical items the median share of right answers given up is
   0–3% under question-style rebuttals and 50% under a plain directive.
2. **The cause is the speech act.** With content held fixed, asking, asserting and telling cost medians of 3%, 32%
   and 48%. Telling exceeds asking reliably in 17 of 21 models.
3. **It is not persuasion.** Models were sure beforehand (18 of 21 unanimous and correct), a
   credential helped in 0 models, and a false claim about the list, which the model could re-read, still worked.
4. **Asking is enough.** Asking already corrected a median of 97% of wrong answers. Telling added a
   median of 0 points and cost 35 points of right answers.
5. **One account.** The model answers the last request, not the question. This also fits the effects of a closing sentence,
   reply format and repeated turns. It is offered as a conjecture.
6. **A trait, and avoidable.** Model order agrees across three unrelated tasks (rank correlation
   0.81–0.95); Claude Haiku 5.5, GPT-6 Luna Pro, GPT-6 Luna and GPT-5.6 Luna hold when told and still accept correct objections.
7. **Fixes.** A fact computed outside the model held the rate at 10% or less in 11 of
   14 models; the evidence-gated prompt of Basta et al. helped 5 and harmed 2.

**What transfers to other evaluations:** cross the instruments before comparing scores; put the deciding fact on the page;
score what the stronger probe buys in both directions; report two numbers, yielding when asked and the defence gap between
asked and told. The paper maps the results onto the four open problems of Track 1 (Table 1) and separates what is shown,
supported and conjectured (Table 5).

The lists are invented and short, the previous answer is scripted and each factorial cell has one wording, so results are for
these tasks and models. Every experiment was specified in writing, with file hashes, before its data was collected; predictions
that failed are listed in the paper (Table M3).

| Part | What it covers | Plan | Folder |
|---|---|---|---|
| **Pushback study (main text)** | published rebuttals on three open-book tasks, 21 models; factorial of speech act, naming and evidence; wordings, multi-turn, fixes; sampling and answer-token probabilities | `followups/stage7/PLAN_G.md`, `PLAN_H.md`, `PLAN_I.md`, `PLAN_J.md` | `followups/stage7/` |
| Decisions and plain confidence (Appendix L) | one-way permission rules: six kinds of request, quick and step-by-step answers, confidence, double-check | `benchmark_v2/PLAN.md` | `benchmark_v2/` |
| Internal signal and wording | answer-word probabilities; each part of the stricter sentence | `followups/stage2/PLAN_B.md` | `followups/stage2/`, `followups/open_model/` |
| Causes, fixes, re-asking and acting | word choice, rulebook size, hidden reasoning, acting with a tool, asking again | `followups/stage3/PLAN_C.md` | `followups/stage3/` |
| Confidence, pushback and citation | Brier rule and word scale; penalty for wrong answers; authority and claims about the list; the cited rule | `followups/stage4/PLAN_D.md` | `followups/stage4/` |
| Harness-side fixes | the model checks the claim first; a check outside the model attaches the result | `followups/stage5/PLAN_E.md` | `followups/stage5/` |
| Cross-task test | the same claim on a stock list and room bookings | `followups/stage6/PLAN_F.md` | `followups/stage6/` |

## What is here

- `paper/Epistemics_Sprint_Paper.pdf` is the report (`.docx` is a copy for pasting into the sprint template).
  `paper/ABSTRACT.txt` is the title and abstract for the submission form.
- `paper/` also holds the sources: `build_data.py` (measurement numbers for Appendix L), `figs.py` to `figs6.py` (figures;
  `figs6.py` draws Figures 2 to 5), `build_paper.py` and `render.js` (PDF).
- `slides/Epistemics_Sprint_Slides.pdf` is the five-slide deck and `slides/SCRIPT.md` the speaker script
  (rebuild with `build_slides.py`, `build_script.py` and `node render_slides.js slides.pdf` from `slides/`).
- `followups/stage7/` holds the pushback study: the four plans with dated amendments, generators (`gen_g.py`, `gen_h.py`,
  `gen_i.py`, `gen_q.py`; `gen_f.py` is the task generator they import), runners (`run_g.py`, `run_h.py`, `run_j.py`),
  analyses (`analyze_g.py` to `analyze_j.py`, `summary.py`, `totals.py`, `paper_stats.py`), results (`results_*.json`,
  `totals.json`) and every raw response (`raw_responses_stage7.zip`). Rebuttal wording and its source are in `gen_g.py`.
- `benchmark_v2/` and `followups/stage2/` to `followups/stage6/` hold the earlier experiments reported in Appendix L: each
  plan, item generator, runner, analysis, results and raw responses.
- `followups/open_model/` holds the scripts for a planned probe in an open-weight model. Both small models tried answered the
  task at chance, so the test was stopped at its preset gate and no probe result is claimed.

## Rebuilding

For the pushback study: unzip `followups/stage7/raw_responses_stage7.zip` inside a folder `v6/` holding the contents of
`followups/stage7/`, then run `python3 analyze_g.py`, `analyze_h.py`, `analyze_i.py`, `analyze_j.py`, `summary.py` and
`totals.py`. The paper and slide scripts expect `v6/` next to `paper/` and `slides/`, with `paper_stats.py` saved as
`paper/_s7.py`; the paper build also reads the earlier results (`v2/` to `v5/`, laid out from `benchmark_v2/` and
`followups/stage2/` to `stage6/` as described in their plans). Running the hosted experiments needs an OpenRouter key in
`OPENROUTER_API_KEY`; the raw-response archives contain model outputs and provider metadata only.
