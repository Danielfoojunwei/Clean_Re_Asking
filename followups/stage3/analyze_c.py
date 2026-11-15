"""Analysis for Stage 3 (X1-X7). Unit: name set (round x naming style); 95% bootstrap intervals over name sets."""
import json, random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = HERE.parent / "v2" / "runs_main"
LABEL = {"openai/gpt-4.1": "GPT-4.1", "x-ai/grok-4.3": "Grok 4.3", "google/gemini-2.5-flash": "Gemini 2.5 Flash", "anthropic/claude-haiku-5.5": "Claude Haiku 5.5",
         "deepseek/deepseek-v3.2": "DeepSeek v3.2", "meta-llama/llama-4-maverick": "Llama 4 Maverick", "qwen/qwen3.5-9b": "Qwen3.5-9B", "amazon/nova-lite-v1": "Nova Lite"}
ALLOW, CHAIN = ("BOTH", "FWD"), ("NEI_PATH", "REV_PATH")
RNG = random.Random(20261115)
refused = lambda r: r.get("answer") != "EXECUTE"
allowed = lambda r: r.get("answer") == "EXECUTE"


def load(p):
    out = {}
    if p.exists():
        for line in p.read_text().splitlines():
            r = json.loads(line)
            if r["status"] == "ok":
                out[r["id"]] = r
    return list(out.values())


def tally(rows, f):
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        by[(r["round"], r["surface"])][0] += bool(f(r)); by[(r["round"], r["surface"])][1] += 1
    return by


def rate(rows, f, B=2000):
    by = tally(rows, f)
    k, n = sum(v[0] for v in by.values()), sum(v[1] for v in by.values())
    if not n:
        return None
    ks = list(by)
    bs = sorted(sum(by[b][0] for b in s) / max(1, sum(by[b][1] for b in s)) for s in ([RNG.choice(ks) for _ in ks] for _ in range(B)))
    return {"k": k, "n": n, "rate": k / n, "ci": [bs[int(.025 * B)], bs[int(.975 * B)]]}


def diff(rows_a, fa, rows_b, fb, B=2000):
    """rate(b) - rate(a), resampling the name sets present in both."""
    a, b = tally(rows_a, fa), tally(rows_b, fb)
    ks = sorted(set(a) & set(b))
    if not ks or not sum(a[x][1] for x in ks) or not sum(b[x][1] for x in ks):
        return None
    d = lambda s: sum(b[x][0] for x in s) / max(1, sum(b[x][1] for x in s)) - sum(a[x][0] for x in s) / max(1, sum(a[x][1] for x in s))
    bs = sorted(d([RNG.choice(ks) for _ in ks]) for _ in range(B))
    out = {"diff": d(ks), "ci": [bs[int(.025 * B)], bs[int(.975 * B)]], "sets": len(ks)}
    out["counts"] = abs(out["diff"]) >= .10 and (out["ci"][0] > 0 or out["ci"][1] < 0)
    return out


def cells(rows, cs):
    return [r for r in rows if r["cell"] in cs]


