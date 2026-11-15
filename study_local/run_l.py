"""Study L runner. One sub-command per part; every part appends JSON lines under runs/<model>/ and skips ids already done.
Model chosen with STUDY_L_MODEL (see lm.MODELS).

  python3 run_l.py bare      # bare question, blocks 8-19, first-token scoring
  python3 run_l.py gate      # the six no-evidence cells, both directions, blocks 8-11, with and without the closing instruction
  python3 run_l.py gencheck  # greedy 8-token generation scored by study/gen_g.score on block 8, to check first-token scoring
  python3 run_l.py wordings  # 49 wordings x both directions (blocks 12-19)
  python3 run_l.py acts      # final-position residual stream of every layer: bare runs and ask/tell runs (blocks 8-19)
  python3 run_l.py patch     # activation patching ask <-> tell, by layer and position group
  python3 run_l.py knock     # attention knockout from the last user turn to earlier token groups
  python3 run_l.py fidelity  # the paper's own items (blocks 0-3), six cells, to compare with the API responses
  python3 run_l.py entropy   # sampled free-form replies at temperature 1, for semantic entropy
  python3 run_l.py steer --layer L [--alphas ...]   # add the mean ask-minus-tell vector at the final position
"""
import argparse, json, os, re, time
import numpy as np, torch
from lm import LM, OUT, BIG, answer_stats
import wordings as W, gen_g

META = ("key", "domain", "block", "listed", "gold", "order", "prior", "prior_right", "pushed")
PAIRS = {"assert": ("Q0", "A0"), "direct": ("Q2", "D0")}   # (ask, tell) with equal token counts; see PLAN_L.md
ACT_W = ("Q0", "A0", "D0", "Q2")
blocks_env = lambda name, default: [int(x) for x in os.environ[name].split(",")] if os.environ.get(name) else list(default)


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


def bare(lm, a):
    p = OUT / "bare.jsonl"; seen = done_ids(p); f = p.open("a")
    its = [it for it in W.base_items(W.ALL_BLOCKS) if it["prior"] is None and it["id"] not in seen]
    for i in range(0, len(its), 12):
        b = its[i:i + 12]
        h, _, _ = lm.run([lm.encode(W.conv(x))[0] for x in b])
        for x, hh in zip(b, h):
            f.write(json.dumps(dict(id=x["id"], exp="bare", **meta(x), **answer_stats(lm, hh, x["gold"]))) + "\n")
        f.flush()


def cells(lm, a, name, blocks, closings):
    p = OUT / name; seen = done_ids(p); f = p.open("a")
    for it in W.base_items(blocks):
        if it["prior"] is None:
            continue
        jobs = [(act, nm, tpl, c) for (act, nm), tpl in W.gate_cells().items() for c in closings]
        if f"{it['id']}/{jobs[-1][0]}-{jobs[-1][1]}/{'dis' if jobs[-1][3] else 'word'}" in seen:
            continue
        sufs = []
        for act, nm, tpl, c in jobs:
            _, pre, suf, _, _ = suffix(lm, it, tpl, c); sufs.append(suf)
        h, _, _ = lm.run(sufs, cache=lm.prefix_cache(pre))
        for (act, nm, tpl, c), hh in zip(jobs, h):
            f.write(json.dumps(dict(id=f"{it['id']}/{act}-{nm}/{'dis' if c else 'word'}", exp=f"{act}/{nm}", act=act, naming=nm, closing=c, **meta(it),
                                    **answer_stats(lm, hh, it["gold"]))) + "\n")
        f.flush()


def gate(lm, a):
    cells(lm, a, "gate.jsonl", W.GATE_BLOCKS, (True, False))


def fidelity(lm, a):
    cells(lm, a, "fidelity.jsonl", range(0, 4), (True,))


def gencheck(lm, a):
    p = OUT / "gencheck.jsonl"; seen = done_ids(p); f = p.open("a")
    for it in W.base_items([8]):
        jobs = [("bare", None)] if it["prior"] is None else [(c, t) for c, t in (("question/named", W.WORDINGS["Q0"]["text"]), ("assertion/named", W.WORDINGS["A0"]["text"]), ("directive/named", W.WORDINGS["D0"]["text"]))]
        for exp, tpl in jobs:
            rid = f"{it['id']}/{exp}"
            if rid in seen:
                continue
            ids, _ = lm.encode(W.conv(it, tpl))
            txt, first = lm.generate(ids, max_new=8)
            f.write(json.dumps(dict(id=rid, exp=exp, text=txt[0], answer=gen_g.score({"step": "decide"}, txt[0]), first_token=answer_stats(lm, first, it["gold"])["answer"], **meta(it))) + "\n"); f.flush()


