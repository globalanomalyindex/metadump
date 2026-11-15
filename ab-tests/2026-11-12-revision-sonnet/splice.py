#!/usr/bin/env python3
"""Make this test's dump for one task: test 20's dump with `essence.angles` replaced by <task>/metadumps/angles.json
(written by the repair worker), re-finalized by the working tree's finalize.py. Nothing else in the dump changes.
Usage: python3 splice.py <task> <slug>"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
task, slug = sys.argv[1], sys.argv[2]
src = os.path.join(HERE, "..", "2026-11-12-three-arms-sonnet", task, "metadumps", slug + ".metadump.json")
out = os.path.join(HERE, task, "metadumps", slug + ".metadump.json")
before = json.load(open(src))
angles = json.load(open(os.path.join(HERE, task, "repair", "angles.json")))
ids = set()
def walk(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, dict) and ("prov" in v or "tier" in v):
                ids.add(k)
            walk(v)
walk({k: v for k, v in before.items() if k != "index"})
for a in angles:
    missing = [i for i in a.get("draws_on", []) if i not in ids]
    assert set(a) >= {"angle", "text"}, a
    if missing:
        print("dropping unknown ids from", a["angle"], missing)
        a["draws_on"] = [i for i in a["draws_on"] if i in ids]
dump = json.loads(json.dumps(before))
dump["essence"]["angles"] = angles
json.dump(dump, open(out, "w"))
run = subprocess.run([sys.executable, os.path.join(HERE, "..", "..", "skills", "metadump", "scripts", "finalize.py"), "build", out], capture_output=True, text=True)
print(run.stdout[-600:], run.stderr[-300:])
after = json.load(open(out))
def strip(d):   # routes carry measured token counts, and a route that reads the head counts the angles
    out = {k: v for k, v in d.items() if k not in ("manifest", "index", "essence", "routing")}
    out["routing"] = [{f: v for f, v in r.items() if f not in ("tokens", "lines")} for r in d.get("routing", [])]
    return out
ess = lambda d: {k: v for k, v in d["essence"].items() if k != "angles"}
print("same outside manifest, index and essence.angles:", strip(before) == strip(after) and ess(before) == ess(after))
print("angles before:", [a["angle"] for a in before["essence"]["angles"]])
print("angles after: ", [a["angle"] for a in after["essence"]["angles"]])
for a in after["essence"]["angles"]:
    print("  -", a["angle"], ":", a["text"][:170])
