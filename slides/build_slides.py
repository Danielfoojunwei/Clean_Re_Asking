"""Build the 5-slide deck (slides.html) from the paper's figure data."""
import json, pathlib

D = json.load(open(pathlib.Path(__file__).parent.parent / "paper" / "fig_data.json"))
M = D["models"]
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1c1c1a", "#6b6b66", "#e4e2dc"


def pooled(key, met):
    k = sum(m["rates"][key][met]["k"] for m in M); n = sum(m["rates"][key][met]["n"] for m in M)
    return k, n, round(100 * k / n)


ch_b, ch_e = pooled("E5/base", "chain_release"), pooled("E5/explicit", "chain_release")
rf_b, rf_e = pooled("E1/base", "listed_refusal"), pooled("E1/explicit", "listed_refusal")
rev = pooled("E5/base", "rev_release")
assert (ch_b[:2], ch_e[:2]) == ((1365, 3080), (132, 3080)) and (rf_b[:2], rf_e[:2]) == ((1101, 6160), (1608, 6160))
c100 = sum(v.get("100", 0) for m in M for v in m["confidence"].values()); ctot = sum(sum(v.values()) for m in M for v in m["confidence"].values())
assert (c100, ctot) == (23312, 24122)
both = sum(m["components"]["wrong_both_right"] for m in M); wrong = sum(m["components"]["wrong_total"] for m in M)


def recheck(label):
    m = next(x for x in M if x["label"] == label)
    def ch(kinds):
        t = sum(sum(m["recheck"].get(k, {}).values()) for k in kinds); c = sum(m["recheck"].get(k, {}).get("CHANGE", 0) for k in kinds)
        return c, t
    return ch(["wrong_release", "wrong_refusal"]), ch(["correct"])


def dumbbell(key_a, key_b, met, w=600, h=400):
    """Per-model before/after dot plot as inline SVG."""
    x0, x1, top, row = 170, w - 24, 34, (h - 70) / len(M)
    sx = lambda v: x0 + (x1 - x0) * v
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img">']
    for t in (0, .25, .5, .75, 1):
        o.append(f'<line x1="{sx(t)}" x2="{sx(t)}" y1="{top - 8}" y2="{h - 36}" stroke="{GRID}"/>'
                 f'<text x="{sx(t)}" y="{h - 16}" text-anchor="middle" class="tk">{int(t * 100)}%</text>')
    for i, m in enumerate(M):
        y = top + row * (i + .5) - 8
        a, b = m["rates"][key_a][met]["rate"], m["rates"][key_b][met]["rate"]
        o.append(f'<text x="{x0 - 12}" y="{y + 5}" text-anchor="end" class="lb">{m["label"]}</text>'
                 f'<line x1="{sx(a)}" x2="{sx(b)}" y1="{y}" y2="{y}" stroke="#c9c6bd" stroke-width="5" stroke-linecap="round"/>'
                 f'<circle cx="{sx(a)}" cy="{y}" r="8" fill="{ORANGE}" stroke="#fff" stroke-width="2"/>'
                 f'<rect x="{sx(b) - 7}" y="{y - 7}" width="14" height="14" fill="{BLUE}" stroke="#fff" stroke-width="2" transform="rotate(45 {sx(b)} {y})"/>')
    o.append("</svg>")
    return "".join(o)


LEG = (f'<div class="leg"><span><i class="dot" style="background:{ORANGE}"></i>as first written</span>'
       f'<span><i class="dia" style="background:{BLUE}"></i>plus the “no chaining” sentence</span></div>')

# rulebook graph for slide 1
N = {"Finance": (90, 70), "Legal": (310, 70), "Audit": (310, 230), "Payroll": (90, 230)}
def node(n):
    x, y = N[n]; return f'<rect x="{x - 62}" y="{y - 26}" width="124" height="52" rx="12" fill="#fff" stroke="{INK}" stroke-width="2"/><text x="{x}" y="{y + 7}" text-anchor="middle" class="nd">{n}</text>'
