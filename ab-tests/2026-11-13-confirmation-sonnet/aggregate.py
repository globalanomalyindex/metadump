#!/usr/bin/env python3
"""Unblind every task, join the functional checks and cost, and write <task>/results.json plus one results.md.
Three arms: A (prompt only), F (the full build: a lite dump from the swarm, use mode), Q (quick mode).
Usage: python3 aggregate.py                    the registered grades (<task>/judgments), the primary analysis
       python3 aggregate.py judgments-full     the full-evidence pass (design.md, amendment 1): writes results-full.json and results-full.md"""
import itertools, json, os, statistics as st, sys
from itertools import combinations, product

HERE = os.path.dirname(os.path.abspath(__file__))
JUDGMENTS = sys.argv[1] if len(sys.argv) > 1 else "judgments"
SUFFIX = JUDGMENTS[len("judgments"):]              # "" or "-full"
ARMS = ["A", "F", "Q"]
PAIRS = [("F", "A"), ("Q", "A"), ("F", "Q")]      # (the arm counted as winning, the arm it is compared with)
CRIT = ["fidelity", "correctness", "craft", "usability", "overall"]
TASKS = {
    "t1-pelican": ("an SVG animation of a pelican riding a bike", CRIT),
    "t2-ascii": ("a simple interactive ascii color mixing engine", CRIT),
    "t3-bento": ("a bento box-inspired collapsible UI menu component for a fictional coffee company site", CRIT),
    "t4-blocks": ("a simple block-building sandbox game with a 32x32 block world", CRIT),
}
mean = lambda xs: round(st.mean(xs), 2) if xs else None


def pearson(a, b):
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b)); den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else None


def permutation_p(a, b):
    """Exact two-sided permutation test on run means: every way to split the runs into two arms."""
    allv = a + b; obs = st.mean(b) - st.mean(a); n = ext = 0
    for idx in itertools.combinations(range(len(allv)), len(b)):
        bb = [allv[i] for i in idx]; aa = [allv[i] for i in range(len(allv)) if i not in idx]
        n += 1; ext += abs(st.mean(bb) - st.mean(aa)) >= abs(obs) - 1e-9
    return round(ext / n, 3)


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
    for f in sorted(x for x in os.listdir(os.path.join(d, JUDGMENTS)) if x.endswith(".json")):
        j = json.load(open(os.path.join(d, JUDGMENTS, f)))
        rank = {lab: i + 1 for i, lab in enumerate(j.get("ranking", []))}
        for lab, sc in j["scores"].items():
            run = key["%s/%s/%s" % (j["block"], j["judge"], lab)]
            rows.append(dict(block=j["block"], judge=j["judge"], run=run, arm=run[0], rank=rank.get(lab), note=sc.get("note", ""),
                             **{c: float(sc[c]) for c in crit}))
    res = {"scores": {}, "pairwise": {}, "functional": func, "cost": {}}
    for a in ARMS:
        ar = [r for r in rows if r["arm"] == a]
        res["scores"][a] = {c: mean([r[c] for r in ar]) for c in crit}
        res["scores"][a]["mean_rank"] = mean([r["rank"] for r in ar if r["rank"]])
        per = {}
        for r in ar:
            per.setdefault(r["run"], []).append(r["overall"])
        res["scores"][a]["per_run_overall"] = {k: mean(v) for k, v in sorted(per.items())}
        ts = [v for k, v in timing.items() if k.startswith(a + "-")]
        res["cost"][a] = {"runs": len(ts), "mean_tokens": round(st.mean(t["tokens"] for t in ts)) if ts else None,
                          "mean_seconds": round(st.mean(t["ms"] for t in ts) / 1000, 1) if ts else None}
    if "dump" in timing:
        res["cost"]["dump"] = timing["dump"]
    for x_arm, y_arm in PAIRS:
        w = l = t = 0
        for b in {r["block"] for r in rows}:
            for jd in {r["judge"] for r in rows if r["block"] == b}:
                xs = [r["overall"] for r in rows if r["block"] == b and r["judge"] == jd and r["arm"] == x_arm]
                ys = [r["overall"] for r in rows if r["block"] == b and r["judge"] == jd and r["arm"] == y_arm]
                for x, y in product(xs, ys):
                    w += x > y; l += x < y; t += x == y
        n = w + l + t
        xr = list(res["scores"][x_arm]["per_run_overall"].values()); yr = list(res["scores"][y_arm]["per_run_overall"].values())
        res["pairwise"]["%s_vs_%s" % (x_arm, y_arm)] = {"wins": w, "losses": l, "ties": t, "win_rate": round((w + 0.5 * t) / n, 2) if n else None,
                                                     "p": permutation_p(yr, xr) if xr and yr else None}
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
    res["notes"] = {"%s/%s/%s" % (r["block"], r["judge"], r["run"]): r["note"] for r in rows}
    json.dump(res, open(os.path.join(d, "results%s.json" % SUFFIX), "w"), indent=1, ensure_ascii=False)
    return res, rows


