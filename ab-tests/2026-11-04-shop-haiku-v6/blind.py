#!/usr/bin/env python3
"""Two blocks of 4 (runs 1-2 and 3-4 of each arm); 3 graders per block, each with its own label order. Writes key.json."""
import json, os, shutil
ROOT = os.path.dirname(os.path.abspath(__file__))
LABELS = ["W", "X", "Y", "Z"]
PERMS = [[2, 0, 3, 1], [3, 1, 0, 2], [1, 3, 2, 0]]  # every run lands on a different label for each grader
BLOCKS = {"b1": (1, 2), "b2": (3, 4)}
key = {}
for b, (x, y) in BLOCKS.items():
    base = ["A-r%d" % x, "A-r%d" % y, "B-r%d" % x, "B-r%d" % y]
    for j, perm in enumerate(PERMS, 1):
        d = os.path.join(ROOT, "blind", b, "j%d" % j)
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        for label, i in zip(LABELS, perm):
            run = base[i]
            shutil.copy(os.path.join(ROOT, "runs", run + ".html"), os.path.join(d, label + ".html"))
            for v in ("desktop", "mobile"):
                shutil.copy(os.path.join(ROOT, "shots", "%s-%s.png" % (run, v)), os.path.join(d, "%s-%s.png" % (label, v)))
            key["%s/j%d/%s" % (b, j, label)] = run
json.dump(key, open(os.path.join(ROOT, "key.json"), "w"), indent=1)
print("blinded", len(key))
