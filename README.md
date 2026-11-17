# Clean Re-asking: Why Pushback Benchmarks Disagree and How It Happens

Daniel Foo, Nanyang Technological University (NTU), Singapore, with Apart Research.
Entry to the Apart Research AI x Epistemics Research Sprint, Track 1 (Model Epistemics and Decision-Making Evals).

**In one sentence:** language models that can see the right answer and are sure of it still give it up when a user *tells*
them they are wrong, but not when the user *asks*; that is why two published pushback benchmarks disagree, and inside one
open-weight model it comes from two different internal routes, which a harness can use by re-asking the original question in
a clean context.

## The study in brief

When a user insists that a model is wrong, a good model changes its answer if the user is right and keeps it if the user is
wrong. Published tests of this disagree: one reports that current models almost never give up a well-anchored fact (Yang et
al. 2026), another that models of the same generation concede most correct answers (Basta et al. 2026). We ran the rebuttals
of five published protocols, word for word, on three open-book tasks where the answer sits on a four-line list in the prompt,
on 21 models through the API, with the user wrong in half of the items and right in half. Scoring is by rule; no model grades
another. We then opened one of the models, Ministral 8B, on local weights.

**Four findings that run against intuition (21 models)**

1. **The loudest rebuttal was the weakest.** An expert claim ending in capitals moved a median of 0% of right answers; a flat
   "Please change your answer" moved 50%. A credential or a cited source added nothing.
2. **A lie the model could check worked anyway.** Told that a line four lines above was missing from the list, the median
   model gave up 67% of right answers, as many as for a claim it could not check. The models were sure beforehand.
3. **Telling bought nothing.** Asking already corrected a median of 97% of wrong answers; telling added 0 points of
   corrections and cost 35 points of right answers.
4. **Two published tests that contradict each other are both right.** On the same items and models their rebuttals give 3%
   and 50%: one asks, the other tells.

**The root cause: form, not evidence.** With content held fixed, asking, asserting and telling cost medians of 3%, 32% and
48% of right answers; telling exceeds asking reliably in 17 of 21 models. Four models (Claude Haiku 5.5, GPT-6 Luna Pro,
GPT-6 Luna, GPT-5.6 Luna) hold when told and still accept correct objections, so the behaviour is avoidable.

**How it happens, inside Ministral 8B (local weights).** Across 49 wordings labelled in advance, questions gave up 2% of right
answers and flat assertions and directives 82–84%. Attention knockout shows two routes: a question is answered again from
what the model computed at the original question, not by re-reading the list; a statement or instruction is carried out on
the model's own previous answer (hiding it restores 38–48 points of right answers). Activation patching places the hand-over
from the rebuttal tokens to the answer position at layers 19–20 of 34, and a linear probe shows the right answer there is
overwritten rather than kept underneath; the reply then presents the user's answer as a reading of the list. Recent work
reports the same signature for opinion sycophancy, persuasion, cue-following and prompt injection.

**The clean re-ask.** From the mechanism: a harness should not relay an objection as a turn to obey, but ask the original
question again in a clean context, without the model's previous answer, with the user's claim given as a third party's, and
change the answer only if that re-ask changes it. Pre-registered on Ministral 8B (96 items per direction): right answers given
up fell from 86% (assertion) and 97% (directive) to 0%, while 99% of correct objections were still accepted. Re-asking with
the previous answer kept fixed the directive (4%) but not the assertion (46%).

**What transfers:** report two numbers for any pushback test, yielding when asked and the defence gap between asked and
told, on the same items and in both directions.

**Scope:** short invented lists with a scripted previous answer; one wording per factorial cell across 21 models; the
mechanism and the clean re-ask come from one 8B model whose MLP weights were held in 8 bits. Every experiment was specified
in writing, with file hashes, before its data was collected.

## What is here

