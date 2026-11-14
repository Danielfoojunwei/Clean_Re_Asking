# One Score, Three Failures

Materials for the Apart Research AI x Epistemics sprint entry (Track 1):
*One Score, Three Failures: What Accuracy on One-Way Authorization Rules Hides*.

- `paper/One_Score_Three_Failures.pdf` is the report. `paper/ABSTRACT.txt` is the abstract for the submission form.
- `paper/` also holds the sources: `build_data.py` (numbers), `figs.py` (figures), `build_paper.py` and `render.js` (PDF).
- `benchmark_v2/` holds the benchmark generator (`gen.py`), runner (`run.py`), analysis (`analyze.py`), the pre-registered
  plan with its dated amendments (`PLAN.md`), results tables, the public-dataset audit and every raw response
  (`raw_responses.zip`).

To rebuild the report: place the `benchmark_v2` scripts and the unzipped `raw_responses.zip` in a `v2/` folder next to
`paper/`, then run `build_data.py`, `figs.py`, `build_paper.py` and `node render.js paper.pdf` from `paper/`.
