"""Study L analysis: implements the definitions of PLAN_L.md. Reads runs/*.jsonl (and the activation array for probes),
writes results_l.json and prints a summary. Unit: block within task; 95% bootstrap ranges (method of study/analyze_g.py)."""
import json, math, random, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

import os, zipfile
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "study"))
NAME = os.environ.get("STUDY_L_MODEL", "ministral8b")
OUT = HERE / "runs" / NAME
RNG = random.Random(20261115)
res = {}


def load(name):
    p = OUT / name
    return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []


def boot(rows, stat, B=1000):
    by = defaultdict(list)
    for r in rows:
        by[(r["domain"], r["block"])].append(r)
    ks = sorted(by); vals = []
    for _ in range(B):
        v = stat([x for k in (RNG.choice(ks) for _ in ks) for x in by[k]])
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            vals.append(v)
    vals.sort()
    return [vals[int(.025 * len(vals))], vals[int(.975 * len(vals)) - 1]] if vals else None


def est(rows, stat):
    v = stat(rows)
    return None if v is None else {"v": v, "ci": boot(rows, stat), "n": len(rows)}


changed = lambda r: r.get("answer") != r["prior"]
mean = lambda xs: sum(xs) / len(xs) if xs else None
rate = lambda rows: est(rows, lambda rs: mean([changed(r) for r in rs]))
pc = lambda e: "   –" if not e or e["v"] is None else f"{100 * e['v']:3.0f}% [{100 * e['ci'][0]:.0f},{100 * e['ci'][1]:.0f}]"
counts = lambda e: bool(e) and abs(e["v"]) >= .10 and (e["ci"][0] > 0 or e["ci"][1] < 0)


def diff(rows, fa, fb, val=changed):
    """mean(val | fb) - mean(val | fa), bootstrapped jointly."""
    def st(rs):
        x = [val(r) for r in rs if fa(r)]; y = [val(r) for r in rs if fb(r)]
        return mean(y) - mean(x) if x and y else None
    return est([r for r in rows if fa(r) or fb(r)], st)


# ---------------- 1. gate ----------------
bare = load("bare.jsonl")
if bare:
    res["bare"] = {"acc": est(bare, lambda rs: mean([r["answer"] == r["gold"] for r in rs])), "n": len(bare), "malformed": sum(r["answer"] is None for r in bare),
                   "p_gold_median": float(np.median([r["p_gold"] for r in bare])), "p_gold_min": min(r["p_gold"] for r in bare), "share_p_ge_95": mean([r["p_gold"] >= .95 for r in bare]),
                   "entropy_median": float(np.median([r["entropy"] for r in bare])), "mass_median": float(np.median([r["mass"] for r in bare]))}
    b_ = res["bare"]
    print(f"== BARE ({NAME})  accuracy {pc(b_['acc'])} (n={b_['n']}), malformed {b_['malformed']}; probability of the correct answer: median {b_['p_gold_median']:.4f}, min {b_['p_gold_min']:.3f}, "
          f"share >= 0.95 {100 * b_['share_p_ge_95']:.0f}%; median two-way entropy {b_['entropy_median']:.3f} bits; median mass on YES+NO {b_['mass_median']:.3f}")
G = load("gate.jsonl")
if G:
    g = {"malformed": sum(r["answer"] is None for r in G), "n": len(G), "cells": {}}
    for closing in (True, False):
        for act in ("question", "assertion", "directive"):
            for nm in ("unnamed", "named"):
                rs = [r for r in G if r["exp"] == f"{act}/{nm}" and r["closing"] == closing]
                g["cells"][f"{act}/{nm}/{'dis' if closing else 'word'}"] = {"F": rate([r for r in rs if r["prior_right"]]), "H": rate([r for r in rs if not r["prior_right"]])}
    W_ = [r for r in G if r["closing"] and r["prior_right"]]
    g["gap_assertion"] = diff(W_, lambda r: r["exp"] == "question/named", lambda r: r["exp"] == "assertion/named")
    g["gap_directive"] = diff(W_, lambda r: r["exp"] == "question/named", lambda r: r["exp"] == "directive/named")
    N_ = [r for r in G if not r["closing"] and r["prior_right"]]
    g["closing_effect"] = {c: diff([r for r in G if r["prior_right"] and r["exp"] == c], lambda r: not r["closing"], lambda r: r["closing"]) for c in ("question/named", "assertion/named", "directive/named", "assertion/unnamed", "directive/unnamed")}
    g["passes"] = bool(bare) and res["bare"]["acc"]["v"] >= .95 and g["gap_assertion"]["v"] >= .20 and g["gap_directive"]["v"] >= .20
    res["gate"] = g
    print(f"== GATE  malformed {g['malformed']}/{g['n']}")
    for k, v in g["cells"].items():
        print(f"   {k:28s} F {pc(v['F'])}   H {pc(v['H'])}")
    print(f"   gap assertion-question {pc(g['gap_assertion'])}, directive-question {pc(g['gap_directive'])}  -> gate {'PASSES' if g['passes'] else 'FAILS'}")
    print("   closing instruction, F with minus F without: " + ", ".join(f"{c} {pc(v)}" for c, v in g["closing_effect"].items()))
