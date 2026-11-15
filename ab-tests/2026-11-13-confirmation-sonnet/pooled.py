#!/usr/bin/env python3
"""Pooled comparison of each pair of arms across the tasks: an exact stratified permutation test.

Within each task, arm labels are shuffled among that pair's 8 run means (all C(8,4) = 70 splits); tasks are
independent strata, so the null distribution of the pooled statistic (the mean over tasks of X minus Y) is the
convolution of the per-task distributions. Reads <task>/results.json (run aggregate.py first); writes pooled.json.
Usage: python3 pooled.py [judgments-full]     (after aggregate.py with the same argument; writes pooled.json or pooled-full.json)
The file also holds the same test on tasks 1 to 3 alone (the tasks in the owner's own words) and on task 4 alone, which design.md
says are reported apart as well as together."""
import json, os, statistics as st, sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
SUFFIX = (sys.argv[1] if len(sys.argv) > 1 else "judgments")[len("judgments"):]              # "" or "-full"
TASKS = ["t1-pelican", "t2-ascii", "t3-bento", "t4-blocks"]
PAIRS = [("F", "A"), ("Q", "A"), ("F", "Q")]
Q = 10 ** 6  # exact enough: run means are averages of 3 integer scores


def split_diffs(a, b):
    allv = a + b; out = {}
    for idx in combinations(range(len(allv)), len(b)):
        bb = [allv[i] for i in idx]; aa = [allv[i] for i in range(len(allv)) if i not in idx]
        k = round((st.mean(bb) - st.mean(aa)) * Q)
        out[k] = out.get(k, 0) + 1
    return out


def pair(x_arm, y_arm, tasks=None):
    dist = {0: 1}; obs = 0; per = {}; used = []; W = L = T = 0
    for t in tasks or TASKS:
        f = os.path.join(HERE, t, "results%s.json" % SUFFIX)
        if not os.path.exists(f):
            continue
        r = json.load(open(f)); s = r["scores"]; pw = r["pairwise"]["%s_vs_%s" % (x_arm, y_arm)]
        W += pw["wins"]; L += pw["losses"]; T += pw["ties"]
        y = list(s[y_arm]["per_run_overall"].values()); x = list(s[x_arm]["per_run_overall"].values())
        d = round((st.mean(x) - st.mean(y)) * Q); obs += d; used.append(t)
        per[t] = {y_arm + "_mean": round(st.mean(y), 2), x_arm + "_mean": round(st.mean(x), 2), "diff": round(d / Q, 2)}
        nd = {}
        for k1, c1 in dist.items():
            for k2, c2 in split_diffs(y, x).items():
                nd[k1 + k2] = nd.get(k1 + k2, 0) + c1 * c2
        dist = nd
    total = sum(dist.values())
    ext = sum(c for k, c in dist.items() if abs(k) >= abs(obs) - 1)
    ge = sum(c for k, c in dist.items() if k >= obs - 1)
    return {"tasks": used, "per_task": per, "pooled_mean_diff": round(obs / Q / len(used), 3) if used else None,
            "p_two_sided": round(ext / total, 4), "p_one_sided_%s_better" % x_arm: round(ge / total, 4), "splits": total,
            "wins": W, "losses": L, "ties": T, "win_rate": round((W + 0.5 * T) / (W + L + T), 2) if W + L + T else None}


def main():
    out = {"%s_vs_%s" % p: pair(*p) for p in PAIRS}
    out["owner_worded_tasks_1_to_3"] = {"%s_vs_%s" % p: pair(*p, tasks=TASKS[:3]) for p in PAIRS}
    out["task_4_alone"] = {"%s_vs_%s" % p: pair(*p, tasks=TASKS[3:]) for p in PAIRS}
    json.dump(out, open(os.path.join(HERE, "pooled%s.json" % SUFFIX), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
