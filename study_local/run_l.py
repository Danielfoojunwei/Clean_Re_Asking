"""Study L runner. One sub-command per part; every part appends JSON lines under runs/ and skips ids already done.

  python3 run_l.py gate      # bare accuracy (blocks 8-19) and the six no-evidence cells (blocks 8-11), greedy generation
  python3 run_l.py wordings  # 49 wordings x both directions (blocks 12-19), first-token scoring
  python3 run_l.py acts      # final-position residual stream of every layer: bare runs and ask/tell runs (blocks 8-19)
  python3 run_l.py patch     # activation patching ask <-> tell, by layer and position group (blocks 8-11)
  python3 run_l.py knock     # attention knockout from the last user turn to earlier token groups (blocks 8-11)
  python3 run_l.py entropy   # sampled free-form replies at temperature 1 (blocks 8-9), for semantic entropy
  python3 run_l.py steer --layer L [--alphas ...]   # add the mean ask-minus-tell vector at the final position
"""
import argparse, json, sys, time
import numpy as np, torch
from lm import LM, OUT, BIG, answer_stats
import wordings as W, gen_g

META = ("key", "domain", "block", "listed", "gold", "order", "prior", "prior_right", "pushed")
PAIRS = {"assert": ("Q0", "A0"), "direct": ("Q2", "D0")}   # (ask, tell) with equal token counts; see PLAN_L.md
ACT_W = ("Q0", "A0", "D0", "Q2")


def done_ids(p):
    return {json.loads(l)["id"] for l in p.read_text().splitlines()} if p.exists() else set()


def meta(it):
    return {k: it.get(k) for k in META}


def suffix(lm, it, text, closing=True):
    ids, sp = lm.encode(W.conv(it, text, closing), W.spans(it, text, closing))
    pre, suf = lm.split(ids)
    k = len(pre)
    grp = {"rebuttal": list(range(sp["rebuttal"][0] - k, sp["rebuttal"][1] - k)), "final": [len(suf) - 1]}
    grp["tail"] = [i for i in range(len(suf) - 1) if i not in grp["rebuttal"]]
    return ids, pre, suf, sp, grp


def gate(lm, a):
    p = OUT / "gate.jsonl"; seen = done_ids(p); f = p.open("a")
    for it in W.base_items(W.ALL_BLOCKS):
        if it["prior"] is None:
            if it["id"] in seen:
                continue
            ids, _ = lm.encode(W.conv(it))
            txt, first = lm.generate(ids, max_new=8)
            r = dict(id=it["id"], exp="bare", text=txt[0], answer=gen_g.score({"step": "decide"}, txt[0]), **meta(it), **{"ft_" + k: v for k, v in answer_stats(lm, first, it["gold"]).items()})
            f.write(json.dumps(r) + "\n"); f.flush(); continue
        if it["block"] not in W.GATE_BLOCKS:
            continue
        cache = None
        for (act, nm), tpl in W.gate_cells().items():
            for closing in (True, False):
                rid = f"{it['id']}/{act}-{nm}/{'dis' if closing else 'word'}"
                if rid in seen:
                    continue
                ids, pre, suf, _, _ = suffix(lm, it, tpl, closing)
                cache = cache or lm.prefix_cache(pre)
                txt, first = lm.generate(suf, max_new=8, cache=cache)
                r = dict(id=rid, exp=f"{act}/{nm}", act=act, naming=nm, closing=closing, text=txt[0], answer=gen_g.score({"step": "decide"}, txt[0]),
                         **meta(it), **{"ft_" + k: v for k, v in answer_stats(lm, first, it["gold"]).items()})
                f.write(json.dumps(r) + "\n"); f.flush()


def wordings(lm, a):
    p = OUT / "wordings.jsonl"; seen = done_ids(p); f = p.open("a")
    for it in W.base_items(W.WORD_BLOCKS):
        if it["prior"] is None or f"{it['id']}/Q0" in seen and f"{it['id']}/QR7" in seen:
            continue
        names = [w for w in W.WORDINGS if f"{it['id']}/{w}" not in seen]
        sufs = []
        for w in names:
            ids, pre, suf, _, _ = suffix(lm, it, W.WORDINGS[w]["text"])
            sufs.append(suf)
        cache = lm.prefix_cache(pre)
        for i in range(0, len(names), 25):
            lg, _, _ = lm.run(sufs[i:i + 25], cache=cache)
            for w, l in zip(names[i:i + 25], lg):
                f.write(json.dumps(dict(id=f"{it['id']}/{w}", w=w, **{k: W.WORDINGS[w][k] for k in ("set", "form", "label")}, **meta(it), **answer_stats(lm, l, it["gold"]))) + "\n")
        f.flush()


