#!/usr/bin/env python3
"""Blind one task: two blocks of 6 (runs 1-2 and 3-4 of each of the three arms), 3 graders per block, each with its
own label order. Usage: python3 blind.py <task>   Writes <task>/blind/ and <task>/key.json."""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ["A", "F", "Q"]
LABELS = ["U", "V", "W", "X", "Y", "Z"]
# Fixed before any run. Base order is A-x, A-y, F-x, F-y, Q-x, Q-y; each arm leads once.
PERMS = [[2, 4, 0, 5, 1, 3], [5, 1, 3, 0, 4, 2], [1, 3, 5, 2, 0, 4]]
BLOCKS = {"b1": (1, 2), "b2": (3, 4)}
FILES = [(".html", ".html"), ("-desktop.png", "-desktop.png"), ("-mobile.png", "-mobile.png"), ("-interact.png", "-use.png")]


def main(task):
    d = os.path.join(HERE, task)
    key = {}
    for b, (x, y) in BLOCKS.items():
        base = ["%s-r%d" % (arm, r) for arm in ARMS for r in (x, y)]
        for j, perm in enumerate(PERMS, 1):
            out = os.path.join(d, "blind", b, "j%d" % j)
            shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
            for label, i in zip(LABELS, perm):
                run = base[i]
                for src_suffix, dst_suffix in FILES:
                    src = os.path.join(d, "runs" if src_suffix in (".html", ".md") else "shots", run + src_suffix)
                    if os.path.exists(src):
                        shutil.copy(src, os.path.join(out, label + dst_suffix))
                    else:
                        print("missing", src)
                key["%s/j%d/%s" % (b, j, label)] = run
    json.dump(key, open(os.path.join(d, "key.json"), "w"), indent=1)
    print(task, "blinded", len(key))


if __name__ == "__main__":
    main(sys.argv[1])
