#!/usr/bin/env python3
"""One picture per task: the twelve builds' desktop screenshots, a row per arm, with each build's mean overall score from the
registered grades and from the full-evidence pass. For people; no grader sees it. Usage: python3 overview.py
Writes <task>/overview.png."""
import json, os, pathlib, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "metadump", "scripts"))
import cdp  # noqa: E402

TASKS = {"t1-pelican": "an SVG animation of a pelican riding a bike", "t2-ascii": "a simple interactive ascii color mixing engine",
         "t3-bento": "a bento box-inspired collapsible UI menu component for a fictional coffee company site",
         "t4-blocks": "a simple block-building sandbox game with a 32x32 block world"}
ARMS = [("A", "A: the prompt alone"), ("F", "F: the full build (a lite dump from the swarm)"), ("Q", "Q: quick mode (the builder's own one-pass dump)")]


def main():
    for task, prompt in TASKS.items():
        d = os.path.join(HERE, task)
        reg = json.load(open(os.path.join(d, "results.json")))["scores"]
        full = json.load(open(os.path.join(d, "results-full.json")))["scores"]
        rows = []
        for arm, name in ARMS:
            cells = []
            for n in range(1, 5):
                run = "%s-r%d" % (arm, n)
                shot = pathlib.Path(os.path.join(d, "shots", run + "-desktop.png")).as_uri()
                cells.append('<figure><img src="%s"><figcaption>%s &nbsp; %s registered, %s full evidence</figcaption></figure>'
                             % (shot, run, reg[arm]["per_run_overall"][run], full[arm]["per_run_overall"][run]))
            rows.append('<h2>%s &nbsp; mean %s registered, %s full evidence</h2><div class="row">%s</div>'
                        % (name, reg[arm]["overall"], full[arm]["overall"], "".join(cells)))
        html = ('<!doctype html><meta charset="utf-8"><style>body{margin:0;padding:18px 20px 24px;background:#fff;color:#111;'
                'font:15px/1.4 system-ui,sans-serif}h1{font-size:19px;margin:0 0 4px}p{margin:0 0 6px;color:#444}'
                'h2{font-size:15px;margin:16px 0 6px}.row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}figure{margin:0}'
                'img{display:block;width:100%%;border:1px solid #999}figcaption{padding-top:3px;font-size:13px}</style>'
                '<h1>Confirmation test: "%s"</h1><p>Each build at rest on a desktop screen, with its mean overall score of 10 from three '
                'blind graders, twice: the registered grades, and the pass by graders who opened every file.</p>%s' % (prompt, "".join(rows)))
        src = os.path.join(tempfile.mkdtemp(prefix="overview-"), "overview.html")
        with open(src, "w", encoding="utf-8") as f:
            f.write(html)
        with cdp.Browser(width=1600, height=1000) as browser:
            page = browser.new_page()
            page.set_viewport(1600, 1000)
            page.navigate(pathlib.Path(src).as_uri(), settle=0.8)
            with open(os.path.join(d, "overview.png"), "wb") as f:
                f.write(page.screenshot(full_page=True))
        print(task, "overview.png written")


if __name__ == "__main__":
    main()
