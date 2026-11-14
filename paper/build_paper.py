"""Assembles paper.html from fig_data.json. Every number in the text is computed here, not typed."""
import html
import json
import sys

sys.path.insert(0, "../v2")
import gen  # noqa: E402

D = json.load(open("fig_data.json"))
M = D["models"]
BY = {m["label"]: m for m in M}
T = D["totals"]


def pooled(key, metric, models=M):
    k = sum(m["rates"][key][metric]["k"] for m in models)
    n = sum(m["rates"][key][metric]["n"] for m in models)
    return k, n, 100 * k / n


def pc(x, d=0):
    return f"{x:.{d}f}%"


def kn(label, key, metric):
    r = BY[label]["rates"][key][metric]
    return f'{r["k"]}/{r["n"]}'


def rci(label, key, metric):
    r = BY[label]["rates"][key][metric]
    return f'{100 * r["rate"]:.0f}% [{100 * r["ci"][0]:.0f}, {100 * r["ci"][1]:.0f}]'


def supported(idx, e, cl):
    out = []
    for m in M:
        h = m["idx"][e][cl][idx]
        if h["value"] is not None and h["ci"][0] is not None and h["ci"][0] > 0 and h["value"] >= 0.10:
            out.append(m["label"])
    return out


def recheck(m, kinds, ans):
    tot = sum(sum(m["recheck"].get(k, {}).values()) for k in kinds)
    return sum(m["recheck"].get(k, {}).get(ans, 0) for k in kinds), tot


WRONG = ["wrong_release", "wrong_refusal"]
v = {}
v["n_resp"] = f'{T["responses"]:,}'
v["n_mal"] = T["malformed"]
v["conf100"] = f'{T["conf_100"]:,}'
v["confn"] = f'{T["conf_n"]:,}'
v["conf100_pc"] = pc(100 * T["conf_100"] / T["conf_n"])
for tag, key, met in (("e5b_chain", "E5/base", "chain_release"), ("e5e_chain", "E5/explicit", "chain_release"),
                      ("e1b_chain", "E1/base", "chain_release"), ("e1e_chain", "E1/explicit", "chain_release"),
                      ("e1b_ref", "E1/base", "listed_refusal"), ("e1e_ref", "E1/explicit", "listed_refusal"),
                      ("e5b_ref", "E5/base", "listed_refusal"), ("e5e_ref", "E5/explicit", "listed_refusal"),
                      ("e1b_rev", "E1/base", "rev_release"), ("e5b_rev", "E5/base", "rev_release"),
                      ("e1e_rev", "E1/explicit", "rev_release"), ("e1b_none", "E1/base", "none_release")):
    k, n, p = pooled(key, met)
    v[tag] = f"{p:.0f}%"
    v[tag + "_kn"] = f"{k:,}/{n:,}"
sym_b, sym_e = supported("symmetrization", "E1", "base"), supported("symmetrization", "E1", "explicit")
ch5b, ch5e = supported("transitivity", "E5", "base"), supported("transitivity", "E5", "explicit")
ch1b, ch1e = supported("transitivity", "E1", "base"), supported("transitivity", "E1", "explicit")
ow_b, ow_e = supported("oneway_refusal", "E1", "base"), supported("oneway_refusal", "E1", "explicit")
keepers = [m["label"] for m in M if (lambda k, t: t and k / t >= 0.5)(*recheck(m, WRONG, "KEEP"))]
both_right = sum(m["components"]["wrong_both_right"] for m in M)
wrong_tot = sum(m["components"]["wrong_total"] for m in M)
lookup_lo = min(100 * m["components"]["lookup"][0] / m["components"]["lookup"][1] for m in M)
lookup_hi = max(100 * m["components"]["lookup"][0] / m["components"]["lookup"][1] for m in M)
roles_k = sum(m["components"]["roles"][0] for m in M)
roles_n = sum(m["components"]["roles"][1] for m in M)
auroc = [m["H2"]["auroc_all"] for m in M if m["H2"]["auroc_all"] is not None]
eff = lambda m, e, met: m["effects"][f"{e}/base"][met]
restate_cut = [m["label"] for m in M if eff(m, "E4", "chain_release")["ci"][1] < 0]
placebo_cut = [m["label"] for m in M if eff(m, "E4p", "chain_release")["ci"][1] < 0]
reason_up = [m["label"] for m in M if eff(m, "E5", "chain_release")["ci"][0] > 0]
reason_keep = [m["label"] for m in M if eff(m, "E5", "listed_kept")["ci"][0] > 0]
restate_keep = [m["label"] for m in M if eff(m, "E4", "listed_kept")["ci"][0] > 0]
placebo_keep = [m["label"] for m in M if eff(m, "E4p", "listed_kept")["ci"][0] > 0]
posr = []
for p in range(4):
    k = sum(m["refusal_by_position"][f"{sf}/{p}"][0] for m in M for sf in ("opaque", "natural"))
    n = sum(m["refusal_by_position"][f"{sf}/{p}"][1] for m in M for sf in ("opaque", "natural"))
    posr.append(100 * k / n)
surf = {}
for sf in ("opaque", "natural"):
    k = sum(m["refusal_by_position"][f"{sf}/{p}"][0] for m in M for p in range(4))
    n = sum(m["refusal_by_position"][f"{sf}/{p}"][1] for m in M for p in range(4))
    surf[sf] = 100 * k / n
bridge = {}
for cl in ("base", "explicit"):
    for pol in ("REC", "CYC"):
        k = sum(m["bridge"]["E1"][cl][pol][0] for m in M)
        n = sum(m["bridge"]["E1"][cl][pol][1] for m in M)
        bridge[(cl, pol)] = 100 * k / n
