#!/usr/bin/env python3
"""Run 0.13.0's look over every finished HTML build of every arm and count what it reports. A check on the mechanism,
not an outcome: C's builders saw these findings while they worked and A's and B's did not.
Writes <task>/lookall.json. Usage: python3 lookall.py"""
import collections, glob, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "metadump", "scripts"))
import look, tools  # noqa: E402

PLAYED = ["js-error", "uneven", "dead", "focus-static", "focus-hidden", "no-keyboard", "washed-out", "covered", "no-reduced-motion"]
AT_REST = ["clipped", "cut-off", "overlap", "overflow", "small-target", "hover-static", "truncated"]


def main():
    browser = tools.find_browser()["path"]
    for task in ("t1-lavalamp", "t2-calculator"):
        out = {}
        for path in sorted(glob.glob(os.path.join(HERE, task, "runs", "*.html"))):
            run = os.path.basename(path)[:-5]
            try:
                res = look.look(path, tempfile.mkdtemp(prefix="lookall-"), browser_path=browser)
            except Exception as exc:
                out[run] = {"error": repr(exc)[:200]}
                continue
            kinds = collections.Counter(f["kind"] for f in res["findings"])
            out[run] = {"findings": dict(kinds), "played": sum(kinds[k] for k in PLAYED), "at_rest": sum(kinds[k] for k in AT_REST),
                        "details": ["%s %s: %s [%s]" % (f["kind"], f["selector"], f.get("detail", "")[:160], f.get("state", "")) for f in res["findings"] if f["kind"] in PLAYED]}
            print(task, run, dict(kinds))
        json.dump(out, open(os.path.join(HERE, task, "lookall.json"), "w"), indent=1)
        for arm in "ABC":
            rows = [v for k, v in out.items() if k.startswith(arm) and "error" not in v]
            if rows:
                print("  %s arm %s: findings from playing %.2f per build, at rest %.2f per build (%d builds)" % (
                    task, arm, sum(r["played"] for r in rows) / len(rows), sum(r["at_rest"] for r in rows) / len(rows), len(rows)))


if __name__ == "__main__":
    main()
