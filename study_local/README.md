# study_local: the mechanism behind "answers the last request", on a local open-weight model

An addendum to the paper. Nothing outside this folder is changed. Results and what they do and do not support are in
[`RESULTS.md`](RESULTS.md); the plan, written with file hashes before the data, is [`PLAN_L.md`](PLAN_L.md).

| File | Contents |
|---|---|
| `PLAN_L.md` | Dated plan, predictions, hashes; Amendment L-1 records the model switch after the first model failed the gate. |
| `wordings.py` | The 49 rebuttal wordings and their labels (fixed before data); items come from `study/gen_g.py`, `gen_i.py`, `gen_q.py`. |
| `lm.py` | Model loading (plain Hugging Face `transformers`, CPU), prompt segmentation, cached-prefix forward passes, residual-stream hooks. |
| `run_l.py` | Runner, one sub-command per part. |
| `analyze_l.py` | All statistics (bootstrap over blocks within task, as in `study/analyze_g.py`), the probes, and `results_l_<model>.json`. |
| `figs_l.py`, `figs/` | Figures. |
| `paper_numbers.py`, `paper_numbers.json` | Every Study L number quoted in the paper, slides and speaker script, computed from the results files. |
| `runs/<model>/*.jsonl` | Raw per-item outputs: answers, logit differences, logit-lens values, patching and knockout results, sampled replies. |
| `runs/<model>/probe_weights.npy`, `probe_results.json` | Probe weights `[layer index, fold, width + 1]` (last entry is the bias) and accuracies. |
| `runs/<model>/steer_vec_L*.npy` | Steering vectors (ask minus tell, final position). |

## Reproduce

Needs Python 3.10+, 16 GB RAM and about 26 GB of disk. No GPU and no API key are used.

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

```bash
pip install transformers accelerate safetensors scikit-learn numpy matplotlib huggingface_hub
```

```bash
hf download mistralai/Ministral-3-8B-Instruct-2512-BF16 --exclude consolidated.safetensors --local-dir /root/models/ministral8b
```

```bash
hf download mistralai/Ministral-3-3B-Instruct-2512-BF16 --exclude consolidated.safetensors --local-dir /root/models/ministral3b
```

Model directories are set in `lm.MODELS`. The first model (it fails the gate, so only the bare question is run):

```bash
cd study_local && STUDY_L_MODEL=ministral3b python3 run_l.py bare
```

The second model, all parts in the order they were run (about fourteen hours on 4 CPU cores):

```bash
for p in bare gate wordings patch acts knock fidelity gencheck entropy; do STUDY_L_MODEL=ministral8b python3 run_l.py $p; done
```

```bash
STUDY_L_MODEL=ministral8b python3 run_l.py steer --layer 22
```

The post-hoc free-form check of question-form requests (Amendment L-3):

```bash
STUDY_L_MODEL=ministral8b python3 run_l.py qrfree
```

```bash
STUDY_L_MODEL=ministral8b python3 analyze_l.py && python3 figs_l.py && python3 paper_numbers.py
```

Every part appends to its `.jsonl` file and skips ids that are already there, so an interrupted run can be restarted.
`acts` writes the activation array (about 1.6 GB) to `/root/work/study_l/<model>/` (`STUDY_L_BIG`); it is not committed, and
`analyze_l.py --no-probe` runs everything that does not need it.

The 8B model does not fit in 16 GB in bf16, so its MLP matrices are held in 8-bit (`lm.QLinear`); on a machine with 24 GB or
more, set the third field of its entry in `lm.MODELS` to `False` to run the released weights unchanged.
