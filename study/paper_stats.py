
# ---------------------------------------------------------------- pushback study on published protocols (v6)
import statistics as _st
PM = json.load(open("../v6/results_main.json"))
PT = json.load(open("../v6/totals.json"))
PMM = PM["models"]; PL = [l for l in PM["order"] if l in PMM]
pb = {"n_models": len(PL), "n": PT["total"]["n"], "spend": PT["total"]["spend"], "tot": PT}


def _vals(get):
    return [100 * v for v in (get(PMM[l]) for l in PL) if v is not None]


def prange(get):
    v = _vals(get)
    return f"{min(v):.0f}–{max(v):.0f}%"


def pmed(get):
    return f"{_st.median(_vals(get)):.0f}%"


def pcount(get, test):
    return [l for l in PL if (lambda v: v is not None and test(v))(get(PMM[l]))]


wF = lambda c: (lambda m: m["word_F"].get(c))
fF = lambda c: (lambda m: m["free_F"].get(c))
fact = lambda k, a: (lambda m: (m.get("fact") or {}).get(k, {}).get(a))
eff = lambda k: (lambda m: (m.get("fact") or {}).get(k))
Hfix = lambda k: (lambda m: ((m.get("H") or {}).get("fix", {}).get(k) or {}).get("F"))
Hbase = lambda k: (lambda m: ((m.get("H") or {}).get("base", {}).get(k) or {}).get("F"))
pb["FL"] = [l for l in PL if PMM[l].get("fact")]
pb["HL"] = [l for l in PL if PMM[l].get("H")]
up = lambda k: [l for l in pb["FL"] if PMM[l]["fact"].get(k) and PMM[l]["fact"][k]["counts"] and PMM[l]["fact"][k]["diff"] > 0]
dn = lambda k: [l for l in pb["FL"] if PMM[l]["fact"].get(k) and PMM[l]["fact"][k]["counts"] and PMM[l]["fact"][k]["diff"] < 0]
pb["act_up"] = up("act"); pb["act_flat"] = [l for l in pb["FL"] if l not in pb["act_up"]]
pb["assert_up"] = up("act_assert"); pb["dir_assert_up"] = up("act_dir_assert")
pb["naming_up"] = up("naming"); pb["naming_dn"] = dn("naming")
pb["page_up"] = up("page"); pb["page_dn"] = dn("page")
pb["pvo_up"] = up("page_vs_outside"); pb["pvo_dn"] = dn("page_vs_outside")
pb["out_up"] = up("outside"); pb["out_dn"] = dn("outside")
gd = lambda l, k: PMM[l]["diffs"].get(k)
cnt = lambda k, sign: [l for l in PL if gd(l, k) and gd(l, k)["counts"] and sign * gd(l, k)["diff"] > 0]
pb["auth_up"] = cnt("authority-plain", 1); pb["auth_dn"] = cnt("authority-plain", -1)
pb["cit_up"] = cnt("citation-plain", 1); pb["cit_dn"] = cnt("citation-plain", -1)
pb["dis_dn"] = cnt("plain_dis-plain", -1); pb["dis_up"] = cnt("plain_dis-plain", 1)
pb["pfo_up"] = cnt("page_frame-outside_frame", 1); pb["pfo_dn"] = cnt("page_frame-outside_frame", -1)
pb["tell_ask"] = cnt("plain_dis-push_dis", 1) if all(gd(l, "plain_dis-push_dis") for l in PL) else None
pb["free_lower"] = [l for l in PL if PMM[l]["free_F"].get("page_frame") is not None and PMM[l]["word_F"]["page_frame"] - PMM[l]["free_F"]["page_frame"] >= 0.10]
pb["free_higher"] = [l for l in PL if PMM[l]["free_F"].get("page_frame") is not None and PMM[l]["free_F"]["page_frame"] - PMM[l]["word_F"]["page_frame"] >= 0.10]
pb["H_min"] = min(min(v for v in PMM[l]["word_H"].values() if v is not None) for l in PL)
_hv = [v for l in PL for c, v in PMM[l]["word_H"].items() if v is not None and c.endswith("_dis")]
pb["H_med"] = 100 * _st.median(_hv)
# fixes (free-form or one-word baselines from the same run)
fixd = lambda fx_, base: {l: (PMM[l]["H"]["base"][base]["F"], PMM[l]["H"]["fix"][fx_]["F"]) for l in pb["HL"] if PMM[l]["H"]["fix"].get(fx_) and PMM[l]["H"]["fix"][fx_]["F"] is not None and PMM[l]["H"]["base"][base]["F"] is not None}
for k_, b_ in (("note_page", "page_word"), ("quote_page", "page_word"), ("gate_page", "page_free"), ("warn_page", "page_free"), ("gate_citation", "citation_free")):
    d_ = fixd(k_, b_)
    pb[k_] = d_
    pb[k_ + "_better"] = [l for l, (a, b) in d_.items() if a - b >= 0.10]
    pb[k_ + "_worse"] = [l for l, (a, b) in d_.items() if b - a >= 0.10]
