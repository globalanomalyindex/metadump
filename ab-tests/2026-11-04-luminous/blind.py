#!/usr/bin/env python3
"""Copy runs into blind/<task>/j<n>/<label>.<ext> with the arm hidden; write key.json. Two different orders per task."""
import json, os, shutil, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
LABELS = ["P", "Q", "R", "S", "T", "U"]
ORDERS = [  # fixed, different permutations; judge 2 never matches judge 1's order
    ["B-r2", "A-r1", "C-r2", "B-r1", "C-r1", "A-r2"],
    ["C-r1", "B-r1", "A-r2", "C-r2", "A-r1", "B-r2"],
    ["A-r2", "C-r1", "B-r1", "A-r1", "B-r2", "C-r2"],
    ["B-r1", "C-r2", "A-r1", "B-r2", "A-r2", "C-r1"],
]
key = json.load(open(os.path.join(ROOT, "key.json"))) if os.path.exists(os.path.join(ROOT, "key.json")) else {}
only = set(sys.argv[1:])
for ti, task in enumerate(sorted(os.listdir(os.path.join(ROOT, "runs")))):
    if only and task not in only:
        continue
    files = {os.path.splitext(f)[0]: f for f in os.listdir(os.path.join(ROOT, "runs", task))}
    for j in (1, 2):
        order = ORDERS[(ti + j - 1) % len(ORDERS)] if j == 1 else ORDERS[(ti + 2) % len(ORDERS)]
        d = os.path.join(ROOT, "blind", task, "j%d" % j)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
        for label, run in zip(LABELS, order):
            ext = os.path.splitext(files[run])[1]
            shutil.copy(os.path.join(ROOT, "runs", task, files[run]), os.path.join(d, label + ext))
            shot = os.path.join(ROOT, "shots", task, run + ".png")
            if os.path.exists(shot):
                shutil.copy(shot, os.path.join(d, label + ".png"))
            key["%s/j%d/%s" % (task, j, label)] = run
json.dump(key, open(os.path.join(ROOT, "key.json"), "w"), indent=1)
print("blinded", len(key), "outputs")