res = {"models": {}}
for mid, lab in LABEL.items():
    rows = load(HERE / "runs_c" / mid.replace("/", "__") / "responses.jsonl")
    if not rows:
        continue
    main = load(MAIN / mid.replace("/", "__") / "responses.jsonl")
    m = {"label": lab, "spend": round(sum(r.get("cost") or 0 for r in rows), 4), "n": len(rows)}
    X = lambda e: [r for r in rows if r["exp"] == e]
    rs = lambda e: sorted({r["round"] for r in X(e)})
    E1 = lambda cl, rounds, exp="E1": [r for r in main if r["exp"] == exp and r["clause"] in cl and r["round"] in rounds]
    m["malformed"] = {e: [sum(r.get("answer") is None for r in X(e)), len(X(e))] for e in sorted({r["exp"] for r in rows})}

    if X("X1"):  # rulebook size
        base4 = [r for r in E1(("base",), rs("X1")) if r["policy"] in ("P", "PT")]
        by = {4: base4, **{K: [r for r in X("X1") if r["size"] == K] for K in (8, 16, 32)}}
        big = [r for r in X("X1") if r["size"] in (16, 32) and r["cell"] in ALLOW and r["pos_fwd"] is not None]
        third = lambda r: min(2, int(3 * r["pos_fwd"] / r["size"]))
        m["X1"] = {"rounds": rs("X1"),
                   "listed_refusal": {K: rate(cells(v, ALLOW), refused) for K, v in by.items()},
                   "chain_release": {K: rate(cells(v, ("NEI_PATH",)), allowed) for K, v in by.items()},
                   "rev_release": {K: rate(cells(v, ("REV",)), allowed) for K, v in by.items()},
                   "none_release": {K: rate(cells(v, ("NEI_NOPATH",)), allowed) for K, v in by.items()},
                   "refusal_32_minus_4": diff(cells(by[4], ALLOW), refused, cells(by[32], ALLOW), refused),
                   "chain_32_minus_4": diff(cells(by[4], ("NEI_PATH",)), allowed, cells(by[32], ("NEI_PATH",)), allowed),
                   "wrong_allow_32_minus_4": diff(cells(by[4], ("NEI_PATH", "NEI_NOPATH", "REV")), allowed, cells(by[32], ("NEI_PATH", "NEI_NOPATH", "REV")), allowed),
                   "wrong_allow": {K: rate(cells(v, ("NEI_PATH", "NEI_NOPATH", "REV")), allowed) for K, v in by.items()},
                   "none_32_minus_4": diff(cells(by[4], ("NEI_NOPATH",)), allowed, cells(by[32], ("NEI_NOPATH",)), allowed),
                   "by_third": [rate([r for r in big if third(r) == t], refused) for t in range(3)],
                   "last_minus_first_third": diff([r for r in big if third(r) == 0], refused, [r for r in big if third(r) == 2], refused)}

    if X("X2"):  # asking again
        o = {}
        for v in ("neutral", "doubt", "affirm"):
            vr = [r for r in X("X2") if r["variant"] == v]
            right = [r for r in vr if r["e1_answer"] == r["gold"]]; wrong = [r for r in vr if r["e1_answer"] != r["gold"]]
            ch = lambda r: r.get("answer") != r["e1_answer"]
            o[v] = {"changed_right": rate(right, ch), "changed_wrong": rate(wrong, ch), "wrong_minus_right": diff(right, ch, wrong, ch),
                    "accuracy_after": rate(vr, lambda r: r.get("answer") == r["gold"]), "accuracy_before": rate(vr, lambda r: r["e1_answer"] == r["gold"])}
        nr = [r for r in X("X2") if r["variant"] == "neutral" and r["e1_answer"] == r["gold"]]
        dr = [r for r in X("X2") if r["variant"] == "doubt" and r["e1_answer"] == r["gold"]]
        o["doubt_minus_neutral_on_right"] = diff(nr, lambda r: r.get("answer") != r["e1_answer"], dr, lambda r: r.get("answer") != r["e1_answer"])
        m["X2"] = o

    if X("X3b"):  # premise first, then decision
        b = X("X3b"); quick = E1(("base",), rs("X3b"))
        said_yes = [r for r in b if r["lookup_answer"] == "YES"]; said_no = [r for r in b if r["lookup_answer"] == "NO"]
        m["X3"] = {"lookup_correct": rate(X("X3a"), lambda r: r.get("answer") == r["gold"]),
                   "listed_refusal_quick": rate(cells(quick, ALLOW), refused), "listed_refusal_scaffold": rate(cells(b, ALLOW), refused),
                   "refusal_change": diff(cells(quick, ALLOW), refused, cells(b, ALLOW), refused),
                   "chain_release_quick": rate(cells(quick, CHAIN), allowed), "chain_release_scaffold": rate(cells(b, CHAIN), allowed),
                   "chain_change": diff(cells(quick, CHAIN), allowed, cells(b, CHAIN), allowed),
                   "said_yes_then_refused": rate(said_yes, refused), "said_no_then_allowed": rate(said_no, allowed),
                   "accuracy_quick": rate(quick, lambda r: r.get("answer") == r["gold"]), "accuracy_scaffold": rate(b, lambda r: r.get("answer") == r["gold"])}

    if X("X4_E5"):  # "route" -> "entry"
        o = {}
        for e in ("E1", "E5"):
            w = X("X4_" + e); f = E1(("base",), rs("X4_" + e), e)
            o[e] = {"chain_route": rate(cells(f, CHAIN), allowed), "chain_entry": rate(cells(w, CHAIN), allowed), "chain_change": diff(cells(f, CHAIN), allowed, cells(w, CHAIN), allowed),
                    "refusal_route": rate(cells(f, ALLOW), refused), "refusal_entry": rate(cells(w, ALLOW), refused), "refusal_change": diff(cells(f, ALLOW), refused, cells(w, ALLOW), refused)}
        m["X4"] = o

    if X("X5"):  # GPT-4.1 role order on fresh name sets
        rev = cells(X("X5"), ("REV",))
        a1 = [r for r in rev if r["rec"] == "a_first"]; d1 = [r for r in rev if r["rec"] == "d_first"]
        allw = X("X5")
        m["X5"] = {"rounds": rs("X5"), "rev_receiver_first": rate(a1, allowed), "rev_sender_first": rate(d1, allowed), "gap": diff(d1, allowed, a1, allowed),
                   "wrong_receiver_first": rate([r for r in allw if r["rec"] == "a_first"], lambda r: r.get("answer") != r["gold"]),
                   "wrong_sender_first": rate([r for r in allw if r["rec"] == "d_first"], lambda r: r.get("answer") != r["gold"])}

    if X("X6"):  # hidden reasoning on
        o = {"reasoning_tokens_mean": sum(r.get("reasoning_tokens") or 0 for r in X("X6")) / len(X("X6"))}
        for cl in ("base", "explicit"):
            t = [r for r in X("X6") if r["clause"] == cl]; f = E1((cl,), rs("X6"))
            o[cl] = {"refusal_off": rate(cells(f, ALLOW), refused), "refusal_on": rate(cells(t, ALLOW), refused), "refusal_change": diff(cells(f, ALLOW), refused, cells(t, ALLOW), refused),
                     "chain_off": rate(cells(f, CHAIN), allowed), "chain_on": rate(cells(t, CHAIN), allowed), "chain_change": diff(cells(f, CHAIN), allowed, cells(t, CHAIN), allowed)}
        m["X6"] = o

    if X("X7"):  # acting with a tool
        o = {}
        for cl in ("base", "explicit"):
            t = [r for r in X("X7") if r["clause"] == cl]; f = E1((cl,), rs("X7"))
            o[cl] = {"refusal_words": rate(cells(f, ALLOW), refused), "refusal_action": rate(cells(t, ALLOW), refused),
                     "chain_words": rate(cells(f, CHAIN), allowed), "chain_action": rate(cells(t, CHAIN), allowed),
                     "rev_words": rate(cells(f, ("REV",)), allowed), "rev_action": rate(cells(t, ("REV",)), allowed),
                     "none_action": rate(cells(t, ("NEI_NOPATH",)), allowed)}
        calls = [r for r in X("X7") if r.get("tool")]
        KEYS = {"opaque": ("document_scope", "active_scope"), "natural": ("sending_department", "receiving_department")}
        def args(r):  # (sender, receiver) as the model passed them, read by parameter name
            try:
                d = json.loads(r["tool"]["arguments"]); k = KEYS[r["surface"]]
                return (d.get(k[0]), d.get(k[1]))
            except Exception:
                return (None, None)
        o["calls"] = len(calls)
        o["swapped_arguments"] = sum(args(r) == (r["a"], r["d"]) for r in calls)
        o["other_arguments"] = sum(args(r) not in ((r["d"], r["a"]), (r["a"], r["d"])) for r in calls)
        o["no_response"] = sum(1 for r in X("X7") if not r.get("tool") and not (r.get("content") or "").strip())
        o["called_while_saying_decline"] = sum("DECLINE" in (r.get("content") or "") for r in calls)
        m["X7"] = o
    res["models"][mid] = m