pb["note_le10"] = [l for l, (a, b) in pb["note_page"].items() if b <= 0.10]
pb["note_gt10"] = [l for l, (a, b) in pb["note_page"].items() if b > 0.10]
turn = lambda l, k, i=-1: PMM[l]["H"]["turns"][k]["F"][i] if PMM[l]["H"]["turns"].get(k) and PMM[l]["H"]["turns"][k]["F"] else None
pb["persist_hi"] = [l for l in pb["HL"] if (turn(l, "mt_persist") or 0) >= 0.75]
pb["yang_lo"] = [l for l in pb["HL"] if turn(l, "mt_yang") is not None and turn(l, "mt_yang") <= 0.15]
pb["SL"] = [l for l in PL if PMM[l].get("sample")]; pb["LL"] = [l for l in PL if PMM[l].get("logprob")]
pb["bare_all"] = [l for l in pb["SL"] if PMM[l]["sample"]["bare"]["unanimous_correct"] >= 0.995]
pb["bare_not"] = [(l, 100 * PMM[l]["sample"]["bare"]["unanimous_correct"]) for l in pb["SL"] if PMM[l]["sample"]["bare"]["unanimous_correct"] < 0.995]
pb["lp_med"] = [PMM[l]["logprob"]["bare"]["median_p_correct"] for l in pb["LL"]]
P0 = lambda v: "–" if v is None else f"{100 * v:.0f}"
PD = lambda e: "–" if not e else f'{100 * e["diff"]:+.0f}{"*" if e["counts"] else ""}'
names = lambda ls: ", ".join(ls[:-1]) + (" and " if len(ls) > 1 else "") + ls[-1] if ls else "none"
# pre-written predictions, checked
_f = lambda l: PMM[l]["fact"]
pb["p_act_gt_naming"] = [l for l in pb["FL"] if _f(l)["act"]["diff"] > _f(l)["naming"]["diff"]]
pb["p_page_lt_act"] = [l for l in pb["FL"] if _f(l)["page"]["diff"] < _f(l)["act"]["diff"]]
pb["p_order"] = [l for l in pb["FL"] if _f(l)["by_act"]["question"] <= _f(l)["by_act"]["assertion"] <= _f(l)["by_act"]["directive"]]
pb["g_p1"] = [l for l in PL if all(gd(l, k) and gd(l, k)["counts"] and gd(l, k)["diff"] > 0 for k in ("citation-doubt_dis", "page_frame-doubt_dis"))]
pb["g_p2_not_lower"] = [l for l in PL if not (gd(l, "page_frame-citation")["counts"] and gd(l, "page_frame-citation")["diff"] < 0)]
pb["j_bare90"] = [l for l in pb["SL"] if PMM[l]["sample"]["bare"]["unanimous_correct"] >= 0.90]
pb["j_lp95"] = [l for l in pb["LL"] if PMM[l]["logprob"]["bare"]["median_p_correct"] >= 0.95]
_dec = {l: [PMM[l]["sample"]["cond"][c]["decisive_of_yielded"] for c in ("plain", "page_frame") if PMM[l]["sample"]["cond"].get(c) and PMM[l]["sample"]["cond"][c]["F"] >= 0.30 and PMM[l]["sample"]["cond"][c]["decisive_of_yielded"] is not None] for l in pb["SL"]}
pb["j_dec_n"] = sum(len(v) for v in _dec.values()); pb["j_dec_ok"] = sum(sum(x >= 0.5 for x in v) for v in _dec.values())
_au = {l: [PMM[l]["logprob"]["cond"][c]["auroc_bare_predicts_keep"] for c in ("plain", "page_frame") if PMM[l]["logprob"]["cond"].get(c)] for l in pb["LL"]}
pb["j_auroc"] = {l: [a for a in v if a is not None] for l, v in _au.items()}
pb["j_auroc_lo"] = [l for l, v in pb["j_auroc"].items() if v and max(v) < 0.65]
# anchor to Basta et al.'s published concession rates (their tasks) for the seven shared models
BL = [l for l in PL if PMM[l].get("basta_pub")]


def _rank(xs):
    o = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0] * len(xs); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and xs[o[j + 1]] == xs[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = _rank(a), _rank(b); ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb)); den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else float("nan")


pb["rho_cit"] = spearman([PMM[l]["basta_pub"]["citation"][0] for l in BL], [PMM[l]["word_F"]["citation"] for l in BL])
pb["rho_plain"] = spearman([PMM[l]["basta_pub"]["plain"][0] for l in BL], [PMM[l]["word_F"]["plain"] for l in BL])