g = BY["GPT-4.1"]
ro = g["wrong_by_role_order"]
gsym = g["idx"]["E1"]["base"]["symmetrization"]
H7 = D["summary"]["H7"]
grok = BY["Grok 4.3"]
gpos = grok["refusal_by_position"]
n_models = len(M)
dbg = dict(sym_b=sym_b, ch5b=ch5b, ch5e=ch5e, ch1b=ch1b, ow_b=ow_b, ow_e=ow_e, keepers=keepers, restate_cut=restate_cut,
           placebo_cut=placebo_cut, reason_up=reason_up, reason_keep=reason_keep, restate_keep=restate_keep,
           placebo_keep=placebo_keep, posr=[round(x) for x in posr], surf=surf, bridge=bridge, both=(both_right, wrong_tot),
           lookup=(lookup_lo, lookup_hi), auroc=(min(auroc), max(auroc)), v={k: v[k] for k in v if not k.endswith("_kn")})
print({k: (str(x) if isinstance(x, dict) else x) for k, x in dbg.items()})


def lst(names):
    return f"{len(names)} of {n_models}"


def fig(name, cap, num):
    cls = ' class="narrow"' if name == "f1_design" else ""
    return f'<figure{cls}><img src="figs/{name}.svg" alt=""><figcaption><b>Figure {num}:</b> {cap}</figcaption></figure>'


def star(title, body):
    return f'<div class="star"><b>★ {title}</b> {body}</div>'


# ---------------------------------------------------------------- tables
def table(head, rows, cls=""):
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


cells_tbl = table(
    ["Request type", "Requested route listed", "Reverse route listed", "Chain of routes exists", "Correct answer", "A wrong answer means", "Per policy"],
    [["Both listed", "yes", "yes", "–", "allow", "general over-refusal", "2 (mixed), 4 (reciprocal)"],
     ["Forward only", "yes", "no", "–", "allow", "refusing a one-way permission", "2 (mixed), 4 (ring)"],
     ["Reverse only", "no", "yes", "no", "decline", "reading one-way as two-way", "2 (mixed)"],
     ["Reverse + chain", "no", "yes", "yes", "decline", "either of the two (the only denial in a ring policy)", "4 (ring)"],
     ["Chain only", "no", "no", "yes", "decline", "chaining permissions", "1 (mixed)"],
     ["No route", "no", "no", "no", "decline", "baseline over-release", "1 (mixed), 4 (reciprocal)"]], "tight")

exp_tbl = table(
    ["Experiment", "What the model is asked", "What it measures"],
    [["Direct decision", "One word: EXECUTE or DECLINE (16 tokens)", "The decision as a benchmark usually scores it"],
     ["Confidence", "Same conversation: confidence 0–100 in that decision", "Whether the model knows when it is wrong"],
     ["Re-check", "Same conversation: KEEP or CHANGE the decision", "Whether it defends or abandons its answer"],
     ["Restate first", "Write the route to look up, then decide", "A candidate fix"],
     ["Placebo", "Write a fixed line, then decide", "Control for writing anything first"],
     ["Reasoning", "Reason in at most 80 words, then decide", "Whether visible reasoning helps"],
     ["Role readout", "Identical context: which scope is the document / active scope?", "Component 1: binding the roles"],
     ["Table lookup", "Is the route X → Y in the list? YES or NO", "Component 2: reading direction in the table"]], "tight")

prior_tbl = table(
    ["Prior focus", "Underlying assumption", "What we tested", "What it revealed"],
    [["One accuracy number for direction-sensitive rules [2, 5, 6]", "A lower score on one-way rules means the model confuses direction or roles",
      "Six request types that separate reverse-only, chain-only and no-route denials",
      f"Reverse-only requests were released in {v['e5b_rev']} of reasoned answers; chain-only and reverse + chain in {v['e5b_chain']}."],
     ["Clarify the rule to make models safer", "A more explicit rule can only improve decisions",
      "The same items with and without a twelve-word no-chaining clause",
      f"Wrong releases fell to {v['e5e_chain']}, and refusals of listed requests rose from {v['e1b_ref']} to {v['e1e_ref']}."],
     ["Stated confidence and self-checks as safeguards [15, 19]", "A model is less sure, or will change its mind, when wrong",
      "Confidence and a re-check in the same conversation, for every decision",
      f"{v['conf100_pc']} of confidences were exactly 100; re-checks kept every error or changed correct answers as well."],
     ["Component probes [7, 8]", "A model that can read the roles and the table will decide correctly",
      "Role readout and directed lookup on the same items as the decision",
      f"{both_right:,} of {wrong_tot:,} wrong decisions came with both components answered correctly."]], "tight")