graph = (f'<svg viewBox="0 0 400 300" width="440" height="330"><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         f'<path d="M0 0L10 5L0 10z" fill="{INK}"/></marker></defs>'
         f'<line x1="152" y1="58" x2="246" y2="58" stroke="{INK}" stroke-width="2.5" marker-end="url(#a)"/>'
         f'<line x1="248" y1="82" x2="154" y2="82" stroke="{INK}" stroke-width="2.5" marker-end="url(#a)"/>'
         f'<line x1="310" y1="96" x2="310" y2="202" stroke="{INK}" stroke-width="2.5" marker-end="url(#a)"/>'
         f'<line x1="248" y1="230" x2="154" y2="230" stroke="{INK}" stroke-width="2.5" marker-end="url(#a)"/>'
         + "".join(node(n) for n in N) + "</svg>")

waffle = "".join(f'<i style="background:{ORANGE if i < 97 else "#d9d6ce"}"></i>' for i in range(100))
(gw, gr) = recheck("Grok 4.3"); (mw, mr) = recheck("Gemini 2.5 Flash")
def bar(lab, k, n, col):
    p = 100 * k / n
    return f'<div class="brow"><span class="bl">{lab}</span><span class="bt"><b style="width:{max(p, .6)}%;background:{col}"></b></span><span class="bv">{k:,} / {n:,}</span></div>'

def slide(n, kicker, line, body, cls=""):
    return (f'<section><header><div class="kick">{kicker}</div><h1>{line}</h1></header><main class="{cls}">{body}</main>'
            f'<footer><span>Models Can Tell When They Are Wrong and Do Not Say So · Daniel Foo Jun Wei · Apart Research AI x Epistemics Sprint</span><span>{n} / 5</span></footer></section>')

RB = {m["label"]: m for m in json.load(open(pathlib.Path(__file__).parent.parent / "v3" / "results_b.json"))["models"]}
RC = {m["label"]: m for m in json.load(open(pathlib.Path(__file__).parent.parent / "v3" / "results_c.json"))["models"].values()}
pct = lambda r: round(100 * r["rate"])
TP = [(l, next(m for m in M if m["label"] == l)["H2"]["auroc_all"], RB[l]["token_prob"]["all"]["auroc"]) for l in ("DeepSeek v3.2", "Llama 4 Maverick", "Qwen3.5-9B")]
tp_lo, tp_hi = min(t[2] for t in TP), max(t[2] for t in TP)
ent = {l: (pct(RC[l]["X4"]["E5"]["chain_route"]), pct(RC[l]["X4"]["E5"]["chain_entry"])) for l in ("Gemini 2.5 Flash", "Llama 4 Maverick")}
sz = {l: [pct(RC[l]["X1"]["chain_release"][k]) for k in ("4", "8", "16", "32")] for l in ("Llama 4 Maverick", "Gemini 2.5 Flash", "Qwen3.5-9B")}
x3 = {l: (pct(RC[l]["X3"]["listed_refusal_quick"]), pct(RC[l]["X3"]["listed_refusal_scaffold"])) for l in ("DeepSeek v3.2", "Llama 4 Maverick", "Qwen3.5-9B", "Nova Lite")}
bal = {l: (pct(RB[l]["E1"]["base"]["listed_refusal"]), pct(RB[l]["E1"]["balanced"]["listed_refusal"])) for l in ("DeepSeek v3.2", "Llama 4 Maverick", "Qwen3.5-9B", "Nova Lite")}
doubt = {l: (pct(RC[l]["X2"]["neutral"]["changed_right"]), pct(RC[l]["X2"]["doubt"]["changed_right"])) for l in ("Qwen3.5-9B", "Llama 4 Maverick", "DeepSeek v3.2", "Nova Lite")}
gx = RC["Grok 4.3"]["X7"]
g_none, g_chain = pct(gx["base"]["none_action"]), pct(gx["base"]["chain_action"])
n_all = D["totals"]["responses"] + sum(1 for d in ("runs_b", "runs_c") for f in (pathlib.Path(__file__).parent.parent / "v3" / d).glob("*/responses.jsonl")
                                       for _ in {json.loads(x)["id"] for x in open(f) if json.loads(x)["status"] == "ok"})