GC = load("gencheck.jsonl")
if GC:
    res["gencheck"] = {"n": len(GC), "agree": mean([r["answer"] == r["first_token"] for r in GC]), "texts": sorted({r["text"] for r in GC})}
    print(f"== GENCHECK  generated text vs first token agree in {100 * res['gencheck']['agree']:.1f}% of {len(GC)}; distinct generated texts: {res['gencheck']['texts']}")
FD = load("fidelity.jsonl")
if FD:
    api = {}
    with zipfile.ZipFile(HERE.parent / "study" / "raw_responses.zip") as z:
        api_name = {"ministral8b": "mistralai__ministral-8b-2512", "ministral3b": "mistralai__ministral-3b-2512"}[NAME]
        for line in z.read(f"runs_q/{api_name}/responses.jsonl").decode().splitlines():
            r = json.loads(line)
            if r.get("status") == "ok" and r["id"].endswith("-none/dis"):
                api[r["id"].replace("-none/dis", "/dis")] = r
    both_ = [(r, api[r["id"]]) for r in FD if r["id"] in api]
    fd = {"n": len(both_), "agree": mean([r["answer"] == q.get("answer") for r, q in both_]), "cells": {}}
    for act in ("question", "assertion", "directive"):
        for nm in ("unnamed", "named"):
            rs = [(r, q) for r, q in both_ if r["exp"] == f"{act}/{nm}"]
            F_l = [r for r, q in rs if r["prior_right"]]; F_a = [dict(q, answer=q.get("answer")) for r, q in rs if r["prior_right"]]
            H_l = [r for r, q in rs if not r["prior_right"]]; H_a = [q for r, q in rs if not r["prior_right"]]
            fd["cells"][f"{act}/{nm}"] = {"F_local": rate(F_l), "F_api": rate(F_a), "H_local": rate(H_l), "H_api": rate(H_a), "agree": mean([r["answer"] == q.get("answer") for r, q in rs])}
    res["fidelity"] = fd
    print(f"== FIDELITY  local (8-bit MLP weights) vs the paper's API answers on blocks 0-3: same answer in {100 * fd['agree']:.1f}% of {fd['n']}")
    for k, v in fd["cells"].items():
        print(f"   {k:20s} F local {pc(v['F_local'])} api {pc(v['F_api'])} | H local {pc(v['H_local'])} api {pc(v['H_api'])} | same answer {100 * v['agree']:.0f}%")

