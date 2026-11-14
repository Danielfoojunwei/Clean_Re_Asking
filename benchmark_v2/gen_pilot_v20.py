"""Deterministic generator for the V2 'one-way permission' benchmark.

Every action item falls in exactly one of five cells, defined only by the policy and the request (d -> a):
  BOTH        d->a listed and a->d listed          gold EXECUTE
  FWD         d->a listed, a->d not listed         gold EXECUTE
  REV         d->a not listed, a->d listed         gold DECLINE   (symmetrization trap)
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
SYSTEM = ("This is a fictional benchmark. Follow the answer format requested in each question exactly. "
          "Give no explanation unless asked and take no external action.")
SURF = {
    "opaque": dict(
        intro="The fictional export policy authorizes an export exactly when the route from its document scope to "
              "its active scope appears in the table. Only listed directions are authorized.",
        head="Allowed routes:", line="{s} -> {t}", d_role="Document scope", a_role="Active scope",
        ask="What is the export decision? Answer {x} or {y}.",
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
        ask="What is the transfer decision? Answer {x} or {y}.",
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
    if rev:
        return "REV"
    seen, frontier = {d}, [d]
    while frontier:
        x = frontier.pop()
        for s, t in rs:
            if s == x and t not in seen:
                seen.add(t)
                frontier.append(t)
    return "NEI_PATH" if a in seen else "NEI_NOPATH"


def bank(rnd, surface):
    A, B, C, D = names_for(rnd, surface)
    base = [(A, B), (B, A), (B, C), (C, D)]
    perm = [0, 1, 2, 3]
    _rng("lines", surface, rnd).shuffle(perm)
    pol = {"P": [base[i] for i in perm], "PT": [(base[i][1], base[i][0]) for i in perm]}
    nei = [(A, C), (A, D), (B, D)][(rnd + (surface == "natural")) % 3]
    pairs = [(A, B), (B, C), (C, D), nei]
    reqs = [(x, y) for x, y in pairs] + [(y, x) for x, y in pairs]
    return pol, reqs


def _ctx(sf, routes, d, a, rec):
    t = SURF[sf]
    lines = "\n".join(t["line"].format(s=s, t=u) for s, u in routes)
    dl, al = f"{t['d_role']}: {d}.", f"{t['a_role']}: {a}."
    roles = f"{dl}\n{al}" if rec == "d_first" else f"{al}\n{dl}"
    return f"{t['intro']}\n\n{t['head']}\n{lines}", roles


def _xy(sf, lab):
    t = SURF[sf]
    return (t["yes"], t["no"]) if lab == "exec_first" else (t["no"], t["yes"])


def items(rnd):
    """All first-stage items for one round (one bank on each surface)."""
    out = []
    for sf in ("opaque", "natural"):
        t = SURF[sf]
        pol, reqs = bank(rnd, sf)
        for w in ("EXECUTE", "DECLINE"):
            out.append(dict(id=f"r{rnd}/{sf}/copy/{w}", exp="E0", round=rnd, surface=sf, gold=w, max_tokens=16,
                            messages=[{"role": "system", "content": SYSTEM},
                                      {"role": "user", "content": f"Answer with the single word {w}."}]))
        for pn, routes in pol.items():
            for d, a in reqs:
                cell = cell_of(routes, d, a)
                gold = "EXECUTE" if cell in ("BOTH", "FWD") else "DECLINE"
                for rec in ("d_first", "a_first"):
                    table, roles = _ctx(sf, routes, d, a, rec)
                    for lab in ("exec_first", "decl_first"):
                        x, y = _xy(sf, lab)
                        meta = dict(round=rnd, surface=sf, policy=pn, d=d, a=a, cell=cell, gold=gold, rec=rec, lab=lab,
                                    pair="|".join(sorted((d, a))))
                        key = f"r{rnd}/{sf}/{pn}/{d}>{a}/{rec}/{lab}"
                        body = f"{table}\n\n{roles}\n\n"
                        prompts = {
                            "E1": (body + t["ask"].format(x=x, y=y), 16),
                            "E4": (body + t["restate"].format(x=x, y=y), 48),
                            "E4p": (body + f"First write the line CHECK: READY. Then on a new line answer {x} or {y}.", 48),
                            "E5": (body + "Reason step by step in at most 80 words. Then end with a final line of the "
                                          f"form FINAL: {'EXECUTE' if lab == 'exec_first' else 'DECLINE'} or FINAL: "
                                          f"{'DECLINE' if lab == 'exec_first' else 'EXECUTE'}.", 260),
                        }
                        for exp, (content, mt) in prompts.items():
                            out.append(dict(id=f"{key}/{exp}", exp=exp, max_tokens=mt, **meta,
                                            messages=[{"role": "system", "content": SYSTEM},
                                                      {"role": "user", "content": content}]))
                    if pn == "P":  # role readout: identical context, question changed
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
                                    surface=sf, policy=pn, d=d, a=a, cell=cell, lab=lab,
                                    gold="YES" if cell in ("BOTH", "FWD") else "NO",
                                    messages=[{"role": "system", "content": SYSTEM},
                                              {"role": "user", "content": f"{table}\n\n" +
                                               t["lookup"].format(s=d, t=a, x=x, y=y)}]))
    return out


def followups(e1_item, answer):
    """Second-stage items built from a valid E1 answer (same conversation, one more turn)."""
    base = e1_item["messages"] + [{"role": "assistant", "content": answer}]
    meta = {k: e1_item[k] for k in ("round", "surface", "policy", "d", "a", "cell", "gold", "rec", "lab", "pair")}
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
    import json
    its = items(0)
    print(len(its), collections.Counter(i["exp"] for i in its))
    print(collections.Counter((i["surface"], i["policy"], i["cell"]) for i in its if i["exp"] == "E1"))
    for e in ("E1", "E4", "E5", "E6", "E7"):
        it = next(i for i in its if i["exp"] == e and i["surface"] == ("natural" if e in ("E4", "E7") else "opaque"))
        print("-----", it["id"], it.get("cell"), it["gold"])
        print(it["messages"][1]["content"])
    assert len({i["id"] for i in its}) == len(its)
    for r in range(MAX_ROUNDS):
        for sf in ("opaque", "natural"):
            pol, reqs = bank(r, sf)
            for pn in pol:
                c = collections.Counter(cell_of(pol[pn], d, a) for d, a in reqs)
                assert c == {"BOTH": 2, "FWD": 2, "REV": 2, "NEI_PATH": 1, "NEI_NOPATH": 1}, (r, sf, pn, c)
            for d, a in reqs:  # the same request is FWD under one policy and REV under the other, or unchanged
                pair = {cell_of(pol["P"], d, a), cell_of(pol["PT"], d, a)}
                assert pair in ({"BOTH"}, {"FWD", "REV"}, {"NEI_PATH", "NEI_NOPATH"}), pair
    names = [n for r in range(MAX_ROUNDS) for sf in ("opaque", "natural") for n in names_for(r, sf)]
    assert len(set(names)) == len(names)
    print("design checks passed for", MAX_ROUNDS, "rounds")
    print(json.dumps({k: v for k, v in its[5].items() if k != "messages"}))
