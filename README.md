# Clean Re-asking

Materials for the Apart Research AI x Epistemics sprint entry (Track 1):
*Clean Re-asking: Why Pushback Benchmarks Disagree and How It Happens*.

Author: Daniel Foo, Nanyang Technological University (NTU), Singapore, with Apart Research.

**In one sentence:** models that can see the right answer and are sure of it will still drop it when a user states a
different answer instead of asking, which explains why two published pushback tests disagree; inside one open-weight model,
asking and telling take different routes, and a harness that re-asks the original question in a clean context, without the
model's previous answer, uses that difference as a defence.

When a user insists that a model is wrong, a good model changes its answer if the user is right and keeps it if the user is
wrong. Published tests of this disagree: one reports that current models almost never give up a well-anchored fact (Yang et
al. 2026), another that models of the same generation concede most correct answers (Basta et al. 2026). This study runs the
rebuttals of five published protocols, word for word, on three open-book tasks where the answer is on a four-line list in the
prompt, on 21 models, with the user wrong in half of the items and right in half. Scoring is by rule; no model grades
another. 370,170 scored answers.

**Four findings that run against intuition**

1. **The loudest rebuttal was the weakest.** An expert claim ending in capitals moved a median of 0% of
   right answers; a flat "Please change your answer" moved 50%. A credential helped in 0 models.
2. **A lie the model could check worked anyway.** Told that a line four lines above was missing from the list, the median
   model gave up 67% of right answers. The models were sure beforehand.
3. **Telling bought nothing.** Asking already corrected a median of 97% of wrong answers. Telling
   added a median of 0 points and cost 35 points of right answers.
4. **Two published tests that contradict each other are both right.** Their rebuttals, on the same items and models, give
   3% and 50%. The gap holds in each task, at temperature 1, after the same number
   of turns and in answer-token probabilities. Taken apart: a question that names the wrong answer costs
   0%, a statement or instruction that names it 48%,
   and either without the name 7%.

**The common cause.** With content held fixed, asking, asserting and telling cost medians of 3%, 32% and 48%;
telling exceeds asking reliably in 17 of 21 models. The answer is given up when the user states the other answer and does
not ask: most models answer the last request, not the question. Claude Haiku 5.5, GPT-6 Luna Pro, GPT-6 Luna and GPT-5.6 Luna do not, and still accept correct objections; model order agrees across three unrelated
tasks (rank correlation 0.81–0.95). A fact computed outside the model held the rate at 10% or
less in 11 of 14 models.

**Inside one model.** On local weights, Ministral 8B (one of the 21) shows the same pattern. Across 49 wordings, questions
gave up 2% of right answers and flat assertions and directives 82–84%. Activation patching places the switch at layers
19–20 of 34, where the difference leaves the rebuttal and reaches the answer, and a linear probe shows the right
answer is overwritten there rather than kept underneath. A steering vector did not fix it. Paper Section 4.8; data and code
in `study_local/`.

**What transfers to other evaluations:** cross the instruments before comparing scores; put the deciding fact on the page;
score what the stronger probe buys in both directions; report two numbers, yielding when asked and the defence gap between
asked and told. The paper maps the results onto the four open problems of Track 1 (Table 1).

The lists are invented and short, the previous answer is scripted and, across the 21 models, each factorial cell has one wording
(49 wordings were tested on one model), so results are for these tasks and models. Every experiment was specified in writing, with file hashes, before its data was collected; pre-specified checks
and their outcomes are listed in the paper (Table B3).

## What is here

| Path | Contents |
|---|---|
| `paper/Epistemics_Sprint_Paper.pdf` | The report: 8 pages of main text, 32 references, four appendices (20 pages in all). |
| `paper/Epistemics_Sprint_Paper.docx` | The same text for pasting into the sprint template. |
| `paper/ABSTRACT.txt` | Title and abstract for the submission form. |
| `paper/paper.html`, `paper/render.js` | The source the PDF is rendered from (`node render.js paper.pdf`). |
| `paper/figs6.py`, `paper/figs.py`, `paper/fig_mech.py`, `paper/figs/` | Figures 2 to 5, drawn from `study/results_main.json`, and Figure 6, drawn from `study_local/`. |
| `slides/Epistemics_Sprint_Slides.pdf` | Six-slide deck. |
| `slides/SCRIPT.md` | Speaker script, about four and a half minutes. |
| `slides/build_slides.py`, `slides/build_script.py`, `slides/render_slides.js` | Deck and script sources; every number is computed from `study/`. |
| `study/PLAN_G.md` to `PLAN_J.md` | The four plans, each written with file hashes before its data, with dated amendments. |
| `study/gen_*.py` | Item generators. Rebuttal wording and the paper each sentence comes from are in `gen_g.py`; the factorial is `gen_i.py` and `gen_q.py`; fixes and multi-turn runs are `gen_h.py`; `gen_f.py` builds the three tasks. |
| `study/run_*.py`, `study/launch_*.sh`, `study/lib/` | Runners, the commands used to launch them, and the request helpers they import. |
| `study/analyze_*.py`, `summary.py`, `totals.py`, `paper_stats.py` | Analysis: rates with bootstrap intervals, the cross-model summary, counts and spend, and the statistics quoted in the text. |
| `study/results_*.json`, `study/totals.json` | Results. `results_main.json` is the file the paper, slides and README read. |
| `study/raw_responses.zip` | Every raw model response with provider metadata. |
| `study_local/` | The local study of Section 4.8 (Ministral 8B on local weights): plan with hashes and amendments, wordings, runner, analysis, raw outputs, probe weights; results in `RESULTS.md`, commands in `README.md`. |

The plan files are the dated records as written during the sprint and are left unedited so that their hashes stay valid;
they refer to this study's parts as G, H, I and J.

## Rebuilding

```bash
cd study && unzip -q raw_responses.zip
```

```bash
python3 analyze_g.py && python3 analyze_h.py && python3 analyze_i.py && python3 analyze_j.py && python3 summary.py && python3 totals.py
```

```bash
cd ../paper && python3 figs6.py && python3 fig_mech.py
```

```bash
cd ../slides && python3 build_slides.py && python3 build_script.py && node render_slides.js slides.pdf
```

The analyses need only the Python standard library; the figures need matplotlib; the PDFs need Node with Playwright.
Re-running the hosted experiments needs an OpenRouter key in `OPENROUTER_API_KEY` (`python3 run_g.py --model <id> --cap <usd>`);
the archive contains model outputs and provider metadata only.
