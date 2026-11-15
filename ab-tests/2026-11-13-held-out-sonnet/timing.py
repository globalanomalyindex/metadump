#!/usr/bin/env python3
"""Append a run's cost, from its completion notice, to <task>/timing.jsonl.
Usage: python3 timing.py <task> <run> <tokens> <ms> <tool_uses> [agents_spawned]"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
task, run, tokens, ms, uses = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
row = {"run": run, "tokens": tokens, "ms": ms, "tool_uses": uses}
if len(sys.argv) > 6:
    row["agents_spawned"] = int(sys.argv[6])
path = os.path.join(HERE, task, "timing.jsonl")
rows = [json.loads(l) for l in open(path)] if os.path.exists(path) else []
rows = [r for r in rows if r["run"] != run] + [row]
open(path, "w").write("".join(json.dumps(r) + "\n" for r in rows))
print(task, run, "logged;", len(rows), "rows")