| Path | Contents |
|---|---|
| `paper/Epistemics_Sprint_Paper.pdf` | The report: 8 pages of main text, 42 references, five appendices (22 pages in all). Appendix E lists every experimental setting: items and how they are generated, seeds, sample sizes, decoding, scoring, bootstrap, baselines and controls. |
| `paper/Epistemics_Sprint_Paper.docx` | The same text for pasting into the sprint template. |
| `paper/ABSTRACT.txt` | Title and abstract for the submission form. |
| `paper/paper.html`, `paper/render.js` | The source the PDF is rendered from (`node render.js paper.pdf`). |
| `paper/figs6.py`, `paper/figs.py`, `paper/fig_mech.py`, `paper/figs/` | Figures 2–4 and B1, drawn from `study/results_main.json`, and Figure 5, drawn from `study_local/`. |
| `slides/Epistemics_Sprint_Slides.pdf`, `slides/Epistemics_Sprint_Slides.pptx` | Six-slide deck, as PDF and as PowerPoint (slides as images, the script in the speaker notes). |
| `slides/SCRIPT.md` | Speaker script, about four minutes (under five spoken slowly). |
| `slides/build_slides.py`, `slides/build_script.py`, `slides/render_slides.js`, `slides/render_pngs.js`, `slides/build_pptx.py` | Deck, script and PowerPoint sources; every number is computed from `study/` and `study_local/`. |
| `poster/Clean_Reasking_Poster.pdf`, `poster/Clean_Reasking_Poster.png` | A0 landscape poster; `poster/build_poster.py` and `poster/render_poster.js` rebuild it, with every number computed from `study/` and `study_local/`. |
| `study/` | The 21-model API study: item generators (`gen_*.py`), runners and launch commands (`run_*.py`, `launch_*.sh`, `lib/`), analysis (`analyze_*.py`, `summary.py`, `totals.py`, `paper_stats.py`), results (`results_*.json`, `totals.json`), every raw response (`raw_responses.zip`), and the four plans written before their data (`PLAN_G.md` to `PLAN_J.md`). |
| `study_local/` | The local study (Ministral 8B; paper Sections 4.6 and 5): plan with hashes and six dated amendments (`PLAN_L.md`), the 49 wordings (`wordings.py`), model access and hooks (`lm.py`), runner (`run_l.py`), analysis (`analyze_l.py`), the numbers quoted in the paper and slides (`paper_numbers.py`), raw outputs, probe weights and steering vectors (`runs/`), and the full write-up (`RESULTS.md`, `README.md`). |

The plan files are the dated records as written and are left unedited so that their hashes stay valid; the API study's plans
refer to its parts as G, H, I and J, and the local study's plan is L.

## Rebuilding

API study (the analyses need only the Python standard library):

```bash
cd study && unzip -q raw_responses.zip
```

```bash
python3 analyze_g.py && python3 analyze_h.py && python3 analyze_i.py && python3 analyze_j.py && python3 summary.py && python3 totals.py
```

Local study (needs about 16 GB of RAM and the model weights; see `study_local/README.md` for downloads and each part):

```bash
cd study_local && STUDY_L_MODEL=ministral8b python3 analyze_l.py && python3 paper_numbers.py
```

Figures, paper, slides and PowerPoint (figures need matplotlib; the PDFs need Node with Playwright; the PowerPoint needs
python-pptx):

```bash
cd paper && python3 figs6.py && python3 fig_mech.py && node render.js Epistemics_Sprint_Paper.pdf
```

```bash
cd slides && python3 build_slides.py && python3 build_script.py && node render_slides.js Epistemics_Sprint_Slides.pdf && node render_pngs.js png && python3 build_pptx.py png
```

```bash
cd poster && python3 build_poster.py && node render_poster.js
```

Re-running the hosted experiments needs an OpenRouter key in `OPENROUTER_API_KEY` (`python3 run_g.py --model <id> --cap <usd>`);
the archive contains model outputs and provider metadata only. Total API spend for the reported experiments was USD 26.91;
the local study used no API.

## Citation

Foo, D. (2026). *Clean Re-asking: Why Pushback Benchmarks Disagree and How It Happens.* Apart Research AI x Epistemics
Research Sprint. https://github.com/Danielfoojunwei/Clean_Re_Asking
