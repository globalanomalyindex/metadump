#!/usr/bin/env python3
"""Unblind judgments, join objective metrics and cost, write results.json and results.md."""
import json, os, statistics as st
from itertools import product

ROOT = os.path.dirname(os.path.abspath(__file__))
ARMS = {"A": "prompt only", "C": "hand-made metadata file", "B": "metadump + skill"}
CRIT = ["fidelity", "specificity", "target_fit", "pitfalls", "overall"]
key = json.load(open(os.path.join(ROOT, "key.json")))
metrics = json.load(open(os.path.join(ROOT, "metrics.json"))) if os.path.exists(os.path.join(ROOT, "metrics.json")) else {}
timing = {}
for line in open(os.path.join(ROOT, "timing.jsonl")):
    if line.strip():
        t = json.loads(line); timing[t["run"]] = t

rows = []  # one per (task, judge, output)
for f in sorted(os.listdir(os.path.join(ROOT, "judgments"))):
    j = json.load(open(os.path.join(ROOT, "judgments", f)))
    rank = {lab: i + 1 for i, lab in enumerate(j.get("ranking", []))}
    for lab, sc in j["scores"].items():
        run = key["%s/%s/%s" % (j["task"], j["judge"], lab)]
        rows.append(dict(task=j["task"], judge=j["judge"], run=run, arm=run[0],
                         rank=rank.get(lab), note=sc.get("note", ""), **{c: sc[c] for c in CRIT}))

def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), 2) if xs else None

tasks = sorted({r["task"] for r in rows})
res = {"by_task": {}, "overall": {}, "pairwise": {}, "cost": {}}
for t in tasks + ["ALL"]:
    sel = [r for r in rows if t == "ALL" or r["task"] == t]
    block = {}
    for a in ARMS:
        ar = [r for r in sel if r["arm"] == a]
        block[a] = {c: mean([r[c] for r in ar]) for c in CRIT}
        block[a]["mean_rank"] = mean([r["rank"] for r in ar])
        block[a]["n"] = len(ar)
    (res["overall"] if t == "ALL" else res["by_task"])[t if t != "ALL" else "all"] = block
# pairwise: within each (task, judge), compare every output of arm X with every output of arm Y on overall
for x, y in [("B", "A"), ("B", "C"), ("C", "A")]:
    w = l = ti = 0
    for t in tasks:
        for jd in {r["judge"] for r in rows if r["task"] == t}:
            xs = [r["overall"] for r in rows if r["task"] == t and r["judge"] == jd and r["arm"] == x]
            ys = [r["overall"] for r in rows if r["task"] == t and r["judge"] == jd and r["arm"] == y]
            for a, b in product(xs, ys):
                w += a > b; l += a < b; ti += a == b
    n = w + l + ti
    res["pairwise"]["%s_vs_%s" % (x, y)] = {"wins": w, "losses": l, "ties": ti, "win_rate": round((w + 0.5 * ti) / n, 2) if n else None}
# judge agreement: correlation of overall scores between j1 and j2 per run
pairs = {}
for r in rows:
    pairs.setdefault((r["task"], r["run"]), {})[r["judge"]] = r["overall"]
both = [(v["j1"], v["j2"]) for v in pairs.values() if "j1" in v and "j2" in v]
if len(both) > 2:
    a, b = zip(*both)
    ma, mb = st.mean(a), st.mean(b)
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    res["judge_agreement_pearson"] = round(cov / den, 2) if den else None
    res["judge_mean_abs_diff"] = round(st.mean(abs(x - y) for x, y in both), 2)
for a in ARMS:
    ts = [v for k, v in timing.items() if k.split("/")[1].startswith(a)]
    res["cost"][a] = {"runs": len(ts), "mean_tokens": round(st.mean(t["tokens"] for t in ts)) if ts else None,
                      "mean_seconds": round(st.mean(t["ms"] for t in ts) / 1000, 1) if ts else None,
                      "mean_tool_uses": round(st.mean(t["tool_uses"] for t in ts), 1) if ts else None}
res["metrics_by_arm"] = {}
for t in tasks:
    for a in ARMS:
        ms = [v for k, v in metrics.items() if k.startswith(t + "/" + a)]
        if ms:
            res["metrics_by_arm"]["%s/%s" % (t, a)] = {k: (mean([m[k] for m in ms]) if isinstance(ms[0][k], (int, float)) and not isinstance(ms[0][k], bool) else [m[k] for m in ms]) for k in ms[0] if k != "clauses_missing"}
res["notes"] = {r["task"] + "/" + r["judge"] + "/" + r["run"]: r["note"] for r in rows}
json.dump(res, open(os.path.join(ROOT, "results.json"), "w"), indent=1)

# markdown
L = ["# A/B results: luminous chromatic translucency", "", "Arms: " + "; ".join("**%s** = %s" % (k, v) for k, v in ARMS.items()), ""]
L += ["## Blind judge scores (0-10, mean of 2 judges x 2 runs per cell)", "", "| task | arm | overall | fidelity | specificity | target fit | pitfalls avoided | mean rank (1-6) |", "|---|---|---|---|---|---|---|---|"]
for t in tasks + ["all"]:
    blk = res["overall"]["all"] if t == "all" else res["by_task"][t]
    for a in ["A", "C", "B"]:
        b = blk[a]
        L.append("| %s | %s | **%s** | %s | %s | %s | %s | %s |" % (t, a, b["overall"], b["fidelity"], b["specificity"], b["target_fit"], b["pitfalls"], b["mean_rank"]))
L += ["", "## Head to head (every output vs every output, same judge, overall score)", ""]
for k, v in res["pairwise"].items():
    L.append("- **%s**: %s wins, %s losses, %s ties (win rate %s)" % (k.replace("_", " "), v["wins"], v["losses"], v["ties"], v["win_rate"]))
if "judge_agreement_pearson" in res:
    L += ["", "Judge agreement: Pearson r = %s, mean |j1 - j2| = %s points." % (res["judge_agreement_pearson"], res["judge_mean_abs_diff"])]
L += ["", "## Cost per run (subagent tokens, includes ~74K of system prompt every run)", "", "| arm | runs | mean tokens | mean seconds | mean tool calls |", "|---|---|---|---|---|"]
for a in ["A", "C", "B"]:
    c = res["cost"][a]
    L.append("| %s | %s | %s | %s | %s |" % (a, c["runs"], c["mean_tokens"], c["mean_seconds"], c["mean_tool_uses"]))
L += ["", "## Objective metrics (means per arm)", "", "```", json.dumps(res["metrics_by_arm"], indent=1), "```"]
open(os.path.join(ROOT, "results.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L[:40]))
