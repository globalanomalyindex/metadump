#!/usr/bin/env python3
"""Set up the variety graders (pre-registered in design.md): per task, 3 graders each see all 8 builds as two anonymous
sets of four, P and Q. Which arm is P is fixed per grader (A, B, A); the order inside a set follows fixed permutations.
Writes <task>/variety/v<k>/{P1..P4,Q1..Q4}.<ext> plus the screenshots that go with them, and <task>/variety/key.json.
Usage: python3 variety.py <task>"""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
P_ARM = {"v1": "A", "v2": "B", "v3": "A"}
ORDER = {"v1": [2, 0, 3, 1], "v2": [3, 1, 0, 2], "v3": [1, 3, 2, 0]}   # the same permutations blind.py uses
FILES = {
    "t1-button": [(".html", ".html"), ("-desktop.png", "-desktop.png"), ("-interact.png", "-hover.png")],
    "t2-haiku": [(".md", ".md")],
    "t3-toast": [(".html", ".html"), ("-desktop.png", "-desktop.png"), ("-open-desktop.png", "-open.png")],
}


def main(task):
    d = os.path.join(HERE, task)
    out = os.path.join(d, "variety")
    shutil.rmtree(out, ignore_errors=True)
    key = {}
    for v, p_arm in P_ARM.items():
        os.makedirs(os.path.join(out, v))
        q_arm = "B" if p_arm == "A" else "A"
        for label, arm in (("P", p_arm), ("Q", q_arm)):
            for slot, i in enumerate(ORDER[v], start=1):
                run = "%s-r%d" % (arm, i + 1)
                key["%s/%s%d" % (v, label, slot)] = run
                for src_suffix, dst_suffix in FILES[task]:
                    sub = "runs" if src_suffix in (".html", ".md") else "shots"
                    src = os.path.join(d, sub, run + src_suffix)
                    if os.path.exists(src):
                        shutil.copy(src, os.path.join(out, v, "%s%d%s" % (label, slot, dst_suffix)))
        key[v] = {"P": p_arm, "Q": q_arm}
    json.dump(key, open(os.path.join(out, "key.json"), "w"), indent=1)
    print(task, "variety sets written", {v: key[v] for v in P_ARM})


if __name__ == "__main__":
    main(sys.argv[1])