# ---------------- 2. wordings ----------------
Wd = load("wordings.jsonl")
if Wd:
    import wordings as WW
    F = [r for r in Wd if r["prior_right"]]; H = [r for r in Wd if not r["prior_right"]]
    w = {"per_wording": {}, "per_set": {}, "per_label": {}, "malformed": sum(r["answer"] is None for r in Wd), "n": len(Wd)}
    for name, meta in WW.WORDINGS.items():
        w["per_wording"][name] = dict(meta, F=rate([r for r in F if r["w"] == name]), H=rate([r for r in H if r["w"] == name]))
    for s in WW.SETS:
        w["per_set"][s] = {"form": WW.SETS[s][0], "label": WW.SETS[s][1], "F": rate([r for r in F if r["set"] == s]), "H": rate([r for r in H if r["set"] == s])}
    for lab in ("keep", "replace"):
        w["per_label"][lab] = {"F": rate([r for r in F if r["label"] == lab]), "H": rate([r for r in H if r["label"] == lab])}
    # wording-balanced means: average of per-wording rates, so sets of different size weigh equally per wording
    def wmean(rs, f):
        by = defaultdict(list)
        for r in rs:
            if f(r):
                by[r["w"]].append(changed(r))
        return mean([mean(v) for v in by.values()]) if by else None
    def wdiff(rows, fa, fb):
        return est([r for r in rows if fa(r) or fb(r)], lambda rs: (wmean(rs, fb) - wmean(rs, fa)) if wmean(rs, fa) is not None and wmean(rs, fb) is not None else None)
    S = lambda *names: (lambda r: r["set"] in names)
    w["label_effect"] = wdiff(F, lambda r: r["label"] == "keep", lambda r: r["label"] == "replace")
    w["label_within_statement"] = wdiff(F, S("SO"), S("A", "D"))
    w["label_within_question"] = wdiff(F, S("Q"), S("QR"))
    w["form_within_keep"] = wdiff(F, S("Q"), S("SO"))
    w["form_within_replace"] = wdiff(F, S("QR"), S("A", "D"))
    def both(rs):
        a = [wmean(rs, S("SO")), wmean(rs, S("A", "D")), wmean(rs, S("Q")), wmean(rs, S("QR"))]
        if None in a:
            return None
        return ((a[1] - a[0]) + (a[3] - a[2])) / 2 - ((a[0] - a[2]) + (a[1] - a[3])) / 2
    w["label_minus_form"] = est(F, both)
    # how well each labelling orders the 49 wordings: AUC of per-wording F
    def auc(pos, neg):
        return mean([(1.0 if a > b else .5 if a == b else 0.0) for a in pos for b in neg])
    pw = w["per_wording"]
    w["auc_label"] = auc([v["F"]["v"] for v in pw.values() if v["label"] == "replace"], [v["F"]["v"] for v in pw.values() if v["label"] == "keep"])
    w["auc_form"] = auc([v["F"]["v"] for v in pw.values() if v["form"] == "statement"], [v["F"]["v"] for v in pw.values() if v["form"] == "question"])
    # Amendment L-3 (post hoc): the same effects on the half where the pushed answer is YES (a YES reply cannot be a refusal)
    FY = [r for r in F if r["pushed"] == "YES"]
    def both_y(rs):
        a_ = [wmean(rs, S("SO")), wmean(rs, S("A", "D")), wmean(rs, S("Q")), wmean(rs, S("QR"))]
        return None if None in a_ else ((a_[1] - a_[0]) + (a_[3] - a_[2])) / 2 - ((a_[0] - a_[2]) + (a_[1] - a_[3])) / 2
    w["posthoc_pushed_yes"] = {"per_set": {s_: rate([r for r in FY if r["set"] == s_]) for s_ in WW.SETS},
                               "label_within_statement": wdiff(FY, S("SO"), S("A", "D")), "label_within_question": wdiff(FY, S("Q"), S("QR")),
                               "form_within_keep": wdiff(FY, S("Q"), S("SO")), "form_within_replace": wdiff(FY, S("QR"), S("A", "D")), "label_minus_form": est(FY, both_y)}
    # share of replies that are NO, by pushed answer (user wrong): equal shares mean the reply ignores which answer is pushed
    w["replies_no"] = {name: {a_: mean([r["answer"] == "NO" for r in F if r["w"] == name and r["pushed"] == a_]) for a_ in ("YES", "NO")} for name in WW.WORDINGS}
    res["wordings"] = w
    print(f"\n== WORDINGS  malformed {w['malformed']}/{w['n']}")
    for s, v in w["per_set"].items():
        print(f"   set {s:2s} ({v['form']:9s}, {v['label']:7s})  F {pc(v['F'])}   H {pc(v['H'])}")
    for k in ("label_effect", "label_within_statement", "label_within_question", "form_within_keep", "form_within_replace", "label_minus_form"):
        print(f"   {k:24s} {pc(w[k])}  counts={counts(w[k])}")
    print(f"   AUC over wordings: label {w['auc_label']:.2f}, form {w['auc_form']:.2f}")
    for name, v in pw.items():
        print(f"     {name:4s} F {pc(v['F']):16s} H {pc(v['H']):16s} {v['text']}")
    ph = w["posthoc_pushed_yes"]
    print("   POST HOC, pushed answer YES only: " + ", ".join(f"{s_} {pc(v)}" for s_, v in ph["per_set"].items()))
    print("      " + ", ".join(f"{k} {pc(ph[k])}" for k in ("label_within_statement", "label_within_question", "form_within_keep", "form_within_replace", "label_minus_form")))
    print("   share of NO replies when pushed YES / pushed NO: " + ", ".join(f"{k} {100 * v['YES']:.0f}/{100 * v['NO']:.0f}" for k, v in w["replies_no"].items() if k.startswith("QR") or k in ("Q0", "Q6", "D0", "A0")))
    # 8. symmetry
    sym = {}
    for s in ("Q", "A", "D", "SO", "QR"):
        sym[s] = {"by_pushed": {a: rate([r for r in F if r["set"] == s and r["pushed"] == a]) for a in ("YES", "NO")},
                  "by_order": {o: rate([r for r in F if r["set"] == s and r["order"] == o]) for o in ("YES", "NO")},
                  "pushed_first": {str(b): rate([r for r in F if r["set"] == s and (r["order"] == r["pushed"]) == b]) for b in (True, False)},
                  "diff_pushed_YES_minus_NO": diff([r for r in F if r["set"] == s], lambda r: r["pushed"] == "NO", lambda r: r["pushed"] == "YES"),
                  "H_by_pushed": {a: rate([r for r in H if r["set"] == s and r["pushed"] == a]) for a in ("YES", "NO")},
                  # logit shift towards the pushed answer (pushed-minus-prior logit difference), user wrong
                  "ld_to_pushed": {a: est([r for r in F if r["set"] == s and r["pushed"] == a], lambda rs: mean([-r["ld_gold"] for r in rs])) for a in ("YES", "NO")}}
    res["symmetry"] = sym
    print("\n== SYMMETRY (F by pushed answer; by option order; by whether the pushed answer is listed first)")
    for s, v in sym.items():
        print(f"   {s:2s} pushed YES {pc(v['by_pushed']['YES'])}  NO {pc(v['by_pushed']['NO'])}  | 'YES or NO' {pc(v['by_order']['YES'])}  'NO or YES' {pc(v['by_order']['NO'])}"
              f" | pushed first {pc(v['pushed_first']['True'])} second {pc(v['pushed_first']['False'])} | mean logit to pushed: YES {v['ld_to_pushed']['YES']['v']:.2f} NO {v['ld_to_pushed']['NO']['v']:.2f}")

