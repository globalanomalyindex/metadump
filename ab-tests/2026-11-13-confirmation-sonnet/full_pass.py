#!/usr/bin/env python3
"""The full-evidence grading pass (design.md, amendment 1): say which graders still have to run, and accept or set aside each
grade by the audit of its grader's transcript. A grade whose grader did not open all 18 pictures and read all six sources is
moved to <task>/judgments-full/discarded/ without being opened, and the grader is rerun fresh, up to three attempts in all. After
a third incomplete attempt, the attempt that opened the most is put back and marked in full-pass.json.
Usage: python3 full_pass.py            Prints one line per grader and the prompts still to launch (prompts.py grade_full ...)."""
import json, os, shutil

import grader_audit

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = ["t1-pelican", "t2-ascii", "t3-bento", "t4-blocks"]
MOST = 3


def main():
    attempts = grader_audit.collect(full=True)
    state, todo = {}, []
    for task in TASKS:
        for block in ("b1", "b2"):
            for judge in ("j1", "j2", "j3"):
                name = "%s-%s" % (block, judge)
                key = "%s/judgments-full/%s" % (task, name)
                rows = attempts.get(key, [])
                d = os.path.join(HERE, task, "judgments-full")
                f = os.path.join(d, name + ".json")
                aside = lambda n: os.path.join(d, "discarded", "%s.attempt%d.json" % (name, n))
                opened = lambda r: r["images_opened"] + r["sources_read"]
                if not rows:
                    state[key] = "to launch"; todo.append((task, block, judge)); continue
                last, n = rows[-1], len(rows)
                if not os.path.exists(f) and not os.path.exists(aside(n)):
                    state[key] = "attempt %d running or without a file" % n; continue
                if last["complete"]:
                    state[key] = "accepted, attempt %d" % n; continue
                if os.path.exists(f):                                   # incomplete: set it aside unread
                    os.makedirs(os.path.dirname(aside(n)), exist_ok=True)
                    shutil.move(f, aside(n))
                if n < MOST:
                    state[key] = "attempt %d opened %d of 24; rerun" % (n, opened(last)); todo.append((task, block, judge)); continue
                best = max(range(n), key=lambda i: (opened(rows[i]), i))
                if os.path.exists(aside(best + 1)):
                    shutil.copy(aside(best + 1), f)
                state[key] = "INCOMPLETE after %d attempts; kept attempt %d, which opened %d of 24" % (n, best + 1, opened(rows[best]))
    json.dump({"state": state, "attempts": {k: [{x: r[x] for x in ("images_opened", "sources_read", "complete", "transcript")} for r in v]
                                            for k, v in attempts.items()}}, open(os.path.join(HERE, "full-pass.json"), "w"), indent=1)
    for k, v in state.items():
        print("%-36s %s" % (k, v))
    print("to launch: %d" % len(todo))
    for t in todo:
        print("  python3 prompts.py grade_full %s %s %s" % t)


if __name__ == "__main__":
    main()