def wordings(lm, a):
    p = OUT / "wordings.jsonl"; seen = done_ids(p); f = p.open("a")
    names = list(W.WORDINGS)
    for it in W.base_items(W.WORD_BLOCKS):
        if it["prior"] is None or f"{it['id']}/{names[-1]}" in seen:
            continue
        sufs = []
        for w in names:
            _, pre, suf, _, _ = suffix(lm, it, W.WORDINGS[w]["text"]); sufs.append(suf)
        h, _, _ = lm.run(sufs, cache=lm.prefix_cache(pre))
        for w, hh in zip(names, h):
            f.write(json.dumps(dict(id=f"{it['id']}/{w}", w=w, **{k: W.WORDINGS[w][k] for k in ("set", "form", "label")}, **meta(it), **answer_stats(lm, hh, it["gold"]))) + "\n")
        f.flush()


def acts(lm, a):
    """Saves a float16 array [n, L+1, D] of the final-position residual stream (written to disk row by row) and a JSON index
    with logit-lens values. Restartable: rows already in the index are skipped."""
    BIG.mkdir(parents=True, exist_ok=True)
    p = OUT / "acts_index.jsonl"; seen = done_ids(p)
    its = W.base_items(blocks_env("ACTS_BLOCKS", W.ALL_BLOCKS))
    bares = [it for it in its if it["prior"] is None]; pushes = [it for it in its if it["prior"] is not None]
    jobs = [(w, c) for c in (True, False) for w in ACT_W]
    n = len(bares) + len(pushes) * len(jobs)
    path = BIG / "acts_final.npy"
    X = np.lib.format.open_memmap(path, mode="r+" if path.exists() and seen else "w+", dtype=np.float16, shape=(n, lm.n_layers + 1, lm.wd.shape[0]))
    row = len(seen); f = p.open("a")

    def put(rid, exp, closing, it, h_last, h):
        nonlocal row
        X[row] = h.float().numpy().astype(np.float16); row += 1
        f.write(json.dumps(dict(id=rid, exp=exp, closing=closing, **meta(it), **answer_stats(lm, h_last, it["gold"]), lens=[round(x, 3) for x in lm.ld_of(h).tolist()])) + "\n")

    for i in range(0, len(bares), 12):
        b = [it for it in bares[i:i + 12] if it["id"] not in seen]
        if not b:
            continue
        hl, hs, ln = lm.run([lm.encode(W.conv(x))[0] for x in b], hidden=True)
        for j, it in enumerate(b):
            put(it["id"], "bare", None, it, hl[j], hs[j, :, ln[j] - 1])
        f.flush(); X.flush()
    for it in pushes:
        if f"{it['id']}/{jobs[-1][0]}/{'dis' if jobs[-1][1] else 'word'}" in seen:
            continue
        sufs = []
        for w, c in jobs:
            _, pre, suf, _, _ = suffix(lm, it, W.WORDINGS[w]["text"], c); sufs.append(suf)
        hl, hs, ln = lm.run(sufs, cache=lm.prefix_cache(pre), hidden=True)
        for i, (w, c) in enumerate(jobs):
            put(f"{it['id']}/{w}/{'dis' if c else 'word'}", w, c, it, hl[i], hs[i, :, ln[i] - 1])
        f.flush(); X.flush()


def patched(lm, cache, suf, donor, pos):
    """One batch of N rows of the run `suf`: row L has the residual stream after block L at positions `pos` replaced by the
    donor run's (donor: [L+1, T, D]). Returns the YES-NO logit difference per row."""
    N = lm.n_layers
    lm.clear()
    for L in range(N):
        def fn(res, L=L):
            res[L, pos] = donor[L + 1, pos].to(res.dtype); return res
        lm.hook_layer(L, fn)
    try:
        h, _, _ = lm.run([suf] * N, cache=cache)
    finally:
        lm.clear()
    return lm.ld_of(h).tolist()


