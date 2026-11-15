#!/usr/bin/env python3
"""Post hoc, and not one of the pre-registered checks: for a block-world build whose scripted `responds` check failed, click and
drag on the world itself and say how much of the picture changed. The scripted check uses only a page's first three controls in
page order (design.md); on some builds those are three palette buttons, which change a few pixels of highlight and nothing else.
Usage: python3 handcheck.py <task> <run> [run ...]   Writes <task>/handcheck.json."""
import json, os, pathlib, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "metadump", "scripts"))
import cdp, play  # noqa: E402
from capture import share  # noqa: E402  (capture.py reads sys.argv[1] as the task, as this script does)

WORLD_JS = r"""(() => { let best = null, area = 0;
  for (const el of document.body.querySelectorAll('canvas, svg, *')) {
    const big = el.tagName === 'CANVAS' || el.tagName === 'svg' || el.children.length >= 256;
    if (!big) continue;
    const r = el.getBoundingClientRect(); const a = r.width * r.height;
    if (a > area) { area = a; best = r; } }
  return best ? {x: best.left, y: best.top, w: best.width, h: best.height} : null; })()"""


def main():
    task, runs = sys.argv[1], sys.argv[2:]
    out_path = os.path.join(HERE, task, "handcheck.json")
    out = json.load(open(out_path)) if os.path.exists(out_path) else {}
    for run in runs:
        url = pathlib.Path(os.path.join(HERE, task, "runs", run + ".html")).resolve().as_uri()
        with cdp.Browser(width=1280, height=800) as browser:
            page = browser.new_page()
            play.install(page)
            page.navigate(url, settle=0.8)
            play.errors(page)
            box = page.evaluate(WORLD_JS)
            res = {"world_box": box}
            if box:
                before = play.frame(page)
                for fx, fy in ((0.5, 0.3), (0.3, 0.6), (0.7, 0.7)):
                    play.click(page, box["x"] + box["w"] * fx, box["y"] + box["h"] * fy)
                    time.sleep(0.3)
                after = play.frame(page)
                res["change_after_three_clicks_on_world_pct"] = share(before, after)
            res["js_errors"] = len(play.errors(page))
        out[run] = res
        print(run, json.dumps(res))
    json.dump(out, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main()
