"""Analysis for V2, following PLAN.md. Usage: analyze.py RUNS_DIR FIRST_ROUND LAST_ROUND OUT_PREFIX"""
import collections
import json
import random
import re
import sys
from pathlib import Path

import gen

CELLS = ["BOTH", "FWD", "REV", "REV_PATH", "NEI_PATH", "NEI_NOPATH"]
DENIED = ("REV", "REV_PATH", "NEI_PATH", "NEI_NOPATH")


def load(model_dir, lo, hi):
    ok, fails = {}, collections.Counter()
    for line in (model_dir / "responses.jsonl").read_text().splitlines():
        r = json.loads(line)
        if not lo <= r["round"] <= hi:
            continue
        if r["status"] == "ok":
            ok[r["id"]] = r
        else:
            fails[r["id"]] += 1
    return ok, fails


def expected_ids(lo, hi):
    return {i["id"]: i for rnd in range(lo, hi + 1) for i in gen.items(rnd)}


def rate(n, d):
    return None if not d else n / d


def boot(banks, fn, reps=4000, seed=7):
    """Percentile interval for fn(list of bank keys), resampling banks."""
    rng = random.Random(seed)
    keys = sorted(banks)
    vals = []
    for _ in range(reps):
        v = fn([rng.choice(keys) for _ in keys])
        if v is not None:
            vals.append(v)
    if not vals:
        return [None, None]
    vals.sort()
    return [vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))]]


def auroc(pos, neg):
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def spearman(x, y):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return None if den == 0 else num / den


