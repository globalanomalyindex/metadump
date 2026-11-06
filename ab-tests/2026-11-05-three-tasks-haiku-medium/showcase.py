#!/usr/bin/env python3
"""Build the live side-by-side showcase into docs/showcase/ (served by GitHub Pages from /docs).

Copies every run (HTML tasks) or rendered card (text tasks) into docs/showcase/<task>/, reads each task's
results.json, and writes docs/showcase/index.html (the GitHub preview) and docs/showcase/scene.html
(a 1080x1350 frame the recorder films for LinkedIn). Run 1 of each arm is featured; it was chosen before grading.
Usage: python3 showcase.py
"""
import html, json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "docs", "showcase")
# One line per task, written after unblinding from results.json and the grader notes.
NOTES = {
    "t1-button": "The meta dump side scored higher on practical (8.4 vs 6.2) and motion (7.9 vs 6.3), though all four of its builds reused the same four curves from the dump.",
    "t2-haiku": "The prompt-only haiku kept a strict 5-7-5 and won on form (9.4 vs 5.6); the meta dump side reached four different rare clouds.",
    "t3-toast": "The meta dump side won all 24 blind head-to-heads (8.6 vs 5.0).",
}
TASKS = [
    ("t1-button", "Dreamlike button", "a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website", "html", "hover"),
    ("t2-haiku", "Rare-cloud haiku", "a haiku about rare clouds", "text", None),
    ("t3-toast", "Dark package toast", "a dark mode, very compact collapsible toast UI menu for tracking a package", "html", "click"),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(ROOT, "docs", ".nojekyll"), "w").close()
    data = []
    for slug, title, prompt, kind, interaction in TASKS:
        src_dir = os.path.join(HERE, slug, "runs" if kind == "html" else "cards")
        dst = os.path.join(OUT, slug)
        os.makedirs(dst, exist_ok=True)
        runs = sorted(f[:-5] for f in os.listdir(src_dir) if f.endswith(".html"))
        for r in runs:
            shutil.copy(os.path.join(src_dir, r + ".html"), os.path.join(dst, r + ".html"))
        res_path = os.path.join(HERE, slug, "results.json")
        res = json.load(open(res_path)) if os.path.exists(res_path) else None
        scores = None
        if res:
            scores = {"A": res["scores"]["A"]["overall"], "B": res["scores"]["B"]["overall"], "win_rate": res["pairwise"]["win_rate"],
                      "wins": res["pairwise"]["wins"], "losses": res["pairwise"]["losses"], "ties": res["pairwise"]["ties"],
                      "p": (res.get("permutation") or {}).get("p"),
                      "A_runs": res["scores"]["A"]["per_run_overall"], "B_runs": res["scores"]["B"]["per_run_overall"]}
        data.append({"slug": slug, "title": title, "prompt": prompt, "kind": kind, "interaction": interaction,
                     "runs": {"A": [r for r in runs if r.startswith("A-")], "B": [r for r in runs if r.startswith("B-")]}, "scores": scores,
                     "note": NOTES.get(slug)})
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    pooled_path = os.path.join(HERE, "pooled.json")
    pooled = json.dumps(json.load(open(pooled_path)) if os.path.exists(pooled_path) else None)
    for name in ("index.html", "scene.html"):
        tpl = open(os.path.join(HERE, "showcase-" + name)).read()
        open(os.path.join(OUT, name), "w").write(tpl.replace("/*__DATA__*/[]", blob).replace("/*__POOLED__*/null", pooled))
    print("wrote", OUT, [d["slug"] for d in data])


if __name__ == "__main__":
    main()
