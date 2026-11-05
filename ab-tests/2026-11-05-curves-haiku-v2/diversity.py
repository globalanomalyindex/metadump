#!/usr/bin/env python3
"""Curve diversity from window.CURVES (curves/<run>.json, written by motion.mjs).

Within a build: mean pairwise distance between its three curves' progress profiles
(mean absolute difference over 101 equal time samples; 0 = identical).
Across an arm: how many distinct bezier tuples its 12 curves use (rounded to 2 decimals).
Usage: python3 diversity.py [test dir ...]   (default: this folder)
"""
import glob, itertools, json, os, sys


def ease_at(b, x):
    x1, y1, x2, y2 = b
    bx = lambda s: 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3
    by = lambda s: 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s * s * y2 + s ** 3
    lo, hi = 0.0, 1.0
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if bx(m) < x else (lo, m)
    return by((lo + hi) / 2)


def profile(b):
    return [ease_at(b, i / 100) for i in range(101)]


def dist(p, q):
    return sum(abs(a - b) for a, b in zip(p, q)) / len(p)


def report(root):
    out = {"within_build": {}, "arms": {}}
    runs = {}
    for f in sorted(glob.glob(os.path.join(root, "curves", "*.json"))):
        runs[os.path.basename(f)[:-5]] = [c["bezier"] for c in json.load(open(f))]
    for run, bs in runs.items():
        ps = [profile(b) for b in bs]
        pairs = [dist(p, q) for p, q in itertools.combinations(ps, 2)]
        out["within_build"][run] = round(sum(pairs) / len(pairs), 3) if pairs else None
    for arm in sorted({r[0] for r in runs}):
        tuples = [tuple(round(v, 2) for v in b) for r, bs in runs.items() if r[0] == arm for b in bs]
        within = [v for r, v in out["within_build"].items() if r[0] == arm and v is not None]
        out["arms"][arm] = {"curves": len(tuples), "distinct_tuples": len(set(tuples)),
                            "mean_within_build_distance": round(sum(within) / len(within), 3) if within else None}
    return out


if __name__ == "__main__":
    for root in sys.argv[1:] or [os.path.dirname(os.path.abspath(__file__))]:
        r = report(root)
        print(os.path.basename(os.path.normpath(root)), json.dumps(r, indent=1))
        if not sys.argv[1:]:
            json.dump(r, open(os.path.join(root, "diversity.json"), "w"), indent=1)
