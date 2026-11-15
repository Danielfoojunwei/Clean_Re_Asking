"""Part C3: add a direction to the residual stream and see whether decisions flip.
Direction = mean(activations | rule listed) - mean(activations | rule not listed) at one layer, learned on training rounds only.
Tested on held-out rounds against random directions of the same length."""
import argparse, json, sys, time
from pathlib import Path
import numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True); ap.add_argument("--gen", required=True); ap.add_argument("--dir", required=True)
ap.add_argument("--layer", type=int, required=True); ap.add_argument("--test-rounds", default="8,9,10,11")
ap.add_argument("--alphas", default="1,2"); ap.add_argument("--n-random", type=int, default=2); ap.add_argument("--max-items", type=int, default=320); ap.add_argument("--device", default="auto")
a = ap.parse_args()
sys.path.insert(0, a.gen)
import gen

import shards
D = Path(a.dir); meta, acts = shards.load(D, "E1")
test_rounds = {int(x) for x in a.test_rounds.split(",")}
rng = np.random.default_rng(20261114)
e1 = [i for i, m in enumerate(meta) if m["exp"] == "E1"]
tr = [i for i in e1 if meta[i]["round"] not in test_rounds]
X = np.asarray(acts[tr, a.layer], dtype=np.float32); y = np.array([meta[i]["gold"] == "EXECUTE" for i in tr])
direction = X[y].mean(0) - X[~y].mean(0)              # "the rule is listed" direction, in activation units
norm = float(np.linalg.norm(direction))
dirs = {"listed": direction}
for k in range(a.n_random):
    r = rng.standard_normal(direction.shape).astype(np.float32); dirs[f"random{k}"] = r / np.linalg.norm(r) * norm

# held-out items: every wrong refusal and wrong allow, plus an equal-sized random sample of correct answers of each kind
te = [i for i in e1 if meta[i]["round"] in test_rounds]
said = lambda m: m["logit"][0] > m["logit"][1]
groups = {"wrong_refusal": [i for i in te if meta[i]["gold"] == "EXECUTE" and not said(meta[i])],
          "wrong_allow": [i for i in te if meta[i]["gold"] == "DECLINE" and said(meta[i])],
          "right_refusal": [i for i in te if meta[i]["gold"] == "DECLINE" and not said(meta[i])],
          "right_allow": [i for i in te if meta[i]["gold"] == "EXECUTE" and said(meta[i])]}
per = a.max_items // 4
pick = {g: sorted(rng.choice(v, min(per, len(v)), replace=False).tolist()) for g, v in groups.items()}
items = {it["id"]: it for r in test_rounds for it in gen.items(r) if it["exp"] == "E1"}

torch.set_num_threads(4)
tok = AutoTokenizer.from_pretrained(a.model); DEV = a.device if a.device != "auto" else ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
DT = torch.float32 if DEV == "cpu" else torch.float16
model = AutoModelForCausalLM.from_pretrained(a.model, dtype=DT).to(DEV); model.eval()
ex, de = tok.encode("EXECUTE", add_special_tokens=False)[0], tok.encode("DECLINE", add_special_tokens=False)[0]
state = {"vec": None}
def hook(_m, _inp, out):
    if state["vec"] is None:
        return out
    h = out[0] if isinstance(out, tuple) else out
    h = h + state["vec"]
    return (h,) + tuple(out[1:]) if isinstance(out, tuple) else h
# hidden_states[L] is the output of block L-1
model.model.layers[a.layer - 1].register_forward_hook(hook)

conds = [("none", 0.0)] + [(n, s * float(al)) for n in dirs for al in a.alphas.split(",") for s in ((1, -1) if n == "listed" else (1,))]
rows, t0 = [], time.time()
with torch.no_grad():
    for g, idxs in pick.items():
        for n, i in enumerate(idxs):
            it = items[meta[i]["id"]]
            ids = tok.apply_chat_template(it["messages"], add_generation_prompt=True, return_tensors="pt")
            ids = (ids["input_ids"] if not torch.is_tensor(ids) else ids).to(DEV)
            for name, alpha in conds:
                state["vec"] = None if name == "none" else torch.tensor(dirs[name] * alpha, dtype=DT, device=DEV)
                lg = model(ids).logits[0, -1]
                rows.append({"id": meta[i]["id"], "group": g, "cell": meta[i]["cell"], "clause": meta[i]["clause"], "dir": name, "alpha": alpha,
                             "margin": float(lg[ex] - lg[de]), "top": tok.decode(int(lg.argmax()))})
            if n % 20 == 0:
                print(g, n, len(idxs), round(time.time() - t0), flush=True)
json.dump({"layer": a.layer, "norm": norm, "test_rounds": sorted(test_rounds), "picked": {g: len(v) for g, v in pick.items()},
           "available": {g: len(v) for g, v in groups.items()}, "rows": rows}, open(D / f"steer_L{a.layer}.json", "w"))
print("done", len(rows), round(time.time() - t0))
