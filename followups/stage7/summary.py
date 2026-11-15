"""Cross-model summary used by the paper and figures: one file from the G, H, I, Q and J analyses."""
import json
from pathlib import Path
from labels import LABEL, BASTA, YANG, FIRST8, BASTA_PUB

HERE = Path(__file__).resolve().parent
G = json.load(open(HERE / "results_g.json"))["models"]; H = json.load(open(HERE / "results_h.json"))["models"]
I = json.load(open(HERE / "results_i.json"))["models"]; J = json.load(open(HERE / "results_j.json"))
ORDER = list(LABEL)
r = lambda x: None if not x or x.get("rate") is None else x["rate"]
out = {"order": [LABEL[m] for m in ORDER if m in G], "groups": {"first8": [LABEL[m] for m in FIRST8], "basta": [LABEL[m] for m in BASTA], "yang": [LABEL[m] for m in YANG]}, "models": {}}
for mid in ORDER:
    if mid not in G:
        continue
    g = G[mid]; w = g["word"]["all"]; f = g["free"]["all"]
    m = {"label": LABEL[mid], "decisions_g": g["decisions"],
         "word_F": {c: r(w[c]["F"]) for c in w}, "word_H": {c: r(w[c]["H"]) for c in w}, "word_n": {c: (w[c]["F"] or {}).get("n") for c in w},
         "word_d": {c: w[c].get("d") for c in w}, "word_c": {c: w[c].get("c") for c in w},
         "free_F": {c: r(f[c]["F"]) for c in f}, "free_H": {c: r(f[c]["H"]) for c in f},
         "diffs": g["word"]["diffs"], "by_task": {t: {c: r(g["word"][t][c]["F"]) for c in g["word"][t]} for t in ("stock", "rooms", "rules")},
         "b0_3": {c: r(v) for c, v in g.get("b0_3", {}).items()}, "b4_7": {c: r(v) for c, v in g.get("b4_7", {}).items()}, "blocks": g.get("blocks")}
    if mid in I and "word" in I[mid]:
        i = I[mid]; iw = i["word"]
        m["fact"] = {"n_F": iw.get("n_F"), "by_act": {a: r(v) for a, v in iw["by_act"].items()}, "by_naming": {a: r(v) for a, v in iw["by_naming"].items()}, "by_evidence": {a: r(v) for a, v in iw["by_evidence"].items()},
                     "act": iw.get("act"), "act_assert": iw.get("act_assert"), "act_dir_assert": iw.get("act_dir_assert"), "naming": iw.get("naming"), "page": iw.get("page"), "outside": iw.get("outside"),
                     "page_vs_outside": iw.get("page_vs_outside"), "H_all": r(iw["H_all"]), "H_by_act": {a: r(v) for a, v in (iw.get("H_by_act") or {}).items()},
                     "cells": {c: r(v["F"]) for c, v in iw["cells"].items()}, "cells_n": {c: (v["F"] or {}).get("n") for c, v in iw["cells"].items()}}
        if "free" in i:
            m["fact_free"] = {"by_act": {a: r(v) for a, v in i["free"]["by_act"].items()}, "act": i["free"].get("act"), "page": i["free"].get("page"), "cells": {c: r(v["F"]) for c, v in i["free"]["cells"].items()}}
        if "word_noinstr" in i:
            n = i["word_noinstr"]
            m["fact_noinstr"] = {"by_act": {a: r(v) for a, v in n["by_act"].items()}, "act_dir_assert": n.get("act_dir_assert"), "naming": n.get("naming"), "page": n.get("page"),
                                 "cells": {c: r(v["F"]) for c, v in n["cells"].items()}, "n_F": n.get("n_F")}
    if mid in H:
        h = H[mid]
        m["H"] = {"base": {k: {"F": r(v["F"]), "H": r(v["H"])} for k, v in h["base"].items()}, "wording": {k: {"F": r(v["F"]), "H": r(v["H"])} for k, v in h["wording"].items()},
                  "fix": {k: {"F": r(v["F"]), "H": r(v["H"]), "n": (v["F"] or {}).get("n")} for k, v in h["fix"].items()}, "turns": h["turns"], "n": h["n"]}
    if mid in J["sample"]:
        m["sample"] = J["sample"][mid]
    if mid in J["logprob"]:
        m["logprob"] = J["logprob"][mid]
    if LABEL[mid] in BASTA_PUB:
        m["basta_pub"] = BASTA_PUB[LABEL[mid]]
    out["models"][LABEL[mid]] = m
json.dump(out, open(HERE / "results_main.json", "w"), indent=1)
M = out["models"]
print("models", len(M))
for l, m in M.items():
    wf = m["word_F"]; fa = m.get("fact", {})
    g = lambda d, k: "  –" if d.get(k) is None else f"{100 * d[k]:3.0f}"
    print(f"{l:18} push* {g(wf, 'push_dis')} doubt* {g(wf, 'doubt_dis')} | plain {g(wf, 'plain')} cit {g(wf, 'citation')} page {g(wf, 'page_frame')} | fact q/a/d {g(fa.get('by_act', {}), 'question')}/{g(fa.get('by_act', {}), 'assertion')}/{g(fa.get('by_act', {}), 'directive')} nF={fa.get('n_F')} | check plain_dis {g(wf, 'plain_dis')} page_dis {g(wf, 'page_frame_dis')}")
