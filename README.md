# Told, Not Persuaded

Materials for the Apart Research AI x Epistemics sprint entry (Track 1):
*Told, Not Persuaded: What Pushback Tests Measure When the Answer Is on the Page*.

Published tests of how models respond to "you are wrong" disagree. One reports that current models almost never give up a
well-anchored fact (Yang et al. 2026); another that models of the same generation concede most correct answers (Basta et al.
2026). This study asks how much of that gap is the test. It takes the rebuttals of five published protocols, word for word,
puts them on three open-book tasks where the answer is read off a four-line list in the prompt, and runs them on
21 models, including models those papers tested. The user is wrong in half of the items and right in half.
Scoring is by rule; no model grades another.

**Findings** (370,170 rule-scored answers)

1. **Same items, different rates.** The median share of right answers given up was 0–3% under
   question-style rebuttals and 50% under a plain directive. Both published pictures reappear on one set
   of items and models.
2. **Asks, asserts, tells.** In a factorial that holds content fixed, the medians were 3%, 32% and 48%.
   Telling exceeded asking reliably in 17 of 21 models; Claude Haiku 5.5, GPT-6 Luna Pro, GPT-6 Luna and GPT-5.6 Luna stayed near zero.
   Naming the answer and adding evidence mattered less.
3. **Evidence adds little.** A stated credential raised the rate in 0 models. A false claim about the
   list, which a model could refute by re-reading it, was reliably weaker than an uncheckable source in 1 model
   and stronger in 5.
4. **The models were sure beforehand.** On the bare question, eight of eight samples were correct on every item in
   18 of 21 models.
5. **Test design moves the number.** Free-form replies and one closing sentence each changed rates by tens of points. Two
   faults found in our own runs are reported with how they were handled.
6. **Fixes.** A fact computed outside the model and attached to the turn held the rate at 10% or less in
   11 of 14 models. The evidence-gated prompt of Basta et al. helped
   5 and harmed 2.

**Recommendations for pushback tests:** report the speech act of each rebuttal and include a question and a directive; report
the reply format and any closing instruction; score both directions; include an open-book condition.

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
  `figs6.py` draws Figures 2 to 4), `build_paper.py` and `render.js` (PDF).
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
