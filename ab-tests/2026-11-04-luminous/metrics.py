#!/usr/bin/env python3
"""Objective metrics per run. Clause list comes from the user's prompt only, never from either dump."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CLAUSES = {  # the user's own prompt, split into clauses; each with regexes for its plain-language variants
    "blue acrylic/vinyl": [r"acrylic", r"vinyl"],
    "overexposed whites": [r"overexpos", r"high[- ]key", r"bloom", r"halation", r"blown[- ]out"],
    "blue-tinted whites": [r"blue[- ]tinted white", r"blue[- ]white", r"cool white", r"ice[- ]white", r"white.{0,20}tint(ed)? (of |with )?blue"],
    "electric green grass": [r"green grass", r"grass"],
    "saturated blue sky": [r"blue sky", r"\bsky\b"],
    "frutiger aero / y2k": [r"frutiger", r"\baero\b", r"y2k"],
    "color inside the material": [r"inside the material", r"within the material", r"through the material", r"transmi", r"subsurface", r"thickness", r"light passes through", r"internal glow"],
}
NEG = re.compile(r"\b(no|not|without|avoid|never|don't|isn't)\b", re.I)


def section(text, label):
    m = re.search(r"%s\W*[:\n](.*?)(?=\n\s*(\*\*|#+|[A-Z]{4,}\b)|\Z)" % label, text, re.S | re.I)
    return m.group(1) if m else ""


def flux_prompt(text):
    # the prompt is the longest paragraph before any notes heading
    body = re.split(r"\n\s*(#+\s*)?(\*\*)?notes?\b", text, flags=re.I)[0]
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if len(p.split()) > 20]
    return max(paras, key=len) if paras else body


def metrics(task, text):
    low = text.lower()
    m = {"words": len(text.split())}
    covered = [c for c, pats in CLAUSES.items() if any(re.search(p, low) for p in pats)]
    m["clause_coverage"] = round(len(covered) / len(CLAUSES), 2)
    m["clauses_missing"] = [c for c in CLAUSES if c not in covered]
    if task.startswith("t1"):
        p = flux_prompt(text)
        m["flux_prompt_words"] = len(p.split())
        m["negations_in_flux_prompt"] = len(NEG.findall(p))  # FLUX.2 has no negative prompt; negations can backfire
    if task.startswith("t2"):
        neg = section(text, "NEGATIVE")
        m["has_negative"] = bool(neg.strip())
        m["negative_terms"] = len([t for t in re.split(r",", neg) if t.strip()])
        m["negations_in_positive"] = len(NEG.findall(section(text, "POSITIVE")))
    if task.startswith("t3"):
        m["backdrop_filter_uses"] = len(re.findall(r"backdrop-filter", text))
        m["reduced_motion"] = "prefers-reduced-motion" in text
        m["bytes"] = len(text.encode())
    if task.startswith("t4"):
        m["list_items"] = len(re.findall(r"^\s*(\d+[.)]|[-*])\s", text, re.M))
    return m


def main():
    out = {}
    for task in sorted(os.listdir(os.path.join(ROOT, "runs"))):
        for f in sorted(os.listdir(os.path.join(ROOT, "runs", task))):
            with open(os.path.join(ROOT, "runs", task, f), encoding="utf-8") as fh:
                out["%s/%s" % (task, os.path.splitext(f)[0])] = metrics(task, fh.read())
    json.dump(out, open(os.path.join(ROOT, "metrics.json"), "w"), indent=1)
    print(json.dumps(out, indent=1)[:3000])


if __name__ == "__main__":
    main()
