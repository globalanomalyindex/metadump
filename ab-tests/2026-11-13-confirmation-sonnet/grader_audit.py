#!/usr/bin/env python3
"""What each grader actually opened. Post hoc to the design, written before any score was read (design.md, amendment 1).
The grading prompt tells a grader to look at every picture and read every source; this reads each grader's own transcript and
counts which of those files it opened, so the write-up can say how much of the evidence the grades rest on. It reads which files
a grader opened and never what it wrote.
Usage: python3 grader_audit.py [judgments-full]     (default: the registered pass, judgments and judgments-variety)
Writes grader-audit.json or grader-audit-full.json and prints one line per grader."""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SESSIONS = os.path.expanduser("~/.claude/projects/-Users-chrisfiore-metadump-skill")
PRINTS = re.compile(r"\b(cat|head|tail|sed|awk|less|more|nl)\b")      # shell commands that put a file's text in front of the grader
REGISTERED = ("judgments", "judgments-variety")


def transcript(path):
    """(first prompt, tool uses) of one subagent transcript; tool uses de-duplicated by id."""
    prompt, uses, seen = None, [], set()
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        m = d.get("message") or {}
        c = m.get("content")
        if prompt is None and m.get("role") == "user":
            prompt = c if isinstance(c, str) else " ".join(x.get("text", "") for x in c if isinstance(x, dict))
        if m.get("role") != "assistant" or not isinstance(c, list):
            continue
        for x in c:
            if isinstance(x, dict) and x.get("type") == "tool_use" and x.get("id") not in seen:
                seen.add(x.get("id"))
                uses.append((x.get("name"), x.get("input") or {}))
    return prompt or "", uses


def row_for(task, folder, name, uses):
    quality = not folder.startswith("judgments-variety")
    labels = list("UVWXYZ") if quality else ["%s%d" % (s, i) for s in "PQR" for i in range(1, 5)]
    kinds = ["desktop", "mobile", "use"] if quality else ["desktop", "use"]
    opened = {k: set() for k in kinds + ["source_read", "source_printed", "source_counted"]}
    for tool, inp in uses:
        f = os.path.basename(inp.get("file_path", ""))
        if tool == "Read" and f:
            mm = re.match(r"(\w+?)-(desktop|mobile|use)\.png$", f)
            if mm and mm.group(2) in opened:
                opened[mm.group(2)].add(mm.group(1))
            elif f.endswith(".html"):
                opened["source_read"].add(f[:-5])
        elif tool == "Bash":
            cmd = inp.get("command", "")
            if ".html" not in cmd and "$f" not in cmd:
                continue
            named = set(re.findall(r"\b([A-Z]\d?)\.html", cmd))
            if "*.html" in cmd or re.search(r"for \w+ in", cmd):
                named |= set(labels)
            opened["source_printed" if PRINTS.search(cmd) else "source_counted"] |= named & set(labels)
    src = opened["source_read"] | opened["source_printed"]
    row = {"task": task, "kind": "quality" if quality else "spread", "grader": name, "designs": len(labels),
           "images_opened": sum(len(opened[k] & set(labels)) for k in kinds), "images_shown": len(labels) * len(kinds),
           "sources_read": len(opened["source_read"] & set(labels)), "sources_opened": len(src),
           "sources_only_counted": len(opened["source_counted"] - src), "tool_uses": len(uses)}
    for k in kinds:
        row[k] = len(opened[k] & set(labels))
    row["complete"] = row["images_opened"] == row["images_shown"] and row["sources_read"] == row["designs"]
    return row


def collect(full=False):
    """{task/folder/name: [one row per attempt, oldest first]} for the registered pass, or for the full-evidence pass."""
    found = {}
    for path in glob.glob(os.path.join(SESSIONS, "*", "subagents", "agent-*.jsonl")):
        prompt, uses = transcript(path)
        m = re.search(r"Write exactly one file, (\S+?/([^/\s]+)/(judgments[\w-]*)/([\w-]+)\.json)", prompt)
        if not m or HERE not in m.group(1):
            continue
        task, folder, name = m.group(2), m.group(3), m.group(4)
        if full != (folder not in REGISTERED):
            continue
        row = row_for(task, folder, name, uses)
        row["transcript"], row["at"] = os.path.basename(path), os.path.getmtime(path)
        found.setdefault("%s/%s/%s" % (task, folder, name), []).append(row)
    return {k: sorted(v, key=lambda r: r["at"]) for k, v in sorted(found.items())}


def main():
    full = len(sys.argv) > 1 and sys.argv[1] == "judgments-full"
    attempts = collect(full)
    out = {k: dict(v[-1], attempts=len(v)) for k, v in attempts.items()}      # the latest attempt is the one whose file stands
    json.dump(out, open(os.path.join(HERE, "grader-audit%s.json" % ("-full" if full else "")), "w"), indent=1)
    for k, r in out.items():
        print("%-44s pictures %2d/%2d (%s)  sources read %2d/%2d, printed by a shell command %d, only counted %d%s%s" % (
            k, r["images_opened"], r["images_shown"], " ".join("%s %d" % (x, r[x]) for x in ("desktop", "mobile", "use") if x in r),
            r["sources_read"], r["designs"], r["sources_opened"] - r["sources_read"], r["sources_only_counted"],
            "  COMPLETE" if r["complete"] else "", "  attempt %d" % r["attempts"] if r["attempts"] > 1 else ""))
    for kind in ("quality", "spread"):
        q = [r for r in out.values() if r["kind"] == kind]
        if not q:
            continue
        print("%s graders: %d (%d complete); pictures opened %d of %d; sources read %d of %d, printed by a shell command %d more" % (
            kind, len(q), sum(r["complete"] for r in q), sum(r["images_opened"] for r in q), sum(r["images_shown"] for r in q),
            sum(r["sources_read"] for r in q), sum(r["designs"] for r in q), sum(r["sources_opened"] - r["sources_read"] for r in q)))
        for pic in ("desktop", "mobile", "use"):
            if pic in q[0]:
                print("   %s pictures opened %d of %d" % (pic, sum(r[pic] for r in q), sum(r["designs"] for r in q)))


if __name__ == "__main__":
    main()
