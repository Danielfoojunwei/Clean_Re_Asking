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
            f'<footer><span>One Score, Three Failures · Daniel Foo Jun Wei · Apart Research AI x Epistemics Sprint</span><span>{n} / 5</span></footer></section>')

S = [
 slide(1, "The problem", "One accuracy score on permission rules hides three different failures.",
   f'''<div class="col c1"><div class="cap">The rulebook: who may send records to whom</div>{graph}<div class="note">Only listed directions are allowed.</div></div>
   <div class="col c2">
     <div class="req"><div class="q">Finance → Audit?<small>needs a chain · should be refused</small></div><div class="r"><b style="color:{ORANGE}">{ch_b[2]}%</b> allowed</div></div>
     <div class="req"><div class="q">Legal → Audit?<small>listed · should be allowed</small></div><div class="r"><b style="color:{ORANGE}">{rf_b[2]}%</b> refused</div></div>
     <div class="req"><div class="q">“How sure are you?”<small>right or wrong</small></div><div class="r"><b style="color:{ORANGE}">97%</b> say “100”</div></div>
     <div class="scale">9 AI models · 165,220 answers · plan fixed in advance</div></div>'''),
 slide(2, "Failure 1 · Chaining", "Models join rules into chains, and one sentence stops it.",
   f'''<div class="col big"><div class="num"><span style="color:{ORANGE}">{ch_b[2]}%</span><em>→</em><span style="color:{BLUE}">{ch_e[2]}%</span></div>
   <div class="sub">of chain requests wrongly allowed<br>(step-by-step answers)</div>
   <div class="quote">A → B and B → C<br>does <u>not</u> mean A → C</div></div>
   <div class="col chart">{LEG}{dumbbell("E5/base", "E5/explicit", "chain_release")}</div>'''),
 slide(3, "Failure 2 · Over-refusing", "The bigger mistake is refusing what is allowed, and a stricter rule makes it worse.",
   f'''<div class="col big"><div class="num"><span style="color:{ORANGE}">{rf_b[2]}%</span><em>→</em><span style="color:{BLUE}">{rf_e[2]}%</span></div>
   <div class="sub">of plainly allowed requests refused<br>(quick answers)</div>
   <div class="quote">The mistake everyone expects,<br>going the wrong way round: <b>{rev[2]}%</b></div></div>
   <div class="col chart">{LEG}{dumbbell("E1/base", "E1/explicit", "listed_refusal")}</div>'''),
 slide(4, "Failure 3 · No self-knowledge", "Models cannot tell when they are wrong.",
   f'''<div class="col big"><div class="waffle">{waffle}</div>
   <div class="sub"><b class="in">97%</b> of answers say “100% sure”,<br>right or wrong ({c100:,} of {ctot:,})</div></div>
   <div class="col chart"><div class="cap">Asked to double-check, a model either…</div>
   <div class="pair"><div class="ptitle">…rubber-stamps <span>Grok 4.3</span></div>
     {bar("wrong answers changed", gw[0], gw[1], ORANGE)}{bar("right answers changed", gr[0], gr[1], BLUE)}</div>
   <div class="pair"><div class="ptitle">…or flips a coin <span>Gemini 2.5 Flash</span></div>
     {bar("wrong answers changed", mw[0], mw[1], ORANGE)}{bar("right answers changed", mr[0], mr[1], BLUE)}</div></div>'''),
 slide(5, "What to do", "Three cheap checks before you trust, or explain, a score.",
   f'''<div class="cards">
   <div class="card"><div class="n">1</div><h3>Split the score</h3><p>Give every kind of mistake its own request, so a wrong answer has one explanation.</p></div>
   <div class="card"><div class="n">2</div><h3>Fix the wording, re-run</h3><p>Say “permissions do not combine”. Watch both wrong allows <i>and</i> wrong refusals.</p></div>
   <div class="card"><div class="n">3</div><h3>Don’t use confidence as a safety net</h3><p>Record it, but a model’s “100% sure” and its self-check do not flag errors.</p></div></div>
   <div class="strip"><b>{both:,} of {wrong:,}</b> wrong decisions came from a model that got every single step right. The failure is in putting the steps together.</div>''', "stack"),
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
.brow {{ display: grid; grid-template-columns: 200px 1fr 130px; align-items: center; gap: 12px; font-size: 16px; margin: 7px 0 }}
.bt {{ height: 20px; background: #e9e7e0; border-radius: 5px; overflow: hidden }} .bt b {{ display: block; height: 100% }} .bv {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600 }}
.cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px; width: 100% }}
.card {{ border: 1.5px solid {GRID}; border-radius: 16px; padding: 26px 26px 30px; background: #faf9f6 }}
.card .n {{ width: 54px; height: 54px; border-radius: 50%; background: {BLUE}; color: #fff; font-size: 28px; font-weight: 700; display: flex; align-items: center; justify-content: center; margin-bottom: 18px }}
.card h3 {{ font-size: 25px; line-height: 1.2; margin-bottom: 10px }} .card p {{ font-size: 18px; line-height: 1.4; color: #3a3a38 }}
.strip {{ width: 100%; font-size: 20px; line-height: 1.4; padding: 14px 22px; border-left: 5px solid {ORANGE}; background: #fdf3ee; border-radius: 0 10px 10px 0 }}
"""
open("slides.html", "w").write(f"<!doctype html><html><head><meta charset='utf-8'><title>One Score, Three Failures: slides</title><style>{CSS}</style></head><body>{''.join(S)}</body></html>")
print("chain", ch_b, ch_e, "refuse", rf_b, rf_e, "rev", rev, "grok", gw, gr, "gemini", mw, mr, "both", both, wrong)
