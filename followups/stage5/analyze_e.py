"""Analysis of the harness-side fixes (E1 check-then-decide, E2 harness check) against the same items without a fix (D3-evidence)."""
import json, random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = {m: v["label"] for m, v in json.load(open(HERE / "results_d.json"))["models"].items()}
HK = "anthropic/claude-haiku-5.5"
RNG = random.Random(20261115)
bank = lambda r: (r["round"], r["surface"])


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
        by[bank(r)].append(r)
    ks = list(by); vals = []
    for _ in range(B):
        v = stat([x for k in (RNG.choice(ks) for _ in ks) for x in by[k]])
        if v is not None:
            vals.append(v)
    vals.sort()
    return [vals[int(.025 * len(vals))], vals[int(.975 * len(vals)) - 1]] if vals else None


def rate(rows, f):
    if not rows:
        return None
    st = lambda rs: (sum(bool(f(r)) for r in rs) / len(rs)) if rs else None
    return {"k": sum(bool(f(r)) for r in rows), "n": len(rows), "rate": st(rows), "ci": boot(rows, st)}


def paired_diff(rows):
    """rows carry base_changed and fix_changed for the same item; fix minus base."""
    st = lambda rs: (sum(r["fix"] for r in rs) - sum(r["base"] for r in rs)) / len(rs) if rs else None
    d = st(rows)
    if d is None:
        return None
    ci = boot(rows, st)
    return {"diff": d, "ci": ci, "counts": abs(d) >= .10 and (ci[0] > 0 or ci[1] < 0)}


res = {"models": {}}
for mid, lab in LAB.items():
    d = mid.replace("/", "__")
    E = load(HERE / "runs_e" / d / "responses.jsonl")
    if not E:
        continue
    base = load(HERE / ("runs_d_long" if mid == HK else "runs_d") / d / "responses.jsonl")
    m = {"label": lab, "n": len(E), "spend": round(sum(r.get("cost") or 0 for r in E.values()), 4)}
    keys = sorted({i.rsplit("/", 1)[0] for i in E})
    B = {k: base.get(k + "/D3-evidence") for k in keys}
    chk = [E[k + "/E1-check"] for k in keys if k + "/E1-check" in E]
    m["check_correct"] = rate(chk, lambda r: r.get("answer") == ("LISTED" if r["listed"] else "MISSING"))
    for name, suf in (("base", None), ("E1", "/E1-decide"), ("E2", "/E2")):
        rows = [B[k] for k in keys if B[k]] if suf is None else [E[k + suf] for k in keys if k + suf in E]
        R = [r for r in rows if r["e1_answer"] == r["gold"]]; W = [r for r in rows if r["e1_answer"] != r["gold"]]
        ch = lambda r: r.get("answer") != r["e1_answer"]
        m[name] = {"right_changed": rate(R, ch), "wrong_changed": rate(W, ch), "accuracy_after": rate(rows, lambda r: r.get("answer") == r["gold"]),
                   "accuracy_before": rate(rows, lambda r: r["e1_answer"] == r["gold"]), "malformed": sum(r.get("answer") is None for r in rows)}
    for name, suf in (("E1", "/E1-decide"), ("E2", "/E2")):
        pr = [dict(B[k], base=B[k].get("answer") != B[k]["e1_answer"], fix=E[k + suf].get("answer") != E[k + suf]["e1_answer"])
              for k in keys if B[k] and k + suf in E and B[k]["e1_answer"] == B[k]["gold"]]
        m[name]["right_changed_vs_base"] = paired_diff(pr)
    res["models"][mid] = m
res["total_spend"] = round(sum(m["spend"] for m in res["models"].values()), 4)
json.dump(res, open(HERE / "results_e.json", "w"), indent=1)
p = lambda x: " n/a" if not x or x.get("rate") is None else f"{100 * x['rate']:3.0f}%"
for m in res["models"].values():
    print(f"{m['label']:18} n={m['n']:4} check ok {p(m['check_correct'])} | right given up: base {p(m['base']['right_changed'])} E1 {p(m['E1']['right_changed'])} E2 {p(m['E2']['right_changed'])}"
          f" | wrong fixed: base {p(m['base']['wrong_changed'])} E1 {p(m['E1']['wrong_changed'])} E2 {p(m['E2']['wrong_changed'])} | acc {p(m['base']['accuracy_before'])} -> base {p(m['base']['accuracy_after'])} E1 {p(m['E1']['accuracy_after'])} E2 {p(m['E2']['accuracy_after'])}"
          f" | malformed {m['E1']['malformed']},{m['E2']['malformed']}")
print("spend", res["total_spend"])