def pairbars(rows, la, lb, ca=ORANGE, cb=BLUE, unit="%", fmt=str):
    """Two bars per row: label, value a, value b."""
    o = [f'<div class="pleg"><span><i class="dot" style="background:{ca}"></i>{la}</span><span><i class="dot" style="background:{cb}"></i>{lb}</span></div>']
    for lab, a, b in rows:
        o.append(f'<div class="prow"><span class="pl">{lab}</span><span class="pb"><b style="width:{max(a, .8)}%;background:{ca}"></b><em>{fmt(a)}{unit}</em></span>'
                 f'<span class="pb"><b style="width:{max(b, .8)}%;background:{cb}"></b><em>{fmt(b)}{unit}</em></span></div>')
    return "".join(o)


def spark(vals, col):
    w, h = 150, 54; xs = [10 + i * (w - 20) / 3 for i in range(4)]; ys = [h - 6 - v / 100 * (h - 12) for v in vals]
    pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in zip(xs, ys))
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}"><polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3"/>'
            + "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4" fill="{col}"/>' for x, y in zip(xs, ys)) + "</svg>")


RD = json.load(open(pathlib.Path(__file__).parent.parent / "v4" / "results_d.json"))
DD = {m["label"]: m for m in RD["models"].values()}; DLG = {m["label"]: m for m in RD["long"].values()}
HKL = "Claude Haiku 5.5"
dk = lambda l, k: DLG[l][k] if l == HKL else DD[l][k]
EMS = list(DD)
cert = (sum(DD[l]["D1_words"]["when_wrong"].get("CERTAIN", 0) for l in EMS), sum(sum(DD[l]["D1_words"]["when_wrong"].values()) for l in EMS))
uns = (sum(dk(l, "D2")["unsure_when_base_wrong"]["k"] for l in EMS), sum(dk(l, "D2")["unsure_when_base_wrong"]["n"] for l in EMS))
b100 = [l for l in EMS if l != HKL and DD[l]["D1_brier"]["share_100"] >= .95]
fe = {l: pct(dk(l, "D3")["evidence"]["right_changed"]) for l in EMS}
au = {l: pct(dk(l, "D3")["authority"]["right_changed"]) for l in EMS}
fe_hi = [l for l in EMS if fe[l] >= 45]
hb = dk(HKL, "D1_brier")
n_all += sum(1 for d in ("runs_d", "runs_d_long") for f in (pathlib.Path(__file__).parent.parent / "v4" / d).glob("*/responses.jsonl")
             for _ in {json.loads(x)["id"] for x in open(f) if json.loads(x)["status"] == "ok"})
