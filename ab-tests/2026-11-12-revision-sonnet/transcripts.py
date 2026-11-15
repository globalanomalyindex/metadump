#!/usr/bin/env python3
"""What each builder did, read from its transcript: whether it dealt and which angle it got, how often it ran the
look (and with --play), which findings the look printed each time, how many images it opened, and how many edits
followed its first look. Writes process.json. Usage: python3 transcripts.py [transcript dir]"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SESSION = os.path.expanduser("~/.claude/projects/-Users-chrisfiore-metadump-skill/b3372dc1-379a-466c-98f0-fe8b40451451/subagents")
RUN = re.compile(r"2026-11-12-revision-sonnet/(t\d-[a-z]+)/runs/([ABCD]-r\d)\.")
FINDING = re.compile(r"^\s+- ([a-z-]+)\s", re.M)


def blocks(path):
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        content = (d.get("message") or {}).get("content")
        if isinstance(content, str):
            yield {"type": "text", "text": content}
        for c in content if isinstance(content, list) else []:
            if isinstance(c, dict):
                yield c


def text_of(block):
    c = block.get("content")
    if isinstance(c, str):
        return c
    return "\n".join(x.get("text", "") for x in c or [] if isinstance(x, dict))


def read(path):
    out = {"dealt": False, "angle": None, "deal_no": None, "looks": 0, "plays": 0, "look_findings": [], "images_read": 0,
           "sheet_read": 0, "edits_after_first_look": 0, "edits": 0}
    task = run = None
    pending = {}                       # tool_use id -> what it was
    for b in blocks(path):
        if task is None and b.get("type") == "text":
            m = RUN.search(b.get("text", ""))
            if m and "Task:" in b.get("text", ""):
                task, run = m.group(1), m.group(2)
        if b.get("type") == "tool_use":
            name, inp = b.get("name"), b.get("input") or {}
            cmd = inp.get("command", "") if name == "Bash" else ""
            if "deal.py" in cmd:
                out["dealt"] = True; pending[b.get("id")] = "deal"
            if "look.py" in cmd:
                out["looks"] += 1; out["plays"] += cmd.count("--play"); pending[b.get("id")] = "look"
            if name == "Read" and str(inp.get("file_path", "")).endswith(".png"):
                out["images_read"] += 1
                out["sheet_read"] += str(inp.get("file_path", "")).endswith("sheet.png")
            if name in ("Edit", "Write", "MultiEdit"):
                out["edits"] += 1
                out["edits_after_first_look"] += out["looks"] > 0
        if b.get("type") == "tool_result" and b.get("tool_use_id") in pending:
            kind, body = pending.pop(b["tool_use_id"]), text_of(b)
            if kind == "deal" and out["angle"] is None:
                m = re.search(r'Start from the angle "([^"]+)"', body)
                out["angle"] = m.group(1) if m else None
                m = re.search(r"deal (\d+) from this dump", body)
                out["deal_no"] = int(m.group(1)) if m else None
            if kind == "look":
                out["look_findings"].append(sorted(FINDING.findall(body.split("Things to look at", 1)[1])) if "Things to look at" in body else [])
    return task, run, out


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SESSION
    process = {}
    for path in glob.glob(os.path.join(src, "agent-*.jsonl")):
        head = open(path, encoding="utf-8", errors="replace").read(6000)
        if "2026-11-12-revision-sonnet" not in head or "/runs/" not in head:
            continue
        task, run, out = read(path)
        if task:
            out["agent"] = os.path.basename(path)[6:-6]
            process.setdefault(task, {})[run] = out
    json.dump(process, open(os.path.join(HERE, "process.json"), "w"), indent=1, sort_keys=True)
    for task in sorted(process):
        print("##", task)
        for run in sorted(process[task]):
            p = process[task][run]
            if run[0] == "A":
                continue
            print("  %s dealt=%s deal#%s angle=%r looks=%d plays=%d images=%d sheet=%d edits_after_look=%d findings=%s" % (
                run, p["dealt"], p["deal_no"], p["angle"], p["looks"], p["plays"], p["images_read"], p["sheet_read"],
                p["edits_after_first_look"], [len(f) for f in p["look_findings"]]))


if __name__ == "__main__":
    main()
