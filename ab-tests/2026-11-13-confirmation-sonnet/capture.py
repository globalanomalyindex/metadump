#!/usr/bin/env python3
"""Capture what the graders see, the same way for every task and arm (design.md), and run each task's scripted checks.
Usage: python3 capture.py <task> [run ...]
Writes <task>/shots/<run>-{desktop,mobile,interact}.png and <task>/functional.json.
  The strip: frames untouched at 0, 2, 6 and 20 seconds, then after each of the page's first three controls is used in
  page order (a click, a slide, a choice, typed text or a drag across a canvas, as the look would use it).
It drives the browser through the frozen skill's cdp.py and play.py."""
import json, os, pathlib, re, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "metadump", "scripts"))
import cdp, pixels, play  # noqa: E402

TASK = sys.argv[1]
DIR = os.path.join(HERE, TASK)
DESKTOP, PHONE = (1280, 800), (390, 844)
BRANDS = ["Starbucks", "Dunkin", "Costa", "Nespresso", "Nescafé", "Nescafe", "Peet's", "Tim Hortons", "Blue Bottle", "Lavazza", "Illy",
          "Folgers", "Maxwell House", "Caribou", "Dutch Bros", "Intelligentsia", "Stumptown", "Philz", "La Colombe", "Tully's",
          "Gloria Jean's", "McCafé", "McCafe", "Keurig"]


GAMES = ["Minecraft", "Mojang", "Creeper", "Terraria", "Roblox", "LEGO"]


def share(a, b):
    """Percent of pixels that differ between two small frames."""
    ia, ib = pixels.decode_png(a), pixels.decode_png(b)
    if (ia.width, ia.height) != (ib.width, ib.height):
        return 100.0
    n = sum(1 for y in range(ia.height) for x in range(ia.width)
            if sum(abs(p - q) for p, q in zip(ia.pixel(x, y)[:3], ib.pixel(x, y)[:3])) > 24)
    return round(100.0 * n / (ia.width * ia.height), 2)


def strip(page, frames, title, out):
    """Lay the frames out in rows with captions, in the browser, and save the picture."""
    tmp = tempfile.mkdtemp(prefix="strip-")
    tiles = []
    for i, (data, cap) in enumerate(frames):
        with open(os.path.join(tmp, "f%d.png" % i), "wb") as f:
            f.write(data)
        cap = cap.replace("&", "&amp;").replace("<", "&lt;")
        tiles.append('<figure><img src="f%d.png"><figcaption>%d. %s</figcaption></figure>' % (i, i + 1, cap))
    html = ('<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#fff;color:#111;font:15px/1.4 system-ui,sans-serif}'
            'h1{font-size:15px;font-weight:600;margin:10px 12px 0}main{display:flex;flex-wrap:wrap;gap:12px;padding:12px}figure{margin:0}'
            'img{display:block;width:620px;border:1px solid #999}figcaption{padding-top:3px}</style><h1>%s</h1><main>%s</main>' % (title, "".join(tiles)))
    src = os.path.join(tmp, "strip.html")
    with open(src, "w", encoding="utf-8") as f:
        f.write(html)
    page.set_viewport(1280, 800)
    page.navigate(pathlib.Path(src).as_uri(), settle=0.3)
    with open(out, "wb") as f:
        f.write(page.screenshot(full_page=True))


def controls(page, n=3):
    """The page's first n controls in page order, as the look sees them."""
    acts = page.evaluate("typeof __look === 'object' ? __look.actionables() : null") or []
    return [a for a in acts if not a["disabled"] and a["kind"] != "skip" and a["w"] >= 4 and a["h"] >= 4][:n]


