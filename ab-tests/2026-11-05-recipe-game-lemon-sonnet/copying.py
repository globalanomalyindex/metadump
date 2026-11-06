#!/usr/bin/env python3
"""Pre-registered copying measure (design.md).
For each HTML task: the illustrative curves and colours the dump's own entries offer (`tokens` of inferred/proposed
entries) and how many of them appear verbatim in each build's source (A builds are the baseline: they never saw
the dump). For the button: how many builds share a curve set with every other build in their arm.
Writes copying.json. Usage: python3 copying.py [dump-dir-test12 for comparison]"""
import glob, itertools, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIT = re.compile(r"cubic-bezier\([^)]*\)|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")
PRESETS = {(0.25, 0.1, 0.25, 1.0), (0.42, 0.0, 1.0, 1.0), (0.0, 0.0, 0.58, 1.0), (0.42, 0.0, 0.58, 1.0), (0.0, 0.0, 1.0, 1.0)}


def norm(lit):
    if lit.lower().startswith("cubic-bezier"):
        try:
            return ("curve", tuple(round(float(x), 3) for x in lit[lit.index("(") + 1:-1].split(",")))
        except ValueError:
            return None
    h = lit.lower().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return ("colour", h)


def dump_literals(dump_path):
    d = json.load(open(dump_path)); out = set()
    def walk(node):
        if isinstance(node, dict):
            if node.get("prov") in ("inferred", "proposed") and isinstance(node.get("tokens"), dict) and \
               node["tokens"].get("status") not in ("measured", "sourced"):
                for m in LIT.findall(json.dumps(node["tokens"])):
                    n = norm(m)
                    if n and not (n[0] == "curve" and n[1] in PRESETS):
                        out.add(n)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(d)
    return out


def build_literals(path):
    return {n for n in (norm(m) for m in LIT.findall(open(path).read())) if n and not (n[0] == "curve" and n[1] in PRESETS)}


def task_report(task_dir):
    dumps = glob.glob(os.path.join(task_dir, "metadumps", "*.metadump.json"))
    if not dumps:
        return None
    offered = dump_literals(dumps[0])
    runs = sorted(glob.glob(os.path.join(task_dir, "runs", "*.html")))
    rep = {"offered": len(offered), "offered_curves": sum(1 for o in offered if o[0] == "curve"), "builds": {}}
    curves = {}
    for r in runs:
        lits = build_literals(r); run = os.path.basename(r)[:-5]
        rep["builds"][run] = {"dump_values_reused": len(lits & offered)}
        curves[run] = {l for l in lits if l[0] == "curve"}
    for arm in "AB":
        rs = [r for r in curves if r.startswith(arm)]
        rep["%s_builds_reusing_any" % arm] = sum(1 for r in rs if rep["builds"][r]["dump_values_reused"])
        rep["%s_mean_reused" % arm] = round(sum(rep["builds"][r]["dump_values_reused"] for r in rs) / max(1, len(rs)), 2)
        common = set.intersection(*[curves[r] for r in rs]) if rs and all(curves[r] for r in rs) else set()
        rep["%s_curves_shared_by_all" % arm] = len(common)
    return rep


def main():
    out = {}
    roots = [HERE] + sys.argv[1:]
    for root in roots:
        for task in ("t2-tictactoe", "t3-lemon"):
            r = task_report(os.path.join(root, task))
            if r:
                out["%s:%s" % (os.path.basename(root), task)] = r
    json.dump(out, open(os.path.join(HERE, "copying.json"), "w"), indent=1)
    for k, r in out.items():
        print(k, {x: r[x] for x in r if x != "builds"})


if __name__ == "__main__":
    main()