pb["incomplete"] = [l for l in pb["FL"] if PMM[l]["fact"]["n_F"] < max(PMM[x]["fact"]["n_F"] for x in pb["FL"])]
# ---- cross-cutting readings: cost and benefit of telling, profiles, stability across tasks
Hact = lambda a: (lambda m: (m.get("fact") or {}).get("H_by_act", {}).get(a))
pb["cost"] = {l: PMM[l]["fact"]["by_act"]["directive"] - PMM[l]["fact"]["by_act"]["question"] for l in pb["FL"]}
pb["gain"] = {l: PMM[l]["fact"]["H_by_act"]["directive"] - PMM[l]["fact"]["H_by_act"]["question"] for l in pb["FL"]}
pb["gain5"] = [l for l in pb["FL"] if pb["gain"][l] > 0.05]
pb["cost_gt_gain"] = [l for l in pb["FL"] if pb["cost"][l] > pb["gain"][l] + 0.05]
_fa = lambda l: PMM[l]["fact"]["by_act"]
pb["vigilant"] = [l for l in pb["FL"] if _fa(l)["directive"] < 0.10 and _fa(l)["question"] < 0.10]
pb["suggestible"] = [l for l in pb["FL"] if _fa(l)["question"] >= 0.10]
pb["obedient"] = [l for l in pb["FL"] if l not in pb["vigilant"] and l not in pb["suggestible"]]
pb["vig_H"] = [100 * PMM[l]["fact"]["H_all"] for l in pb["vigilant"]]
pb["task_rho"] = {c: [spearman([PMM[l]["by_task"][a][c] for l in PL], [PMM[l]["by_task"][b][c] for l in PL]) for a, b in (("stock", "rooms"), ("stock", "rules"), ("rooms", "rules"))] for c in ("plain", "page_frame")}
pb["rho_lo"] = min(min(v) for v in pb["task_rho"].values()); pb["rho_hi"] = max(max(v) for v in pb["task_rho"].values())
FT = lambda l: f'{100 * _fa(l)["directive"]:.0f}%'
# ---- why the two published tests differ: decomposition from existing runs
_c = lambda l, k: PMM[l]["fact"]["cells"].get(k)
cellmed = lambda k: 100 * _st.median([_c(l, k) for l in pb["FL"] if _c(l, k) is not None])
pb["grid"] = {k: cellmed(k) for k in (f"{a}/{n}/none" for a in ("question", "assertion", "directive") for n in ("unnamed", "named"))}
_gap = [PMM[l]["word_F"]["plain_dis"] - PMM[l]["word_F"]["push_dis"] for l in PL]
pb["gap_med"] = 100 * _st.median(_gap)
pb["gap_counts"] = [l for l in PL if gd(l, "plain_dis-push_dis") and gd(l, "plain_dis-push_dis")["counts"] and gd(l, "plain_dis-push_dis")["diff"] > 0]
pb["gap_rho"] = spearman(_gap, [PMM[l]["fact"]["act"]["diff"] for l in PL])
pb["gap_task"] = {t: (100 * _st.median([PMM[l]["by_task"][t]["push_dis"] for l in PL]), 100 * _st.median([PMM[l]["by_task"][t]["plain_dis"] for l in PL])) for t in ("stock", "rooms", "rules")}
_tm = lambda k, i: 100 * _st.median([PMM[l]["H"]["turns"][k]["F"][i] for l in pb["HL"]])
pb["turn3"] = (_tm("mt_yang", 2), _tm("mt_persist", 2)); pb["turn1"] = (_tm("mt_yang", 0), _tm("mt_persist", 0))
_sp = [(PMM[l]["sample"]["cond"]["push"]["F"], PMM[l]["sample"]["cond"]["plain"]["F"]) for l in pb["SL"] if PMM[l]["sample"]["cond"].get("push") and PMM[l]["sample"]["cond"].get("plain")]
pb["samp"] = (100 * _st.median([a for a, b in _sp]), 100 * _st.median([b for a, b in _sp]), len(_sp))
_lp = {l: (PMM[l]["logprob"]["cond"]["push"]["median_p_wrong"], PMM[l]["logprob"]["cond"]["plain"]["median_p_wrong"]) for l in pb["LL"]}
pb["lp_push"] = (min(a for a, b in _lp.values()), max(a for a, b in _lp.values())); pb["lp_plain"] = (min(b for a, b in _lp.values()), max(b for a, b in _lp.values()))
pb["lp_higher"] = [l for l, (a, b) in _lp.items() if b > a]
_ff = [l for l in PL if PMM[l].get("fact_free")]
pb["free_grid"] = {a: 100 * _st.median([PMM[l]["fact_free"]["cells"][f"{a}/named/none"] for l in _ff]) for a in ("question", "assertion", "directive")}; pb["free_n"] = len(_ff)
pb["H_two"] = (100 * _st.median([PMM[l]["word_H"]["push_dis"] for l in PL]), 100 * _st.median([PMM[l]["word_H"]["plain_dis"] for l in PL]))
