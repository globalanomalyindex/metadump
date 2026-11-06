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
    "t1-button": "The meta dump side scored higher on practical (8.1 vs 6.1): focus states, reduced motion, cheap properties.",
    "t2-sandbox": "Better physics on the meta dump side (7.8 vs 5.9), but the prompt-only builds explained themselves better (clarity 7.8 vs 4.7).",
    "t3-poem": "The meta dump side won 23 of 24 blind head-to-heads (p = 0.03).",
    "t4-figma": "3 of 4 prompt-only builds rebuilt Figma's logo, which graders marked down. No meta dump build did.",
}
TASKS = [
    ("t1-button", "Dreamlike button", "a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website", "html", "hover"),
    ("t2-sandbox", "Physics sandbox", "a 2D physics sandbox where you can drag boxes around", "html", "drag"),
    ("t3-poem", "Rare-cloud poem", "a short poem about rare clouds, ending with a question", "text", None),
    ("t4-figma", "Figma-style loop", "a 5 second looping animation in the style of Figma brand visuals", "html", "watch"),
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
