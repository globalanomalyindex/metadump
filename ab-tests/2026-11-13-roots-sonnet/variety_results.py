#!/usr/bin/env python3
"""Unblind the variety graders: per task, each arm's variety score from each grader. Writes variety.json.
Usage: python3 variety_results.py"""
import json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = ["t1-lavalamp", "t2-calculator"]
out = {}
for task in TASKS:
    kf = os.path.join(HERE, task, "variety", "key.json")
    jd = os.path.join(HERE, task, "judgments-variety")
    if not os.path.exists(kf) or not os.path.isdir(jd) or not os.listdir(jd):
        continue
    key = json.load(open(kf)); per = {"A": [], "C": [], "R": []}; notes = {}; breaks = {"A": [], "C": [], "R": []}
    for f in sorted(os.listdir(jd)):
        j = json.load(open(os.path.join(jd, f))); g = j["grader"]
        for letter, score in j["variety"].items():
            per[key[g][letter]].append(float(score))
        for letter, n in (j.get("breaks") or {}).items():
            breaks[key[g][letter]].append(float(n))
        notes[g] = {"sets": key[g], "most_varied": key[g].get(j.get("most_varied"), j.get("most_varied")), "note": j.get("note", "")}
    out[task] = {"scores": per, "mean": {a: round(st.mean(v), 2) for a, v in per.items() if v},
                 "breaks": breaks, "mean_breaks": {a: round(st.mean(v), 2) for a, v in breaks.items() if v}, "graders": notes}
    print(task, "variety", out[task]["mean"], per, "| breaks of what is fixed, of 4:", out[task]["mean_breaks"], breaks)
    for g, n in notes.items():
        print("   %s %s most varied: %s | %s" % (g, n["sets"], n["most_varied"], n["note"][:400]))
json.dump(out, open(os.path.join(HERE, "variety.json"), "w"), indent=1)
