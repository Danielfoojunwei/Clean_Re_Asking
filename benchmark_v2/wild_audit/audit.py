#!/usr/bin/env python3
"""Label-free direction-blindness audit. Usage: python3 -I audit.py DATA_ROOT OUT_DIR CONTROL_FIXTURES
Every dataset is reduced to items (ctx, r1, r2, label); the SAME function `audit()` is applied to all."""
import json, sys, glob, os, collections, re
import yaml, pandas as pd

def norm(x):
    return re.sub(r"\s+", " ", str(x)).strip().lower() if x is not None else ""

def audit(items):
    """items: list of dicts ctx(hashable), r1, r2, label. Items with an empty role are dropped by the adapter
    (counted there as unparsed). Returns metrics."""
    n = len(items)
    if n == 0:
        return {"n_audited": 0}
    maj_label = collections.Counter(i["label"] for i in items).most_common(1)[0][1] / n
    # 1. direction-blind ceiling: group by (ctx, unordered roles), majority label per group
    g = collections.defaultdict(collections.Counter)
    for i in items:
        g[(i["ctx"], frozenset((i["r1"], i["r2"])))][i["label"]] += 1
    ceiling = sum(max(c.values()) for c in g.values()) / n
    # 2. mirror coverage (only items with r1 != r2 can be mirrored)
    ordered = collections.defaultdict(collections.Counter)
    for i in items:
        ordered[(i["ctx"], i["r1"], i["r2"])][i["label"]] += 1
    distinct = [i for i in items if i["r1"] != i["r2"]]
    mirrored_items = [i for i in distinct if (i["ctx"], i["r2"], i["r1"]) in ordered]
    pairs, diff = 0, 0
    seen = set()
    for (ctx, a, b), c in ordered.items():
        if a == b or (ctx, b, a) not in ordered or (ctx, b, a) in seen:
            continue
        seen.add((ctx, a, b))
        pairs += 1
        if c.most_common(1)[0][0] != ordered[(ctx, b, a)].most_common(1)[0][0]:
            diff += 1
    # items sitting in an orientation pair whose majority labels differ
    diff_items = 0
    for i in mirrored_items:
        if ordered[(i["ctx"], i["r1"], i["r2"])].most_common(1)[0][0] != ordered[(i["ctx"], i["r2"], i["r1"])].most_common(1)[0][0]:
            diff_items += 1
    return {
        "n_audited": n, "n_distinct_roles": len(distinct), "n_identical_roles": n - len(distinct),
        "n_groups_unordered": len(g),
        "direction_blind_ceiling": ceiling,
        "majority_baseline": maj_label,
        "mirror_coverage_of_distinct": len(mirrored_items) / len(distinct) if distinct else None,
        "n_mirrored_items": len(mirrored_items), "n_mirrored_orientation_pairs": pairs,
        "share_mirrored_pairs_different_label": diff / pairs if pairs else None,
        "share_of_all_audited_items_testing_direction": diff_items / n,
    }

# ---------- adapters: return (total_items_in_dataset, items, n_unparsed, notes) ----------
def a_control(path):
    d = json.load(open(path))["splits"]["held_out"]
    rows = [r for r in d if r.get("readout") == "action"]
    out = {}
    for fam in ("reciprocal", "directed", "ALL"):
        its, unp = [], 0
        for r in rows:
            if fam != "ALL" and r["policy_family"] != fam: continue
            if not r.get("doc_scope") or not r.get("active_scope"): unp += 1; continue
            its.append(dict(ctx=(r["bank_id"], r["policy"]), r1=r["doc_scope"], r2=r["active_scope"], label=r["gold"], row=r))
        out[fam] = its, unp
    return len(rows), out

def control_oracle(its):
    """swapped-role oracle: authorised iff (doc, active) in routes; oracle applies the rule to (active, doc)."""
    ok_rule = ok_swap = 0
    for i in its:
        r = i["row"]; routes = {tuple(x) for x in r["routes"]}
        rule = "EXECUTE" if (r["doc_scope"], r["active_scope"]) in routes else "DECLINE"
        swap = "EXECUTE" if (r["active_scope"], r["doc_scope"]) in routes else "DECLINE"
        ok_rule += rule == r["gold"]; ok_swap += swap == r["gold"]
    n = len(its); return {"correct_rule_accuracy": ok_rule / n, "swapped_role_oracle_accuracy": ok_swap / n}