def frames_for(page, res):
    small = lambda: play.frame(page)
    frames = [(page.screenshot(), "at rest")]
    f0 = small()
    time.sleep(2.0); frames.append((page.screenshot(), "untouched, 2 s")); f2 = small()
    time.sleep(4.0); frames.append((page.screenshot(), "untouched, 6 s"))
    time.sleep(14.0); frames.append((page.screenshot(), "untouched, 20 s")); f20 = small()
    time.sleep(2.0); f22 = small()
    res["change_0_to_2s_pct"], res["change_20_to_22s_pct"] = share(f0, f2), share(f20, f22)
    used, last = [], f22
    for a in controls(page):
        did = play._perform(page, a)
        if did is None:
            continue
        time.sleep(0.6)
        now = small()
        used.append({"control": a["label"] or a["show"], "kind": a["kind"], "verb": did[0], "change_pct": share(last, now)})
        frames.append((page.screenshot(), '%s "%s"' % (did[0], (a["label"] or a["show"])[:40])))
        last = now
    res["controls_used"] = used
    return frames


# ---- scripted checks, one set per task (design.md) ----
PELICAN_JS = r"""(() => { const vw = innerWidth, vh = innerHeight; let best = null, area = 0;
  for (const el of document.querySelectorAll('svg, canvas, img')) {
    if (el.closest('svg') && el.closest('svg') !== el) continue;
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const w = Math.min(r.right, vw) - Math.max(r.left, 0), h = Math.min(r.bottom, vh) - Math.max(r.top, 0);
    if (w > 0 && h > 0 && w * h > area) { area = w * h; best = el.tagName.toLowerCase(); } }
  return {largest: best, share: area / (vw * vh), canvas: document.querySelectorAll('canvas').length,
          img: document.querySelectorAll('img').length, image: document.querySelectorAll('svg image').length}; })()"""
ASCII_JS = r"""(() => { let chars = 0, canvas = 0;
  for (const el of document.body.querySelectorAll('*')) {
    const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    if (el.tagName === 'CANVAS') { canvas = Math.max(canvas, r.width * r.height / (innerWidth * innerHeight)); continue; }
    const mono = ['PRE', 'CODE', 'SAMP', 'KBD', 'TEXTAREA'].includes(el.tagName) || /mono|courier|consolas|menlo/i.test(cs.fontFamily);
    if (!mono) continue;
    const own = el.tagName === 'TEXTAREA' ? el.value : [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.nodeValue).join('');
    chars += own.replace(/\s/g, '').length; }
  return {mono_chars: chars, canvas_share: canvas}; })()"""
BENTO_JS = r"""(() => { const t = document.querySelector('[aria-expanded], summary');
  let grid = 0;
  for (const el of document.body.querySelectorAll('*')) { const d = getComputedStyle(el).display;
    if ((d === 'grid' || d === 'inline-grid') && el.children.length > grid) grid = el.children.length; }
  const state = () => t ? (t.getAttribute('aria-expanded') || String(!!(t.closest('details') || {}).open)) + '|' + document.documentElement.scrollHeight : null;
  window.__bentoState = state;
  return {toggle: t ? (t.tagName.toLowerCase() + (t.id ? '#' + t.id : '')) : null, focusable: t ? t.tabIndex >= 0 : false, grid_children: grid,
          text: document.body.innerText}; })()"""