def patch(lm, a):
    p = OUT / "patch.jsonl"; seen = done_ids(p); f = p.open("a")
    for closing, blocks in ((True, blocks_env("PATCH_BLOCKS_DIS", (8, 9))), (False, blocks_env("PATCH_BLOCKS_WORD", (8,)))):
        for it in W.base_items(blocks):
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
                hl, hs, _ = lm.run([s_ask, s_tell], cache=cache, hidden=True)
                sign = 1 if it["gold"] == "YES" else -1
                clean = [sign * x for x in lm.ld_of(hl).tolist()]
                r = dict(id=rid, pair=pair, closing=closing, **meta(it), ld_ask=clean[0], ld_tell=clean[1], ask_into_tell={}, tell_into_ask={})
                for g, pos in g_ask.items():
                    x, y = patched(lm, cache, s_tell, hs[0], pos), patched(lm, cache, s_ask, hs[1], pos)
                    r["ask_into_tell"][g] = [round(sign * v, 3) for v in x]; r["tell_into_ask"][g] = [round(sign * v, 3) for v in y]
                f.write(json.dumps(r) + "\n"); f.flush()


def knock(lm, a):
    """Attention knockout in every layer: positions of the last user turn cannot attend to one earlier token group."""
    p = OUT / "knock.jsonl"; seen = done_ids(p); f = p.open("a")
    NEG = float("-inf"); GR = ("none", "list", "question", "prior_answer", "rebuttal")
    for it in W.base_items(blocks_env("KNOCK_BLOCKS", (8, 9))):
        if it["prior"] is None or f"{it['id']}/D0" in seen:
            continue
        enc = [suffix(lm, it, W.WORDINGS[w]["text"]) for w in ("Q0", "A0", "D0")]
        T = max(len(e[0]) for e in enc)
        ids = torch.full((3 * len(GR), T), lm.PAD, dtype=torch.long)
        m = torch.zeros(T, T).masked_fill(torch.triu(torch.ones(T, T), 1).bool(), NEG).repeat(3 * len(GR), 1, 1)
        for j, (x, pre, suf, sp, grp) in enumerate(enc):
            k = len(pre)
            prior_pos = max(i for i in range(k) if x[i] in (lm.YES, lm.NO))
            src = {"none": [], "list": range(*sp["list"]), "question": range(*sp["question"]), "prior_answer": [prior_pos], "rebuttal": range(*sp["rebuttal"])}
            for i, g in enumerate(GR):
                row = j * len(GR) + i
                ids[row, :len(x)] = torch.tensor(x)
                rows0 = sp["rebuttal"][1] if g == "rebuttal" else k   # the rebuttal is hidden from the tokens after it
                for c in src[g]:
                    m[row, rows0:, c] = NEG
        hk = lm.layers[-1].register_forward_hook(lambda mod, i, o: setattr(lm, "_last", o[0] if isinstance(o, tuple) else o))
        try:
            lm.lm(input_ids=ids, attention_mask=m[:, None].to(torch.bfloat16))
        finally:
            hk.remove()
        for j, w in enumerate(("Q0", "A0", "D0")):
            last = len(enc[j][0]) - 1
            f.write(json.dumps(dict(id=f"{it['id']}/{w}", w=w, **meta(it), **{g: answer_stats(lm, lm._last[j * len(GR) + i, last], it["gold"]) for i, g in enumerate(GR)})) + "\n")
        f.flush()


def entropy(lm, a):
    """Free-form format of the paper (study/gen_i.py): 8 replies sampled at temperature 1, then the final-answer turn for each."""
    p = OUT / "entropy.jsonl"; seen = done_ids(p); f = p.open("a")
    for it in W.base_items(blocks_env("ENTROPY_BLOCKS", (8,))):
        if it["prior"] is None:
            continue
        for w in ("Q0", "A0", "D0"):
            rid = f"{it['id']}/{w}/free"
            if rid in seen:
                continue
            msgs = [{"role": "system", "content": gen_g.SYSTEM_FREE}, {"role": "user", "content": f"{it['head']}\n\n{it['question']}"},
                    {"role": "assistant", "content": it["prior"].capitalize() + "."}, {"role": "user", "content": W.WORDINGS[w]["text"].format(A=it["pushed"])}]
            ids, _ = lm.encode(msgs)
            reps, _ = lm.generate(ids, max_new=a.max_new, temperature=1.0, n=8, seed=sum(map(ord, rid)))
            finals = [lm.encode(msgs + [{"role": "assistant", "content": rep or "(no reply)"}, {"role": "user", "content": gen_g.FINAL_FREE + it["one"]}])[0] for rep in reps]
            h, _, _ = lm.run(finals)
            fin = [answer_stats(lm, hh, it["gold"])["answer"] for hh in h]
            said = [sorted({x.upper() for x in re.findall(r"\b(yes|no)\b", rep, flags=re.I)}) for rep in reps]
            f.write(json.dumps(dict(id=rid, w=w, **meta(it), replies=reps, said=said, final=fin)) + "\n"); f.flush()


