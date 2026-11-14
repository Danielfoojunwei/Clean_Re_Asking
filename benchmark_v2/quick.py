import json,collections,sys,glob,os
CE=["BOTH","FWD","REV","REV_PATH","NEI_PATH","NEI_NOPATH"]
out={}
for f in sorted(glob.glob("runs_main/*/responses.jsonl")):
    m=os.path.basename(os.path.dirname(f)).replace("__","/")
    ok={}
    for l in open(f):
        r=json.loads(l)
        if r["status"]=="ok" and r["round"]>=1: ok[r["id"]]=r
    rounds=sorted({r["round"] for r in ok.values()})
    t=collections.Counter(); mal=collections.Counter(); n=collections.Counter()
    for r in ok.values():
        if r["exp"] in("E1","E4","E4p","E5"):
            k=(r["exp"],r["clause"],r["cell"]); n[k]+=1
            if r["answer"] is None: mal[(r["exp"],r["clause"])]+=1
            elif r["answer"]!=r["gold"]: t[k]+=1
    out[m]=(rounds,t,n,mal,ok)
for e in ("E1","E5","E4","E4p"):
    for cl in ("base","explicit"):
        print(f"\n== {e} / clause={cl}: wrong/n per cell (BOTH,FWD = wrong refusals; others = wrong releases); malformed")
        for m,(rounds,t,n,mal,ok) in out.items():
            print(f"{m:32s} r{rounds[0]}-{rounds[-1]}({len(rounds)}) "+"  ".join(f"{c}:{t[(e,cl,c)]}/{n[(e,cl,c)]}" for c in CE)+f"  mal:{mal[(e,cl)]}")
print("\n== components: E6 roles, E7 lookup (wrong/n), E0")
for m,(rounds,t,n,mal,ok) in out.items():
    e6=[r for r in ok.values() if r["exp"]=="E6"]; e7=[r for r in ok.values() if r["exp"]=="E7"]
    print(f"{m:32s} E6 wrong {sum(r['answer']!=r['gold'] for r in e6)}/{len(e6)}  E7 wrong {sum(r['answer']!=r['gold'] for r in e7)}/{len(e7)}  E7 by cell "+" ".join(f"{c}:{sum(r['answer']!=r['gold'] for r in e7 if r['cell']==c)}" for c in CE))