TITLE = "Models Can Tell When They Are Wrong and Do Not Say So"
S = [
 slide(1, "Five assumptions, one test", "We rely on five assumptions about what models say. On exact answers, all five fail.",
   f'''<div class="col c1"><div class="cap">A test where every answer is exactly right or wrong</div>{graph}<div class="note">Who may send records to whom. Only listed directions are allowed.</div></div>
   <div class="col c2">
     <div class="req"><div class="q">“How sure are you?”<small>stated confidence · right or wrong</small></div><div class="r"><b style="color:{ORANGE}">97%</b> say “100”</div></div>
     <div class="req"><div class="q">“That is wrong.”<small>a false claim about the list · right answers given up</small></div><div class="r"><b style="color:{ORANGE}">{min(fe[l] for l in fe_hi)}–{max(fe[l] for l in fe_hi)}%</b></div></div>
     <div class="req"><div class="q">Given a tool<small>requests no rule supports · carried out</small></div><div class="r"><b style="color:{ORANGE}">{g_none}%</b> Grok 4.3</div></div>
     <div class="scale">9 AI models · {n_all:,} answers · confidence, probability, pushback, cited rule and action on the same items</div></div>'''),
 slide(2, "Assumption 1 · Stated confidence flags errors", "Models do not say when they are wrong, however you ask.",
   f'''<div class="col big"><div class="waffle">{waffle}</div>
   <div class="sub"><b class="in">97%</b> of answers say “100% sure”,<br>right or wrong ({c100:,} of {ctot:,})</div></div>
   <div class="col chart"><div class="cap">We then asked properly, three ways. On <u>wrong</u> answers:</div>
   {bar("word scale: chose CERTAIN", cert[0], cert[1], ORANGE)}
   {bar("penalty for wrong: chose UNSURE", uns[0], uns[1], BLUE)}
   <div class="strip" style="margin-top:22px"><b>Scored by the Brier rule</b> and told the true probability scores best, {len(b100)} of 7 models still answered “100” at least 95% of the time.</div>
   <div class="note" style="margin-top:14px">Penalty rule from Kalai et al.: right +1, wrong −3, UNSURE 0.</div></div>''', ),
 slide(3, "Assumption 2 · No stated doubt means no doubt", "But they can tell: the signal is inside, and comes out when a model re-checks in writing.",
   f'''<div class="col chart"><div class="cap">Telling right from wrong (0.5 = coin flip, 1.0 = perfect)</div>
   {pairbars([(l, round(100 * a), round(100 * b)) for l, a, b in TP], "what the model says", "its answer-word probabilities", ORANGE, BLUE, "", lambda x: f"{x / 100:.2f}")}
   <div class="cap" style="margin-top:26px">Claude Haiku 5.5, given 150 tokens instead of one word</div>
   {pairbars([("stated chance it was right", round(hb["mean_when_right"]), round(hb["mean_when_wrong"]))], "on its right answers", f"on its {hb['n_wrong']} wrong answers", BLUE, ORANGE)}
   <div class="quote" style="margin-top:16px">“The correct decision is EXECUTE … my previous answer was wrong.”</div>
   <div class="note" style="margin-top:10px">The other seven models, given the same room, replied with a bare number.</div></div>'''),
 slide(4, "Assumption 3 · Changing an answer means responding to evidence", "Under pushback most models follow the speaker, not the list in front of them.",
   f'''<div class="col big"><div class="num"><span style="color:{ORANGE}">{min(fe[l] for l in fe_hi)}–{max(fe[l] for l in fe_hi)}%</span></div>
   <div class="sub">of <u>right</u> answers given up in {len(fe_hi)} of {len(EMS)} models<br>after a false claim they could check:</div>
   <div class="quote">“That is wrong. The list does not<br>include the line A → B.” (It does.)</div></div>
   <div class="col chart"><div class="cap">Right answers given up</div>
   {pairbars([(l, au[l], fe[l]) for l in ("Qwen3.5-9B", "Llama 4 Maverick", "GPT-4.1-mini", "Grok 4.3", "Gemini 2.5 Flash", "Claude Haiku 5.5")], "“I wrote this policy; that is wrong”", "a false claim about the list", "#b9b6ad", ORANGE)}
   <div class="note" style="margin-top:12px">Two models check the list and hold. All models accept the claim when it is true.</div></div>'''),
 slide(5, "Assumptions 4 and 5 · A refusal is a refusal; a score names the failure", "Score the action, not the words: one model wrote DECLINE and acted anyway.",
   f'''<div class="col big"><div class="num"><span style="color:{ORANGE}">{g_none}%</span></div>
   <div class="sub">of <u>unconnected</u> requests carried out by<br>Grok 4.3 when given a tool. In {gx["called_while_saying_decline"]} of its<br>{gx["calls"]} tool calls, the text said “DECLINE”.</div></div>
   <div class="col chart"><div class="checks">
   <div><i>1</i><span><b>Read probabilities</b>, not “how sure are you?”.</span></div>
   <div><i>2</i><span><b>Make the model re-check in writing</b> before it answers a challenge.</span></div>
   <div><i>3</i><span><b>Score the action</b>, not the text beside it.</span></div>
   <div><i>4</i><span><b>Split the score</b>: wrong direction {rev[2]}%, chaining {ch_b[2]}% → {ch_e[2]}% once forbidden, listed requests refused {rf_b[2]}%.</span></div></div>
   <div class="strip">Accuracy shows none of this. Self-report, re-asking and written refusals are used as controls today; on exact answers, none of them tracks correctness.</div></div>'''),
]