def qrfree(lm, a):
    """Amendment L-3 (post hoc): free-form format of the paper for the question-form requests, whose one-word replies are
    ambiguous. Greedy reply of 16 tokens, then the paper's final-answer turn. Block 12, previous answer right."""
    p = OUT / "qrfree.jsonl"; seen = done_ids(p); f = p.open("a")
    for it in W.base_items(blocks_env("QRFREE_BLOCKS", (12,))):
        if not it.get("prior_right"):
            continue
        for w in ("QR0", "QR2", "QR5", "QR7", "D0", "Q0"):
            rid = f"{it['id']}/{w}/free"
            if rid in seen:
                continue
            msgs = [{"role": "system", "content": gen_g.SYSTEM_FREE}, {"role": "user", "content": f"{it['head']}\n\n{it['question']}"},
                    {"role": "assistant", "content": it["prior"].capitalize() + "."}, {"role": "user", "content": W.WORDINGS[w]["text"].format(A=it["pushed"])}]
            reps, _ = lm.generate(lm.encode(msgs)[0], max_new=16)
            ids2, _ = lm.encode(msgs + [{"role": "assistant", "content": reps[0] or "(no reply)"}, {"role": "user", "content": gen_g.FINAL_FREE + it["one"]}])
            h, _, _ = lm.run([ids2])
            f.write(json.dumps(dict(id=rid, w=w, **meta(it), reply=reps[0], **answer_stats(lm, h[0], it["gold"]))) + "\n"); f.flush()


def steer(lm, a):
    """Adds alpha x (mean ask - mean tell) of the final-position residual stream after block `layer` (vector from acts on
    blocks 12-19, closing instruction on, previous answer right) to runs on blocks 8-11. Both directions are scored."""
    idx = [json.loads(l) for l in (OUT / "acts_index.jsonl").read_text().splitlines()]
    X = np.load(BIG / "acts_final.npy", mmap_mode="r")
    sel = lambda w: [i for i, r in enumerate(idx) if r["exp"] == w and r["closing"] and r["prior_right"] and r["block"] >= 12]
    vec = {name: torch.tensor(X[sel("Q0"), a.layer + 1].astype(np.float32).mean(0) - X[sel(qt), a.layer + 1].astype(np.float32).mean(0)) for name, qt in (("assert", "A0"), ("direct", "D0"))}
    np.save(OUT / f"steer_vec_L{a.layer}.npy", np.stack([vec["assert"].numpy(), vec["direct"].numpy()]).astype(np.float16))
    p = OUT / f"steer_L{a.layer}.jsonl"; seen = done_ids(p); f = p.open("a")
    alphas = [float(x) for x in a.alphas.split(",")]
    jobs = [(w, vn, al) for w, vn in (("A0", "assert"), ("D0", "direct"), ("Q0", "assert")) for al in alphas]
    for it in W.base_items(blocks_env("STEER_BLOCKS", W.GATE_BLOCKS)):
        if it["prior"] is None or f"{it['id']}/Q0" in seen:
            continue
        sufs = []
        for w, vn, al in jobs:
            _, pre, suf, _, _ = suffix(lm, it, W.WORDINGS[w]["text"]); sufs.append(suf)
        def fn(res):
            for i, (w, vn, al) in enumerate(jobs):
                res[i, len(sufs[i]) - 1] += (al * vec[vn]).to(res.dtype)
            return res
        lm.clear(); lm.hook_layer(a.layer, fn)
        try:
            h, _, _ = lm.run(sufs, cache=lm.prefix_cache(pre))
        finally:
            lm.clear()
        for w in ("A0", "D0", "Q0"):
            f.write(json.dumps(dict(id=f"{it['id']}/{w}", w=w, layer=a.layer, **meta(it),
                                    by_alpha={str(al): answer_stats(lm, h[i], it["gold"]) for i, (w2, vn, al) in enumerate(jobs) if w2 == w})) + "\n")
        f.flush()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("part", choices=["bare", "gate", "gencheck", "wordings", "acts", "patch", "knock", "fidelity", "entropy", "steer", "qrfree"])
    ap.add_argument("--layer", type=int); ap.add_argument("--alphas", default="-1,0,0.5,1,2,4"); ap.add_argument("--max-new", type=int, default=24)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t = time.time(); lm = LM(); print("loaded in", round(time.time() - t), "s", flush=True)
    globals()[a.part](lm, a)
    print(a.part, "done in", round(time.time() - t), "s", flush=True)
