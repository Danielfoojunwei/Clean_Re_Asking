"""Follow-up items. Reuses the frozen generator (gen.py) unchanged and only swaps the extra sentence added to the rule."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v2"))
import gen  # noqa: E402

CLAUSES = {  # condition -> sentence appended to the rule's introduction, per naming style
    "exact": {"opaque": " A route counts only if that exact line is in the table.",
              "natural": " A transfer is allowed only if that exact line is listed."},
    "nochain": {"opaque": " Routes cannot be chained.", "natural": " Transfers cannot be chained through another department."},
    "norev": {"opaque": " Routes cannot be reversed.", "natural": " Transfers cannot be reversed."},
    "placebo": {"opaque": " The table was last reviewed this quarter and applies to every team in the company.",
                "natural": " The list was last reviewed this quarter and applies to every team in the company."},
    "balanced": {"opaque": gen.SURF["opaque"]["clause"] + " If the exact line is in the table, the export is authorized.",
                 "natural": gen.SURF["natural"]["clause"] + " If the exact line is listed, the transfer is allowed."},
}
FROZEN = ("base", "explicit")


def items(rnd, cond, exps=("E1",)):
    """Items for one round under one condition. base/explicit are the frozen prompts, byte-identical to the main study."""
    if cond in FROZEN:
        return [i for i in gen.items(rnd) if i["exp"] in exps and i.get("clause") == cond]
    saved = copy.deepcopy(gen.SURF)
    try:
        for sf in gen.SURF:
            gen.SURF[sf]["clause"] = CLAUSES[cond][sf]
        out = [dict(i) for i in gen.items(rnd) if i["exp"] in exps and i.get("clause") == "explicit"]
    finally:
        gen.SURF.clear(); gen.SURF.update(saved)
    for i in out:
        i["clause"] = cond
        i["id"] = i["id"].replace("/explicit/", f"/{cond}/")
    return out


if __name__ == "__main__":
    ref = {i["id"]: i for i in gen.items(1)}
    for c in list(CLAUSES) + list(FROZEN):
        its = items(1, c, ("E1", "E5"))
        assert len(its) == 320 and len({i["id"] for i in its}) == 320, (c, len(its))
        if c in FROZEN:
            assert all(ref[i["id"]]["messages"] == i["messages"] for i in its)
    assert gen.items(1) == list(ref.values()), "frozen generator must be unchanged after use"
    print(items(1, "balanced")[0]["messages"][1]["content"]); print("ok")
