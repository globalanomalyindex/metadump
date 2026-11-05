#!/usr/bin/env python3
"""Unblind, join functional checks and cost, write results.json + results.md."""
import json, os, statistics as st
from itertools import combinations, product
ROOT = os.path.dirname(os.path.abspath(__file__))
ARMS = {"A": "task only", "B": "task + metadump 0.5.0 (lite)"}
CRIT = ["compact", "minimal", "modern", "usability", "craft", "overall"]
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
        rows.append(dict(block=j["block"], judge=j["judge"], run=run, arm=run[0], rank=rank.get(lab), note=sc.get("note", ""),
                         **{c: float(sc[c]) for c in CRIT}))
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
w = l = t = 0
for b in {r["block"] for r in rows}:
    for jd in {r["judge"] for r in rows if r["block"] == b}:
        xs = [r["overall"] for r in rows if r["block"] == b and r["judge"] == jd and r["arm"] == "B"]
        ys = [r["overall"] for r in rows if r["block"] == b and r["judge"] == jd and r["arm"] == "A"]
        for a_, b_ in product(xs, ys):
            w += a_ > b_; l += a_ < b_; t += a_ == b_
n = w + l + t
res["pairwise"]["B_vs_A"] = {"wins": w, "losses": l, "ties": t, "win_rate": round((w + 0.5 * t) / n, 2) if n else None}
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
FK = ["works", "action_found", "action_changes_state", "qty_found", "qty_changes_number", "mobile_no_overflow"]
for a in ARMS:
    fr = [v for k, v in func.items() if k.startswith(a)]
    res["functional"][a] = {k: "%d/%d" % (sum(bool(v[k]) for v in fr), len(fr)) for k in FK} if fr else {}
    if fr:
        res["functional"][a]["js_errors_total"] = sum(v["js_errors"] for v in fr)
        res["functional"][a]["unnamed_buttons_total"] = sum(v["unnamed_buttons"] for v in fr)
    ts = [v for k, v in timing.items() if k.startswith(a + "-")]
    res["cost"][a] = {"runs": len(ts), "mean_tokens": round(st.mean(t["tokens"] for t in ts)) if ts else None,
                      "mean_seconds": round(st.mean(t["ms"] for t in ts) / 1000, 1) if ts else None,
                      "mean_tool_uses": round(st.mean(t["tool_uses"] for t in ts), 1) if ts else None}
if "dump" in timing:
    res["cost"]["dump_build"] = timing["dump"]
res["notes"] = {"%s/%s/%s" % (r["block"], r["judge"], r["run"]): r["note"] for r in rows}
json.dump(res, open(os.path.join(ROOT, "results.json"), "w"), indent=1)
L = ["# A/B test 5 results: the shopping test from scratch on metadump 0.5.0, Haiku everything", "", "Arms: " + "; ".join("**%s** = %s" % kv for kv in ARMS.items()), "",
     "## Blind grader scores (0-10; 4 runs per arm x 3 graders = 12 scores per arm)", "",
     "| arm | overall | compact | minimal | modern | usability | craft | mean rank (1-4) | overall per run |", "|---|---|---|---|---|---|---|---|---|"]
for a in ARMS:
    s = res["scores"][a]
    L.append("| %s | **%s** | %s | %s | %s | %s | %s | %s | %s |" % (a, s["overall"], s["compact"], s["minimal"], s["modern"], s["usability"], s["craft"], s["mean_rank"],
                                                                 ", ".join("%s" % v for v in s["per_run_overall"].values())))
p = res["pairwise"]["B_vs_A"]
L += ["", "## Head to head (same grader, same block, overall)", "", "- **B vs A**: %s wins, %s losses, %s ties (win rate %s)" % (p["wins"], p["losses"], p["ties"], p["win_rate"]),
      "", "Grader agreement: mean pairwise Pearson r = %s." % res["judge_agreement_mean_pearson"], "",
      "## Does it work? (headless Chrome: click the main shopping action, click +, check 390 px)", "",
      "| arm | works | action found | action changes page | qty control | qty changes | no overflow at 390 px | JS errors | unnamed buttons |", "|---|---|---|---|---|---|---|---|---|"]
for a in ARMS:
    f = res["functional"][a]
    if f:
        L.append("| %s | **%s** | %s | %s | %s | %s | %s | %s | %s |" % (a, f["works"], f["action_found"], f["action_changes_state"], f["qty_found"], f["qty_changes_number"], f["mobile_no_overflow"], f["js_errors_total"], f["unnamed_buttons_total"]))
L += ["", "## Cost per build run (Haiku)", "", "| arm | runs | mean tokens | mean seconds | mean tool calls |", "|---|---|---|---|---|"]
for a in ARMS:
    c = res["cost"][a]
    L.append("| %s | %s | %s | %s | %s |" % (a, c["runs"], c["mean_tokens"], c["mean_seconds"], c["mean_tool_uses"]))
if "dump_build" in res["cost"]:
    d = res["cost"]["dump_build"]
    L += ["", "Dump build (one-off, Haiku main loop and workers): %s tokens reported for the main loop, %s s." % (d["tokens"], round(d["ms"] / 1000))]
open(os.path.join(ROOT, "results.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
