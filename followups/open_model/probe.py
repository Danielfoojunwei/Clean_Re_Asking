"""Part C1/C2: linear probes on last-token activations, tested on held-out name sets (grouped by round)."""
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); a = ap.parse_args()
D = Path(a.dir)
import shards
M, acts = shards.load(D, "E1")
rng = np.random.default_rng(20261114)
e1 = np.arange(len(M))
rounds = np.array([m["round"] for m in M]); folds = sorted(set(rounds))
gold = np.array([m["gold"] == "EXECUTE" for m in M])                      # the exact rule is listed
said = np.array([m["logit"][0] > m["logit"][1] for m in M])               # model says EXECUTE
margin = np.array([m["logit"][0] - m["logit"][1] for m in M])
correct = said == gold
cell = np.array([m["cell"] for m in M]); clause = np.array([m["clause"] for m in M])
L = acts.shape[1]
STEP = 2 if len(folds) >= 6 else 1


def cv_scores(X, y, shuffle=False):
    """Out-of-fold probe scores; folds are pairs of rounds, so every test name is unseen in training."""
    out = np.zeros(len(y))
    for k in range(0, len(folds), STEP):
        te = np.isin(rounds, folds[k:k + STEP]); tr = ~te
        ytr = y[tr].copy()
        if shuffle:
            rng.shuffle(ytr)
        sc = StandardScaler().fit(X[tr])
        clf = RidgeClassifier(alpha=1000.0).fit(sc.transform(X[tr]), ytr)  # linear probe, closed form
        out[te] = clf.decision_function(sc.transform(X[te]))
    return out


def boot(fn, B=1000):
    """95% interval over name sets (round x naming style)."""
    surf = np.array([m["surface"] for m in M]); keys = sorted({(r, s) for r, s in zip(rounds, surf)})
    idx = {k: np.where((rounds == k[0]) & (surf == k[1]))[0] for k in keys}
    vals = []
    for _ in range(B):
        s = np.concatenate([idx[keys[j]] for j in rng.integers(0, len(keys), len(keys))])
        try:
            vals.append(fn(s))
        except ValueError:
            pass
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


res = {"n": int(len(M)), "layers": int(L), "model_accuracy": float(correct.mean()), "by_cell": {}, "layers_listed": [], "layers_correct": []}
for cl in ("base", "explicit"):
    for c in sorted(set(cell)):
        s = (cell == c) & (clause == cl)
        res["by_cell"][f"{cl}/{c}"] = [int((~correct[s]).sum()), int(s.sum())]
lk = shards.load(D, "E7")[0]
res["lookup_accuracy"] = [sum((m["logit"][0] > m["logit"][1]) == (m["gold"] == "YES") for m in lk), len(lk)]
all_idx = np.arange(len(M))
scores = {}
for layer in range(L):
    X = np.asarray(acts[e1, layer], dtype=np.float32)
    s1 = cv_scores(X, gold); s1c = cv_scores(X, gold, shuffle=True); s2 = cv_scores(X, correct)
    scores[layer] = (s1, s2)
    wr = (~correct) & gold  # allowed requests the model refused
    wa = (~correct) & ~gold
    res["layers_listed"].append({"layer": layer, "acc": float(((s1 > 0) == gold).mean()), "auroc": float(roc_auc_score(gold, s1)),
                                 "shuffled_acc": float(((s1c > 0) == gold).mean()),
                                 "acc_on_wrong_refusals": float((s1[wr] > 0).mean()) if wr.any() else None,
                                 "acc_on_wrong_allows": float((s1[wa] <= 0).mean()) if wa.any() else None})
    res["layers_correct"].append({"layer": layer, "auroc": float(roc_auc_score(correct, s2))})
    print(layer, res["layers_listed"][-1], res["layers_correct"][-1], flush=True)
best = max(res["layers_listed"], key=lambda r: r["acc"])["layer"]; s1, _ = scores[best]
bc = max(res["layers_correct"], key=lambda r: r["auroc"])["layer"]; _, s2 = scores[bc]
wr, wa = (~correct) & gold, (~correct) & ~gold
res["best_listed"] = {"layer": best, "probe_acc": float(((s1 > 0) == gold).mean()), "probe_acc_ci": boot(lambda s: ((s1[s] > 0) == gold[s]).mean()),
                      "model_acc_ci": boot(lambda s: correct[s].mean()),
                      "gap_ci": boot(lambda s: ((s1[s] > 0) == gold[s]).mean() - correct[s].mean()),
                      "wrong_refusals": [int((s1[wr] > 0).sum()), int(wr.sum())], "wrong_allows": [int((s1[wa] <= 0).sum()), int(wa.sum())]}
conf = np.abs(margin)
res["best_correct"] = {"layer": bc, "probe_auroc": float(roc_auc_score(correct, s2)), "probe_auroc_ci": boot(lambda s: roc_auc_score(correct[s], s2[s])),
                       "margin_auroc": float(roc_auc_score(correct, conf)), "margin_auroc_ci": boot(lambda s: roc_auc_score(correct[s], conf[s])),
                       "gap_ci": boot(lambda s: roc_auc_score(correct[s], s2[s]) - roc_auc_score(correct[s], conf[s]))}
json.dump(res, open(D / "probe_results.json", "w"), indent=1)
np.save(D / "probe_scores_listed.npy", s1)
print(json.dumps({k: v for k, v in res.items() if not k.startswith("layers_")}, indent=1))
