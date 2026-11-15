#!/usr/bin/env python3
"""Capture what the graders see for the two HTML tasks, in the local headless browser.
Usage: python3 capture.py t2-pomodoro|t3-snowglobe [run ...]
Writes <task>/shots/<run>-{desktop,mobile,interact}.png and <task>/functional.json.
  t2-pomodoro:  at rest, then start, 2 s and 4 s on, pause, 1.6 s later, reset. Whether the time falls after start,
                holds while paused and returns on reset.
  t3-snowglobe: frames over 1.4 s untouched, then three quick drags across the globe (a shake), 0.4 s and 1.5 s after,
                then a click. How much of the picture changes untouched and after the shake.
The same script and the same steps for every arm. It drives the browser through the skill's cdp.py."""
import json, os, pathlib, re, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "metadump", "scripts"))
import cdp, pixels, play  # noqa: E402

TASK = sys.argv[1]
DIR = os.path.join(HERE, TASK)
DESKTOP, PHONE = (1280, 800), (390, 844)
START = re.compile(r"start|begin|play|resume|go\b|▶|►", re.I)
PAUSE = re.compile(r"pause|stop|hold|⏸|❚❚|\|\|", re.I)
RESET = re.compile(r"reset|restart|↺|⟲|↻|clear", re.I)
TIME_JS = r"""(() => { let best = null, size = 0;
  for (const el of document.body.querySelectorAll('*')) {
    const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.nodeValue).join('');
    const text = /\d{1,2}\s*:\s*\d{2}/.test(own) ? own : (el.children.length <= 4 && /^\s*\d{1,2}\s*:\s*\d{2}\s*$/.test(el.innerText || '') ? el.innerText : null);
    if (!text) continue;
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs > size) { size = fs; best = text.match(/\d{1,2}\s*:\s*\d{2}/)[0].replace(/\s/g, ''); } }
  return best; })()"""


def seconds(t):
    if not t:
        return None
    m, s = t.split(":")
    return int(m) * 60 + int(s)


def find(page, pattern, avoid=None):
    for a in page.evaluate("__look.actionables()") or []:
        if a["kind"] == "click" and not a["disabled"] and pattern.search(a["label"] or "") and not (avoid and avoid.search(a["label"] or "")):
            return a
    return None


def tap(page, a):
    at = page.evaluate("__look.locate(%s)" % json.dumps(a["key"]))
    if at:
        play.click(page, at["x"], at["y"])
    return bool(at)


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


def pomodoro(page, res):
    frames = [(page.screenshot(), "at rest")]
    t0 = page.evaluate(TIME_JS)
    start = find(page, START, avoid=RESET) or find(page, re.compile("."), avoid=RESET)
    res["start_found"] = bool(start and tap(page, start))
    time.sleep(2.2)
    t1 = page.evaluate(TIME_JS); frames.append((page.screenshot(), "2 s after pressing %s" % (('"%s"' % start["label"]) if start else "start")))
    time.sleep(2.2)
    t2 = page.evaluate(TIME_JS); frames.append((page.screenshot(), "4 s after start"))
    pause = find(page, PAUSE, avoid=RESET) or start
    res["pause_found"] = bool(pause and tap(page, pause))
    time.sleep(0.4)
    tp1 = page.evaluate(TIME_JS); frames.append((page.screenshot(), "just after pressing %s" % (('"%s"' % pause["label"]) if pause else "pause")))
    time.sleep(1.6)
    tp2 = page.evaluate(TIME_JS); frames.append((page.screenshot(), "1.6 s later, still paused"))
    reset = find(page, RESET)
    res["reset_found"] = bool(reset and tap(page, reset))
    time.sleep(0.5)
    tr = page.evaluate(TIME_JS); frames.append((page.screenshot(), "after pressing %s" % (('"%s"' % reset["label"]) if reset else "reset (none found)")))
    res["times"] = {"rest": t0, "after_2s": t1, "after_4s": t2, "paused": tp1, "paused_later": tp2, "after_reset": tr}
    s = {k: seconds(v) for k, v in res["times"].items()}
    res["counts_down"] = None not in (s["rest"], s["after_4s"]) and 2 <= s["rest"] - s["after_4s"] <= 6
    res["holds_when_paused"] = None not in (s["paused"], s["paused_later"]) and s["paused"] == s["paused_later"]
    res["reset_restores"] = None not in (s["rest"], s["after_reset"]) and s["rest"] == s["after_reset"]
    res["works"] = bool(res["counts_down"] and res["holds_when_paused"] and res["reset_restores"])
    return frames, "a scripted use: start, 2 s and 4 s on, pause, 1.6 s later, reset"


def snowglobe(page, res, src):
    res["renderer"] = ("webgl" if re.search(r"getContext\(\s*['\"](experimental-)?webgl", src) else "canvas2d" if re.search(r"getContext\(\s*['\"]2d", src)
                       else "svg" if re.search(r"<svg", src, re.I) else "css")
    small = lambda: play.frame(page)
    frames = [(page.screenshot(), "at rest")]
    f0 = small()
    time.sleep(0.7); frames.append((page.screenshot(), "untouched +0.7 s")); f1 = small()
    time.sleep(0.7); frames.append((page.screenshot(), "untouched +1.4 s")); f2 = small()
    mv = page.evaluate("__look.mainVisual()")
    at = page.evaluate("__look.locate(%s)" % json.dumps(mv["key"])) if mv else None
    if not at:
        at = {"x": DESKTOP[0] / 2, "y": DESKTOP[1] / 2, "w": 400, "h": 400}
    res["main_visual"] = mv["show"] if mv else None
    span = min(140, at["w"] * 0.3)
    for dx in (span, -span, span):                      # a shake: three quick drags across it
        play.drag(page, at["x"] - dx / 2, at["y"], dx, 0, steps=5)
    frames.append((page.screenshot(), "just after three quick drags across it (a shake)")); f3 = small()
    time.sleep(0.4); frames.append((page.screenshot(), "0.4 s after the shake")); f4 = small()
    time.sleep(1.1); frames.append((page.screenshot(), "1.5 s after the shake"))
    play.click(page, at["x"], at["y"])
    time.sleep(0.5); frames.append((page.screenshot(), "0.5 s after a click on it")); f5 = small()
    res["untouched_change_pct"] = share(f0, f2)
    res["shake_change_pct"] = max(share(f2, f3), share(f2, f4))
    res["click_change_pct"] = share(f4, f5)
    res["moves_untouched"] = res["untouched_change_pct"] > 0.05
    res["changes_when_shaken"] = res["shake_change_pct"] > max(0.3, 1.5 * res["untouched_change_pct"])
    res["works"] = bool(res["moves_untouched"] or res["changes_when_shaken"])
    return frames, "frames untouched, then three quick drags across it (a shake), then a click"


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
            frames, how = pomodoro(page, res) if TASK == "t2-pomodoro" else snowglobe(page, res, src)
            errs = play.errors(page)
            res["js_errors"] = len(errs)
            res["js_error_text"] = [e[:160] for e in errs[:2]]
            res["works"] = bool(res.get("works")) and not errs
            strip(page, frames, "%s" % how, os.path.join(DIR, "shots", run + "-interact.png"))
        results[run] = res
        print(run, json.dumps(res))
    json.dump(results, open(fpath, "w"), indent=1)


if __name__ == "__main__":
    main()
