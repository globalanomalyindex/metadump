#!/usr/bin/env python3
"""Blocks of 6 (runs 1-2, runs 3-4); 3 judges per block, each with its own label order. Writes key.json."""
import json, os, shutil
ROOT = os.path.dirname(os.path.abspath(__file__))
LABELS = ["P", "Q", "R", "S", "T", "U"]
PERMS = [[3, 0, 5, 2, 4, 1], [4, 2, 1, 5, 0, 3], [1, 5, 3, 0, 2, 4]]
BLOCKS = {"b1": (1, 2), "b2": (3, 4)}
key = {}
for b, (x, y) in BLOCKS.items():
    base = ["A-r%d" % x, "A-r%d" % y, "B-r%d" % x, "B-r%d" % y, "C-r%d" % x, "C-r%d" % y]
    for j, perm in enumerate(PERMS, 1):
        d = os.path.join(ROOT, "blind", b, "j%d" % j)
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        for label, i in zip(LABELS, perm):
            run = base[i]
            shutil.copy(os.path.join(ROOT, "runs", run + ".html"), os.path.join(d, label + ".html"))
            shutil.copy(os.path.join(ROOT, "shots", run + ".png"), os.path.join(d, label + ".png"))
            key["%s/j%d/%s" % (b, j, label)] = run
json.dump(key, open(os.path.join(ROOT, "key.json"), "w"), indent=1)
print("blinded", len(key))
