#!/usr/bin/env python3
"""Unblind every task, join click tests and cost, and write <task>/results.json plus one results.md for the whole test.
Usage: python3 aggregate.py"""
import itertools, json, os, statistics as st
from itertools import combinations, product

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = {
    "t1-button": ("a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website",
                  ["dreamlike", "practical", "motion", "craft", "overall"]),
    "t2-sandbox": ("a 2D physics sandbox where you can drag boxes around", ["physics", "interaction", "stability", "clarity", "craft", "overall"]),
    "t3-poem": ("a short poem about rare clouds, ending with a question", ["imagery", "specificity", "question", "freshness", "resonance", "overall"]),
    "t4-figma": ("a 5 second looping animation in the style of Figma brand visuals", ["style", "motion", "loop", "craft", "originality", "overall"]),
}
mean = lambda xs: round(st.mean(xs), 2) if xs else None


def pearson(a, b):
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b)); den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else None


def permutation_p(a, b):
    allv = a + b; obs = st.mean(b) - st.mean(a); n = ext = 0
    for idx in itertools.combinations(range(len(allv)), len(b)):
        bb = [allv[i] for i in idx]; aa = [allv[i] for i in range(len(allv)) if i not in idx]
        n += 1; ext += abs(st.mean(bb) - st.mean(aa)) >= abs(obs) - 1e-9
    return round(ext / n, 3), ext, n


def task_results(task, crit):
    d = os.path.join(HERE, task)
    key = json.load(open(os.path.join(d, "key.json")))
    func = json.load(open(os.path.join(d, "functional.json"))) if os.path.exists(os.path.join(d, "functional.json")) else {}
    timing = {}
    if os.path.exists(os.path.join(d, "timing.jsonl")):
        for line in open(os.path.join(d, "timing.jsonl")):
            if line.strip():
                t = json.loads(line); timing[t["run"]] = t
    rows = []
    for f in sorted(os.listdir(os.path.join(d, "judgments"))):
        j = json.load(open(os.path.join(d, "judgments", f)))
        rank = {lab: i + 1 for i, lab in enumerate(j.get("ranking", []))}
        for lab, sc in j["scores"].items():
            run = key["%s/%s/%s" % (j["block"], j["judge"], lab)]
            rows.append(dict(block=j["block"], judge=j["judge"], run=run, arm=run[0], rank=rank.get(lab), note=sc.get("note", ""),
                             **{c: float(sc[c]) for c in crit}))
    res = {"scores": {}, "pairwise": {}, "functional": func, "cost": {}}
    for a in "AB":
        ar = [r for r in rows if r["arm"] == a]
        res["scores"][a] = {c: mean([r[c] for r in ar]) for c in crit}
        res["scores"][a]["mean_rank"] = mean([r["rank"] for r in ar if r["rank"]])
        per = {}
        for r in ar:
            per.setdefault(r["run"], []).append(r["overall"])
        res["scores"][a]["per_run_overall"] = {k: mean(v) for k, v in sorted(per.items())}
        ts = [v for k, v in timing.items() if k.startswith(a + "-")]
        res["cost"][a] = {"runs": len(ts), "mean_tokens": round(st.mean(t["tokens"] for t in ts)) if ts else None,
                          "mean_seconds": round(st.mean(t["ms"] for t in ts if not t.get("exclude_from_time_mean")) / 1000, 1) if ts else None}
    if "dump" in timing:
        res["cost"]["dump"] = timing["dump"]
    w = l = t = 0
    for b in {r["block"] for r in rows}:
        for jd in {r["judge"] for r in rows if r["block"] == b}:
            xs = [r["overall"] for r in rows if r["block"] == b and r["judge"] == jd and r["arm"] == "B"]
            ys = [r["overall"] for r in rows if r["block"] == b and r["judge"] == jd and r["arm"] == "A"]
            for x, y in product(xs, ys):
                w += x > y; l += x < y; t += x == y
    n = w + l + t
    res["pairwise"] = {"wins": w, "losses": l, "ties": t, "win_rate": round((w + 0.5 * t) / n, 2) if n else None}
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
    res["agreement_r"] = round(st.mean(rs), 2) if rs else None
    a_runs = list(res["scores"]["A"]["per_run_overall"].values()); b_runs = list(res["scores"]["B"]["per_run_overall"].values())
    res["permutation"] = dict(zip(("p", "extreme", "of"), permutation_p(a_runs, b_runs))) if a_runs and b_runs else None
    res["notes"] = {"%s/%s/%s" % (r["block"], r["judge"], r["run"]): r["note"] for r in rows}
    json.dump(res, open(os.path.join(d, "results.json"), "w"), indent=1, ensure_ascii=False)
    return res, rows


def main():
    L = ["# A/B test 11 results: four example tasks, Haiku 5.5 at low effort for everything, metadump 0.7.1", "",
         "Arms: **A** = task only; **B** = task + a lite meta dump (0.7.1). Builders, dump agents and graders: Haiku 5.5 at low effort. Graders blind, 3 per block of 4.", ""]
    summary = []
    for task, (prompt, crit) in TASKS.items():
        jd = os.path.join(HERE, task, "judgments")
        if not os.path.exists(os.path.join(HERE, task, "key.json")) or not os.path.isdir(jd) or not os.listdir(jd):
            continue
        res, rows = task_results(task, crit)
        sa, sb, p = res["scores"]["A"], res["scores"]["B"], res["pairwise"]
        summary.append((task, sa["overall"], sb["overall"], p["win_rate"], res["permutation"]["p"] if res["permutation"] else None))
        L += ["## %s" % task, "", "Prompt: %s" % prompt, "",
              "| arm | " + " | ".join(crit) + " | per-run overall |", "|---|" + "---|" * (len(crit) + 1)]
        for a, s in (("A", sa), ("B", sb)):
            L.append("| %s | %s | %s |" % (a, " | ".join(("**%s**" % s[c]) if c == "overall" else str(s[c]) for c in crit),
                                          ", ".join(str(v) for v in s["per_run_overall"].values())))
        L += ["", "B vs A head to head: %s wins, %s losses, %s ties (win rate %s). Grader agreement r = %s. Permutation test on run means: p = %s." % (
            p["wins"], p["losses"], p["ties"], p["win_rate"], res["agreement_r"], res["permutation"]["p"] if res["permutation"] else "n/a"), ""]
        c = res["cost"]
        L.append("Builder cost: A %s tokens, %s s; B %s tokens, %s s per run." % (c["A"]["mean_tokens"], c["A"]["mean_seconds"], c["B"]["mean_tokens"], c["B"]["mean_seconds"]) +
                 (" Dump: %s tokens reported for the main loop, %s s." % (c["dump"]["tokens"], round(c["dump"]["ms"] / 1000)) if "dump" in c else ""))
        L.append("")
    if summary:
        L[4:4] = ["## Summary", "", "| task | A overall | B overall | B vs A win rate | p |", "|---|---|---|---|---|"] + \
                 ["| %s | %s | %s | %s | %s |" % (t, ("**%s**" % a) if a > b else a, ("**%s**" % b) if b > a else b, w, pp) for t, a, b, w, pp in summary] + [""]
    wu = os.path.join(HERE, "writeup.md")   # the hand-written part, kept across re-runs
    if os.path.exists(wu):
        L += [open(wu).read().rstrip()]
    open(os.path.join(HERE, "results.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