def analyse_model(model_dir, lo, hi):
    ok, fails = load(model_dir, lo, hi)
    exp = expected_ids(lo, hi)
    res = {"model": model_dir.name.replace("__", "/"), "rounds": [lo, hi]}
    bank_of = lambda r: (r["round"], r["surface"])

    def rows(e):
        return [ok[i] for i, it in exp.items() if it["exp"] == e and i in ok]

    def missing(e):
        return sum(1 for i, it in exp.items() if it["exp"] == e and i not in ok)

    # ---- accounting: every expected first-stage item is ok or missing
    res["accounting"] = {e: {"expected": sum(1 for it in exp.values() if it["exp"] == e), "ok": len(rows(e)),
                             "missing_after_retries": missing(e),
                             "malformed": sum(r["answer"] is None for r in rows(e))} for e in
                         ("E0", "E1", "E4", "E4p", "E5", "E6", "E7")}
    e1 = rows("E1")
    e1_valid = [r for r in e1 if r["answer"] is not None]
    for e in ("E2", "E3"):
        got = [r for r in ok.values() if r["exp"] == e]
        res["accounting"][e] = {"expected": len(e1_valid), "ok": len(got),
                                "missing_after_retries": len(e1_valid) - len(got),
                                "malformed": sum(r["answer"] is None for r in got)}
    res["providers"] = dict(collections.Counter(r.get("provider") for r in ok.values()))
    res["finish"] = dict(collections.Counter(r.get("finish") for r in ok.values()))
    res["spend"] = round(sum(r.get("cost") or 0 for r in ok.values()), 4)

    # ---- per-cell outcome tables for each decision procedure
    def cell_table(rs):
        t = {}
        for c in CELLS:
            sub = [r for r in rs if r["cell"] == c]
            t[c] = {"n": len(sub), "correct": sum(r["answer"] == r["gold"] for r in sub),
                    "wrong_execute": sum(r["answer"] == "EXECUTE" and r["gold"] == "DECLINE" for r in sub),
                    "wrong_decline": sum(r["answer"] == "DECLINE" and r["gold"] == "EXECUTE" for r in sub),
                    "malformed": sum(r["answer"] is None for r in sub)}
        return t

    res["cells"] = {e: cell_table(rows(e)) for e in ("E1", "E4", "E4p", "E5")}

    def _rate(rs, cell, want, keys=None):
        sub = [r for r in rs if r["cell"] == cell]
        if keys is not None:
            ks = collections.Counter(keys)
            return rate(sum(ks[bank_of(r)] * (r["answer"] == want) for r in sub), sum(ks[bank_of(r)] for r in sub))
        return rate(sum(r["answer"] == want for r in sub), len(sub))

    def exec_rate(rs, cell, keys=None):
        return _rate(rs, cell, "EXECUTE", keys)

    def decl_rate(rs, cell, keys=None):
        return _rate(rs, cell, "DECLINE", keys)

    banks = {bank_of(r) for r in e1}

    def diff(f, rs, c1, c2):
        want = "EXECUTE" if f is exec_rate else "DECLINE"
        per = collections.defaultdict(lambda: [0, 0, 0, 0])  # hits1, n1, hits2, n2 per bank (built once per comparison)
        for r in rs:
            if r["cell"] == c1:
                per[bank_of(r)][0] += r["answer"] == want
                per[bank_of(r)][1] += 1
            elif r["cell"] == c2:
                per[bank_of(r)][2] += r["answer"] == want
                per[bank_of(r)][3] += 1
        def fn(keys=None):
            ks = list(per) if keys is None else [k for k in keys if k in per]
            n1, n2 = sum(per[k][1] for k in ks), sum(per[k][3] for k in ks)
            if not n1 or not n2:
                return None
            return sum(per[k][0] for k in ks) / n1 - sum(per[k][2] for k in ks) / n2
        return {"value": fn(), "ci": boot(banks, fn)}

    def indices(rs):
        return {"symmetrization": diff(exec_rate, rs, "REV", "NEI_NOPATH"),
                "transitivity": diff(exec_rate, rs, "NEI_PATH", "NEI_NOPATH"),
                "combined": diff(exec_rate, rs, "REV_PATH", "NEI_NOPATH"),
                "oneway_refusal": diff(decl_rate, rs, "FWD", "BOTH")}

    res["H1"] = {e: indices(rows(e)) for e in ("E1", "E4", "E4p", "E5")}
    res["H10_clause"] = {e: {cl: indices([r for r in rows(e) if r["clause"] == cl]) for cl in ("base", "explicit")}
                         for e in ("E1", "E4", "E5")}
    res["cells_by_clause"] = {e: {cl: cell_table([r for r in rows(e) if r["clause"] == cl]) for cl in ("base", "explicit")}
                              for e in ("E1", "E4", "E4p", "E5")}
    def pol_acc(rs, pols, cl):
        sub = [r for r in rs if r["policy"] in pols and r["clause"] == cl]
        return [sum(r["answer"] == r["gold"] for r in sub), len(sub)]
    res["H11_bridge"] = {e: {cl: {"REC": pol_acc(rows(e), ("REC",), cl), "CYC": pol_acc(rows(e), ("CYC", "CYCT"), cl),
                                  "MIXED": pol_acc(rows(e), ("P", "PT"), cl)} for cl in ("base", "explicit")}
                         for e in ("E1", "E5")}
    inter = collections.Counter()
    for r in e1:
        if r["cell"] in ("BOTH", "FWD") and r["answer"] is not None:
            if r["cell"] == "BOTH":
                state = "reverse_line_first" if r["pos_rev"] < r["pos_fwd"] else "match_line_first"
            else:
                state = "single_source_route" if r["src_out"] == 1 else "source_has_two_routes"
            inter[(r["cell"], state, "wrong" if r["answer"] != r["gold"] else "ok")] += 1
    res["H9_interference"] = {"/".join(k): v for k, v in sorted(inter.items())}
    res["H8_surface"] = {sf: indices([r for r in e1 if r["surface"] == sf]) for sf in ("opaque", "natural")}
    res["H1_by_presentation"] = {
        f"{rec}/{lab}": exec_rate([r for r in e1 if r["rec"] == rec and r["lab"] == lab], "REV")
        for rec in ("d_first", "a_first") for lab in ("exec_first", "decl_first")}
    res["H1_banks_positive"] = {
        "n_banks": len(banks),
        "banks_with_REV_exec_above_NEI_NOPATH": sum(
            (exec_rate(e1, "REV", [b]) or 0) > (exec_rate(e1, "NEI_NOPATH", [b]) or 0) for b in banks)}

    # ---- H2 confidence
    e2 = {r["id"][:-3]: r for r in ok.values() if r["exp"] == "E2" and r["answer"] is not None}
    conf = collections.defaultdict(list)
    for r in e1_valid:
        c = e2.get(r["id"][:-3])
        if c:
            conf[(r["cell"], r["answer"] == r["gold"])].append(c["answer"])
    mean = lambda v: None if not v else sum(v) / len(v)
    den_ok = [x for c in DENIED for x in conf[(c, True)]]
    den_bad = [x for c in DENIED for x in conf[(c, False)]]
    all_ok = [x for (c, k), v in conf.items() if k for x in v]
    all_bad = [x for (c, k), v in conf.items() if not k for x in v]
    res["H2"] = {"mean_conf": {f"{c}/{'correct' if k else 'wrong'}": [mean(v), len(v)] for (c, k), v in sorted(conf.items())},
                 "wrong_REV_minus_correct_NEI_NOPATH": None if not conf[("REV", False)] or not conf[("NEI_NOPATH", True)]
                 else mean(conf[("REV", False)]) - mean(conf[("NEI_NOPATH", True)]),
                 "auroc_denied": auroc(den_ok, den_bad), "auroc_all": auroc(all_ok, all_bad),
                 "share_conf_ge_90_when_wrong": rate(sum(x >= 90 for x in all_bad), len(all_bad))}

    # ---- H3 defence
    e3 = {r["id"][:-3]: r for r in ok.values() if r["exp"] == "E3"}
    d3 = collections.Counter()
    for r in e1_valid:
        v = e3.get(r["id"][:-3])
        if v:
            d3[("correct" if r["answer"] == r["gold"] else "wrong", r["cell"], v["answer"] or "MALFORMED")] += 1
    def agg(state, cells=CELLS):
        tot = collections.Counter()
        for (s, c, a), n in d3.items():
            if s == state and c in cells:
                tot[a] += n
        return dict(tot)
    res["H3"] = {"wrong_all": agg("wrong"), "wrong_REV": agg("wrong", ["REV"]), "correct_all": agg("correct")}

    # ---- H4/H5 paired procedure comparisons on identical items
    def paired(e_a, e_b, cell, want):
        a = {r["id"].rsplit("/", 1)[0]: r for r in rows(e_a) if r["cell"] == cell}
        b = {r["id"].rsplit("/", 1)[0]: r for r in rows(e_b) if r["cell"] == cell}
        keys = sorted(set(a) & set(b))
        per = collections.defaultdict(lambda: [0, 0, 0])
        for k in keys:
            p = per[bank_of(a[k])]
            p[0] += a[k]["answer"] == want
            p[1] += b[k]["answer"] == want
            p[2] += 1
        def fn(bk=None):
            bs = list(per) if bk is None else [q for q in bk if q in per]
            n = sum(per[q][2] for q in bs)
            return None if not n else (sum(per[q][0] for q in bs) - sum(per[q][1] for q in bs)) / n
        return {"n": len(keys), "diff": fn(), "ci": boot(banks, fn, reps=1500),
                "a_only": sum(a[k]["answer"] == want and b[k]["answer"] != want for k in keys),
                "b_only": sum(b[k]["answer"] == want and a[k]["answer"] != want for k in keys)}

    res["H4_H5"] = {}
    for proc in ("E4", "E4p", "E5"):
        res["H4_H5"][proc] = {
            "REV_wrong_execute_vs_E1": paired(proc, "E1", "REV", "EXECUTE"),
            "FWD_correct_vs_E1": paired(proc, "E1", "FWD", "EXECUTE"),
            "BOTH_correct_vs_E1": paired(proc, "E1", "BOTH", "EXECUTE")}
    res["H4_H5"]["E4_vs_placebo_REV_wrong_execute"] = paired("E4", "E4p", "REV", "EXECUTE")
    restate = collections.Counter()
    for r in rows("E4"):
        m = re.search(r"CHECK:\s*([A-Za-z]+)\s*->\s*([A-Za-z]+)", r.get("content") or "")
        kind = "unparsed" if not m else "correct" if (m.group(1), m.group(2)) == (r["d"], r["a"]) else \
            "reversed" if (m.group(1), m.group(2)) == (r["a"], r["d"]) else "other"
        restate[(r["cell"], kind, "ok" if r["answer"] == r["gold"] else "wrong")] += 1
    res["E4_restated_route"] = {"/".join(k): v for k, v in sorted(restate.items())}

    # ---- H6 components
    e6, e7 = rows("E6"), rows("E7")
    res["H6"] = {"E6_role_accuracy": [sum(r["answer"] == r["gold"] for r in e6), len(e6)],
                 "E6_named_other_role": sum(r["answer"] == r["other"] for r in e6),
                 "E7_lookup_by_cell": {c: [sum(r["answer"] == r["gold"] for r in e7 if r["cell"] == c),
                                           sum(r["cell"] == c for r in e7)] for c in CELLS}}
    res["H4_H5"]["by_cell_wrong_execute_vs_E1"] = {proc: {c: paired(proc, "E1", c, "EXECUTE") for c in DENIED}
                                                   for proc in ("E4", "E4p", "E5")}
    role_ok = collections.defaultdict(lambda: [0, 0])
    for r in e6:
        k = (r["round"], r["surface"], r["d"], r["a"], r["rec"])
        role_ok[k][0] += r["answer"] == r["gold"]
        role_ok[k][1] += 1
    look_ok = collections.defaultdict(lambda: [0, 0])
    for r in e7:
        k = (r["round"], r["surface"], r["policy"], r["d"], r["a"])
        look_ok[k][0] += r["answer"] == r["gold"]
        look_ok[k][1] += 1
    comp = collections.Counter()
    for r in e1_valid:
        if r["answer"] != r["gold"]:
            kk = (r["round"], r["surface"], r["d"], r["a"], r["rec"])
            ro = role_ok[kk] if kk in role_ok else [2, 2]
            lo_ = look_ok[(r["round"], r["surface"], r["policy"], r["d"], r["a"])]
            comp[(r["cell"], "both_components_correct" if ro == [2, 2] and lo_ == [2, 2] else
                  "role_wrong" if ro != [2, 2] and lo_ == [2, 2] else
                  "lookup_wrong" if ro == [2, 2] else "both_wrong")] += 1
    res["H6"]["wrong_E1_by_component_state"] = {"/".join(k): v for k, v in sorted(comp.items())}

    # ---- H7 inputs and qualification
    def acc(cells):
        sub = [r for r in e1 if r["cell"] in cells]
        return rate(sum(r["answer"] == r["gold"] for r in sub), len(sub))
    res["H7_inputs"] = {"symmetric_subset_acc": acc(("BOTH", "NEI_NOPATH")), "oneway_subset_acc": acc(("FWD", "REV")),
                        "overall_acc": acc(CELLS)}
    e0 = rows("E0")
    mal = rate(sum(r["answer"] is None for r in e1), len(e1))
    role = rate(sum(r["answer"] == r["gold"] for r in e6), len(e6))
    res["qualification"] = {"E0": [sum(r["answer"] == r["gold"] for r in e0), len(e0)], "E1_malformed_rate": mal,
                            "E6_accuracy": role, "qualified": bool(mal is not None and mal <= 0.05 and role is not None
                                                                   and role >= 0.95)}
    return res