res["total_spend"] = round(sum(m["spend"] for m in res["models"].values()), 4)
json.dump(res, open(HERE / "results_c.json", "w"), indent=1)
p = lambda x: " n/a" if not x else f"{100 * x['rate']:3.0f}%"
dd = lambda x: "n/a" if not x else f"{100 * x['diff']:+.0f} [{100 * x['ci'][0]:+.0f},{100 * x['ci'][1]:+.0f}]{'*' if x['counts'] else ''}"
for mid, m in res["models"].items():
    print(f"\n== {m['label']}  n={m['n']}  ${m['spend']}  malformed {m['malformed']}")
    if "X1" in m:
        x = m["X1"]; print(" X1 refusal by size", {K: p(v) for K, v in x["listed_refusal"].items()}, "32-4", dd(x["refusal_32_minus_4"]), "| thirds", [p(v) for v in x["by_third"]], dd(x["last_minus_first_third"]),
                         "| unconnected allowed", {K: p(v) for K, v in x["none_release"].items()}, "| chain", {K: p(v) for K, v in x["chain_release"].items()})
    if "X2" in m:
        for v in ("neutral", "doubt", "affirm"):
            x = m["X2"][v]; print(f" X2 {v:8} changed right {p(x['changed_right'])} wrong {p(x['changed_wrong'])} gap {dd(x['wrong_minus_right'])} acc {p(x['accuracy_before'])}->{p(x['accuracy_after'])}")
        print("    doubt-neutral on right:", dd(m["X2"]["doubt_minus_neutral_on_right"]))
    if "X3" in m:
        x = m["X3"]; print(f" X3 lookup {p(x['lookup_correct'])} | refusal {p(x['listed_refusal_quick'])}->{p(x['listed_refusal_scaffold'])} {dd(x['refusal_change'])} | chain {p(x['chain_release_quick'])}->{p(x['chain_release_scaffold'])} {dd(x['chain_change'])} | yes-then-refused {x['said_yes_then_refused'] and (x['said_yes_then_refused']['k'], x['said_yes_then_refused']['n'])} no-then-allowed {x['said_no_then_allowed'] and (x['said_no_then_allowed']['k'], x['said_no_then_allowed']['n'])}")
    if "X4" in m:
        for e in ("E1", "E5"):
            x = m["X4"][e]; print(f" X4 {e} chain {p(x['chain_route'])}->{p(x['chain_entry'])} {dd(x['chain_change'])} | refusal {p(x['refusal_route'])}->{p(x['refusal_entry'])} {dd(x['refusal_change'])}")
    if "X5" in m:
        x = m["X5"]; print(f" X5 wrong-way allowed: receiver first {x['rev_receiver_first']['k']}/{x['rev_receiver_first']['n']} sender first {x['rev_sender_first']['k']}/{x['rev_sender_first']['n']} gap {dd(x['gap'])} | all wrong {p(x['wrong_receiver_first'])} vs {p(x['wrong_sender_first'])}")
    if "X6" in m:
        for cl in ("base", "explicit"):
            x = m["X6"][cl]; print(f" X6 {cl:8} refusal {p(x['refusal_off'])}->{p(x['refusal_on'])} {dd(x['refusal_change'])} | chain {p(x['chain_off'])}->{p(x['chain_on'])} {dd(x['chain_change'])}")
    if "X7" in m:
        for cl in ("base", "explicit"):
            x = m["X7"][cl]; print(f" X7 {cl:8} refusal words {p(x['refusal_words'])} action {p(x['refusal_action'])} | chain {p(x['chain_words'])} / {p(x['chain_action'])} | wrong-way {p(x['rev_words'])} / {p(x['rev_action'])} | unconnected {p(x['none_action'])}")
        x = m["X7"]; print(f"    calls {x['calls']} swapped {x['swapped_arguments']} other-args {x['other_arguments']} called-while-saying-DECLINE {x['called_while_saying_decline']} empty {x['no_response']}")
print("\ntotal spend", res["total_spend"])