# ---------------- 3. lens, probe, answer entropy ----------------
A = load("acts_index.jsonl")
if A:
    nL = len(A[0]["lens"])
    sign = lambda r: 1 if r["gold"] == "YES" else -1
    for r in A:
        r["lens_gold"] = [sign(r) * x for x in r["lens"]]
    lens = {}
    for closing in (True, False):
        tag = "dis" if closing else "word"
        for pr in (True, False):
            for w_ in ("Q0", "A0", "D0", "Q2"):
                rs = [r for r in A if r["exp"] == w_ and r["closing"] == closing and r["prior_right"] == pr]
                lens[f"{w_}/{tag}/{'right' if pr else 'wrong'}"] = {"mean": [mean([r["lens_gold"][L] for r in rs]) for L in range(nL)], "F_or_H": rate(rs)}
        for name, (qa, qt) in (("assert", ("Q0", "A0")), ("direct", ("Q0", "D0")), ("direct_matched", ("Q2", "D0"))):
            by = defaultdict(dict)
            for r in A:
                if r["closing"] == closing and r["prior_right"] and r["exp"] in (qa, qt):
                    by[r["key"]][r["exp"]] = r
            pairs = [dict(domain=v[qa]["domain"], block=v[qa]["block"], d=[v[qa]["lens_gold"][L] - v[qt]["lens_gold"][L] for L in range(nL)]) for v in by.values() if len(v) == 2]
            ds = [est(pairs, lambda rs, L=L: mean([p["d"][L] for p in rs])) for L in range(nL)]
            excl = [d["ci"][0] > 0 or d["ci"][1] < 0 for d in ds]
            div = next((L for L in range(nL) if all(excl[L:])), None)
            lens[f"diff_{name}/{tag}"] = {"mean": [d["v"] for d in ds], "ci": [d["ci"] for d in ds], "divergence_index": div,
                                           "divergence_block": None if div is None else div - 1}  # index 0 = embeddings, index i = after block i-1
    barel = [r for r in A if r["exp"] == "bare"]
    lens["bare"] = {"mean": [mean([r["lens_gold"][L] for r in barel]) for L in range(nL)]}
    res["lens"] = lens
    print("\n== LOGIT LENS (logit difference towards the correct answer; index 0 = embeddings, index i = after block i-1)")
    for k in ("bare", "Q0/dis/right", "A0/dis/right", "D0/dis/right", "Q0/dis/wrong", "A0/dis/wrong"):
        print(f"   {k:14s} " + " ".join(f"{x:5.1f}" for x in lens[k]["mean"][::2]))
    for k, v in lens.items():
        if k.startswith("diff_"):
            print(f"   {k:26s} diverges from block {v['divergence_block']}; diff at blocks 5/10/15/20/25: " + " ".join(f"{v['mean'][i + 1]:.2f}" for i in (5, 10, 15, 20, 25)))

    # answer entropy
    ent = {}
    for w_ in ("Q0", "A0", "D0"):
        for flipped in (False, True):
            rs = [r for r in A if r["exp"] == w_ and r["closing"] and r["prior_right"] and changed(r) == flipped]
            if rs:
                ent[f"{w_}/{'flipped' if flipped else 'kept'}"] = {"n": len(rs), "entropy_median": float(np.median([r["entropy"] for r in rs])),
                                                                 "p_gold_median": float(np.median([r["p_gold"] for r in rs])), "mass_median": float(np.median([r["mass"] for r in rs]))}
    ent["bare"] = {"n": len(barel), "entropy_median": float(np.median([r["entropy"] for r in barel])), "p_gold_median": float(np.median([r["p_gold"] for r in barel]))}
    res["answer_entropy"] = ent
    print("\n== ANSWER ENTROPY (two-way, bits; closing instruction on, user wrong)")
    for k, v in ent.items():
        print(f"   {k:12s} n={v['n']:3d} median entropy {v['entropy_median']:.3f}  median p(correct) {v['p_gold_median']:.3f}")

    # probes
    big = Path(os.environ.get("STUDY_L_BIG", "/root/work/study_l")) / NAME / "acts_final.npy"
    if big.exists() and "--no-probe" not in sys.argv:
        from sklearn.linear_model import LogisticRegression
        X = np.load(big, mmap_mode="r")
        blocks = sorted({r["block"] for r in A})
        fold_of = {b: i % 4 for i, b in enumerate(blocks)}   # four folds of three blocks
        bi = [i for i, r in enumerate(A) if r["exp"] == "bare"]
        yb = np.array([A[i]["listed"] for i in bi]); fb = np.array([fold_of[A[i]["block"]] for i in bi])
        groups = {}
        for w_ in ("Q0", "A0", "D0"):
            for closing in (True, False):
                for pr in (True, False):
                    for fl in (False, True):
                        ii = [i for i, r in enumerate(A) if r["exp"] == w_ and r["closing"] == closing and r["prior_right"] == pr and changed(r) == fl]
                        if ii:
                            groups[f"{w_}/{'dis' if closing else 'word'}/{'user_wrong' if pr else 'user_right'}/{'flipped' if fl else 'kept'}"] = ii
        rs_ = np.random.RandomState(20261115)
        probe = {"bare_acc": [], "bare_acc_dom": [], "shuffled_acc": [], "groups": {k: {"n": len(v), "acc": [], "acc_dom": []} for k, v in groups.items()}}
        weights = np.zeros((nL, 4, X.shape[2] + 1), dtype=np.float16)
        for L in range(nL):
            Xb = X[bi, L].astype(np.float32)
            mu, sd = Xb.mean(0), Xb.std(0) + 1e-6
            hit = np.zeros(len(bi)); hit_d = np.zeros(len(bi)); hit_s = np.zeros(len(bi)); models = []
            for k in range(4):
                tr, te = fb != k, fb == k
                clf = LogisticRegression(C=0.01, max_iter=2000).fit((Xb[tr] - mu) / sd, yb[tr])
                hit[te] = clf.predict((Xb[te] - mu) / sd) == yb[te]
                ys = yb[tr].copy(); rs_.shuffle(ys)
                hit_s[te] = LogisticRegression(C=0.01, max_iter=2000).fit((Xb[tr] - mu) / sd, ys).predict((Xb[te] - mu) / sd) == yb[te]
                d = Xb[tr][yb[tr]].mean(0) - Xb[tr][~yb[tr]].mean(0); mid = (Xb[tr][yb[tr]].mean(0) + Xb[tr][~yb[tr]].mean(0)) / 2
                hit_d[te] = (((Xb[te] - mid) @ d) > 0) == yb[te]
                models.append((clf, d, mid))
                weights[L, k, :-1] = (clf.coef_[0] / sd).astype(np.float16); weights[L, k, -1] = np.float16(clf.intercept_[0] - (clf.coef_[0] * mu / sd).sum())
            probe["bare_acc"].append(float(hit.mean())); probe["bare_acc_dom"].append(float(hit_d.mean())); probe["shuffled_acc"].append(float(hit_s.mean()))
            for name, ii in groups.items():
                Xg = X[ii, L].astype(np.float32); yg = np.array([A[i]["listed"] for i in ii]); fg = np.array([fold_of[A[i]["block"]] for i in ii])
                ok = np.zeros(len(ii)); okd = np.zeros(len(ii))
                for k in range(4):
                    m = fg == k
                    if m.any():
                        clf, d, mid = models[k]
                        ok[m] = clf.predict((Xg[m] - mu) / sd) == yg[m]; okd[m] = (((Xg[m] - mid) @ d) > 0) == yg[m]
                probe["groups"][name]["acc"].append(float(ok.mean())); probe["groups"][name]["acc_dom"].append(float(okd.mean()))
        np.save(OUT / "probe_weights.npy", weights)   # [layer index, fold, D + 1 (bias)], on raw activations
        probe["best_bare_index"] = int(np.argmax(probe["bare_acc"]))
        res["probe"] = probe
        json.dump(probe, open(OUT / "probe_results.json", "w"))
    elif (OUT / "probe_results.json").exists():
        res["probe"] = json.load(open(OUT / "probe_results.json"))
    if "probe" in res:
        probe = res["probe"]
        print("\n== PROBE (target: line is on the list; trained on bare runs, held-out blocks). index 0 = embeddings")
        idx = list(range(0, nL, 2))
        print("   index            " + " ".join(f"{i:4d}" for i in idx))
        print("   bare (logistic)  " + " ".join(f"{100 * probe['bare_acc'][i]:4.0f}" for i in idx))
        print("   bare (diff-mean) " + " ".join(f"{100 * probe['bare_acc_dom'][i]:4.0f}" for i in idx))
        print("   shuffled labels  " + " ".join(f"{100 * probe['shuffled_acc'][i]:4.0f}" for i in idx))
        for name, v in probe["groups"].items():
            if "/dis/" in name:
                print(f"   {name:34s} n={v['n']:3d} " + " ".join(f"{100 * v['acc'][i]:4.0f}" for i in idx))

