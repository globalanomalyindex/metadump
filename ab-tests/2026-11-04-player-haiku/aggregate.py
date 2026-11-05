#!/usr/bin/env python3
"""Unblind, join functional checks and cost, write results.json + results.md."""
import json, os, statistics as st
from itertools import combinations, product
ROOT = os.path.dirname(os.path.abspath(__file__))
ARMS = {"A": "prompt only", "C": "hand-made metadata file", "B": "metadump + fixed skill"}
CRIT = ["fidelity", "specificity", "target_fit", "pitfalls", "overall"]
key = json.load(open(os.path.join(ROOT, "key.json")))
func = json.load(open(os.path.join(ROOT, "functional.json"))) if os.path.exists(os.path.join(ROOT, "functional.json")) else {}
timing = {}
for line in open(os.path.join(ROOT, "timing.jsonl")):
    if line.strip():
        t = json.loads(line); timing[t["run"]] = t
rows = []
for f in sorted(os.listdir(os.path.join(ROOT, "judgments"))):
    j = json.load(open(os.path.join(ROOT, "judgments", f)))
    rank = {lab: i + 1 for i, lab in enumerate(j.get("ranking", []))}
    for lab, sc in j["scores"].items():
        run = key["%s/%s/%s" % (j["block"], j["judge"], lab)]
        rows.append(dict(block=j["block"], judge=j["judge"], run=run, arm=run[0], rank=rank.get(lab), note=sc.get("note", ""), **{c: float(sc[c]) for c in CRIT}))
mean = lambda xs: round(st.mean(xs), 2) if xs else None
res = {"scores": {}, "pairwise": {}, "functional": {}, "cost": {}}
for a in ARMS:
    ar = [r for r in rows if r["arm"] == a]
    res["scores"][a] = {c: mean([r[c] for r in ar]) for c in CRIT}
    res["scores"][a]["mean_rank"] = mean([r["rank"] for r in ar if r["rank"]])
    res["scores"][a]["n_scores"] = len(ar)
    per_run = {}
    for r in ar:
        per_run.setdefault(r["run"], []).append(r["overall"])
    res["scores"][a]["per_run_overall"] = {k: mean(v) for k, v in sorted(per_run.items())}
for x, y in [("B", "A"), ("B", "C"), ("C", "A")]:
    w = l = t = 0
    for b in {r["block"] for r in rows}:
        for jd in {r["judge"] for r in rows if r["block"] == b}:
            xs = [r["overall"] for r in rows if r["block"] == b and r["judge"] == jd and r["arm"] == x]
            ys = [r["overall"] for r in rows if r["block"] == b and r["judge"] == jd and r["arm"] == y]
            for a_, b_ in product(xs, ys):
                w += a_ > b_; l += a_ < b_; t += a_ == b_
    n = w + l + t
    res["pairwise"]["%s_vs_%s" % (x, y)] = {"wins": w, "losses": l, "ties": t, "win_rate": round((w + 0.5 * t) / n, 2) if n else None}
# judge agreement: mean pairwise Pearson across the 3 judges of each block
def pearson(a, b):
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b)); den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else None
rs = []
for b in {r["block"] for r in rows}:
    by = {}
    for r in rows:
        if r["block"] == b:
            by.setdefault(r["judge"], {})[r["run"]] = r["overall"]
    for j1, j2 in combinations(sorted(by), 2):
        runs = sorted(set(by[j1]) & set(by[j2]))
        p = pearson([by[j1][k] for k in runs], [by[j2][k] for k in runs])
        if p is not None:
            rs.append(p)
res["judge_agreement_mean_pearson"] = round(st.mean(rs), 2) if rs else None
for a in ARMS:
    fr = [v for k, v in func.items() if k.startswith(a)]
    res["functional"][a] = {k: "%d/%d" % (sum(bool(v[k]) for v in fr), len(fr)) for k in ["works", "play_button_found", "advances_while_playing", "next_changes_track", "stops_when_paused"]} if fr else {}
    res["functional"][a]["js_errors_total"] = sum(v["js_errors"] for v in fr)
    ts = [v for k, v in timing.items() if k.startswith(a)]
    res["cost"][a] = {"runs": len(ts), "mean_tokens": round(st.mean(t["tokens"] for t in ts)) if ts else None,
                      "mean_seconds": round(st.mean(t["ms"] for t in ts) / 1000, 1) if ts else None,
                      "mean_tool_uses": round(st.mean(t["tool_uses"] for t in ts), 1) if ts else None}
res["notes"] = {"%s/%s/%s" % (r["block"], r["judge"], r["run"]): r["note"] for r in rows}
json.dump(res, open(os.path.join(ROOT, "results.json"), "w"), indent=1)
L = ["# A/B test 2 results: mini music player, Haiku builders and graders", "", "Arms: " + "; ".join("**%s** = %s" % kv for kv in ARMS.items()), "",
     "## Blind grader scores (0-10; 4 runs per arm x 3 graders = 12 scores per arm)", "",
     "| arm | overall | fidelity | specificity | target fit | pitfalls avoided | mean rank (1-6) | overall per run |", "|---|---|---|---|---|---|---|---|"]
for a in ["A", "C", "B"]:
    s = res["scores"][a]
    L.append("| %s | **%s** | %s | %s | %s | %s | %s | %s |" % (a, s["overall"], s["fidelity"], s["specificity"], s["target_fit"], s["pitfalls"], s["mean_rank"], ", ".join("%s" % v for v in s["per_run_overall"].values())))
L += ["", "## Head to head (same grader, overall score)", ""] + ["- **%s**: %s wins, %s losses, %s ties (win rate %s)" % (k.replace("_", " "), v["wins"], v["losses"], v["ties"], v["win_rate"]) for k, v in res["pairwise"].items()]
L += ["", "Grader agreement: mean pairwise Pearson r = %s." % res["judge_agreement_mean_pearson"], "",
      "## Does it actually work? (headless Chrome clicks play, waits, clicks next, pauses)", "", "| arm | works | play found | advances while playing | next changes track | stops when paused | JS errors |", "|---|---|---|---|---|---|---|"]
for a in ["A", "C", "B"]:
    f = res["functional"][a]
    if f.get("works"):
        L.append("| %s | **%s** | %s | %s | %s | %s | %s |" % (a, f["works"], f["play_button_found"], f["advances_while_playing"], f["next_changes_track"], f["stops_when_paused"], f["js_errors_total"]))
L += ["", "## Cost per run (Haiku, medium effort)", "", "| arm | runs | mean tokens | mean seconds | mean tool calls |", "|---|---|---|---|---|"]
for a in ["A", "C", "B"]:
    c = res["cost"][a]
    L.append("| %s | %s | %s | %s | %s |" % (a, c["runs"], c["mean_tokens"], c["mean_seconds"], c["mean_tool_uses"]))
open(os.path.join(ROOT, "results.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