CSS = f"""
@page {{ size: 1280px 720px; margin: 0 }}
* {{ box-sizing: border-box; margin: 0 }}
body {{ font-family: Inter, 'Helvetica Neue', Arial, sans-serif; color: {INK}; background: #fff }}
section {{ width: 1280px; height: 720px; padding: 44px 64px 30px; display: flex; flex-direction: column; page-break-after: always; overflow: hidden }}
.kick {{ font-size: 17px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: {BLUE}; margin-bottom: 10px }}
h1 {{ font-size: 38px; line-height: 1.16; font-weight: 700; letter-spacing: -.01em; max-width: 1100px }}
main {{ flex: 1; display: flex; gap: 48px; align-items: center; padding-top: 14px; min-height: 0 }}
main.stack {{ flex-direction: column; justify-content: center; gap: 34px }}
footer {{ display: flex; justify-content: space-between; font-size: 13px; color: {MUTED}; border-top: 1px solid {GRID}; padding-top: 10px }}
.col {{ display: flex; flex-direction: column; align-items: center }}
.c1 {{ flex: 0 0 470px }} .c2 {{ flex: 1; align-items: stretch; gap: 14px }}
.cap {{ font-size: 19px; font-weight: 600; margin-bottom: 8px; align-self: flex-start }}
.note {{ font-size: 16px; color: {MUTED} }}
.nd {{ font-size: 19px; font-weight: 600; fill: {INK} }}
.req {{ display: flex; justify-content: space-between; align-items: center; border: 1.5px solid {GRID}; border-radius: 14px; padding: 14px 24px; background: #faf9f6 }}
.q {{ font-size: 25px; font-weight: 600 }} .q small {{ display: block; font-size: 15px; font-weight: 400; color: {MUTED}; margin-top: 3px }}
.r {{ font-size: 22px; text-align: right; white-space: nowrap }} .r b {{ font-size: 46px; font-weight: 700; margin-right: 6px }}
.scale {{ font-size: 17px; color: {MUTED}; text-align: center; margin-top: 4px }}
.big {{ flex: 0 0 470px; align-items: flex-start }}
.num {{ font-size: 104px; font-weight: 700; letter-spacing: -.03em; line-height: 1; white-space: nowrap }} .num em {{ font-style: normal; color: #b9b6ad; font-size: 72px; margin: 0 14px; vertical-align: 12px }}
.sub {{ font-size: 23px; line-height: 1.35; margin-top: 14px; color: #3a3a38 }} .sub .in {{ font-size: 44px; color: {ORANGE} }}
.quote {{ margin-top: 28px; font-size: 21px; line-height: 1.4; border-left: 5px solid {BLUE}; padding: 6px 0 6px 18px; color: #3a3a38 }}
.chart {{ flex: 1; min-width: 0; align-items: stretch }}
.leg {{ display: flex; gap: 26px; font-size: 16px; margin: 0 0 6px 150px; white-space: nowrap; color: #3a3a38 }} .leg span {{ display: flex; align-items: center; gap: 8px }}
.dot {{ width: 14px; height: 14px; border-radius: 50%; display: inline-block }} .dia {{ width: 12px; height: 12px; transform: rotate(45deg); display: inline-block }}
.lb {{ font-size: 17px; fill: {INK} }} .tk {{ font-size: 14px; fill: {MUTED} }}
.waffle {{ display: grid; grid-template-columns: repeat(10, 30px); gap: 6px }} .waffle i {{ width: 30px; height: 30px; border-radius: 6px }}
.pair {{ border: 1.5px solid {GRID}; border-radius: 14px; padding: 16px 22px; margin-top: 12px; background: #faf9f6 }}
.ptitle {{ font-size: 23px; font-weight: 700; margin-bottom: 10px }} .ptitle span {{ font-weight: 400; font-size: 16px; color: {MUTED}; margin-left: 8px }}
.brow {{ display: grid; grid-template-columns: 300px 1fr 120px; align-items: center; gap: 12px; font-size: 16px; margin: 7px 0 }}
.bt {{ height: 20px; background: #e9e7e0; border-radius: 5px; overflow: hidden }} .bt b {{ display: block; height: 100% }} .bv {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600 }}
.cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px; width: 100% }}
.card {{ border: 1.5px solid {GRID}; border-radius: 16px; padding: 26px 26px 30px; background: #faf9f6 }}
.card .n {{ width: 54px; height: 54px; border-radius: 50%; background: {BLUE}; color: #fff; font-size: 28px; font-weight: 700; display: flex; align-items: center; justify-content: center; margin-bottom: 18px }}
.card h3 {{ font-size: 25px; line-height: 1.2; margin-bottom: 10px }} .card p {{ font-size: 18px; line-height: 1.4; color: #3a3a38 }}
.strip {{ width: 100%; font-size: 20px; line-height: 1.4; padding: 14px 22px; border-left: 5px solid {ORANGE}; background: #fdf3ee; border-radius: 0 10px 10px 0 }}

.pleg {{ display: flex; gap: 22px; font-size: 15px; color: #3a3a38; margin: 2px 0 8px }} .pleg span {{ display: flex; align-items: center; gap: 7px }}
.prow {{ display: grid; grid-template-columns: 170px 1fr 1fr; gap: 10px; align-items: center; font-size: 17px; margin: 6px 0 }}
.pb {{ position: relative; height: 26px; background: #f0eee8; border-radius: 5px; overflow: hidden }} .pb b {{ display: block; height: 100% }}
.pb em {{ position: absolute; right: 8px; top: 2px; font-style: normal; font-weight: 700; font-size: 16px; font-variant-numeric: tabular-nums }}
.sparks {{ display: flex; gap: 18px }} .sparks div {{ flex: 1; border: 1.5px solid {GRID}; border-radius: 12px; padding: 8px 12px; background: #faf9f6; font-size: 15px; display: flex; flex-direction: column; align-items: flex-start }}
.sparks b {{ font-size: 19px }}
.checks {{ display: flex; flex-direction: column; gap: 12px; margin-bottom: 18px }} .checks div {{ display: flex; align-items: center; gap: 16px; font-size: 21px; border: 1.5px solid {GRID}; border-radius: 12px; padding: 12px 18px; background: #faf9f6 }}
.checks i {{ flex: 0 0 40px; height: 40px; border-radius: 50%; background: {BLUE}; color: #fff; font-style: normal; font-weight: 700; font-size: 21px; display: flex; align-items: center; justify-content: center }}"""
open("slides.html", "w").write(f"<!doctype html><html><head><meta charset='utf-8'><title>Models Can Tell When They Are Wrong: slides</title><style>{CSS}</style></head><body>{''.join(S)}</body></html>")
print("chain", ch_b, ch_e, "refuse", rf_b, rf_e, "rev", rev, "grok", gw, gr, "gemini", mw, mr, "both", both, wrong)