def main():
    runs, lo, hi, prefix = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    out = [analyse_model(d, lo, hi) for d in sorted(runs.iterdir()) if (d / "responses.jsonl").exists()]
    q = [m for m in out if m["qualification"]["qualified"]]
    summary = {"rounds": [lo, hi], "n_models": len(out), "n_qualified": len(q),
               "total_spend": round(sum(m["spend"] for m in out), 4)}
    if len(q) >= 3:
        x = [m["H7_inputs"]["symmetric_subset_acc"] for m in q]
        y = [m["H7_inputs"]["oneway_subset_acc"] for m in q]
        swaps = sum((x[i] - x[j]) * (y[i] - y[j]) < 0 for i in range(len(q)) for j in range(i))
        summary["H7"] = {"spearman_symmetric_vs_oneway": spearman(x, y), "model_pairs": len(q) * (len(q) - 1) // 2,
                         "pairs_that_swap_order": swaps}
    def sup(m, k, e="E1", cl=None):
        d = m["H1"][e][k] if cl is None else m["H10_clause"][e][cl][k]
        return d["value"] is not None and d["ci"][0] is not None and d["ci"][0] > 0 and d["value"] >= 0.10
    for k in ("symmetrization", "transitivity", "combined", "oneway_refusal"):
        for e in ("E1", "E5"):
            for cl in ("base", "explicit"):
                summary[f"{k}/{e}/{cl}"] = [m["model"] for m in q if sup(m, k, e, cl)]
    Path(prefix + ".json").write_text(json.dumps({"summary": summary, "models": out}, indent=1))
    f = lambda v: "  -  " if v is None else f"{100 * v:5.1f}"
    L = [f"# V2.1 results, rounds {lo}-{hi}", "", json.dumps(summary, indent=1), ""]
    for e, title in (("E1", "E1 direct decision"), ("E5", "E5 visible reasoning"), ("E4", "E4 restate the route first")):
        for cl in ("base", "explicit"):
            L += [f"## {title}, clause = {cl}: wrong answers by cell (count/n)", "",
                  "| Model | Qual | BOTH wrongDEC | FWD wrongDEC | REV wrongEXE | REV_PATH wrongEXE | NEI_PATH wrongEXE | NEI_NOPATH wrongEXE | malformed | Symmetrization | Chaining | Combined | One-way refusal |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
            for m in out:
                c, h = m["cells_by_clause"][e][cl], m["H10_clause"][e][cl]
                ix = lambda k: f"{f(h[k]['value'])} [{f(h[k]['ci'][0])},{f(h[k]['ci'][1])}]"
                L.append(f"| {m['model']} | {'yes' if m['qualification']['qualified'] else 'NO'} | "
                         f"{c['BOTH']['wrong_decline']}/{c['BOTH']['n']} | {c['FWD']['wrong_decline']}/{c['FWD']['n']} | "
                         f"{c['REV']['wrong_execute']}/{c['REV']['n']} | {c['REV_PATH']['wrong_execute']}/{c['REV_PATH']['n']} | "
                         f"{c['NEI_PATH']['wrong_execute']}/{c['NEI_PATH']['n']} | {c['NEI_NOPATH']['wrong_execute']}/{c['NEI_NOPATH']['n']} | "
                         f"{sum(c[k]['malformed'] for k in CELLS)} | {ix('symmetrization')} | {ix('transitivity')} | {ix('combined')} | {ix('oneway_refusal')} |")
            L.append("")
    L += ["## V1 bridge: accuracy by policy structure (E1 base / E1 explicit / E5 base / E5 explicit)", "",
          "| Model | REC | CYC | MIXED |", "|---|---|---|---|"]
    for m in out:
        b = m["H11_bridge"]
        cellf = lambda p: " / ".join(f"{b[e][cl][p][0]}/{b[e][cl][p][1]}" for e in ("E1", "E5") for cl in ("base", "explicit"))
        L.append(f"| {m['model']} | {cellf('REC')} | {cellf('CYC')} | {cellf('MIXED')} |")
    L += ["", "## REV wrong-EXECUTE by procedure (both clauses pooled), components, confidence, defence", "",
          "| Model | E1 | E4 restate | E4p placebo | E5 reasoning | E6 roles | E7 lookup REV | conf wrong-REV | conf correct-NEI_NOPATH | AUROC denied | KEEP when wrong | CHANGE when correct | wrong with both components right |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in out:
        cc = m["cells"]
        rv = lambda e: f"{cc[e]['REV']['wrong_execute']}/{cc[e]['REV']['n']}"
        mc = m["H2"]["mean_conf"]
        g = lambda k: "-" if k not in mc or mc[k][0] is None else f"{mc[k][0]:.0f} (n={mc[k][1]})"
        w, co = m["H3"]["wrong_all"], m["H3"]["correct_all"]
        comp = m["H6"]["wrong_E1_by_component_state"]
        both = sum(v for k, v in comp.items() if k.endswith("both_components_correct"))
        L.append(f"| {m['model']} | {rv('E1')} | {rv('E4')} | {rv('E4p')} | {rv('E5')} | "
                 f"{m['H6']['E6_role_accuracy'][0]}/{m['H6']['E6_role_accuracy'][1]} | "
                 f"{m['H6']['E7_lookup_by_cell']['REV'][0]}/{m['H6']['E7_lookup_by_cell']['REV'][1]} | "
                 f"{g('REV/wrong')} | {g('NEI_NOPATH/correct')} | "
                 f"{'-' if m['H2']['auroc_denied'] is None else format(m['H2']['auroc_denied'], '.2f')} | "
                 f"{w.get('KEEP', 0)}/{sum(w.values())} | {co.get('CHANGE', 0)}/{sum(co.values())} | {both}/{sum(comp.values())} |")
    L += ["", "## Accounting (expected / ok / missing after retries / malformed)", ""]
    for m in out:
        L.append(f"- {m['model']}: " + "; ".join(f"{e} {a['expected']}/{a['ok']}/{a['missing_after_retries']}/{a['malformed']}"
                                                   for e, a in m["accounting"].items()) + f"; spend ${m['spend']}")
    Path(prefix + ".md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
