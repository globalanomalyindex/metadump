#!/usr/bin/env python3
"""Unblind the variety judgments: mean variety per arm per task, and how often each arm was called more varied.
Writes variety.json. Usage: python3 variety_results.py"""
import json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
out = {}
for task in ("t1-button", "t2-haiku", "t3-toast"):
    d = os.path.join(HERE, task)
    kp, jd = os.path.join(d, "variety", "key.json"), os.path.join(d, "judgments-variety")
    if not (os.path.exists(kp) and os.path.isdir(jd) and os.listdir(jd)):
        continue
    key = json.load(open(kp)); per = {"A": [], "B": []}; more = {"A": 0, "B": 0, "tie": 0}; notes = []
    for f in sorted(os.listdir(jd)):
        j = json.load(open(os.path.join(jd, f))); v = j["grader"]; arms = key[v]
        for label in ("P", "Q"):
            per[arms[label]].append(float(j["variety"][label]))
        m = j.get("more_varied", "tie"); more[arms[m] if m in arms else "tie"] += 1
        notes.append("%s (P=%s): %s" % (v, arms["P"], j.get("note", "")))
    out[task] = {"A_mean": round(st.mean(per["A"]), 2), "B_mean": round(st.mean(per["B"]), 2), "A": per["A"], "B": per["B"],
                 "more_varied": more, "notes": notes}
json.dump(out, open(os.path.join(HERE, "variety.json"), "w"), indent=1)
for t, r in out.items():
    print(t, "variety A %.2f  B %.2f  more varied: %s" % (r["A_mean"], r["B_mean"], r["more_varied"]))
    for n in r["notes"]: print("   ", n[:300])
