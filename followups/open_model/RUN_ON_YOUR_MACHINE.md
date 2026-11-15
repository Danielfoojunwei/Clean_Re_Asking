# Running the probe on your own machine

Needs Python 3.10+, about 20 GB of free memory for a 9-billion-parameter model in half precision (a GPU with 24 GB, or an Apple
Silicon Mac with 32 GB), and the model's weights from Hugging Face.

```bash
pip install torch transformers scikit-learn numpy
```

Run from this folder. `<model>` is the Hugging Face id of the open-weight model (ideally the same Qwen model used in the study).

```bash
python3 extract.py --model <model> --gen ../../benchmark_v2 --out out --rounds 0-0 --exps E1
```

That first round is the gate: check the printed accuracy with `probe.py` before spending more time. If the model is above 60%
correct, run the rest (it resumes round by round):

```bash
python3 extract.py --model <model> --gen ../../benchmark_v2 --out out --rounds 0-11 --exps E1
```

```bash
python3 extract.py --model <model> --gen ../../benchmark_v2 --out out --rounds 0-3 --exps E7
```

```bash
python3 probe.py --dir out
```

`probe.py` writes `out/probe_results.json` and names the best layer. Use that layer for the steering test:

```bash
python3 steer.py --model <model> --gen ../../benchmark_v2 --dir out --layer <best layer>
```

Send back `out/probe_results.json`, `out/steer_L*.json` and the `out/meta_r*.json` files (not the large `acts_*.npy` files).
