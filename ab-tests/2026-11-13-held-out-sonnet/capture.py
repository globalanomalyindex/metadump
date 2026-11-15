#!/usr/bin/env python3
"""Capture what the graders see for the two HTML tasks, in the local headless browser.
Usage: python3 capture.py t1-lavalamp|t2-calculator [run ...]
Writes <task>/shots/<run>-{desktop,mobile,interact}.png and <task>/functional.json.
  t1-lavalamp:   frames untouched at 0, 2, 4 and 6 s, then after a click on the lamp, then after its first control.
                 How much of the picture changes untouched and after each.
  t2-calculator: the nine scripted checks in design.md, each from a fresh load, with frames of five of them.
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


LAMP_JS = r"""(() => { let best = null, area = 0;
  for (const el of document.querySelectorAll('canvas, svg')) {
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    if (r.width < 40 || r.height < 40 || cs.display === 'none' || cs.visibility === 'hidden') continue;
    const w = Math.min(r.right, innerWidth) - Math.max(r.left, 0), h = Math.min(r.bottom, innerHeight) - Math.max(r.top, 0);
    if (w * h > area) { area = w * h; best = {x: Math.max(r.left, 0) + w / 2, y: Math.max(r.top, 0) + h / 2, drawn: el.tagName.toLowerCase()}; } }
  return best; })()"""


def lavalamp(page, res, src):
    res["renderer"] = ("webgl" if re.search(r"getContext\(\s*['\"](experimental-)?webgl", src) else "canvas2d" if re.search(r"getContext\(\s*['\"]2d", src)
                       else "svg" if re.search(r"<svg", src, re.I) else "css")
    small = lambda: play.frame(page)
    frames = [(page.screenshot(), "at rest")]
    f0 = small()
    for t in (2, 4, 6):
        time.sleep(2.0); frames.append((page.screenshot(), "untouched +%d s" % t))
    f6 = small()
    mv = None
    at = page.evaluate(LAMP_JS) or {"x": DESKTOP[0] / 2, "y": DESKTOP[1] / 2, "drawn": None}
    res["main_visual"] = at["drawn"]          # a lamp is tall and narrow, so the look's own main-visual test (12% of the screen) misses it
    play.click(page, at["x"], at["y"])
    time.sleep(0.5); frames.append((page.screenshot(), "0.5 s after a click on the lamp")); f7 = small()
    time.sleep(2.0); frames.append((page.screenshot(), "2.5 s after the click")); f8 = small()
    control = next((a for a in page.evaluate("__look.actionables()") or []
                    if a["kind"] == "click" and not a["disabled"] and not (mv and a["key"] == mv["key"])), None)
    res["first_control"] = control["label"] if control else None
    f10 = f8
    if control and tap(page, control):
        time.sleep(0.5); frames.append((page.screenshot(), 'the first control, "%s": 0.5 s after pressing it' % control["label"]))
        time.sleep(2.0); frames.append((page.screenshot(), "2.5 s after pressing it")); f10 = small()
    res["untouched_change_pct"] = share(f0, f6)
    res["click_change_pct"] = max(share(f6, f7), share(f6, f8))
    res["control_change_pct"] = share(f8, f10)
    res["moves_untouched"] = res["untouched_change_pct"] > 0.05
    res["works"] = bool(res["moves_untouched"] or res["click_change_pct"] > 0.3 or res["control_change_pct"] > 0.3)
    return frames, "frames untouched over 6 s, then a click on the lamp, then its first control"


# ---- the calculator: nine scripted checks, the same for every build (design.md) ----
WORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"}
KEY = {"+": r"\+|plus|add|addition", "-": r"-|−|–|—|minus|subtract|subtraction", "*": r"×|x|\*|✕|✖|⨯|times|multiply|multiplication|multiplied by",
       "/": r"÷|/|∕|divide|division|divided by", "=": r"=|equals?|calculate|result", ".": r"\.|,|decimal|decimal point|point|dot",
       "C": r"ac|all clear|clear all|c|clear|reset|ce|clear entry"}
CLEAR_ORDER = ["ac", "all clear", "clear all", "c", "clear", "reset", "ce", "clear entry"]
# Mark the display: the largest text that reads exactly `want`, outside any key. Returns a path of child indexes from <body>.
FIND_DISPLAY = r"""((want) => { let best = null, size = 0;
  for (const el of document.body.querySelectorAll('*')) {
    if (el.closest('button, [role="button"], a, script, style')) continue;
    const field = ['INPUT', 'TEXTAREA', 'OUTPUT'].includes(el.tagName);
    let text = field ? (el.value || el.textContent) : [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.nodeValue).join('');
    if ((text || '').replace(/\s/g, '') !== want) continue;
    const r = el.getBoundingClientRect(); if (r.width <= 2 || r.height <= 2) continue;     // not a screen-reader-only region
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs > size) { size = fs; best = el; } }
  // A display drawn as segments has no text of its own: read what it announces instead.
  if (!best) best = document.querySelector('[aria-live], [role="status"], output');
  if (!best) return null;
  const path = []; for (let el = best; el !== document.body; el = el.parentElement) path.unshift([...el.parentElement.children].indexOf(el));
  return path; })"""
# Read the display at that path: its text, and whether the text sits wholly inside it.
READ_DISPLAY = r"""((path) => { let el = document.body;
  for (const i of path) { el = el && el.children[i]; }
  if (!el) return null;
  const field = ['INPUT', 'TEXTAREA', 'OUTPUT'].includes(el.tagName) && el.value !== undefined && el.tagName !== 'OUTPUT';
  const text = (field ? el.value : el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
  const box = el.getBoundingClientRect(); let ink = box;
  if (box.width <= 2 || box.height <= 2) {      // an announcement: judge the drawn digits around it by their own boxes
    const win = el.parentElement, wr = win.getBoundingClientRect(); let inside = true;
    for (const d of win.querySelectorAll('*')) { const r = d.getBoundingClientRect();
      if (r.width <= 2 || r.height <= 2 || d === el) continue;
      if (r.left < wr.left - 1 || r.right > wr.right + 1 || r.top < wr.top - 1 || r.bottom > wr.bottom + 1) inside = false; }
    return {text: (el.textContent || '').replace(/\s+/g, ' ').trim(), within: inside, announced: true, scrollWidth: win.scrollWidth, clientWidth: win.clientWidth, font: null}; }
  if (!field && el.firstChild) { const range = document.createRange(); range.selectNodeContents(el); ink = range.getBoundingClientRect(); }
  let within = el.scrollWidth <= el.clientWidth + 1 && ink.left >= box.left - 1 && ink.right <= box.right + 1 &&
               box.left >= -1 && box.right <= window.innerWidth + 1;
  for (let p = el.parentElement, n = 0; p && p !== document.body && n < 3; p = p.parentElement, n++) {
    const pr = p.getBoundingClientRect(); if (box.left < pr.left - 1 || box.right > pr.right + 1) within = false; }
  return {text, within, scrollWidth: el.scrollWidth, clientWidth: el.clientWidth, font: parseFloat(getComputedStyle(el).fontSize)}; })"""


def key_for(page, ch):
    """The on-screen key for one character of a script, or None."""
    acts = [a for a in page.evaluate("__look.actionables()") or [] if a["kind"] == "click" and not a["disabled"]]
    norm = lambda a: (a["label"] or "").strip().lower()
    if ch.isdigit():
        return next((a for a in acts if norm(a) == ch or WORDS.get(norm(a)) == ch), None)
    hits = [a for a in acts if re.fullmatch(KEY[ch], norm(a))]
    if ch == "C" and hits:
        hits.sort(key=lambda a: CLEAR_ORDER.index(norm(a)) if norm(a) in CLEAR_ORDER else 99)
    return hits[0] if hits else None


def keys(page, script):
    """Press each character's key. Returns the characters that had no key."""
    missing = []
    for ch in script:
        a = key_for(page, ch)
        if a and tap(page, a):
            time.sleep(0.06)
        else:
            missing.append(ch)
    time.sleep(0.15)
    return missing


def number(text):
    t = re.sub(r"\s*point\s*", ".", re.sub(r"^(minus|negative)\s*", "-", (text or "").strip(), flags=re.I), flags=re.I).replace("−", "-").replace("–", "-").replace(",", "").replace(" ", "").replace(" ", "").replace(" ", "")
    m = re.fullmatch(r"=?(-?\d*\.?\d+(?:e[+-]?\d+)?)\.?", t, re.I)
    return (float(m.group(1)), len(m.group(1))) if m else (None, len(t))


def calculator(page, res, url):
    checks, shown, frames = {}, {}, [(page.screenshot(), "at rest")]
    fresh = lambda: (page.navigate(url, settle=0.5), play.errors(page))
    keys(page, "7")
    path = page.evaluate("%s(%s)" % (FIND_DISPLAY, json.dumps("7")))
    res["display_found"] = path is not None
    def read():
        if path is None:
            return {}
        got = page.evaluate("%s(%s)" % (READ_DISPLAY, json.dumps(path))) or {}
        if got.get("announced"):                 # announcements can trail the keypress
            time.sleep(0.5)
            got = page.evaluate("%s(%s)" % (READ_DISPLAY, json.dumps(path))) or {}
        return got
    res["display_read_from"] = "what it announces (a segmented display with no text)" if read().get("announced") else "its text"

    def sums(name, script, want, frame=None):
        fresh()
        missing = keys(page, script)
        got = read()
        shown[name] = got.get("text")
        if frame:
            frames.append((page.screenshot(), frame))
        if missing or path is None:
            checks[name] = None
            res.setdefault("not_run", {})[name] = "no key for %s" % " ".join(missing) if missing else "no display found"
            return
        value, length = number(got.get("text"))
        checks[name] = value is not None and any(abs(value - w) < 1e-9 for w in want) and length <= 12

    sums("1 add", "12+7=", [19], "pressed 1 2 + 7 =")
    sums("2 multiply", "9*8=", [72])
    sums("3 negative", "7-10=", [-3])
    sums("4 decimals", "0.1+0.2=", [0.3], "from a fresh load, pressed 0 . 1 + 0 . 2 =")
    sums("5 chained", "2+3*4=", [14, 20])
    # 6: dividing by zero says something, and the calculator still works after clear
    fresh(); missing = keys(page, "8/0="); got = read(); shown["6 divide by zero"] = got.get("text")
    frames.append((page.screenshot(), "from a fresh load, pressed 8 ÷ 0 ="))
    if missing or path is None:
        checks["6 divide by zero"] = None
    else:
        said = bool(got.get("text")) and not re.search(r"nan|undefined", got["text"], re.I)
        recovered = None
        if not keys(page, "C"):
            keys(page, "1+1="); v, _ = number(read().get("text")); recovered = v == 2
            shown["6 after clear, 1 + 1 ="] = read().get("text")
        checks["6 divide by zero"] = said and recovered is not False
    # 7: a long number stays inside the display
    fresh(); missing = keys(page, "9" * 20); got = read(); shown["7 long number"] = got.get("text")
    frames.append((page.screenshot(), "from a fresh load, pressed 9 twenty times"))
    checks["7 long number"] = None if (missing or path is None) else bool(got.get("within"))
    res["long_number"] = {k: got.get(k) for k in ("within", "scrollWidth", "clientWidth", "font")}
    # 8: clear
    fresh(); missing = keys(page, "12+7=") + keys(page, "C"); got = read(); shown["8 clear"] = got.get("text")
    frames.append((page.screenshot(), "pressed 1 2 + 7 = and then clear"))
    cleared = got.get("text") in ("0", "", "0.") or bool(got.get("announced") and re.search(r"clear|zero", got.get("text") or "", re.I))
    checks["8 clear"] = None if (missing or path is None) else cleared
    # 9: the keyboard
    fresh()
    for k in ("4", "*", "5", "Enter"):
        play.press(page, k); time.sleep(0.06)
    time.sleep(0.15); got = read(); shown["9 keyboard"] = got.get("text")
    v, _ = number(got.get("text"))
    checks["9 keyboard"] = None if path is None else v == 20
    res["checks"], res["shown"] = checks, shown
    res["passed"] = sum(1 for v in checks.values() if v is True)
    res["not_run_count"] = sum(1 for v in checks.values() if v is None)
    res["works"] = bool(checks.get("1 add"))
    return frames, "a scripted use: 12 + 7 =, 0.1 + 0.2 =, 8 ÷ 0 =, the 9 key twenty times, clear"


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
            frames, how = lavalamp(page, res, src) if TASK == "t1-lavalamp" else calculator(page, res, url)
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
