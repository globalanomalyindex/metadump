#!/usr/bin/env python3
"""Pooled B-vs-A test across the tasks: an exact stratified permutation test.

Within each task, arm labels are shuffled among that task's 8 run means (all C(8,4) = 70 splits); tasks are
independent strata, so the null distribution of the pooled statistic (the mean over tasks of B minus A) is the
convolution of the per-task distributions. Reads <task>/results.json (run aggregate.py first); writes pooled.json.
Usage: python3 pooled.py"""
import json, os, statistics as st
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = ["t1-recipe", "t2-tictactoe", "t3-lemon"]
Q = 10 ** 6  # exact enough: run means are averages of 3 integer scores


def split_diffs(a, b):
    allv = a + b; out = {}
    for idx in combinations(range(len(allv)), len(b)):
        bb = [allv[i] for i in idx]; aa = [allv[i] for i in range(len(allv)) if i not in idx]
        k = round((st.mean(bb) - st.mean(aa)) * Q)
        out[k] = out.get(k, 0) + 1
    return out


def main():
    dist = {0: 1}; obs = 0; per = {}; used = []; W = L = T = 0
    for t in TASKS:
        f = os.path.join(HERE, t, "results.json")
        if not os.path.exists(f):
            continue
        r = json.load(open(f)); s = r["scores"]; pw = r["pairwise"]
        W += pw["wins"]; L += pw["losses"]; T += pw["ties"]
        a = list(s["A"]["per_run_overall"].values()); b = list(s["B"]["per_run_overall"].values())
        d = round((st.mean(b) - st.mean(a)) * Q); obs += d; used.append(t)
        per[t] = {"A_mean": round(st.mean(a), 2), "B_mean": round(st.mean(b), 2), "diff": round(d / Q, 2)}
        nd = {}
        for k1, c1 in dist.items():
            for k2, c2 in split_diffs(a, b).items():
                nd[k1 + k2] = nd.get(k1 + k2, 0) + c1 * c2
        dist = nd
    total = sum(dist.values())
    ext = sum(c for k, c in dist.items() if abs(k) >= abs(obs) - 1)
    ge = sum(c for k, c in dist.items() if k >= obs - 1)
    out = {"tasks": used, "per_task": per, "pooled_mean_diff": round(obs / Q / len(used), 3),
           "p_two_sided": round(ext / total, 4), "p_one_sided_B_better": round(ge / total, 4), "splits": total,
           "pooled_wins": W, "pooled_losses": L, "pooled_ties": T, "pooled_win_rate": round((W + 0.5 * T) / (W + L + T), 2) if W + L + T else None}
    json.dump(out, open(os.path.join(HERE, "pooled.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
