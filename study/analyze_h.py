"""Analysis of experiment H: wordings, turns and fixes. Baselines (page_frame, citation; one-word and free-form) come from experiment G, same items."""
import json, random
from collections import defaultdict
from pathlib import Path
from labels import LABEL
import gen_h

HERE = Path(__file__).resolve().parent
RNG = random.Random(20261115)


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
rate = lambda rows: {"k": sum(map(ch, rows)), "n": len(rows), "rate": mean(rows), "ci": boot(rows, mean)} if rows else None


def FH(rows):
    return {"F": rate([r for r in rows if r["prior_right"]]), "H": rate([r for r in rows if not r["prior_right"]])}


res = {"models": {}}
for mid, lab in LABEL.items():
    R = load(HERE / "runs_h" / mid.replace("/", "__") / "responses.jsonl")
    if not R:
        continue
    G = [r for r in load(HERE / "runs_g" / mid.replace("/", "__") / "responses.jsonl").values() if r["step"] == "decide" and r["block"] < 4]
    dec = [r for r in R.values() if r["step"] == "decide"]
    m = {"label": lab, "n": len(R), "spend": round(sum(r.get("cost") or 0 for r in R.values()), 4), "malformed": sum(r.get("answer") is None for r in dec)}
    base = lambda c, fmt: FH([r for r in G if r["exp"] == c and r["fmt"] == fmt])
    m["base"] = {"page_word": base("page_frame", "word"), "citation_word": base("citation", "word"), "page_free": base("page_frame", "free"), "citation_free": base("citation", "free")}
    # wordings
    m["wording"] = {c: FH([r for r in dec if r["exp"] == c]) for c in ("citation_t1", "citation_t3", "page_b")}
    # fixes
    m["fix"] = {c: FH([r for r in dec if r["exp"] == c]) for c in ("note_page", "quote_page", "gate_page", "gate_citation", "warn_page")}
    q = [r for r in R.values() if r["exp"] == "quote_page" and r["step"] == "reply"]
    m["quote_exact"] = {"k": sum((r["line"].rstrip(".").lower() in (r.get("content") or "").lower()) == r["listed"] and (("none" in (r.get("content") or "").lower()) != r["listed"] or r["listed"]) for r in q), "n": len(q)} if q else None
    # turns: cumulative share changed by turn t (a conversation stops at its first change)
    m["turns"] = {}
    for c, turns in gen_h.MULTI.items():
        convs = defaultdict(dict)
        for r in dec:
            if r["exp"] == c:
                convs[r["id"].rsplit("-t", 1)[0]][int(r["id"].rsplit("-t", 1)[1])] = r
        out = {}
        for side, flag in (("F", True), ("H", False)):
            cs = [v for v in convs.values() if v[min(v)]["prior_right"] == flag]
            out[side] = [sum(any(ch(v[t]) for t in v if t <= T) for v in cs) / len(cs) if cs else None for T in range(1, len(turns) + 1)]
            out[side + "_n"] = len(cs)
        m["turns"][c] = out
    res["models"][mid] = m
res["total_spend"] = round(sum(m["spend"] for m in res["models"].values()), 4)
json.dump(res, open(HERE / "results_h.json", "w"), indent=1)
pc = lambda x: " –" if not x or x.get("rate") is None else f"{100 * x['rate']:3.0f}"
for m in res["models"].values():
    b, w, f, t = m["base"], m["wording"], m["fix"], m["turns"]
    tt = lambda c: "/".join("–" if v is None else f"{100 * v:.0f}" for v in t[c]["F"])
    print(f"{m['label']:17} F: page {pc(b['page_word']['F'])} page_b {pc(w['page_b']['F'])} | cit t1/t2/t3 {pc(w['citation_t1']['F'])}/{pc(b['citation_word']['F'])}/{pc(w['citation_t3']['F'])}"
          f" | fixes on page: note {pc(f['note_page']['F'])} (H {pc(f['note_page']['H'])}) quote {pc(f['quote_page']['F'])} (H {pc(f['quote_page']['H'])}) | free: base {pc(b['page_free']['F'])} gate {pc(f['gate_page']['F'])} (H {pc(f['gate_page']['H'])}) warn {pc(f['warn_page']['F'])}"
          f" | cit free base {pc(b['citation_free']['F'])} gate {pc(f['gate_citation']['F'])} | turns F: persist {tt('mt_persist')} yang {tt('mt_yang')} cit {tt('mt_citation')} page {tt('mt_page')}")
print("spend", res["total_spend"])
