"""Prints every Study L number quoted in the paper, slides and script, from results_l_<model>.json and runs/.
Run after analyze_l.py:  python3 paper_numbers.py  (writes paper_numbers.json next to this file)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results_l_ministral8b.json"))
P = json.load(open(HERE / "runs" / "ministral8b" / "probe_results.json"))
load = lambda p: [json.loads(l) for l in open(p)]
pc = lambda e: round(100 * e["v"])
ci = lambda e: [round(100 * e["ci"][0]), round(100 * e["ci"][1])]
N = {}

# gate and fidelity
b3 = load(HERE / "runs" / "ministral3b" / "bare.jsonl")
N["bare_3b"] = {"correct": sum(r["answer"] == r["gold"] for r in b3), "n": len(b3)}
N["bare_8b"] = {"correct": round(R["bare"]["acc"]["v"] * R["bare"]["n"]), "n": R["bare"]["n"], "p_median": round(R["bare"]["p_gold_median"], 3)}
c = R["gate"]["cells"]
N["gate_F"] = {k: pc(v["F"]) for k, v in c.items()}
N["gate_H"] = {k: pc(v["H"]) for k, v in c.items()}
N["gate_gap"] = {"assertion": [pc(R["gate"]["gap_assertion"]), ci(R["gate"]["gap_assertion"])], "directive": [pc(R["gate"]["gap_directive"]), ci(R["gate"]["gap_directive"])]}
N["fidelity"] = {"agree_pct": round(100 * R["fidelity"]["agree"], 1), "n": R["fidelity"]["n"],
                 "named": {k: [pc(v["F_local"]), pc(v["F_api"])] for k, v in R["fidelity"]["cells"].items() if k.endswith("/named")}}

# wordings
w = R["wordings"]
N["wordings_sets_F"] = {s: [pc(v["F"]), ci(v["F"])] for s, v in w["per_set"].items()}
N["wordings_sets_H_min"] = min(pc(v["H"]) for v in w["per_set"].values())
N["wordings_label_F"] = {k: pc(v["F"]) for k, v in w["per_label"].items()}
for k in ("label_within_statement", "label_within_question", "form_within_keep", "form_within_replace", "label_minus_form"):
    N["wordings_" + k] = [pc(w[k]), ci(w[k])]
N["wordings_auc"] = {"label": round(w["auc_label"], 2), "form": round(w["auc_form"], 2)}
ph = w["posthoc_pushed_yes"]
N["clean_half_sets_F"] = {s: pc(v) for s, v in ph["per_set"].items()}
for k in ("label_within_statement", "label_within_question", "form_within_keep", "form_within_replace", "label_minus_form"):
    N["clean_half_" + k] = [pc(ph[k]), ci(ph[k])]
N["n_wording_runs"] = w["n"]
N["per_wording_F"] = {k: pc(v["F"]) for k, v in w["per_wording"].items()}
N["qrfree_F"] = {k: [pc(v["F"]), ci(v["F"])] for k, v in R["qrfree"].items()}

# patching
pt = R["patch"]
N["patch"] = {k: {"n": v["n"], "handover": v["handover_block"], "rebuttal_ge80_until": v["rebuttal_last_block_over_80"], "rebuttal_lt20_from": v["rebuttal_first_block_under_20"],
                  "final_ge80_from": v["final_first_block_over_80"], "final_lt20_until": v["final_last_block_under_20"],
                  "rebuttal_restored_b16": round(100 * v["rebuttal"]["restored"][16]["v"]), "final_restored_b22": round(100 * v["final"]["restored"][22]["v"]),
                  "tail_restored_max": round(100 * max(e["v"] for e in v["tail"]["restored"])),
                  "tell_correct_clean": round(100 * v["final"]["correct_after_ask_into_tell"][0]),
                  "tell_correct_after_rebuttal_patch_b16": round(100 * v["rebuttal"]["correct_after_ask_into_tell"][16]),
                  "tell_correct_after_final_patch_b24": round(100 * v["final"]["correct_after_ask_into_tell"][24])} for k, v in pt.items()}

# probe and lens (index i = after block i-1)
blk = lambda arr, b: round(100 * arr[b + 1])
N["probe_bare"] = {"b15": blk(P["bare_acc"], 15), "b17": blk(P["bare_acc"], 17), "min_from_b18": min(round(100 * x) for x in P["bare_acc"][19:])}
N["probe_shuffled_range"] = [min(round(100 * x) for x in P["shuffled_acc"][1:]), max(round(100 * x) for x in P["shuffled_acc"][1:])]
g = P["groups"]
rng = lambda k, a, b: [min(round(100 * x) for x in g[k]["acc"][a + 1:b + 2]), max(round(100 * x) for x in g[k]["acc"][a + 1:b + 2])]
N["probe_ask_kept_from_b19"] = rng("Q0/dis/user_wrong/kept", 19, 33)
for w_, name in (("D0", "directive"), ("A0", "assertion")):
    k = f"{w_}/dis/user_wrong/flipped"
    N[f"probe_flipped_{name}"] = {"n": g[k]["n"], "b17": blk(g[k]["acc"], 17), "b19": blk(g[k]["acc"], 19), "b20_27": rng(k, 20, 27), "b28_33": rng(k, 28, 33)}
N["probe_user_right_from_b19"] = [min(rng(f"{w_}/dis/user_right/flipped", 19, 33)[0] for w_ in ("Q0", "A0", "D0")), 100]
L = R["lens"]
first = lambda arr, t: next(i - 1 for i, x in enumerate(arr) if abs(x) >= t)
N["lens"] = {k: {"first_half_logit": first(L[f"diff_{k}/dis"]["mean"], .5), "b28_33": [round(min(L[f"diff_{k}/dis"]["mean"][29:]), 1), round(max(L[f"diff_{k}/dis"]["mean"][29:]), 1)]} for k in ("assert", "direct")}
e = R["answer_entropy"]
N["answer_p_correct"] = {"bare": round(e["bare"]["p_gold_median"], 3), "ask_kept": round(e["Q0/kept"]["p_gold_median"], 3),
                         "assert_flipped": round(e["A0/flipped"]["p_gold_median"], 2), "direct_flipped": round(e["D0/flipped"]["p_gold_median"], 2)}

# knockout
kn = R["knock"]
d = lambda k, gname: [pc(kn[k][gname]["delta_correct"]), ci(kn[k][gname]["delta_correct"])]
N["knock"] = {"ask_hide_list_user_right": d("Q0/user_right", "list"), "ask_hide_question_user_right": d("Q0/user_right", "question"),
              "assert_hide_prior": d("A0/user_wrong", "prior_answer"), "direct_hide_prior": d("D0/user_wrong", "prior_answer"),
              "assert_correct": {gname: pc(kn["A0/user_wrong"][gname]["correct"]) for gname in kn["A0/user_wrong"]},
              "direct_correct": {gname: pc(kn["D0/user_wrong"][gname]["correct"]) for gname in kn["D0/user_wrong"]},
              "n": kn["Q0/user_wrong"]["none"]["correct"]["n"]}

# semantic entropy, free-form
se = R["semantic_entropy"]
N["free_F"] = {w_: pc(se[f"{w_}/user_wrong"]["share_changed"]) for w_ in ("Q0", "A0", "D0")}
N["sem_entropy"] = {w_: round(se[f"{w_}/user_wrong"]["sem_entropy"]["v"], 2) for w_ in ("Q0", "A0", "D0")}
N["sem_entropy_tell_minus_ask"] = {k: [round(se[k]["v"], 2), [round(x, 2) for x in se[k]["ci"]]] for k in ("tell_minus_ask_A0", "tell_minus_ask_D0")}

# steering
st = R["steer"]["steer_L22"]; sg = R["steer_by_gold"]["steer_L22"]
N["steer_F"] = {w_: {a: pc(st[f"{w_}/user_wrong"][a]["changed"]) for a in ("0.0", "1.0", "4.0")} for w_ in ("Q0", "A0", "D0")}
N["steer_by_gold_a4"] = {k: pc(v["4.0"]["correct"]) for k, v in sg.items()}
N["steer_by_gold_a0"] = {k: pc(v["0.0"]["correct"]) for k, v in sg.items()}

# symmetry
sy = R["symmetry"]
N["assert_pushed"] = {a: pc(sy["A"]["by_pushed"][a]) for a in ("YES", "NO")}

# size of the local study: scored answers (first-token answers), excluding the patching read-outs
runs = HERE / "runs"
cnt = (len(b3) + R["bare"]["n"] + len(load(runs / "ministral8b" / "gate.jsonl")) + len(load(runs / "ministral8b" / "gencheck.jsonl"))
       + len(load(runs / "ministral8b" / "fidelity.jsonl")) + w["n"] + len(load(runs / "ministral8b" / "acts_index.jsonl"))
       + 5 * len(load(runs / "ministral8b" / "knock.jsonl")) + 8 * len(load(runs / "ministral8b" / "entropy.jsonl"))
       + len(load(runs / "ministral8b" / "qrfree.jsonl")) + 6 * len(load(runs / "ministral8b" / "steer_L22.jsonl")))
N["local_scored_answers"] = cnt
N["patch_readouts"] = sum(2 + 6 * len(r["ask_into_tell"]["final"]) for r in load(runs / "ministral8b" / "patch.jsonl"))
json.dump(N, open(HERE / "paper_numbers.json", "w"), indent=1)
for k, v in N.items():
    print(k, v)
