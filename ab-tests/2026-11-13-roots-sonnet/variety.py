#!/usr/bin/env python3
"""Set up the variety graders (pre-registered in design.md): per task, 3 graders each see all 12 builds as three
anonymous sets of four, P, Q and R. Which arm is behind each letter rotates per grader; the order inside a set
follows fixed permutations. Writes <task>/variety/v<k>/ and <task>/variety/key.json. Usage: python3 variety.py <task>"""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SETS = {"v1": {"P": "A", "Q": "C", "R": "R"}, "v2": {"P": "C", "Q": "R", "R": "A"}, "v3": {"P": "R", "Q": "A", "R": "C"}}
ORDER = {"v1": [2, 0, 3, 1], "v2": [3, 1, 0, 2], "v3": [1, 3, 2, 0]}   # the permutations tests 13 to 19 used
FILES = {
    "t1-lavalamp": [(".html", ".html"), ("-desktop.png", "-desktop.png"), ("-interact.png", "-motion.png")],
    "t2-calculator": [(".html", ".html"), ("-desktop.png", "-desktop.png"), ("-interact.png", "-use.png")],
}


def main(task):
    d = os.path.join(HERE, task)
    out = os.path.join(d, "variety")
    shutil.rmtree(out, ignore_errors=True)
    key = {}
    for v, sets in SETS.items():
        os.makedirs(os.path.join(out, v))
        for label, arm in sets.items():
            for slot, i in enumerate(ORDER[v], start=1):
                run = "%s-r%d" % (arm, i + 1)
                key["%s/%s%d" % (v, label, slot)] = run
                for src_suffix, dst_suffix in FILES[task]:
                    sub = "runs" if src_suffix in (".html", ".md") else "shots"
                    src = os.path.join(d, sub, run + src_suffix)
                    if os.path.exists(src):
                        shutil.copy(src, os.path.join(out, v, "%s%d%s" % (label, slot, dst_suffix)))
        key[v] = sets
    json.dump(key, open(os.path.join(out, "key.json"), "w"), indent=1)
    print(task, "variety sets written", {v: key[v] for v in SETS})


if __name__ == "__main__":
    main(sys.argv[1])