def acts(lm, a):
    """Saves float16 arrays [n, L+1, D] of the final-position residual stream and a JSON index with logit-lens values."""
    BIG.mkdir(parents=True, exist_ok=True)
    p = OUT / "acts_index.jsonl"
    if p.exists():
        print("acts already done"); return
    rows, X = [], []
    for it in W.base_items(W.ALL_BLOCKS):
        if it["prior"] is None:
            ids, _ = lm.encode(W.conv(it))
            lg, hs, ln = lm.run([ids], hidden=True)
            h = hs[0, :, -1]
            rows.append(dict(id=it["id"], exp="bare", closing=None, **meta(it), **answer_stats(lm, lg[0], it["gold"]), lens=[round(x, 3) for x in lm.ld_of(h).tolist()]))
            X.append(h.float().numpy().astype(np.float16)); continue
        cache = None
        for closing in (True, False):
            sufs = []
            for w in ACT_W:
                ids, pre, suf, _, _ = suffix(lm, it, W.WORDINGS[w]["text"], closing); sufs.append(suf)
            cache = cache or lm.prefix_cache(pre)
            lg, hs, ln = lm.run(sufs, cache=cache, hidden=True)
            for i, w in enumerate(ACT_W):
                h = hs[i, :, ln[i] - 1]
                rows.append(dict(id=f"{it['id']}/{w}/{'dis' if closing else 'word'}", exp=w, closing=closing, **meta(it), **answer_stats(lm, lg[i], it["gold"]),
                                 lens=[round(x, 3) for x in lm.ld_of(h).tolist()]))
                X.append(h.float().numpy().astype(np.float16))
    np.save(BIG / "acts_final.npy", np.stack(X))
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


def patched(lm, cache, suf, donor, pos):
    """One batch: row L has the residual stream after block L at positions `pos` replaced by the donor run's. Returns YES-NO logit difference per layer."""
    lm.clear()
    for L in range(lm.n_layers):
        def fn(res, L=L):
            res[L, pos] = donor[L + 1, pos].to(res.dtype); return res
        lm.hook_layer(L, fn)
    try:
        _, hs, ln = lm.run([suf] * lm.n_layers, cache=cache, hidden=True)
    finally:
        lm.clear()
    return lm.ld_of(hs[:, -1, -1]).tolist()


def patch(lm, a):
    p = OUT / "patch.jsonl"; seen = done_ids(p); f = p.open("a")
    for closing in (True, False):
        for it in W.base_items(W.GATE_BLOCKS if closing else range(8, 10)):
            if not it.get("prior_right"):
                continue
            cache = None
            for pair, (qa, qt) in PAIRS.items():
                rid = f"{it['id']}/{pair}/{'dis' if closing else 'word'}"
                if rid in seen:
                    continue
                _, pre, s_ask, _, g_ask = suffix(lm, it, W.WORDINGS[qa]["text"], closing)
                _, _, s_tell, _, g_tell = suffix(lm, it, W.WORDINGS[qt]["text"], closing)
                assert g_ask == g_tell, "position groups must align"
                cache = cache or lm.prefix_cache(pre)
                _, hs, _ = lm.run([s_ask, s_tell], cache=cache, hidden=True)
                sign = 1 if it["gold"] == "YES" else -1
                clean = [sign * x for x in lm.ld_of(hs[:, -1, -1]).tolist()]
                r = dict(id=rid, pair=pair, closing=closing, **meta(it), ld_ask=clean[0], ld_tell=clean[1], ask_into_tell={}, tell_into_ask={})
                for g, pos in g_ask.items():
                    r["ask_into_tell"][g] = [round(sign * x, 3) for x in patched(lm, cache, s_tell, hs[0], pos)]
                    r["tell_into_ask"][g] = [round(sign * x, 3) for x in patched(lm, cache, s_ask, hs[1], pos)]
                f.write(json.dumps(r) + "\n"); f.flush()


def knock(lm, a):
    """Attention knockout in every layer: positions of the last user turn cannot attend to one earlier token group."""
    p = OUT / "knock.jsonl"; seen = done_ids(p); f = p.open("a")
    NEG = float("-inf")
    for it in W.base_items(W.GATE_BLOCKS):
        if it["prior"] is None:
            continue
        for w in ("Q0", "A0", "D0"):
            rid = f"{it['id']}/{w}"
            if rid in seen:
                continue
            ids, pre, suf, sp, grp = suffix(lm, it, W.WORDINGS[w]["text"])
            T, k = len(ids), len(pre)
            prior_pos = max(i for i in range(k) if ids[i] in (lm.YES, lm.NO))
            src = {"none": [], "list": range(*sp["list"]), "question": range(*sp["question"]), "prior": [prior_pos], "rebuttal": range(*sp["rebuttal"])}
            base = torch.zeros(T, T).masked_fill(torch.triu(torch.ones(T, T), 1).bool(), NEG)
            m = base.repeat(len(src), 1, 1)
            for i, (g, cols) in enumerate(src.items()):
                rows0 = sp["rebuttal"][1] if g == "rebuttal" else k   # the rebuttal is hidden from the tokens after it
                for c in cols:
                    m[i, rows0:, c] = NEG
            o = lm.lm(input_ids=torch.tensor([ids] * len(src)), attention_mask=m[:, None].to(torch.bfloat16))
            lg = lm.logits_of(o.last_hidden_state[:, -1])
            f.write(json.dumps(dict(id=rid, w=w, **meta(it), **{g: answer_stats(lm, lg[i], it["gold"]) for i, g in enumerate(src)})) + "\n"); f.flush()