def a_openfga(root):
    items, total, unp = [], 0, 0
    for f in sorted(glob.glob(root + "/sample-stores/stores/**/*.fga.yaml", recursive=True)):
        try: d = yaml.safe_load(open(f))
        except Exception: unp += 1; continue
        store = os.path.relpath(f, root + "/sample-stores/stores")
        for t in (d or {}).get("tests") or []:
            for c in t.get("check") or []:
                for rel, v in (c.get("assertions") or {}).items():
                    total += 1
                    u, o = str(c["user"]), str(c["object"])
                    if ":" not in u or ":" not in o: unp += 1; continue
                    if u.split(":")[0] == o.split(":")[0]:  # same-typed principals only
                        items.append(dict(ctx=(store, t.get("name"), rel), r1=u, r2=o, label=bool(v)))
    return total, items, unp

def a_cedar(root):
    items, total, unp = [], 0, 0
    for f in sorted(glob.glob(root + "/cedar-examples/**/*.json", recursive=True)):
        parts = f.split(os.sep)
        lab = "ALLOW" if "ALLOW" in parts else "DENY" if "DENY" in parts else None
        if not lab: continue
        try: r = json.load(open(f))
        except Exception: unp += 1; continue
        if not (isinstance(r, dict) and "principal" in r and "resource" in r): unp += 1; continue
        total += 1
        p, rs = r["principal"], r["resource"]
        if not (isinstance(p, str) and isinstance(rs, str) and "::" in p and "::" in rs): unp += 1; continue
        usecase = os.sep.join(parts[:parts.index(lab)])
        if p.rsplit("::", 1)[0] == rs.rsplit("::", 1)[0]:
            items.append(dict(ctx=(usecase, str(r.get("action"))), r1=p, r2=rs, label=lab))
    return total, items, unp

def a_privacylens(root):
    d = json.load(open(root + "/PrivacyLens/data/main_data.json")); items, unp = [], 0
    for x in d:
        s = x.get("seed", {}); a, b = norm(s.get("data_sender")), norm(s.get("data_recipient"))
        if not a or not b: unp += 1; continue
        items.append(dict(ctx=(norm(s.get("data_type")), norm(s.get("data_subject")), norm(s.get("transmission_principle"))), r1=a, r2=b, label="norm_violating_seed"))
    return len(d), items, unp

def a_ci_synth(root):
    df = pd.read_parquet(root + "/hf/ci.parquet"); items, unp, total = [], 0, 0
    for _, row in df.iterrows():
        try:
            seed = json.loads(row["seed"]); it = json.loads(row["dataset_item"])
            allowed = it["annotation"]["allowed"].keys(); dis = it["annotation"]["disallowed"].keys()
            a, b = norm(seed["sender"]), norm(seed["recipient"])
            assert a and b
        except Exception:
            unp += 1; continue
        for k, lab in [(k, "allowed") for k in allowed] + [(k, "disallowed") for k in dis]:
            total += 1
            items.append(dict(ctx=(norm(seed.get("scenario")), norm(seed.get("domain")), norm(seed.get("user_intention")), norm(seed.get("data_subject")), norm(seed.get("transmission_principle")), norm(k)), r1=a, r2=b, label=lab))
    return total, items, unp

def main(root, out, fx):
    res = {}
    n, c = a_control(fx)
    for fam, (its, unp) in c.items():
        r = audit(its); r.update(n_total=n if fam == "ALL" else sum(1 for i in its), n_unparsed=unp, **control_oracle(its)); res["POSITIVE_CONTROL held_out/action/" + fam] = r
    for name, fn in [("OpenFGA sample-stores (check assertions)", a_openfga), ("Cedar examples (ALLOW/DENY requests)", a_cedar),
                     ("PrivacyLens main_data (sender/recipient)", a_privacylens), ("ContextualIntegritySyntheticDataset (HF)", a_ci_synth)]:
        total, its, unp = fn(root)
        r = audit(its); r.update(n_total=total, n_unparsed=unp, swapped_role_oracle="not computable (no machine-readable rule over the role pair)"); res[name] = r
    json.dump(res, open(out + "/results.json", "w"), indent=1)
    for k, v in res.items():
        print(k); print("  ", {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items()})

if __name__ == "__main__":
    main(*sys.argv[1:4])
