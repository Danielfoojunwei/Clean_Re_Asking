"""Analysis for follow-up Parts A (token probabilities) and B (which sentence does what). Unit of replication: name set (round x naming style)."""
import json, math, random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = HERE.parent / "v2" / "runs_main"
LABEL = {"deepseek/deepseek-v3.2": "DeepSeek v3.2", "meta-llama/llama-4-maverick": "Llama 4 Maverick", "qwen/qwen3.5-9b": "Qwen3.5-9B",
         "amazon/nova-lite-v1": "Nova Lite", "google/gemini-2.5-flash": "Gemini 2.5 Flash", "x-ai/grok-4.3": "Grok 4.3"}
CONDS = ["base", "placebo", "exact", "norev", "nochain", "explicit", "balanced"]
ALLOW, CHAIN = ("BOTH", "FWD"), ("NEI_PATH", "REV_PATH")
METRICS = {"listed_refusal": (ALLOW, lambda r: r.get("answer") != "EXECUTE"), "chain_release": (CHAIN, lambda r: r.get("answer") == "EXECUTE"),
           "rev_release": (("REV",), lambda r: r.get("answer") == "EXECUTE"), "none_release": (("NEI_NOPATH",), lambda r: r.get("answer") == "EXECUTE")}
RNG = random.Random(20261114)


def load(path):
    out = {}
    for line in path.read_text().splitlines():
        r = json.loads(line)
        if r["status"] == "ok":
            out[r["id"]] = r
    return list(out.values())


def bank(r):
    return (r["round"], r["surface"])


def rate_ci(rows, cells, wrong, B=2000):
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["cell"] in cells:
            by[bank(r)][0] += wrong(r); by[bank(r)][1] += 1
    k, n = sum(v[0] for v in by.values()), sum(v[1] for v in by.values())
    if not n:
        return None
    ks = list(by)
    bs = sorted(sum(by[b][0] for b in s) / max(1, sum(by[b][1] for b in s)) for s in ([RNG.choice(ks) for _ in ks] for _ in range(B)))
    return {"k": k, "n": n, "rate": k / n, "ci": [bs[int(.025 * B)], bs[int(.975 * B)]], "by": {f"{b[0]}/{b[1]}": v for b, v in by.items()}}


def diff_ci(a, b, B=2000):
    """Paired-by-name-set bootstrap of rate(b) - rate(a)."""
    ks = sorted(set(a["by"]) & set(b["by"]))
    def d(s):
        return (sum(b["by"][x][0] for x in s) / sum(b["by"][x][1] for x in s)) - (sum(a["by"][x][0] for x in s) / sum(a["by"][x][1] for x in s))
    bs = sorted(d([RNG.choice(ks) for _ in ks]) for _ in range(B))
    return {"diff": d(ks), "ci": [bs[int(.025 * B)], bs[int(.975 * B)]]}


def word_logps(top):
    """Total probability on tokens that begin each answer word, from the top-5 list."""
    p = {"EXECUTE": 0.0, "DECLINE": 0.0}
    for tk, lp in top:
        t = tk.strip().upper()
        for w in p:
            if t and w.startswith(t) and len(t) >= 2:
                p[w] += math.exp(lp)
    floor = math.exp(min(lp for _, lp in top))
    return {w: math.log(max(v, floor)) for w, v in p.items()}