def main():
    L = ["# Confirmation test results: metadump 1.0.0, frozen before the tasks were known, Sonnet 5.5 at medium effort", "",
         "Arms: **A** = task only; **F** = task + a lite meta dump built by the frozen skill's swarm, read with its use mode; **Q** = task + "
         "quick mode (the builder writes its own dump in one pass). Tasks named by the owner after the freeze. Builders and graders: "
         "Sonnet 5.5 at medium effort, all fresh. Graders blind, 3 per block of 6.", ""]
    summary = []
    for task, (prompt, crit) in TASKS.items():
        jd = os.path.join(HERE, task, JUDGMENTS)
        if not os.path.exists(os.path.join(HERE, task, "key.json")) or not os.path.isdir(jd) or not os.listdir(jd):
            continue
        res, rows = task_results(task, crit)
        s, pw = res["scores"], res["pairwise"]
        summary.append((task, s["A"]["overall"], s["F"]["overall"], s["Q"]["overall"], pw))
        L += ["## %s" % task, "", "Prompt: %s" % prompt, "",
              "| arm | " + " | ".join(crit) + " | per-run overall |", "|---|" + "---|" * (len(crit) + 1)]
        for a in ARMS:
            L.append("| %s | %s | %s |" % (a, " | ".join(("**%s**" % s[a][c]) if c == "overall" else str(s[a][c]) for c in crit),
                                          ", ".join(str(v) for v in s[a]["per_run_overall"].values())))
        L.append("")
        for x_arm, y_arm in PAIRS:
            p = pw["%s_vs_%s" % (x_arm, y_arm)]
            L.append("%s vs %s head to head: %s wins, %s losses, %s ties (win rate %s); permutation test on run means p = %s." % (
                x_arm, y_arm, p["wins"], p["losses"], p["ties"], p["win_rate"], p["p"]))
        L += ["", "Grader agreement r = %s." % res["agreement_r"], ""]
        c = res["cost"]
        L.append("Builder cost per run: " + "; ".join("%s %s tokens, %s s" % (a, c[a]["mean_tokens"], c[a]["mean_seconds"]) for a in ARMS) + "." +
                 (" Dump: %s tokens reported for the main loop, %s s." % (c["dump"]["tokens"], round(c["dump"]["ms"] / 1000)) if "dump" in c else ""))
        L.append("")
    if summary:
        rows = ["## Summary", "", "| task | A | F (full build) | Q (quick) | F vs A | Q vs A | F vs Q |", "|---|---|---|---|---|---|---|"]
        for t, a, b, c, pw in summary:
            top = max(a, b, c)
            cell = lambda k: "%s–%s–%s" % (pw[k]["wins"], pw[k]["losses"], pw[k]["ties"])
            rows.append("| %s | %s | %s | %s | %s | %s | %s |" % (t, *[("**%s**" % v) if v == top else v for v in (a, b, c)],
                                                                 cell("F_vs_A"), cell("Q_vs_A"), cell("F_vs_Q")))
        L[4:4] = rows + [""]
    if SUFFIX:
        L[0] += " (the %s pass of amendment 1, not the registered grades)" % SUFFIX.lstrip("-").replace("full", "full-evidence")
    open(os.path.join(HERE, "results%s.md" % SUFFIX), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
