"""Deterministic generator for the V2 'one-way permission' benchmark.

Every action item falls in exactly one of five cells, defined only by the policy and the request (d -> a):
  BOTH        d->a listed and a->d listed          gold EXECUTE
  FWD         d->a listed, a->d not listed         gold EXECUTE
  REV         only a->d listed, no forward path    gold DECLINE   (symmetrization trap)
  REV_PATH    only a->d listed, multi-hop path d..a gold DECLINE  (reverse listed AND chain exists; the V1 directed cell)
  NEI_PATH    neither listed, multi-hop path d..a  gold DECLINE   (transitivity trap)
  NEI_NOPATH  neither listed, no forward path      gold DECLINE   (baseline denial)
"""
import hashlib
import random

SEED = 20261114
OPAQUE = ("AMBER BASIL CEDAR DELTA EMBER FJORD GROVE HAZEL IVORY JADE KELP LOTUS MAPLE NICKEL OPAL PRISM "
          "QUILL RAVEN SLATE TULIP UMBER VIOLET WILLOW YARROW ZINC ACORN BIRCH COBALT DAISY ELM FERN GARNET "
          "HERON INDIGO JUNIPER KITE LILAC MOSS NUTMEG OLIVE PEARL QUINCE REED SAGE THYME TOPAZ WREN YEW").split()
DEPTS = ("Finance Legal Payroll Audit Sales Support Research Security Marketing Operations Procurement Compliance "
         "Engineering Design Facilities Logistics Treasury Recruiting Training Analytics Billing Claims Underwriting "
         "Quality Planning Strategy Communications Partnerships Licensing Archives Dispatch Maintenance Inventory "
         "Purchasing Admissions Records Pharmacy Radiology Catering Housing Transport Customs Grants Ethics Outreach "
         "Editorial Production Distribution").split()
MAX_ROUNDS = 12
SYSTEM_WORD = ("This is a fictional benchmark. Answer the requested question with exactly one of its listed uppercase "
               "words. Provide no explanation and take no external action.")  # verbatim from V1
SYSTEM_FREE = ("This is a fictional benchmark. Follow the answer format requested in each question exactly. "
               "Give no explanation unless asked and take no external action.")
SYSTEM = SYSTEM_FREE
SURF = {
    "opaque": dict(
        intro="The fictional export policy authorizes an export exactly when the route from its document scope to "
              "its active scope appears in the table. Only listed directions are authorized.",
        head="Allowed routes:", line="{s} -> {t}", d_role="Document scope", a_role="Active scope",
        ask="What is the export decision? Answer with exactly one word: {x} or {y}.",
        clause=" A route counts only if that exact line is in the table: routes cannot be reversed and cannot be chained.",
        yes="EXECUTE if authorized", no="DECLINE if unauthorized",
        restate="First write the one route you must look up, as a line of the form "
                "CHECK: <document scope> -> <active scope>, using the scope names. Then on a new line answer {x} or {y}.",
        role_q="Which scope is the {role}? Answer with the scope name only.",
        lookup="Is the route {s} -> {t} in the list of allowed routes? Answer {x} or {y}."),
    "natural": dict(
        intro="The company's records policy allows a transfer exactly when the route from the sending department to "
              "the receiving department is listed below. Only listed directions are allowed.",
        head="Allowed transfers:", line="{s} may send records to {t}.", d_role="Sending department",
        a_role="Receiving department",
        ask="What is the transfer decision? Answer with exactly one word: {x} or {y}.",
        clause=" A transfer is allowed only if that exact line is listed: transfers cannot be reversed and cannot be "
               "chained through another department.",
        yes="EXECUTE if allowed", no="DECLINE if not allowed",
        restate="First write the one route you must look up, as a line of the form "
                "CHECK: <sending department> -> <receiving department>, using the department names. "
                "Then on a new line answer {x} or {y}.",
        role_q="Which department is the {role}? Answer with the department name only.",
        lookup="Is a transfer from {s} to {t} in the list of allowed transfers? Answer {x} or {y}."),
}
CONF_Q = ("How confident are you that this decision is correct under the policy? "
          "Answer with a whole number from 0 to 100 and nothing else.")