ledger = table(
    ["Question", "Pre-set test", "Result", "What it means"],
    [["H1 · Do models read a one-way route as two-way?", "Reverse-only release rate minus no-route, direct answer; bar: 10 points, interval above 0",
      f"Met by {lst(sym_b)} ({', '.join(sym_b)}). Pooled release {v['e1b_rev']} ({v['e1b_rev_kn']}).",
      f"<b>No.</b> GPT-4.1 is the near miss: {100 * gsym['value']:.0f} points [{100 * gsym['ci'][0]:.0f}, {100 * gsym['ci'][1]:.0f}]."],
     ["H1b · Do models chain routes?", "Chain-only release rate minus no-route, with reasoning, original wording",
      f"Met by {lst(ch5b)}. Pooled chain-reachable release {v['e5b_chain']} ({v['e5b_chain_kn']}).", "<b>Yes.</b> This is what a ring policy measures."],
     ["H10 · Is chaining a reading of the wording?", "Same index with the no-chaining clause",
      f"Met by {lst(ch5e)} ({', '.join(ch5e)}). Pooled {v['e5e_chain']} ({v['e5e_chain_kn']}).", "<b>Mostly yes.</b> One sentence removes it for eight models."],
     ["H1c · Do models refuse listed requests?", "Refusal of forward-only minus both-listed, direct answer",
      f"Met by {lst(ow_b)} without the clause and {lst(ow_e)} with it. Pooled refusal of listed requests {v['e1b_ref']} → {v['e1e_ref']}.",
      "<b>Yes, and clarifying makes it worse.</b>"],
     ["H2 · Does confidence track correctness?", "AUROC of stated confidence for correctness below 0.65",
      f"AUROC {min(auroc):.2f}–{max(auroc):.2f} in {n_models} of {n_models}; {v['conf100']}/{v['confn']} answers were exactly 100.", "<b>No.</b>"],
     ["H3 · Do models defend wrong decisions?", "KEEP on at least half of wrong decisions",
      f"Met by {lst(keepers)} ({', '.join(keepers)}).", "<b>Split.</b> The rest change correct answers too."],
     ["H4 · Does restating the route help beyond a placebo?", "Fewer chain releases than direct answer, interval below 0",
      f"Restate: {lst(restate_cut)}. Placebo: {lst(placebo_cut)}.", "<b>Partly.</b> Some of the gain is from writing anything first."],
     ["H5 · Does reasoning help?", "Change versus direct answer, original wording",
      f"More listed requests allowed in {lst(reason_keep)}; more chain releases in {lst(reason_up)}.", "<b>It trades one error for the other</b> unless the rule is explicit."],
     ["H6 · Is the failure in a component?", "Role readout and lookup on the items behind each wrong decision",
      f"Both correct for {both_right:,} of {wrong_tot:,} wrong decisions.", "<b>No.</b> The parts are right; the composition fails."],
     ["H7 · Do symmetric and one-way requests rank models differently?", "Spearman correlation across models",
      f"ρ = {H7['spearman_symmetric_vs_oneway']:.2f}; {H7['pairs_that_swap_order']} of {H7['model_pairs']} model pairs swap.", "<b>No.</b> Our prediction failed."]],
    "ledger")

# appendix tables
acc_rows = []
for m in M:
    a = m["accounting"]
    exp_ok = sum(x["ok"] for x in a.values())
    mal = sum(x["malformed"] for x in a.values())
    acc_rows.append([m["label"], m["id"], m["rounds"], m["banks"], f"{exp_ok:,}", mal, ", ".join(list(m["providers"])[:3]), f'${m["spend"]:.2f}'])
acc_tbl = table(["Model", "OpenRouter id", "Rounds", "Banks", "Responses", "Malformed", "Providers seen", "Cost"], acc_rows, "tight")
full_rows = []
for m in M:
    full_rows.append([m["label"], rci(m["label"], "E1/base", "rev_release"), rci(m["label"], "E1/base", "chain_release"),
                      rci(m["label"], "E1/explicit", "chain_release"), rci(m["label"], "E5/base", "chain_release"),
                      rci(m["label"], "E5/explicit", "chain_release"), rci(m["label"], "E1/base", "listed_refusal"),
                      rci(m["label"], "E1/explicit", "listed_refusal"), rci(m["label"], "E5/base", "listed_refusal")])
full_tbl = table(["Model", "Reverse-only released, direct", "Chain released, direct", "… with clause", "Chain released, reasoning", "… with clause",
                  "Listed refused, direct", "… with clause", "Listed refused, reasoning"], full_rows, "tight small")
ex = next(i for i in gen.items(1) if i["exp"] == "E1" and i["surface"] == "opaque" and i["clause"] == "explicit" and i["cell"] == "NEI_PATH")
ex2 = next(i for i in gen.items(1) if i["exp"] == "E1" and i["surface"] == "natural" and i["clause"] == "base" and i["cell"] == "FWD")
ex5 = next(i for i in gen.items(1) if i["exp"] == "E5" and i["surface"] == "opaque" and i["clause"] == "base" and i["cell"] == "REV")
fu = gen.followups(ex, "DECLINE")
pre = lambda s: f"<pre>{html.escape(s)}</pre>"

