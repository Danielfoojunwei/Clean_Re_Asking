"""Builds fig_data.json: the single source for every figure and table in the paper."""
import collections, glob, json, os, random
V2 = "../v2"
ORDER = [("openai/gpt-4.1", "GPT-4.1"), ("openai/gpt-4.1-mini", "GPT-4.1-mini"), ("x-ai/grok-4.3", "Grok 4.3"),
         ("google/gemini-2.5-flash", "Gemini 2.5 Flash"), ("anthropic/claude-haiku-5.5", "Claude Haiku 5.5"),
         ("deepseek/deepseek-v3.2", "DeepSeek v3.2"), ("meta-llama/llama-4-maverick", "Llama 4 Maverick"),
         ("qwen/qwen3.5-9b", "Qwen3.5-9B"), ("amazon/nova-lite-v1", "Nova Lite")]
CELLS = ["BOTH", "FWD", "REV", "REV_PATH", "NEI_PATH", "NEI_NOPATH"]
res = {m["model"]: m for m in json.load(open(f"{V2}/main_results.json"))["models"]}

def load(mid):
    ok = {}
    for l in open(f"{V2}/runs_main/{mid.replace('/', '__')}/responses.jsonl"):
        r = json.loads(l)
        if r["status"] == "ok" and r["round"] >= 1:
            ok[r["id"]] = r
    return list(ok.values())

def boot(per, fn, reps=4000, seed=11):
    rng = random.Random(seed); keys = sorted(per); vals = []
    for _ in range(reps):
        v = fn([rng.choice(keys) for _ in keys])
        if v is not None: vals.append(v)
    vals.sort()
    return [vals[int(.025 * len(vals))], vals[min(len(vals) - 1, int(.975 * len(vals)))]] if vals else [None, None]