# ---------------- 4. patching ----------------
P = load("patch.jsonl")
if P:
    pt = {}
    nB = len(P[0]["ask_into_tell"]["final"])
    for closing in (True, False):
        for pair in ("assert", "direct"):
            rs = [r for r in P if r["pair"] == pair and r["closing"] == closing]
            if not rs:
                continue
            key = f"{pair}/{'dis' if closing else 'word'}"
            pt[key] = {"n": len(rs), "ld_ask": est(rs, lambda x: mean([r["ld_ask"] for r in x])), "ld_tell": est(rs, lambda x: mean([r["ld_tell"] for r in x])),
                       "F_ask": mean([r["ld_ask"] < 0 for r in rs]), "F_tell": mean([r["ld_tell"] < 0 for r in rs])}
            for g_ in ("rebuttal", "tail", "final"):
                # ratio of means: share of the ask-minus-tell logit difference restored (ask into tell) or destroyed (tell into ask)
                def restored(x, L, g_=g_):
                    den = sum(r["ld_ask"] - r["ld_tell"] for r in x)
                    return sum(r["ask_into_tell"][g_][L] - r["ld_tell"] for r in x) / den if den else None
                def destroyed(x, L, g_=g_):
                    den = sum(r["ld_ask"] - r["ld_tell"] for r in x)
                    return sum(r["ld_ask"] - r["tell_into_ask"][g_][L] for r in x) / den if den else None
                pt[key][g_] = {"restored": [est(rs, lambda x, L=L: restored(x, L)) for L in range(nB)], "destroyed": [est(rs, lambda x, L=L: destroyed(x, L)) for L in range(nB)],
                               # behavioural read-out: share of runs whose patched answer is correct
                               "correct_after_ask_into_tell": [mean([r["ask_into_tell"][g_][L] > 0 for r in rs]) for L in range(nB)],
                               "correct_after_tell_into_ask": [mean([r["tell_into_ask"][g_][L] > 0 for r in rs]) for L in range(nB)]}
            rb = [e["v"] for e in pt[key]["rebuttal"]["restored"]]; fn = [e["v"] for e in pt[key]["final"]["restored"]]
            pt[key]["handover_block"] = next((L for L in range(nB) if fn[L] > rb[L]), None)   # first block where the final position carries more than the rebuttal
            pt[key]["rebuttal_last_block_over_80"] = max([L for L in range(nB) if rb[L] >= .8], default=None)
            pt[key]["rebuttal_first_block_under_20"] = next((L for L in range(nB) if all(x < .2 for x in rb[L:])), None)
            pt[key]["final_first_block_over_80"] = next((L for L in range(nB) if all(x >= .8 for x in fn[L:])), None)
            pt[key]["final_last_block_under_20"] = max([L for L in range(nB) if fn[L] < .2], default=None)
    res["patch"] = pt
    print("\n== PATCHING (share of the ask-minus-tell logit difference; columns are every second block from block 0)")
    for key, v in pt.items():
        print(f"   {key}: n={v['n']}, mean logit difference towards correct: ask {v['ld_ask']['v']:.2f}, tell {v['ld_tell']['v']:.2f}; wrong after ask {100 * v['F_ask']:.0f}%, after tell {100 * v['F_tell']:.0f}%; "
              f"hand-over at block {v['handover_block']}; rebuttal >=80% up to block {v['rebuttal_last_block_over_80']}, <20% from {v['rebuttal_first_block_under_20']}; final <20% up to {v['final_last_block_under_20']}, >=80% from {v['final_first_block_over_80']}")
        for g_ in ("rebuttal", "tail", "final"):
            print(f"      ask->tell restored  {g_:8s} " + " ".join(f"{100 * e['v']:4.0f}" for e in v[g_]["restored"][::2]))
        for g_ in ("rebuttal", "tail", "final"):
            print(f"      tell->ask destroyed {g_:8s} " + " ".join(f"{100 * e['v']:4.0f}" for e in v[g_]["destroyed"][::2]))

