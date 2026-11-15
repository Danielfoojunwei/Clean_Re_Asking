"""Analysis of experiment I: speech act x naming x evidence. Unit: block within task; 95% bootstrap ranges."""
import json, random
from collections import defaultdict
from pathlib import Path
from labels import LABEL

HERE = Path(__file__).resolve().parent
RNG = random.Random(20261115)
ACTS, NAMES, EVS = ("question", "assertion", "directive"), ("unnamed", "named"), ("none", "outside", "page")


def load(p):
    out = {}
    if p.exists():
        for line in p.read_text().splitlines():
            r = json.loads(line)
            if r["status"] == "ok":
                out[r["id"]] = r
    return out


def boot(rows, stat, B=600):
    by = defaultdict(list)
    for r in rows:
        by[(r["domain"], r["block"])].append(r)
    ks = list(by); vals = []
    for _ in range(B):
        v = stat([x for k in (RNG.choice(ks) for _ in ks) for x in by[k]])
        if v is not None:
            vals.append(v)
    vals.sort()
    return [vals[int(.025 * len(vals))], vals[int(.975 * len(vals)) - 1]] if vals else None


ch = lambda r: r.get("answer") != r["prior"]
mean = lambda rs: sum(map(ch, rs)) / len(rs) if rs else None


def rate(rows):
    return {"k": sum(map(ch, rows)), "n": len(rows), "rate": mean(rows), "ci": boot(rows, mean)} if rows else None


def contrast(rows, key, hi, lo):
    """Difference in the share changed between two levels of one factor, averaged over the cells of the other factors."""
    others = [k for k in ("act", "naming", "evidence") if k != key]
    def st(rs):
        cells = defaultdict(lambda: {hi: [], lo: []})
        for r in rs:
            if r[key] in (hi, lo):
                cells[tuple(r[o] for o in others)][r[key]].append(ch(r))
        d = [sum(c[hi]) / len(c[hi]) - sum(c[lo]) / len(c[lo]) for c in cells.values() if c[hi] and c[lo]]
        return sum(d) / len(d) if d else None
    d = st(rows)
    if d is None:
        return None
    ci = boot(rows, st)
    return {"diff": d, "ci": ci, "counts": abs(d) >= .10 and (ci[0] > 0 or ci[1] < 0)}


res = {"models": {}}
for mid, lab in LABEL.items():
    R = load(HERE / "runs_i" / mid.replace("/", "__") / "responses.jsonl")
    Q = [r for r in load(HERE / "runs_q" / mid.replace("/", "__") / "responses.jsonl").values() if r["step"] == "decide" and not r["exp"].startswith("g_")]
    # one-word format: "word" = with the closing instruction (Amendment I-2, all cells); "word_noinstr" = without it (question cells there are the faulty measurement)
    dec = [dict(r, fmt="word_noinstr") if r["fmt"] == "word" else r for r in R.values() if r["step"] == "decide"]
    dec += [dict(r, fmt="word") for r in Q]
    if not dec:
        continue
    m = {"label": lab, "n": len(R), "spend": round(sum(r.get("cost") or 0 for r in R.values()), 4), "malformed": sum(r.get("answer") is None for r in dec), "decisions": len(dec)}
    for fmt in ("word", "free", "word_noinstr"):
        rows = [r for r in dec if r["fmt"] == fmt]
        if not rows:
            continue
        F = [r for r in rows if r["prior_right"]]; H = [r for r in rows if not r["prior_right"]]
        d = {"cells": {f"{a}/{n}/{e}": {"F": rate([r for r in F if (r["act"], r["naming"], r["evidence"]) == (a, n, e)]), "H": rate([r for r in H if (r["act"], r["naming"], r["evidence"]) == (a, n, e)])}
                       for a in ACTS for n in NAMES for e in EVS if any((r["act"], r["naming"], r["evidence"]) == (a, n, e) for r in rows)},
             "by_act": {a: rate([r for r in F if r["act"] == a]) for a in ACTS}, "by_naming": {n: rate([r for r in F if r["naming"] == n]) for n in NAMES},
             "by_evidence": {e: rate([r for r in F if r["evidence"] == e]) for e in EVS}, "n_F": len(F), "H_min": min((mean([r for r in H if r["exp"] == c]) for c in {r["exp"] for r in H}), default=None),
             "H_all": rate(H)}
        if True:
            d.update({"act": contrast(F, "act", "directive", "question"), "act_assert": contrast(F, "act", "assertion", "question"), "act_dir_assert": contrast(F, "act", "directive", "assertion"),
                      "naming": contrast(F, "naming", "named", "unnamed"), "page": contrast(F, "evidence", "page", "none"), "outside": contrast(F, "evidence", "outside", "none"),
                      "page_vs_outside": contrast(F, "evidence", "page", "outside"), "H_by_act": {a_: rate([r for r in H if r["act"] == a_]) for a_ in ACTS}})
        m[fmt] = d
    res["models"][mid] = m
res["total_spend"] = round(sum(m["spend"] for m in res["models"].values()), 4)
json.dump(res, open(HERE / "results_i.json", "w"), indent=1)
pc = lambda x: " –" if not x or x.get("rate") is None else f"{100 * x['rate']:3.0f}"
dd = lambda x: "  –" if not x else f"{100 * x['diff']:+4.0f}{'*' if x['counts'] else ' '}"
print(f"{'model':18} {'n':>5} | F by act: q  a  d | named-unnamed | eff: act(d-q) assert-q naming page-none outside-none page-outside | H | free F by act")
for m in res["models"].values():
    w = m.get("word")
    if not w:
        continue
    f = m.get("free")
    print(f"{m['label']:18} {m['n']:5} | {pc(w['by_act']['question'])} {pc(w['by_act']['assertion'])} {pc(w['by_act']['directive'])} | {pc(w['by_naming']['unnamed'])} {pc(w['by_naming']['named'])} | "
          f"{dd(w['act'])} {dd(w['act_assert'])} {dd(w['naming'])} {dd(w['page'])} {dd(w['outside'])} {dd(w['page_vs_outside'])} | {pc(w['H_all'])} | " + (f"{pc(f['by_act']['question'])} {pc(f['by_act']['assertion'])} {pc(f['by_act']['directive'])} page-none {dd(f['page'])}" if f else ""))
print("spend", res["total_spend"])