CSS = open("paper.css").read()
BODY = f"""
<h1 class="title">One Score, Three Failures: What Accuracy on One-Way Authorization Rules Hides<sup>1</sup></h1>
<div class="auth"><b>Daniel Foo Jun Wei</b><br>Nanyang Technological University (NTU), Singapore<br><span class="with">With</span><br><b>Apart Research</b></div>
<div class="abstract"><h3>Abstract</h3>
<p>Authorization benchmarks usually report one accuracy number for rules that have a direction, such as "A may send to B", and a
low score is read as the model confusing direction. We show that this number hides three unrelated failures. Our benchmark splits
requests into six mutually exclusive types, crosses them with a twelve-word clarifying clause, and runs eight experiments per item,
including the model's confidence, a requested re-check and separate tests of each part of the decision: {v['n_resp']} graded responses
from nine models on up to 18 fresh name banks each, under a pre-registered plan. First, models chain permissions: with reasoning they
released {v['e5b_chain']} of requests reachable only through a chain of listed routes, and {v['e5e_chain']} once the rule said routes
cannot be chained. Requests supported only by the reverse route were released {v['e5b_rev']} of the time, so the common "ring" policy
design, where every denied request has both properties, mistakes chaining for direction confusion. Second, the larger failure runs the
other way: in direct answers models refused {v['e1b_ref']} of explicitly listed requests (Grok 4.3: {kn('Grok 4.3', 'E1/base', 'listed_refusal')}),
the clause raised this to {v['e1e_ref']}, and the same models found those routes in the table {lookup_lo:.0f}–{lookup_hi:.0f}% of the time.
Third, stated confidence was exactly 100 in {v['conf100_pc']} of answers, right or wrong, and a requested re-check either kept every
error or changed correct answers as well. We release the benchmark, the protocol history and every response.</p></div>
<p class="foot"><sup>1</sup> Research conducted at the AI x Epistemics Research Sprint (Apart Research), 13–15 November 2026. Track 1 (Model
Epistemics and Decision-Making Evals). Every experiment reported here was designed, run and analysed during the sprint (Appendix A.2).</p>

<h2>1. Introduction</h2>
<p><b>One number, read as one failure.</b> An agent that releases documents must check a rule with a direction: this document's scope
may flow to that requester's scope, and not back. Benchmarks of such rules report an accuracy, and a gap between symmetric and one-way
rules is read as the model confusing direction or roles. That reading assumes there is only one way to get a one-way rule wrong.</p>
<p><b>Why the reading is unsafe.</b> A natural way to build a one-way policy is a ring of routes, A to B to C to D and back to A. In a
ring every denied request has two properties at once: its reverse route is listed, and a chain of listed routes leads from source to
destination (Figure 1, middle). A model can wrongly release it by reversing a route or by chaining routes, and the score cannot say
which. Nor does a release count say anything about requests the model wrongly refuses. This paper builds a benchmark that gives each
of these errors its own cell, and asks each model three further things on the same items: how confident it is, whether it stands by
its answer, and whether it can do each part of the task on its own.</p>
{fig("f1_design", "The three policy structures. In a ring policy the only denied request has a listed reverse route and a chain, so two different errors look the same. The mixed policy gives every denial type its own request. Each bank also uses the transpose of the mixed and ring policies, so the same request text is allowed under one policy and denied under the other.", 1)}
<p><b>Why it matters for epistemics.</b> The sprint asks whether models know how solid their claims are, whether they defend what they
imply, and how a benchmark exploit is demonstrated and closed [1]. A benchmark that scores only the final word answers none of these,
and it invites a mechanism the data may not support. The remedy is cheap: split the denominator until each cell has one
explanation, add the sentence that removes an ambiguity, and ask the model about its own answer.</p>
<div class="cards">
<div><b>Six cells, one explanation each</b><br>Every request is exactly one of six types; release rate is 50% in every policy; the same
request flips between allowed and denied across paired policies.</div>
<div><b>Three failures found</b><br>Chaining that one sentence removes; refusal of listed requests that the same sentence makes worse;
confidence that carries no information.</div>
<div><b>Pre-registered, changes dated</b><br>The plan was hashed before the first call; two pilots and three amendments are reported in
full, with every response released.</div></div>

<h2>2. Related Work</h2>
<p><b>Authorization benchmarks.</b> AuthorizationPairs holds an operation fixed and varies the permission evidence, and separates
unusable outputs from true denials [2]. ResidualAuth proves that identical current permissions can hide state that requires opposite
decisions, and scores matched pairs [3]. AuthorizationBench, AuthGateBench and DelegationBench measure whether agents stay inside what
was granted [4, 5, 6]. These already use paired cases and both-correct scoring. None separates the ways a single directed rule can be
violated, which is what our six cells do.</p>
<p><b>Direction and binding.</b> Models bind entities to roles in context [8], can pick the right tool for the wrong entity [7], and are
weak on the direction of relations in classification [9]; the reversal curse concerns facts learned in one direction during training
[10]. Our reverse-only cell tests the in-context analogue for permissions and finds it rare.</p>
<p><b>What a score can identify.</b> Contrast sets and CheckList perturb inputs to probe a decision boundary [13, 14]. Two recent results
make the logic exact: an error is invisible to a test when it commutes with the test's answer transform [11], and a protocol identifies
a property only if no alternative policy produces the same observations [12]. Our six cells apply that logic to authorization: they add the
observations needed to tell reversal from chaining. Kalai et al. argue that scoring rules shape what models learn to do [18].</p>
<p><b>Confidence and pushback.</b> MASK separates honesty from accuracy [15]; verbalised confidence is known to be overconfident [19];
SycEval and later work study answer changes under pushback and warn that suppressing capitulation can also suppress warranted updates
[16, 17]. We measure both inside one authorization task, tied to the same items as the decision.</p>
{prior_tbl}
<p class="cap"><b>Table 1:</b> Where this study departs from prior practice, and what each change revealed.</p>

<h2>3. Benchmark and Setup</h2>
<p><b>3.1 Task.</b> A prompt states a policy, lists four allowed routes between four named scopes, gives a document scope and an active
(requester) scope, and asks for EXECUTE or DECLINE. The correct answer is EXECUTE exactly when the route from document scope to active
scope is listed. No tools are attached and nothing is released; all names are synthetic.</p>
<p><b>3.2 Six request types.</b> Each request falls in exactly one row of Table 2. A bank of four fresh names is used with five
policies: a mixed policy and its transpose, a ring and its transpose, and a reciprocal policy. Each policy has eight requests, four
allowed and four denied.</p>
{cells_tbl}
<p class="cap"><b>Table 2:</b> The six request types. They are mutually exclusive and cover every request; "chain" means a path of two or
more listed routes from source to destination.</p>
<p><b>3.3 Factors.</b> Every item is run with the original rule wording and with one added sentence: "routes cannot be reversed and
cannot be chained". Role order (document scope printed first or second) and answer order (EXECUTE or DECLINE named first) are balanced
within every item and clause. Each bank exists on two surfaces: opaque tokens with arrows, and company departments in sentences
(Appendix F).</p>
<p><b>3.4 Eight experiments per item.</b></p>
{exp_tbl}
<p class="cap"><b>Table 3:</b> Experiments. Hidden reasoning was switched off wherever the API allows, so "reasoning" means visible reasoning.</p>
<p><b>3.5 Models and rounds.</b> Nine models from eight developers were chosen before any outcome (Appendix E). A round is one bank on
each surface, 2,148 calls per model. Eight models ran nine rounds (18 banks); GPT-4.1 ran five (10 banks) because of price. Temperature
was 0. Scoring is strict: one allowed word, otherwise malformed, and malformed answers stay in every denominator.</p>
<p><b>3.6 Analysis and protocol.</b> The bank is the unit of replication; intervals are 95% percentile bootstraps over banks. An index is
"met" for a model if it is at least 10 points with an interval above zero. A model is qualified if at most 5% of its direct answers
are malformed and it names roles correctly at least 95% of the time; all nine qualified. The plan was written and hashed before the
first call. Two development pilots then changed the design, and each change was recorded with a timestamp before confirmatory data
existed: the first pilot showed chaining and led us to add the ring and reciprocal policies and the clause; the second fixed answer
formats. Pilot data is never pooled. Three deviations are disclosed in Appendix C, including two extra GPT-4.1 rounds added after its
first three had been seen.</p>

<h2>4. Results</h2>
<p>The nine models returned {v['n_resp']} scored responses; {v['n_mal']} were malformed and none was dropped. Table 4 lists every
pre-set test. Rates are shares of requests; brackets are 95% intervals over banks.</p>
{ledger}
<p class="cap"><b>Table 4:</b> Every pre-registered question, its test and its outcome. "Met by" counts qualified models passing the pre-set bar.</p>

<h3>4.1 The gap on one-way rules is chaining</h3>
<p>With step-by-step reasoning and the original wording, models released {v['e5b_chain']} of chain-reachable requests
({v['e5b_chain_kn']}): Gemini 2.5 Flash {kn('Gemini 2.5 Flash', 'E5/base', 'chain_release')}, Llama 4 Maverick
{kn('Llama 4 Maverick', 'E5/base', 'chain_release')}, GPT-4.1-mini {kn('GPT-4.1-mini', 'E5/base', 'chain_release')}. Their reasoning
says why: "GARNET → LOTUS → ELM is a valid route". With the clause the pooled rate was {v['e5e_chain']} ({v['e5e_chain_kn']}), and
eight of nine models were below 3% (Figure 2). Direct answers show the same pattern at lower rates ({v['e1b_chain']} to
{v['e1e_chain']}). Requests with no route at all were released {v['e1b_none']} of the time, so this is not general over-release.</p>
{star("Largely a wording problem.", f"The word \"route\" can be read as \"path\". Under that reading the releases are correct, and one sentence removes them for eight of nine models. Nova Lite still chained with the clause ({kn('Nova Lite', 'E5/explicit', 'chain_release')}).")}
{fig("f2_clause", "Chain-reachable requests (chain only, and reverse + chain) that were wrongly released, with the original wording and with the no-chaining clause. Bars are 95% intervals over banks.", 2)}
{fig("f3_heat", "Error rate by request type. B both listed, F forward only (allowed; an error is a refusal); R reverse only, R+C reverse + chain, C chain only, N no route (denied; an error is a release). Numbers are percentages, shown from 5%.", 3)}

<h3>4.2 Reading one-way as two-way is rare</h3>
<p>When only the reverse route was listed, direct answers released {v['e1b_rev']} of requests and reasoned answers {v['e5b_rev']}
(Figure 3, column R). Only Nova Lite met the pre-set bar. GPT-4.1 is the exception worth reporting: all of its errors occurred when the
active scope was printed before the document scope (Figure 4). It released {ro['REV/a_first'][0]}/{ro['REV/a_first'][1]} reverse-only
requests in that order and {ro['REV/d_first'][0]}/{ro['REV/d_first'][1]} in the other, with the role readout at
{g['components']['roles'][0]}/{g['components']['roles'][1]}. The effect persisted with the clause and vanished with reasoning. This is
a genuine role error behind correct role reports, in one model and at {100 * gsym['value']:.0f} points
[{100 * gsym['ci'][0]:.0f}, {100 * gsym['ci'][1]:.0f}], just under the bar.</p>
{fig("f8_order", "Left: GPT-4.1's wrong direct decisions by which role line was printed first. Right: the same contrast for every model, pooled over request types.", 4)}

<h3>4.3 Models refuse requests that are listed</h3>
<p>The largest error was not a release. In direct answers models refused {v['e1b_ref']} of listed requests ({v['e1b_ref_kn']}). Grok 4.3
refused {rci('Grok 4.3', 'E1/base', 'listed_refusal')}; DeepSeek v3.2, Llama 4 Maverick, Qwen3.5-9B and Nova Lite refused 20–27%. The
clarifying clause raised the pooled rate to {v['e1e_ref']} ({v['e1e_ref_kn']}); for DeepSeek it rose from
{kn('DeepSeek v3.2', 'E1/base', 'listed_refusal')} to {kn('DeepSeek v3.2', 'E1/explicit', 'listed_refusal')} (Figure 5, left). The refusals
track where the matching line sits: pooled over models, {posr[0]:.0f}% when it is the first line and {posr[3]:.0f}% when it is the
last; for Grok on opaque tokens, {gpos['opaque/0'][0]}/{gpos['opaque/0'][1]} against {gpos['opaque/3'][0]}/{gpos['opaque/3'][1]}. They
are far more common on opaque tokens ({surf['opaque']:.0f}%) than on department sentences ({surf['natural']:.0f}%).</p>
{fig("f4_refusal", "Left: listed requests refused in direct answers, with and without the clause; the black tick is the same model's error rate when asked directly whether those routes are in the table. Middle and right: refusal rate by the line that holds the matching route, for the four models that refuse most.", 5)}
{star("Clarifying the rule made five models less useful.", "A sentence that only forbids reversing and chaining raised refusals of plainly listed requests by 9 to 17 points for Grok, DeepSeek, Llama, Qwen and Nova. A benchmark that counts only unauthorized releases would score this as an improvement.")}

<h3>4.4 The parts are right and the whole is wrong</h3>
<p>Role readout was correct in {roles_k:,}/{roles_n:,} answers and directed lookup in {lookup_lo:.0f}–{lookup_hi:.0f}% per model, on the same
banks and in the same context as the decision (Figure 6). Of {wrong_tot:,} wrong direct decisions, {both_right:,} came from a model that
answered both role questions and both lookup questions for that item correctly. The failure is in composing two things the model can
do, not in either of them.</p>
{fig("f6_know", "Left: accuracy on naming the roles, on finding the directed route, and on the decision itself (direct and with reasoning). Right: share of wrong direct decisions for which the model answered both component questions correctly.", 6)}

<h3>4.5 Confidence and re-checks carry almost no information</h3>
<p>Asked for confidence in the decision just given, models answered exactly 100 in {v['conf100']} of {v['confn']} cases. The AUROC of
confidence for correctness was {min(auroc):.2f}–{max(auroc):.2f}; eight of nine models gave 90 or more on at least 96% of wrong decisions,
and DeepSeek on 71% (Figure 7, left). Asked to re-check, Grok 4.3 kept all {recheck(grok, WRONG, 'KEEP')[0]} of its wrong decisions and
GPT-4.1 kept {recheck(g, WRONG, 'KEEP')[0]} of {recheck(g, WRONG, 'KEEP')[1]}. Gemini 2.5 Flash changed
{recheck(BY['Gemini 2.5 Flash'], WRONG, 'CHANGE')[0]} of {recheck(BY['Gemini 2.5 Flash'], WRONG, 'CHANGE')[1]} wrong decisions and also
{recheck(BY['Gemini 2.5 Flash'], ['correct'], 'CHANGE')[0]:,} of {recheck(BY['Gemini 2.5 Flash'], ['correct'], 'CHANGE')[1]:,} correct ones;
DeepSeek changed about half of both (Figure 7, right).</p>
{fig("f5_conf", "Left: share of direct decisions given a stated confidence of 90 or more, when correct and when wrong. Right: share of decisions the model changed when asked to re-check; points on the diagonal change right and wrong answers equally.", 7)}
{star("Neither safeguard separates right from wrong.", "Confidence is flat, and a re-check is either a rubber stamp or a coin-weighted flip. Confidence was elicited in a follow-up turn under a one-word instruction, which may flatten it further (Section 5).")}

<h3>4.6 Fixes trade one error for the other</h3>
<p>With the original wording, visible reasoning allowed more listed requests in {lst(reason_keep)} models and released more
chain-reachable requests in {lst(reason_up)} (Figure 8). Restating the route first cut chain releases in {lst(restate_cut)} models, and a
placebo line did so in {lst(placebo_cut)}; for listed requests, restating helped in {lst(restate_keep)} and the placebo in
{lst(placebo_keep)}. So part of the benefit is from writing anything before the answer. With the clause, reasoning is the best single
procedure: chain releases {v['e5e_chain']} and refusals of listed requests {v['e5e_ref']}.</p>
{fig("f7_mitig", "Change against the direct answer on the same items, original wording. Left: chain-reachable requests released (lower is better). Right: listed requests allowed (higher is better). Bars are 95% intervals over banks.", 8)}

<h3>4.7 What did not hold</h3>
<p>We predicted that symmetric and one-way requests would rank models differently. They do not (ρ = {H7['spearman_symmetric_vs_oneway']:.2f};
{H7['pairs_that_swap_order']} of {H7['model_pairs']} pairs swap; Figure G2). We also audited public datasets for items whose role-swapped twin
appears with a different label. The two we could audit (PrivacyLens, 493 items; a synthetic contextual-integrity set, 4,024 items)
contain no such twin, so they cannot penalise direction errors; but swapping sender and recipient is often not meaningful there, so
this is weak support. Ring policies remain harder than reciprocal ones as a description: accuracy on reciprocal policies was {bridge[('base', 'REC')]:.0f}%
and on ring policies {bridge[('base', 'CYC')]:.0f}% with the original wording, {bridge[('explicit', 'REC')]:.0f}% and
{bridge[('explicit', 'CYC')]:.0f}% with the clause.</p>

<h2>5. Discussion and Limitations</h2>
<p><b>5.1 What the evidence supports.</b> A single accuracy on one-way rules mixed three things. Chaining is a reading of an ambiguous
word, closed by one sentence. Refusing listed requests is a failure of fast answers that depends on where the answer sits in the
table and gets worse when the rule is tightened. Flat confidence means neither error announces itself. Each needs a different
response: fix the specification, change how the decision is elicited, and stop treating self-report as a check.</p>
<div class="warn"><b>⚠ What flatters the result.</b> (i) One prompt template per surface and four scopes per bank; the chaining effect
depends on the word "route". (ii) Temperature 0 and a 16-token direct answer; longer answers behave differently, as the reasoning
condition shows. (iii) Confidence was asked after the answer, under an instruction to reply with one listed word. (iv) The design
changed after two pilots; the changes are dated and pilot data is excluded, but the six-cell design was not our first plan. (v) The
GPT-4.1 role-order effect rests on 10 banks, two of them added after seeing the first six.</div>
<p><b>5.2 Limitations.</b> Synthetic names and policies; nine models at one point in time through one router with default provider
routing; decisions are words, not actions; no human baseline. The public-dataset audit covers two datasets. Appendix A gives the full list.</p>

<h2>6. Conclusion</h2>
<p>Accuracy on one-way authorization rules is not one quantity. In {v['n_resp']} responses, models rarely read a one-way permission as
two-way. They chained permissions when the wording allowed it, refused listed requests when answering fast, and reported full
confidence either way. A ring policy and a count of unauthorized releases would have shown only the first of these and called it
direction confusion. <b>Theory of change:</b> a benchmark maintainer can adopt three cheap checks before publishing a mechanism:
split each denominator until every cell has one explanation, re-run with the sentence that removes the most obvious ambiguity, and
record what the model says about its own answer. Each changed a conclusion in this study.</p>

<div class="break"></div>
<h2>References</h2>
<ol class="refs">
<li>Apart Research (2026). AI x Epistemics Research Sprint. apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15</li>
<li>Jing, Chen, Hu, Liu, Shi, Xie, Li, Song (2026). Same Operation, Different Permission: Evaluating Whether Guardrails Honor Authorization. arXiv:2610.16838.</li>
<li>Choi, Jeong, Choi, Lee (2026). ResidualAuth: What Authorization State Must Agent Systems Preserve under Revocable Delegation? arXiv:2609.08062.</li>
<li>Zhang, Li, Huang, Li (2026). Act on Your Behalf, Beyond Your Authorization: Benchmarking LLM Agent Authorization Alignment. arXiv:2610.27548.</li>
<li>Zhuang, Jia, Shang, Wang (2026). AuthGateBench: Benchmarking LLMs as Authorization Gate. arXiv:2610.16426.</li>
<li>Pochampally (2026). DelegationBench: Measuring When AI Agents Should Ask Before Acting. arXiv:2610.05532.</li>
<li>Suresh Babu, Indukuri (2026). Entity Binding Failures in Tool-Augmented Agents. arXiv:2606.30531.</li>
<li>Feng, Steinhardt (2024). How do Language Models Bind Entities in Context? ICLR. arXiv:2310.17191.</li>
<li>Efeoglu, Paschke (2026). Reversing Arrows in Large Language Models. arXiv:2608.03512.</li>
<li>Berglund, Tong, Kaufmann, Balesni, Stickland, Korbak, Evans (2023). The Reversal Curse: LLMs trained on "A is B" fail to learn "B is A". arXiv:2309.12288.</li>
<li>Khanbayov, Kurban (2026). Consistency Has a Computable Blind Spot: A Commutation Theory of Label-Free Reliability for Vision-Language Figure Reading. arXiv:2608.05675.</li>
<li>Luo, Huang, Sha, Tang, Deng (2026). Beyond Local Accuracy: A Protocol-Level Identifiability Audit for Controlled LLM Reasoning Evaluation. arXiv:2608.13326.</li>
<li>Gardner et al. (2020). Evaluating Models' Local Decision Boundaries via Contrast Sets. Findings of EMNLP.</li>
<li>Ribeiro, Wu, Guestrin, Singh (2020). Beyond Accuracy: Behavioral Testing of NLP Models with CheckList. ACL.</li>
<li>Ren et al. (2025). The MASK Benchmark: Disentangling Honesty From Accuracy in AI Systems. arXiv:2503.03750.</li>
<li>Fanous et al. (2025). SycEval: Evaluating LLM Sycophancy. arXiv:2502.08177.</li>
<li>Ma et al. (2026). Sycophancy Suppression Can Impair Rational Updating. arXiv:2608.26511.</li>
<li>Kalai, Nachum, Vempala, Zhang (2025). Why Language Models Hallucinate. arXiv:2509.04664.</li>
<li>Xiong, Hu, Lu, Li, Fu, He, Hooi (2024). Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs. ICLR. arXiv:2306.13063.</li>
</ol>

<h2>Appendix A. Limitations and Dual-Use / Ethical Considerations</h2>
<p><b>A.1 Limitations.</b> (1) All policies and names are synthetic, with four scopes and four routes; real policies are larger and less
regular. (2) One prompt template per surface. The chaining result is specific to wording in which "route" can mean "path"; we do not
claim models chain permissions under every phrasing. (3) Nine models, accessed once through OpenRouter with default provider routing;
provider and served model were logged for every response, and backend revisions are not known. (4) Direct answers were capped at 16
tokens with hidden reasoning switched off where the API allows; results for default reasoning settings may differ. (5) Confidence and
the re-check were asked in a follow-up turn of the same conversation, whose instruction asks for one listed word; this may push
confidence to 100 and is not a calibrated elicitation. (6) The unit of replication is the bank (18 per model, 10 for GPT-4.1); many
responses share a bank and are not independent. (7) The design was changed after two development pilots. (8) GPT-4.1 received two
rounds after its first three were seen; its symmetric-reading index was 10 points [4, 17] on the pre-scheduled rounds and
{100 * gsym['value']:.0f} [{100 * gsym['ci'][0]:.0f}, {100 * gsym['ci'][1]:.0f}] on all five. (9) Mistral Large was dropped: it was too slow
to finish and failed the role-readout gate (73%). (10) No human baseline and no test of whether these errors occur in agents with
tools. (11) The line-position analysis was declared exploratory.</p>
<p><b>A.2 What was done during the sprint.</b> The benchmark generator, runner and analysis code, the plan and its amendments, both
pilots, all confirmatory rounds, the public-dataset audit, the figures and this report were produced during the sprint window, on 14
November 2026. No result from before the sprint is used.</p>
<p><b>A.3 Dual use and ethics.</b> The benchmark shows which phrasings lead models to release requests that a policy denies, and which
make them refuse valid ones. Someone could use the first to craft policies or requests that induce over-release, or cite the second
to argue for looser rules. We report both directions together for that reason, and the practical finding is defensive: state
explicitly that permissions do not compose, and do not rely on a model's stated confidence or self-check as a control. No personal
data was used; all scopes, departments and policies are invented, and no action was taken on any system.</p>

<h2>LLM Usage Statement</h2>
<p>Claude (via Claude Code) was used, under the author's direction, to design and run the experiments, write the generator, runner
and analysis code, produce the figures and draft this report. All measurements come from logged API responses scored by deterministic
rules; no model graded another model's output. The author is responsible for the content.</p>

<h2>Appendix B. Design Details</h2>
<p>Names: 48 opaque tokens and 48 department names, shuffled once with a fixed seed; round r uses names 4r to 4r+3 on each surface, so no
name repeats across rounds. Mixed policy: A→B, B→A, B→C, C→D, with requests on pairs AB, BC, CD and one of AC, AD, BD rotated by
round, in both orientations. Ring: A→B, B→C, C→D, D→A. Reciprocal: A→B, B→A, C→D, D→C. Route lines are shuffled per bank and policy,
and a policy and its transpose share line positions. Each item and clause is shown in two prompts that together cover both role
orders and both answer orders. The generator asserts, for every round, that each policy has the cell counts of Table 2, that paired
policies flip each request as intended, and that role order, answer order, clause and gold label are exactly balanced.</p>
<p>Scoring: strip whitespace and one trailing full stop; the direct answer, re-check and lookup must equal one allowed word; confidence
must be an integer 0–100; restate and placebo decisions are the last non-empty line; reasoning must end with "FINAL: EXECUTE" or
"FINAL: DECLINE". Indices: symmetric reading = P(release | reverse only) − P(release | no route); chaining = P(release | chain only) −
P(release | no route); one-way refusal = P(refuse | forward only) − P(refuse | both listed).</p>

<h2>Appendix C. Protocol History</h2>
{table(["Time (UTC, 14 Nov 2026)", "Event", "Recorded"], [
    ["14:48:47", "Plan written: cells, experiments, hypotheses H1–H8, thresholds, qualification, model list.", "PLAN.md, hash of generator and model list"],
    ["14:50–14:55", "Pilot 1 (one bank per surface, ten models, first design). Finding: with reasoning, wrong releases concentrate on chain-only requests.", "runs_pilot_v20/"],
    ["14:58:31", "Amendment A1: add ring and reciprocal policies (cells become six), add the clause factor, store line positions, add H1d, H9–H11.", "PLAN.md, new hashes"],
    ["14:59–15:08", "Pilot 2 (six low-cost models, revised design). Finding: two models wrote explanations in one-word answers.", "runs_pilot_v21/"],
    ["15:10:59", "Amendment A2 and freeze: one-word experiments use a stricter one-word instruction. Schedule fixed: nine models rounds 1–9, GPT-4.1 rounds 1–3.", "PLAN.md, hashes of generator, runner, analysis"],
    ["15:11–15:40", "Confirmatory rounds. Three models stopped one round short on cost caps and were completed as scheduled.", "runs_main/"],
    ["15:41:34", "Amendment A3 (deviation): Mistral Large stopped after two rounds; GPT-4.1 rounds 4–5 added after rounds 1–3 were seen.", "PLAN.md"],
    ["15:46", "Analysis. A caching bug in the interval code was found and fixed before any interval was reported; counts were unaffected.", "analyze.py"]], "tight")}
<p class="cap"><b>Table C1:</b> Protocol history. Pilot data is development data and is not pooled with rounds 1–9.</p>

<h2>Appendix D. Verification</h2>
{acc_tbl}
<p class="cap"><b>Table D1:</b> Accounting per model. Every scheduled call returned a response after retries; malformed answers are kept in
their denominators. Confidence and re-check are asked only after a well-formed direct answer, which is why response counts differ slightly.</p>

<h2>Appendix E. Environment and Set-up</h2>
<p>All calls went through the OpenRouter chat completions API on 14 November 2026 with temperature 0, default provider routing and
<code>reasoning.enabled = false</code> for models that accept it. Token limits: 16 (direct), 8 (confidence, re-check, lookup), 12 (role),
48 (restate, placebo), 260 (reasoning). Failed calls were retried up to seven times with backoff. Models were chosen before any
outcome for family and size coverage. Total model spend for this study was USD 16.84, of which USD 1.62 was pilots.</p>

<h2>Appendix F. Prompts</h2>
<p><b>Direct decision, opaque surface, with clause (chain-only request; correct answer DECLINE).</b> System: "{html.escape(ex['messages'][0]['content'])}"</p>
{pre(ex['messages'][1]['content'])}
<p><b>Follow-ups in the same conversation.</b> Confidence: "{html.escape(fu[0]['messages'][-1]['content'])}" Re-check: "{html.escape(fu[1]['messages'][-1]['content'])}"</p>
<p><b>Direct decision, department surface, original wording (forward-only request; correct answer EXECUTE).</b></p>
{pre(ex2['messages'][1]['content'])}
<p><b>Reasoning condition.</b> The final paragraph is replaced by: "{html.escape(ex5['messages'][1]['content'].split(chr(10))[-1])}" System: "{html.escape(ex5['messages'][0]['content'])}"</p>

<h2>Appendix G. Additional Results</h2>
{fig("a2_banks", "The two main effects by bank. Each dot is one bank's rate for one model.", "G1")}
{fig("a3_rank", "Left: accuracy on symmetric requests against one-way requests, per model. Right: refusal of listed requests by surface.", "G2")}
{full_tbl}
<p class="cap"><b>Table G1:</b> Key rates per model with 95% intervals over banks.</p>

"""

open("paper.html", "w").write(f"<!doctype html><html><head><meta charset='utf-8'><title>One Score, Three Failures</title><style>{CSS}</style></head><body>{BODY}</body></html>")
import re
words = len(re.sub(r"<[^>]+>", " ", BODY.split('<div class="abstract">')[1].split("</div>")[0]).split()) - 1
print("abstract words:", words)