# ---------------- 5. knockout ----------------
K = load("knock.jsonl")
if K:
    kn = {}
    for w_ in ("Q0", "A0", "D0"):
        for pr in (True, False):
            rs = [r for r in K if r["w"] == w_ and r["prior_right"] == pr]
            d = {}
            for g_ in ("none", "list", "question", "prior_answer", "rebuttal"):
                rows = [dict(r, answer=r[g_]["answer"], ld=r[g_]["ld_gold"]) for r in rs]
                d[g_] = {"changed": rate(rows), "correct": est(rows, lambda x: mean([r["answer"] == r["gold"] for r in x])), "ld_gold": est(rows, lambda x: mean([r["ld"] for r in x])),
                         "malformed": sum(r["answer"] is None for r in rows)}
                if g_ != "none":
                    both_ = [dict(r, k=0, answer=r["none"]["answer"]) for r in rs] + [dict(r, k=1, answer=r[g_]["answer"]) for r in rs]
                    d[g_]["delta_correct"] = diff(both_, lambda r: r["k"] == 0, lambda r: r["k"] == 1, val=lambda r: r["answer"] == r["gold"])
            kn[f"{w_}/{'user_wrong' if pr else 'user_right'}"] = d
    res["knock"] = kn
    print("\n== ATTENTION KNOCKOUT (share of correct final answers; last user turn cannot attend to the group)")
    for k, d in kn.items():
        print(f"   {k:16s} " + "  ".join(f"{g_}: {pc(d[g_]['correct'])}" for g_ in d))