def entropy(lm, a):
    """Free-form format of the paper (study/gen_i.py): 8 replies sampled at temperature 1, then the final-answer turn for each."""
    import re
    p = OUT / "entropy.jsonl"; seen = done_ids(p); f = p.open("a")
    for it in W.base_items(range(8, 10)):
        if it["prior"] is None:
            continue
        for w in ("Q0", "A0", "D0"):
            rid = f"{it['id']}/{w}/free"
            if rid in seen:
                continue
            msgs = [{"role": "system", "content": gen_g.SYSTEM_FREE}, {"role": "user", "content": f"{it['head']}\n\n{it['question']}"},
                    {"role": "assistant", "content": it["prior"].capitalize() + "."}, {"role": "user", "content": W.WORDINGS[w]["text"].format(A=it["pushed"])}]
            ids, _ = lm.encode(msgs)
            reps, _ = lm.generate(ids, max_new=48, temperature=1.0, n=8, seed=abs(hash(rid)) % 2**31 if False else sum(map(ord, rid)))
            finals = []
            for rep in reps:
                ids2, _ = lm.encode(msgs + [{"role": "assistant", "content": rep or "(no reply)"}, {"role": "user", "content": gen_g.FINAL_FREE + it["one"]}])
                finals.append(ids2)
            lg, _, _ = lm.run(finals)
            fin = [answer_stats(lm, l, it["gold"])["answer"] for l in lg]
            said = [sorted({x.upper() for x in re.findall(r"\b(yes|no)\b", rep, flags=re.I)}) for rep in reps]
            f.write(json.dumps(dict(id=rid, w=w, **meta(it), replies=reps, said=said, final=fin)) + "\n"); f.flush()


def steer(lm, a):
    """Adds alpha x (mean ask - mean tell) of the final-position residual stream after block `layer` (from acts, blocks 12-19,
    closing instruction on, previous answer right) to runs on blocks 8-11. Reports both directions."""
    idx = [json.loads(l) for l in (OUT / "acts_index.jsonl").read_text().splitlines()]
    X = np.load(BIG / "acts_final.npy", mmap_mode="r")
    sel = lambda w: [i for i, r in enumerate(idx) if r["exp"] == w and r["closing"] and r["prior_right"] and r["block"] >= 12]
    vec = {}
    for name, (qa, qt) in (("assert", ("Q0", "A0")), ("direct", ("Q0", "D0"))):
        vec[name] = torch.tensor(X[sel(qa), a.layer + 1].astype(np.float32).mean(0) - X[sel(qt), a.layer + 1].astype(np.float32).mean(0))
    np.save(OUT / f"steer_vec_L{a.layer}.npy", np.stack([vec["assert"].numpy(), vec["direct"].numpy()]).astype(np.float16))
    p = OUT / f"steer_L{a.layer}.jsonl"; seen = done_ids(p); f = p.open("a")
    alphas = [float(x) for x in a.alphas.split(",")]
    for it in W.base_items(W.GATE_BLOCKS):
        if it["prior"] is None:
            continue
        cache = None
        for w, vname in (("A0", "assert"), ("D0", "direct"), ("Q0", "assert")):
            rid = f"{it['id']}/{w}"
            if rid in seen:
                continue
            _, pre, suf, _, _ = suffix(lm, it, W.WORDINGS[w]["text"])
            cache = cache or lm.prefix_cache(pre)
            v = vec[vname]
            def fn(res):
                for i, al in enumerate(alphas):
                    res[i, -1] += (al * v).to(res.dtype)
                return res
            lm.clear(); lm.hook_layer(a.layer, fn)
            try:
                lg, _, _ = lm.run([suf] * len(alphas), cache=cache)
            finally:
                lm.clear()
            f.write(json.dumps(dict(id=rid, w=w, layer=a.layer, **meta(it), by_alpha={str(al): answer_stats(lm, lg[i], it["gold"]) for i, al in enumerate(alphas)})) + "\n"); f.flush()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("part", choices=["gate", "wordings", "acts", "patch", "knock", "entropy", "steer"])
    ap.add_argument("--layer", type=int); ap.add_argument("--alphas", default="-1,0,0.5,1,2,4")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t = time.time(); lm = LM()
    globals()[a.part](lm, a)
    print(a.part, "done in", round(time.time() - t), "s")