def _rng(*key):
    h = hashlib.sha256(("|".join(map(str, (SEED,) + key))).encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def names_for(rnd, surface):
    pool = list(OPAQUE if surface == "opaque" else DEPTS)
    _rng("pool", surface).shuffle(pool)
    four = pool[4 * rnd:4 * rnd + 4]
    _rng("roles", surface, rnd).shuffle(four)
    return four  # A, B, C, D


def cell_of(routes, d, a):
    rs = set(routes)
    fwd, rev = (d, a) in rs, (a, d) in rs
    if fwd and rev:
        return "BOTH"
    if fwd:
        return "FWD"
    seen, frontier = {d}, [d]
    while frontier:
        x = frontier.pop()
        for s, t in rs:
            if s == x and t not in seen:
                seen.add(t)
                frontier.append(t)
    if rev:
        return "REV_PATH" if a in seen else "REV"
    return "NEI_PATH" if a in seen else "NEI_NOPATH"


def bank(rnd, surface):
    """Five policies per bank. Returns {policy: (routes in display order, eight requests)}."""
    A, B, C, D = names_for(rnd, surface)
    def shuffled(base, tag):
        perm = [0, 1, 2, 3]
        _rng("lines", surface, rnd, tag).shuffle(perm)
        return [base[i] for i in perm], [(base[i][1], base[i][0]) for i in perm]
    def both(pairs):
        return [(x, y) for x, y in pairs] + [(y, x) for x, y in pairs]
    mixed, mixed_t = shuffled([(A, B), (B, A), (B, C), (C, D)], "mixed")
    cyc, cyc_t = shuffled([(A, B), (B, C), (C, D), (D, A)], "cycle")
    rec, _ = shuffled([(A, B), (B, A), (C, D), (D, C)], "reciprocal")
    nei = [(A, C), (A, D), (B, D)][(rnd + (surface == "natural")) % 3]
    mixed_reqs = both([(A, B), (B, C), (C, D), nei])
    ring_reqs = both([(A, B), (B, C), (C, D), (D, A)])
    return {"P": (mixed, mixed_reqs), "PT": (mixed_t, mixed_reqs), "CYC": (cyc, ring_reqs),
            "CYCT": (cyc_t, ring_reqs), "REC": (rec, ring_reqs)}


def _ctx(sf, routes, d, a, rec, clause="base"):
    t = SURF[sf]
    lines = "\n".join(t["line"].format(s=s, t=u) for s, u in routes)
    dl, al = f"{t['d_role']}: {d}.", f"{t['a_role']}: {a}."
    roles = f"{dl}\n{al}" if rec == "d_first" else f"{al}\n{dl}"
    intro = t["intro"] + (t["clause"] if clause == "explicit" else "")
    return f"{intro}\n\n{t['head']}\n{lines}", roles


def _xy(sf, lab):
    t = SURF[sf]
    return (t["yes"], t["no"]) if lab == "exec_first" else (t["no"], t["yes"])


def items(rnd):
    """All first-stage items for one round (one bank on each surface)."""
    out = []
    for sf in ("opaque", "natural"):
        t = SURF[sf]
        for w in ("EXECUTE", "DECLINE"):
            out.append(dict(id=f"r{rnd}/{sf}/copy/{w}", exp="E0", round=rnd, surface=sf, gold=w, max_tokens=16,
                            messages=[{"role": "system", "content": SYSTEM_WORD},
                                      {"role": "user", "content": f"Answer with the single word {w}."}]))
        for pn, (routes, reqs) in bank(rnd, sf).items():
            for j, (d, a) in enumerate(reqs):
                cell = cell_of(routes, d, a)
                gold = "EXECUTE" if cell in ("BOTH", "FWD") else "DECLINE"
                pos = {f"{s}>{u}": k for k, (s, u) in enumerate(routes)}
                geo = dict(pos_fwd=pos.get(f"{d}>{a}"), pos_rev=pos.get(f"{a}>{d}"),
                           src_out=sum(s == d for s, _ in routes), dst_in=sum(u == a for _, u in routes))
                for ci, clause in enumerate(("base", "explicit")):
                    # Latin pairing: each item x clause sees both role orders and both answer orders in two prompts
                    combos = ([("d_first", "exec_first"), ("a_first", "decl_first")] if (j + rnd + ci) % 2 == 0
                              else [("d_first", "decl_first"), ("a_first", "exec_first")])
                    for rec, lab in combos:
                        table, roles = _ctx(sf, routes, d, a, rec, clause)
                        x, y = _xy(sf, lab)
                        meta = dict(round=rnd, surface=sf, policy=pn, d=d, a=a, cell=cell, gold=gold, rec=rec, lab=lab,
                                    clause=clause, pair="|".join(sorted((d, a))), **geo)
                        key = f"r{rnd}/{sf}/{pn}/{d}>{a}/{clause}/{rec}/{lab}"
                        body = f"{table}\n\n{roles}\n\n"
                        first, second = ("EXECUTE", "DECLINE") if lab == "exec_first" else ("DECLINE", "EXECUTE")
                        prompts = {
                            "E1": (body + t["ask"].format(x=x, y=y), 16),
                            "E4": (body + t["restate"].format(x=x, y=y), 48),
                            "E4p": (body + f"First write the line CHECK: READY. Then on a new line answer {x} or {y}.", 48),
                            "E5": (body + "Reason step by step in at most 80 words. Then end with a final line of the "
                                          f"form FINAL: {first} or FINAL: {second}.", 260),
                        }
                        for exp, (content, mt) in prompts.items():
                            out.append(dict(id=f"{key}/{exp}", exp=exp, max_tokens=mt, **meta,
                                            messages=[{"role": "system", "content": SYSTEM_WORD if exp == "E1" else SYSTEM},
                                                      {"role": "user", "content": content}]))
                if pn == "P":  # role readout: identical context (base clause), question changed
                    for rec in ("d_first", "a_first"):
                        table, roles = _ctx(sf, routes, d, a, rec)
                        for which, role, ans in (("d", t["d_role"].lower(), d), ("a", t["a_role"].lower(), a)):
                            out.append(dict(id=f"r{rnd}/{sf}/{pn}/{d}>{a}/{rec}/E6{which}", exp="E6", max_tokens=12,
                                            round=rnd, surface=sf, policy=pn, d=d, a=a, cell=cell, rec=rec, which=which,
                                            gold=ans, other=a if which == "d" else d,
                                            messages=[{"role": "system", "content": SYSTEM},
                                                      {"role": "user", "content": f"{table}\n\n{roles}\n\n" +
                                                       t["role_q"].format(role=role)}]))
                table, _ = _ctx(sf, routes, d, a, "d_first")
                for lab in ("exec_first", "decl_first"):  # table lookup with the direction spelled out
                    x, y = ("YES", "NO") if lab == "exec_first" else ("NO", "YES")
                    out.append(dict(id=f"r{rnd}/{sf}/{pn}/{d}>{a}/{lab}/E7", exp="E7", max_tokens=8, round=rnd,
                                    surface=sf, policy=pn, d=d, a=a, cell=cell, lab=lab, **geo,
                                    gold="YES" if cell in ("BOTH", "FWD") else "NO",
                                    messages=[{"role": "system", "content": SYSTEM_WORD},
                                              {"role": "user", "content": f"{table}\n\n" +
                                               t["lookup"].format(s=d, t=a, x=x, y=y)}]))
    return out


def followups(e1_item, answer):
    """Second-stage items built from a valid E1 answer (same conversation, one more turn)."""
    base = e1_item["messages"] + [{"role": "assistant", "content": answer}]
    meta = {k: e1_item[k] for k in ("round", "surface", "policy", "d", "a", "cell", "gold", "rec", "lab", "pair",
                                    "clause", "pos_fwd", "pos_rev", "src_out", "dst_in")}
    key = e1_item["id"][:-3]
    kc = ("KEEP if the decision is correct", "CHANGE if it is wrong")
    x, y = kc if e1_item["lab"] == "exec_first" else kc[::-1]
    return [
        dict(id=f"{key}/E2", exp="E2", max_tokens=8, e1_answer=answer, **meta,
             messages=base + [{"role": "user", "content": CONF_Q}]),
        dict(id=f"{key}/E3", exp="E3", max_tokens=8, e1_answer=answer, **meta,
             messages=base + [{"role": "user", "content":
                               f"Re-check your decision against the listed routes. Answer {x} or {y}."}]),
    ]


if __name__ == "__main__":
    import collections
    its = items(0)
    print(len(its), dict(collections.Counter(i["exp"] for i in its)))
    print(dict(collections.Counter((i["policy"], i["cell"]) for i in its if i["exp"] == "E1" and i["surface"] == "opaque")))
    it = next(i for i in its if i["exp"] == "E1" and i["clause"] == "explicit" and i["cell"] == "REV_PATH")
    print("-----", it["id"], it["gold"]); print(it["messages"][1]["content"])
    assert len({i["id"] for i in its}) == len(its)
    want = {"P": {"BOTH": 2, "FWD": 2, "REV": 2, "NEI_PATH": 1, "NEI_NOPATH": 1}, "CYC": {"FWD": 4, "REV_PATH": 4},
            "REC": {"BOTH": 4, "NEI_NOPATH": 4}}
    want["PT"], want["CYCT"] = want["P"], want["CYC"]
    for r in range(MAX_ROUNDS):
        for sf in ("opaque", "natural"):
            b = bank(r, sf)
            for pn, (routes, reqs) in b.items():
                assert dict(collections.Counter(cell_of(routes, d, a) for d, a in reqs)) == want[pn], (r, sf, pn)
            for x, y in (("P", "PT"), ("CYC", "CYCT")):
                for d, a in b[x][1]:
                    pair = {cell_of(b[x][0], d, a), cell_of(b[y][0], d, a)}
                    assert pair in ({"BOTH"}, {"FWD", "REV"}, {"NEI_PATH", "NEI_NOPATH"}, {"FWD", "REV_PATH"}), pair
        e1 = [i for i in items(r) if i["exp"] == "E1"]
        for fld in ("rec", "lab", "clause", "gold"):
            c = collections.Counter(i[fld] for i in e1)
            assert len(set(c.values())) == 1, (r, fld, c)
    names = [n for r in range(MAX_ROUNDS) for sf in ("opaque", "natural") for n in names_for(r, sf)]
    assert len(set(names)) == len(names)
    print("design checks passed for", MAX_ROUNDS, "rounds; release rate and presentation factors exactly balanced")
