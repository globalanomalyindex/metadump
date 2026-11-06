#!/usr/bin/env python3
"""Blind one task: two blocks of 4 (runs 1-2 and 3-4 of each arm), 3 graders per block, each with its own label order.
Usage: python3 blind.py <task>   Writes <task>/blind/ and <task>/key.json."""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS = ["W", "X", "Y", "Z"]
PERMS = [[2, 0, 3, 1], [3, 1, 0, 2], [1, 3, 2, 0]]  # the same orders as tests 3-9
BLOCKS = {"b1": (1, 2), "b2": (3, 4)}
FILES = {
    "t1-recipe": [(".md", ".md")],
    "t2-tictactoe": [(".html", ".html"), ("-desktop.png", "-desktop.png"), ("-mobile.png", "-mobile.png"), ("-interact.png", "-play.png"),
                     ("-end.png", "-end.png")],
    "t3-lemon": [(".html", ".html"), ("-desktop.png", "-desktop.png"), ("-mobile.png", "-mobile.png"), ("-interact.png", "-turn.png")],
}


def main(task):
    d = os.path.join(HERE, task)
    key = {}
    for b, (x, y) in BLOCKS.items():
        base = ["A-r%d" % x, "A-r%d" % y, "B-r%d" % x, "B-r%d" % y]
        for j, perm in enumerate(PERMS, 1):
            out = os.path.join(d, "blind", b, "j%d" % j)
            shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
            for label, i in zip(LABELS, perm):
                run = base[i]
                for src_suffix, dst_suffix in FILES[task]:
                    src = os.path.join(d, "runs" if src_suffix in (".html", ".md") else "shots", run + src_suffix)
                    if os.path.exists(src):
                        shutil.copy(src, os.path.join(out, label + dst_suffix))
                key["%s/j%d/%s" % (b, j, label)] = run
    json.dump(key, open(os.path.join(d, "key.json"), "w"), indent=1)
    print(task, "blinded", len(key))


if __name__ == "__main__":
    main(sys.argv[1])