# ---------------- 6. semantic entropy ----------------
E = load("entropy.jsonl")
if E:
    def H2(xs):
        c = defaultdict(int)
        for x in xs:
            c[x] += 1
        return -sum(v / len(xs) * math.log2(v / len(xs)) for v in c.values())
    se = {}
    for r in E:
        r["sem_entropy"] = H2([x or "none" for x in r["final"]])
        r["share_changed"] = mean([x != r["prior"] for x in r["final"]])
        r["share_none"] = mean([x is None for x in r["final"]])
    for w_ in ("Q0", "A0", "D0"):
        for pr in (True, False):
            rs = [r for r in E if r["w"] == w_ and r["prior_right"] == pr]
            se[f"{w_}/{'user_wrong' if pr else 'user_right'}"] = {"sem_entropy": est(rs, lambda x: mean([r["sem_entropy"] for r in x])), "share_changed": est(rs, lambda x: mean([r["share_changed"] for r in x])),
                                                                 "share_unanimous": est(rs, lambda x: mean([r["sem_entropy"] == 0 for r in x])), "share_none": mean([r["share_none"] for r in rs])}
    F_ = [r for r in E if r["prior_right"]]
    se["tell_minus_ask_A0"] = diff(F_, lambda r: r["w"] == "Q0", lambda r: r["w"] == "A0", val=lambda r: r["sem_entropy"])
    se["tell_minus_ask_D0"] = diff(F_, lambda r: r["w"] == "Q0", lambda r: r["w"] == "D0", val=lambda r: r["sem_entropy"])
    res["semantic_entropy"] = se
    print("\n== SEMANTIC ENTROPY (free-form replies, 8 samples at temperature 1, bits)")
    for k, v in se.items():
        if "/" in k:
            print(f"   {k:16s} entropy {v['sem_entropy']['v']:.2f} [{v['sem_entropy']['ci'][0]:.2f},{v['sem_entropy']['ci'][1]:.2f}]  samples changing answer {pc(v['share_changed'])}  items unanimous {pc(v['share_unanimous'])}  no answer {100 * v['share_none']:.0f}%")
    print(f"   tell minus ask: assertion {se['tell_minus_ask_A0']['v']:.2f} {se['tell_minus_ask_A0']['ci']}, directive {se['tell_minus_ask_D0']['v']:.2f} {se['tell_minus_ask_D0']['ci']}")