out = {"models": [], "order": [lab for _, lab in ORDER], "cells": CELLS}
tot = collections.Counter()
for mid, lab in ORDER:
    rs = load(mid); M = res[mid]
    bank = lambda r: f'{r["round"]}/{r["surface"]}'
    d = {"id": mid, "label": lab, "banks": len({bank(r) for r in rs}), "rounds": len({r["round"] for r in rs}),
         "spend": M["spend"], "accounting": M["accounting"], "providers": M["providers"],
         "cells": M["cells_by_clause"], "idx": M["H10_clause"], "H2": M["H2"], "H3": M["H3"], "H6": M["H6"],
         "H7": M["H7_inputs"], "bridge": M["H11_bridge"], "surface": M["H8_surface"], "qual": M["qualification"],
         "restate": M["E4_restated_route"]}
    tot["responses"] += len(rs); tot["malformed"] += sum(r.get("answer") is None for r in rs)
    dec = {e: [r for r in rs if r["exp"] == e] for e in ("E1", "E4", "E4p", "E5")}
    # rate tables with bank-bootstrap intervals
    def rate(rows, cells, want, clause=None, extra=None):
        per = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            if r["cell"] in cells and (clause is None or r["clause"] == clause) and (extra is None or extra(r)):
                per[bank(r)][0] += r["answer"] == want; per[bank(r)][1] += 1
        f = lambda ks: (lambda n: None if not n else sum(per[k][0] for k in ks) / n)(sum(per[k][1] for k in ks))
        return {"n": sum(v[1] for v in per.values()), "k": sum(v[0] for v in per.values()), "rate": f(list(per)),
                "ci": boot(per, f), "per_bank": {k: v[0] / v[1] for k, v in sorted(per.items()) if v[1]}}
    d["rates"] = {}
    for e in dec:
        for cl in ("base", "explicit"):
            d["rates"][f"{e}/{cl}"] = {
                "chain_release": rate(dec[e], ("REV_PATH", "NEI_PATH"), "EXECUTE", cl),
                "chainonly_release": rate(dec[e], ("NEI_PATH",), "EXECUTE", cl),
                "revpath_release": rate(dec[e], ("REV_PATH",), "EXECUTE", cl),
                "rev_release": rate(dec[e], ("REV",), "EXECUTE", cl),
                "none_release": rate(dec[e], ("NEI_NOPATH",), "EXECUTE", cl),
                "listed_refusal": rate(dec[e], ("FWD", "BOTH"), "DECLINE", cl),
                "fwd_refusal": rate(dec[e], ("FWD",), "DECLINE", cl),
                "both_refusal": rate(dec[e], ("BOTH",), "DECLINE", cl),
                "accuracy": (lambda rows: sum(r["answer"] == r["gold"] for r in rows) / max(1, len(rows)))(
                    [r for r in dec[e] if r["clause"] == cl])}
    # paired procedure effects versus direct answers (same items), by clause
    def paired(e, cells, want, cl):
        a = {r["id"].rsplit("/", 1)[0]: r for r in dec[e] if r["cell"] in cells and r["clause"] == cl}
        b = {r["id"].rsplit("/", 1)[0]: r for r in dec["E1"] if r["cell"] in cells and r["clause"] == cl}
        per = collections.defaultdict(lambda: [0, 0, 0])
        for k in set(a) & set(b):
            p = per[bank(a[k])]; p[0] += a[k]["answer"] == want; p[1] += b[k]["answer"] == want; p[2] += 1
        f = lambda ks: (lambda n: None if not n else (sum(per[k][0] for k in ks) - sum(per[k][1] for k in ks)) / n)(
            sum(per[k][2] for k in ks))
        return {"diff": f(list(per)), "ci": boot(per, f, reps=3000)}
    d["effects"] = {f"{e}/{cl}": {"chain_release": paired(e, ("REV_PATH", "NEI_PATH"), "EXECUTE", cl),
                                  "listed_kept": paired(e, ("FWD", "BOTH"), "EXECUTE", cl)}
                    for e in ("E4", "E4p", "E5") for cl in ("base", "explicit")}
    e1 = dec["E1"]
    pos = collections.defaultdict(lambda: [0, 0])
    for r in e1:
        if r["cell"] in ("FWD", "BOTH"):
            pos[f'{r["surface"]}/{r["pos_fwd"]}'][0] += r["answer"] == "DECLINE"; pos[f'{r["surface"]}/{r["pos_fwd"]}'][1] += 1
    d["refusal_by_position"] = dict(sorted(pos.items()))
    ro = collections.defaultdict(lambda: [0, 0])
    for r in e1:
        ro[f'{r["cell"]}/{r["rec"]}'][0] += (r["answer"] is not None and r["answer"] != r["gold"]); ro[f'{r["cell"]}/{r["rec"]}'][1] += 1
    d["wrong_by_role_order"] = dict(sorted(ro.items()))
    e2 = {r["id"][:-3]: r["answer"] for r in rs if r["exp"] == "E2" and r["answer"] is not None}
    e3 = {r["id"][:-3]: r["answer"] for r in rs if r["exp"] == "E3"}
    conf = collections.defaultdict(collections.Counter); rc = collections.defaultdict(collections.Counter)
    for r in e1:
        if r["answer"] is None: continue
        k = r["id"][:-3]
        kind = "correct" if r["answer"] == r["gold"] else ("wrong_refusal" if r["gold"] == "EXECUTE" else "wrong_release")
        if k in e2:
            c = e2[k]; conf[kind]["100" if c == 100 else "90-99" if c >= 90 else "50-89" if c >= 50 else "<50"] += 1
            tot["conf_n"] += 1; tot["conf_100"] += c == 100
        if k in e3: rc[kind][e3[k] or "MALFORMED"] += 1
    d["confidence"] = {k: dict(v) for k, v in conf.items()}; d["recheck"] = {k: dict(v) for k, v in rc.items()}
    e6 = [r for r in rs if r["exp"] == "E6"]; e7 = [r for r in rs if r["exp"] == "E7"]
    d["components"] = {"roles": [sum(r["answer"] == r["gold"] for r in e6), len(e6)],
                       "lookup": [sum(r["answer"] == r["gold"] for r in e7), len(e7)],
                       "decision": [sum(r["answer"] == r["gold"] for r in e1), len(e1)],
                       "decision_reasoned": [sum(r["answer"] == r["gold"] for r in dec["E5"]), len(dec["E5"])]}
    comp = M["H6"]["wrong_E1_by_component_state"]
    d["components"]["wrong_total"] = sum(comp.values())
    d["components"]["wrong_both_right"] = sum(v for k, v in comp.items() if k.endswith("both_components_correct"))
    out["models"].append(d)
out["totals"] = dict(tot)
out["totals"]["spend_main"] = round(sum(m["spend"] for m in out["models"]), 2)
out["summary"] = json.load(open(f"{V2}/main_results.json"))["summary"]
json.dump(out, open("fig_data.json", "w"), indent=1)
print(out["totals"], [(m["label"], m["banks"]) for m in out["models"]])