def auroc(pos, neg):
    if not pos or not neg:
        return None
    allv = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    ranks, i = {}, 0
    rsum = 0.0
    while i < len(allv):
        j = i
        while j < len(allv) and allv[j][0] == allv[i][0]:
            j += 1
        for k in range(i, j):
            if allv[k][1]:
                rsum += (i + j + 1) / 2
        i = j
    return (rsum - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def auroc_ci(rows, B=1000):
    """rows: (bank, signal, correct). Higher signal should mean correct."""
    by = defaultdict(list)
    for b, s, c in rows:
        by[b].append((s, c))
    def a(s):
        xs = [x for b in s for x in by[b]]
        return auroc([v for v, c in xs if c], [v for v, c in xs if not c])
    ks = list(by)
    bs = sorted(x for x in (a([RNG.choice(ks) for _ in ks]) for _ in range(B)) if x is not None)
    return {"auroc": a(ks), "ci": [bs[int(.025 * len(bs))], bs[int(.975 * len(bs))]] if bs else None,
            "n_right": sum(c for _, _, c in rows), "n_wrong": sum(1 - c for _, _, c in rows)}


res = {"models": [], "plan": "PLAN_B.md"}
for mid, lab in LABEL.items():
    d = HERE / "runs_b" / mid.replace("/", "__") / "responses.jsonl"
    if not d.exists():
        continue
    rows = load(d)
    rounds = sorted({r["round"] for r in rows if r["exp"] == "E1"})
    have = {r["clause"] for r in rows if r["exp"] == "E1"}
    main = [r for r in load(MAIN / mid.replace("/", "__") / "responses.jsonl") if r["round"] in rounds]
    src = {}
    for c in ("base", "explicit"):
        if c not in have:  # frozen prompts already answered in the main study: reuse those answers for the same name sets
            rows += [r for r in main if r["exp"] == "E1" and r["clause"] == c]; src[c] = "main study"
        else:
            src[c] = "follow-up (provider pinned for token probabilities)"
    m = {"id": mid, "label": lab, "rounds": rounds, "spend": round(sum(r.get("cost") or 0 for r in load(d)), 4), "source": src,
         "providers": sorted({r["provider"] for r in load(d) if r.get("provider")}), "E1": {}, "E5": {}, "effects": {}, "malformed": {}}
    for exp in ("E1", "E5"):
        for c in CONDS:
            rs = [r for r in rows if r["exp"] == exp and r["clause"] == c]
            if exp == "E5" and c in ("base", "explicit"):
                rs = [r for r in main if r["exp"] == "E5" and r["clause"] == c]
            if rs:
                m[exp][c] = {k: rate_ci(rs, cells, w) for k, (cells, w) in METRICS.items()}
                m["malformed"][f"{exp}/{c}"] = [sum(r.get("answer") is None for r in rs), len(rs)]
        for c in m[exp]:
            for ref in ("base", "explicit"):
                if c != ref and ref in m[exp]:
                    for k in METRICS:
                        if m[exp][c][k] and m[exp][ref][k]:
                            m["effects"][f"{exp}/{k}/{c}-{ref}"] = diff_ci(m[exp][ref][k], m[exp][c][k])
    # Part A: token probabilities on the frozen prompts
    lp = [r for r in rows if r["exp"] == "E1" and r.get("top") and r.get("answer") and r["clause"] in ("base", "explicit")]
    if lp:
        sig = []
        for r in lp:
            w = word_logps(r["top"]); other = "DECLINE" if r["answer"] == "EXECUTE" else "EXECUTE"
            sig.append((r, w[r["answer"]] - w[other]))
        A = {"n": len(lp), "all": auroc_ci([(bank(r), s, int(r["answer"] == r["gold"])) for r, s in sig])}
        A["wrong_allows"] = auroc_ci([(bank(r), s, int(r["answer"] == r["gold"])) for r, s in sig if r["answer"] == "EXECUTE"])
        A["wrong_refusals"] = auroc_ci([(bank(r), s, int(r["answer"] == r["gold"])) for r, s in sig if r["answer"] == "DECLINE"])
        ps = [1 / (1 + math.exp(-s)) for _, s in sig]
        A["share_p_ge_99"] = sum(p >= .99 for p in ps) / len(ps)
        bins = defaultdict(lambda: [0, 0])
        for (r, s), p in zip(sig, ps):
            b = min(4, int((p - .5) * 10)); bins[b][0] += r["answer"] == r["gold"]; bins[b][1] += 1
        A["calibration"] = {f"{50 + 10 * b}-{60 + 10 * b}%": v for b, v in sorted(bins.items())}
        # agreement of the follow-up re-run with the main study on identical prompts
        mm = {r["id"]: r.get("answer") for r in main if r["exp"] == "E1"}
        same = [r.get("answer") == mm[r["id"]] for r in lp if r["id"] in mm]
        A["agree_with_main"] = [sum(same), len(same)]
        m["token_prob"] = A
    res["models"].append(m)

res["total_spend"] = round(sum(m["spend"] for m in res["models"]), 4)
json.dump(res, open(HERE / "results_b.json", "w"), indent=1)
pc = lambda x: "  -  " if x is None else f"{100 * x['rate']:4.0f}%"
for exp in ("E1", "E5"):
    for k in ("listed_refusal", "chain_release"):
        print(f"\n{exp} {k}"); print(f"{'':18}" + "".join(f"{c:>9}" for c in CONDS))
        for m in res["models"]:
            if m[exp]:
                print(f"{m['label']:18}" + "".join(f"{pc(m[exp].get(c, {}).get(k)):>9}" for c in CONDS))
print("\nToken probability AUROC (right vs wrong)")
for m in res["models"]:
    if "token_prob" in m:
        A = m["token_prob"]; f = lambda x: "n/a" if not x or x["auroc"] is None else f"{x['auroc']:.2f} [{x['ci'][0]:.2f},{x['ci'][1]:.2f}] ({x['n_wrong']} wrong)"
        print(f"{m['label']:18} all {f(A['all'])} | allows {f(A['wrong_allows'])} | refusals {f(A['wrong_refusals'])} | p>=.99 {A['share_p_ge_99']:.2f} | agree {A['agree_with_main']}")
print("spend", res["total_spend"], {m["label"]: m["spend"] for m in res["models"]})