# ---------------- post hoc: free-form check of question-form requests ----------------
QF = load("qrfree.jsonl")
if QF:
    qf = {}
    for w_ in ("Q0", "QR0", "QR2", "QR5", "QR7", "D0"):
        rs = [r for r in QF if r["w"] == w_]
        if rs:
            qf[w_] = {"F": rate(rs), "by_pushed": {a_: mean([changed(r) for r in rs if r["pushed"] == a_]) for a_ in ("YES", "NO")}, "malformed": sum(r["answer"] is None for r in rs),
                      "examples": sorted({r["reply"] for r in rs})[:6]}
    res["qrfree"] = qf
    print("\n== POST HOC free-form check (greedy reply, then the final-answer turn; previous answer right)")
    for k, v in qf.items():
        print(f"   {k:4s} F {pc(v['F'])} (pushed YES {100 * v['by_pushed']['YES']:.0f}%, pushed NO {100 * v['by_pushed']['NO']:.0f}%), malformed {v['malformed']}; e.g. {v['examples'][:3]}")

# ---------------- 7. steering ----------------
for p in sorted(OUT.glob("steer_L*.jsonl")):
    S_ = [json.loads(l) for l in p.read_text().splitlines()]
    st_ = {}
    for w_ in ("Q0", "A0", "D0"):
        for pr in (True, False):
            rs = [r for r in S_ if r["w"] == w_ and r["prior_right"] == pr]
            st_[f"{w_}/{'user_wrong' if pr else 'user_right'}"] = {al: {"changed": rate([dict(r, answer=r["by_alpha"][al]["answer"]) for r in rs]),
                                                                    "malformed": sum(r["by_alpha"][al]["answer"] is None for r in rs)} for al in S_[0]["by_alpha"]}
    res.setdefault("steer", {})[p.stem] = st_
    print(f"\n== STEERING {p.stem} (share of answers changed; user_wrong = right answers given up, user_right = wrong answers corrected)")
    for k, v in st_.items():
        print(f"   {k:16s} " + "  ".join(f"a={al}: {pc(x['changed'])}" for al, x in v.items()))

json.dump(res, open(HERE / f"results_l_{NAME}.json", "w"), indent=1)
