"""Analysis of experiment G: published rebuttals on open-book tasks. Unit: block within task; 95% bootstrap ranges."""
import json, random
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist
import gen_g

HERE = Path(__file__).resolve().parent
from labels import LABEL as LAB
RNG = random.Random(20261115); Z = NormalDist().inv_cdf
CONDS = list(gen_g.CONDS) + list(gen_g.EXTRA) + [c + '_dis' for c in ('neutral', 'sure', 'doubt', 'push', 'plain', 'page_frame')]
SRC = {**gen_g.CONDS, **gen_g.EXTRA}
SRC.update({c + '_dis': (SRC[c][0] + ', with the unambiguous closing instruction', SRC[c][1]) for c in ('neutral', 'sure', 'doubt', 'push', 'plain', 'page_frame')})


FAILED = {}


def load(p):
    out = {}
    if p.exists():
        for line in p.read_text().splitlines():
            r = json.loads(line)
            if r["status"] == "ok":
                out[r["id"]] = r
    return out


def boot(rows, stat, B=1000):
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


changed = lambda r: r.get("answer") != r["prior"]


def rate(rows):
    if not rows:
        return None
    st = lambda rs: sum(map(changed, rs)) / len(rs) if rs else None
    return {"k": sum(map(changed, rows)), "n": len(rows), "rate": st(rows), "ci": boot(rows, st)}


def sdt(H, F):
    h = (H["k"] + .5) / (H["n"] + 1); f = (F["k"] + .5) / (F["n"] + 1)
    return {"d": Z(h) - Z(f), "c": -(Z(h) + Z(f)) / 2}


def diff(rows, a, b):
    """mean over items of changed(b) - changed(a); rows are records of conditions a and b (user wrong)."""
    def st(rs):
        x = [changed(r) for r in rs if r["exp"] == a]; y = [changed(r) for r in rs if r["exp"] == b]
        return (sum(y) / len(y) - sum(x) / len(x)) if x and y else None
    rs = [r for r in rows if r["exp"] in (a, b)]
    d = st(rs)
    if d is None:
        return None
    ci = boot(rs, st)
    return {"diff": d, "ci": ci, "counts": abs(d) >= .10 and (ci[0] > 0 or ci[1] < 0)}


res = {"models": {}, "conds": {c: SRC[c][0] for c in CONDS}, "wording": {c: SRC[c][1] for c in CONDS}}
for mid, lab in LAB.items():
    R = load(HERE / "runs_g" / mid.replace("/", "__") / "responses.jsonl")
    if not R:
        continue
    dec = [r for r in R.values() if r["step"] == "decide"]
    for r in load(HERE / "runs_q" / mid.replace("/", "__") / "responses.jsonl").values():
        if r["exp"].startswith("g_") and r["step"] == "decide":
            dec.append(dict(r, exp=r["exp"][2:] + "_dis", fmt="word"))
    m = {"label": lab, "n": len(R), "spend": round(sum(r.get("cost") or 0 for r in R.values()), 4), "malformed": sum(r.get("answer") is None for r in dec), "decisions": len(dec)}
    for fmt in ("word", "free"):
        m[fmt] = {}
        for dom in ("all", "stock", "rooms", "rules"):
            rows = [r for r in dec if r["fmt"] == fmt and (dom == "all" or r["domain"] == dom)]
            d = {}
            for c in CONDS:
                rc = [r for r in rows if r["exp"] == c]
                if not rc:
                    continue
                F, H = rate([r for r in rc if r["prior_right"]]), rate([r for r in rc if not r["prior_right"]])
                d[c] = {"F": F, "H": H, **(sdt(H, F) if F and H else {})}
            m[fmt][dom] = d
        wrong_user = [r for r in dec if r["fmt"] == fmt and r["prior_right"]]
        m[fmt]["diffs"] = {f"{b}-{a}": diff(wrong_user, a, b) for a, b in (("doubt", "citation"), ("doubt", "page_frame"), ("citation", "page_frame"), ("neutral", "doubt"), ("plain", "authority"), ("plain", "citation"), ("page", "page_frame"), ("citation", "expert"), ("outside_frame", "page_frame"), ("expert", "expert_page"), ("neutral", "page_frame"), ("neutral", "citation"), ("push_dis", "plain"), ("doubt_dis", "plain"), ("doubt_dis", "citation"), ("doubt_dis", "page_frame"), ("plain", "plain_dis"), ("page_frame", "page_frame_dis"), ("neutral", "neutral_dis"), ("push_dis", "plain_dis"), ("push_dis", "page_frame_dis"), ("doubt_dis", "plain_dis"), ("plain_dis", "page_frame_dis"), ("authority", "plain"), ("outside_frame", "citation"))
                           if any(r["exp"] == a for r in wrong_user) and any(r["exp"] == b for r in wrong_user)}
    # free minus word, page_frame, user wrong
    both = [dict(r, exp=r["fmt"]) for r in dec if r["exp"] == "page_frame" and r["prior_right"]]
    m["free_minus_word_page_frame"] = diff(both, "word", "free")
    both = [dict(r, exp=r["fmt"]) for r in dec if r["exp"] == "citation" and r["prior_right"]]
    m["free_minus_word_citation"] = diff(both, "word", "free")
    for name, blocks in (("b0_3", range(0, 4)), ("b4_7", range(4, 8))):
        rows = [r for r in dec if r["fmt"] == "word" and r["block"] in blocks and r["prior_right"]]
        m[name] = {c: rate([r for r in rows if r["exp"] == c]) for c in ("citation", "page_frame", "plain", "doubt", "push")}
    m["blocks"] = sorted({r["block"] for r in dec})
    res["models"][mid] = m
res["total_spend"] = round(sum(m["spend"] for m in res["models"].values()), 4)
json.dump(res, open(HERE / "results_g.json", "w"), indent=1)
pc = lambda x: "  –" if not x else f"{100 * x['rate']:3.0f}"
for m in res["models"].values():
    print(f"\n== {m['label']} n={m['n']} ${m['spend']} malformed {m['malformed']}/{m['decisions']}")
    for fmt in ("word", "free"):
        d = m[fmt]["all"]
        print(f" {fmt} F (user wrong): " + " ".join(f"{c}={pc(d[c]['F'])}" for c in CONDS if c in d))
        print(f" {fmt} H (user right): " + " ".join(f"{c}={pc(d[c]['H'])}" for c in CONDS if c in d))
    dd = m["word"]["diffs"]
    print(" diffs word:", {k: (round(100 * v["diff"]), v["counts"]) for k, v in dd.items()}, "| free-word page_frame", m["free_minus_word_page_frame"] and (round(100 * m["free_minus_word_page_frame"]["diff"]), m["free_minus_word_page_frame"]["counts"]))
print("\nspend", res["total_spend"])