def checks(page, url, res, src):
    fresh = lambda: (page.navigate(url, settle=0.6), play.errors(page))
    out = {}
    if TASK == "t1-pelican":
        fresh(); d = page.evaluate(PELICAN_JS)
        out["svg_main"] = d["largest"] == "svg"
        out["no_raster"] = d["canvas"] == 0 and d["img"] == 0 and d["image"] == 0
        out["animates"] = res["change_0_to_2s_pct"] > 0.02
        out["still_animating"] = res["change_20_to_22s_pct"] > 0.02
        res["pelican"] = d
    elif TASK == "t2-ascii":
        fresh(); d = page.evaluate(ASCII_JS)
        out["responds"] = any(u["change_pct"] > 0.3 for u in res["controls_used"]) if res["controls_used"] else None
        out["ascii_text"] = None if (d["mono_chars"] < 40 and d["canvas_share"] > 0.1) else d["mono_chars"] >= 40
        out["no_script_errors"] = res["js_errors"] == 0
        res["ascii"] = d
    elif TASK == "t3-bento":
        fresh(); d = page.evaluate(BENTO_JS)
        before = page.evaluate("__bentoState()")
        out["collapses"] = out["keyboard"] = None if d["toggle"] is None else False
        if d["toggle"]:
            f0 = play.frame(page)
            at = page.evaluate("(() => { const t = document.querySelector('[aria-expanded], summary'); t.scrollIntoView({block: 'center'}); "
                               "const r = t.getBoundingClientRect(); return {x: r.left + r.width / 2, y: r.top + r.height / 2}; })()")
            f0 = play.frame(page)
            play.click(page, at["x"], at["y"]); time.sleep(0.7)
            out["collapses"] = page.evaluate("__bentoState()") != before or share(f0, play.frame(page)) > 0.3
            fresh(); page.evaluate(BENTO_JS); before = page.evaluate("__bentoState()")
            if d["focusable"]:
                toggled = False
                for key in ("Enter", "Space"):
                    page.evaluate("document.querySelector('[aria-expanded], summary').focus()")
                    f1 = play.frame(page)
                    play.press(page, key); time.sleep(0.7)
                    if page.evaluate("__bentoState()") != before or share(f1, play.frame(page)) > 0.3:
                        toggled = True
                        break
                out["keyboard"] = toggled
        out["grid"] = d["grid_children"] >= 4
        named = [b for b in BRANDS if re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(b), d["text"] + " " + src, re.I)]
        out["fictional"] = not named
        res["bento"] = {"toggle": d["toggle"], "focusable": d["focusable"], "grid_children": d["grid_children"], "brands_named": named}
    elif TASK == "t4-blocks":
        fresh(); text = page.evaluate("document.body.innerText") or ""
        out["responds"] = any(u["change_pct"] > 0.3 for u in res["controls_used"]) if res["controls_used"] else None
        out["no_script_errors"] = res["js_errors"] == 0
        out["world_32"] = bool(re.search(r"(?<![\w.#])32(?![\w.])", src))
        named = [g for g in GAMES if re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(g), text + " " + src, re.I)]
        out["own_game"] = not named
        res["blocks"] = {"games_named": named}
    res["checks"] = out
    res["passed"] = sum(1 for v in out.values() if v is True)
    res["failed"] = sum(1 for v in out.values() if v is False)
    res["not_run"] = sum(1 for v in out.values() if v is None)


def main():
    runs = sys.argv[2:] or sorted(f[:-5] for f in os.listdir(os.path.join(DIR, "runs")) if f.endswith(".html"))
    os.makedirs(os.path.join(DIR, "shots"), exist_ok=True)
    fpath = os.path.join(DIR, "functional.json")
    results = json.load(open(fpath)) if os.path.exists(fpath) else {}
    for run in runs:
        path = os.path.join(DIR, "runs", run + ".html")
        url = pathlib.Path(path).resolve().as_uri()
        src = open(path, encoding="utf-8", errors="replace").read()
        res = {"bytes": len(src)}
        with cdp.Browser(width=DESKTOP[0], height=DESKTOP[1]) as browser:
            page = browser.new_page()
            play.install(page)
            page.set_viewport(PHONE[0], PHONE[1], mobile=True)
            page.navigate(url, settle=0.8)
            with open(os.path.join(DIR, "shots", run + "-mobile.png"), "wb") as f:
                f.write(page.screenshot())
            page.set_viewport(DESKTOP[0], DESKTOP[1])
            page.navigate(url, settle=0.8)
            play.errors(page)
            with open(os.path.join(DIR, "shots", run + "-desktop.png"), "wb") as f:
                f.write(page.screenshot())
            frames = frames_for(page, res)
            errs = play.errors(page)
            res["js_errors"] = len(errs)
            res["js_error_text"] = [e[:160] for e in errs[:2]]
            checks(page, url, res, src)
            strip(page, frames, "untouched at 0, 2, 6 and 20 s, then its first three controls used in page order",
                  os.path.join(DIR, "shots", run + "-interact.png"))
        results[run] = res
        print(run, json.dumps({k: v for k, v in res.items() if k not in ("bento", "pelican", "ascii", "blocks")})[:600])
    json.dump(results, open(fpath, "w"), indent=1)


if __name__ == "__main__":
    main()
