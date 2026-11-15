#!/usr/bin/env python3
"""Look at what you built: render a page headlessly, screenshot it, play it, and list what a grader would see
(ADRs 0018, 0020).

Builders that read a meta dump have more to fit into a design than builders that don't, and in A/B tests 16 and 17
the dump builds shipped clipped timelines, overlapping icons and wrapped rows that nobody looked at. This renders the
page in the local Chromium-family browser (through cdp.py, nothing installed), screenshots it at desktop and phone
widths, hovers the main control and clicks the main toggle when it finds one, and runs a few layout checks: content
running off the screen, content clipped by an ancestor, controls that overlap, and tiny targets. Then it plays the
page (play.py): it acts on everything a person could, tabs through it, and after every action checks what holds for
any page, because in test 19 the defects that cost points only existed once the page was used. It prints an account
of what the page said and lays every state out on one sheet. The findings are things to look at, not rules; the
builder reads them and decides.

Usage: python3 look.py <page.html> [--out DIR] [--play STEPS]... [--no-walk] [--hover SELECTOR] [--click SELECTOR] [--json]
Python 3.9+, standard library only. Without a browser it says so and exits 0.
"""
import argparse
import json
import os
import pathlib
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp  # noqa: E402
import pixels  # noqa: E402
import play  # noqa: E402
import tools  # noqa: E402

DESKTOP = (1280, 800)
PHONE = (390, 844)
SETTLE = 0.8          # seconds for hover and open transitions to run before the shot
MIN_TARGET = 24       # CSS px; smaller controls are hard to hit (WCAG 2.5.8)
OVERLAP_SHARE = 0.25  # of the smaller control's area

# One pass over the DOM in the page. Returns [{kind, selector, detail}]. Kept small and readable on purpose.
CHECKS_JS = r"""
(() => {
  const out = [];
  const vw = window.innerWidth, vh = window.innerHeight;
  const path = (el) => {
    if (el.id) return '#' + el.id;
    const parts = [];
    for (let e = el, n = 0; e && e.nodeType === 1 && n < 3; e = e.parentElement, n++) {
      if (e.id) { parts.unshift('#' + e.id); break; }
      let s = e.tagName.toLowerCase();
      const sib = e.parentElement ? [...e.parentElement.children].filter(c => c.tagName === e.tagName) : [];
      if (sib.length > 1) s += ':nth-of-type(' + (sib.indexOf(e) + 1) + ')';
      parts.unshift(s);
    }
    return parts.join(' > ');
  };
  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.bottom > 0 && r.right > 0 && r.top < vh && r.left < vw;
  };
  const all = [...document.body.querySelectorAll('*')].filter(visible);
  // 1. content running off the screen
  if (document.documentElement.scrollWidth > vw + 1)
    out.push({kind: 'overflow', selector: 'html', detail: 'the page is ' + document.documentElement.scrollWidth + 'px wide in a ' + vw + 'px viewport'});
  for (const el of all) {
    const r = el.getBoundingClientRect();
    if (r.right > vw + 1 || r.left < -1) {
      out.push({kind: 'overflow', selector: path(el), detail: Math.round(r.width) + 'px wide, ' + (r.right > vw ? Math.round(r.right - vw) + 'px past the right edge' : Math.round(-r.left) + 'px past the left edge') + ' of a ' + vw + 'px viewport'});
      if (out.filter(f => f.kind === 'overflow').length > 6) break;
    }
  }
  // 2. content clipped by an ancestor with overflow hidden
  for (const el of all) {
    if (el === document.body || el === document.documentElement) continue;
    const cs = getComputedStyle(el);
    const clipsY = ['hidden', 'clip'].includes(cs.overflowY), clipsX = ['hidden', 'clip'].includes(cs.overflowX);
    if (!clipsY && !clipsX) continue;
    if (el.clientHeight < 4 || el.getAttribute('aria-hidden') === 'true') continue;   // collapsed on purpose
    if (!el.textContent.trim() && !el.querySelector('img,svg,canvas')) continue;
    const dy = el.scrollHeight - el.clientHeight, dx = el.scrollWidth - el.clientWidth;
    if (clipsY && dy > 2)
      out.push({kind: 'clipped', selector: path(el), detail: el.scrollHeight + 'px of content in a ' + el.clientHeight + 'px box with overflow hidden; ' + dy + 'px cut off below'});
    else if (clipsX && dx > 2) {
      const ellipsis = cs.textOverflow === 'ellipsis' && cs.whiteSpace === 'nowrap';
      out.push({kind: ellipsis ? 'truncated' : 'clipped', selector: path(el), detail: el.scrollWidth + 'px of content in a ' + el.clientWidth + 'px box; ' + dx + 'px cut off at the side' + (ellipsis ? ' (ellipsis)' : '')});
    }
  }
  // 2b. a scrolling box whose last visible row is cut in half at its edge (test 16's timelines)
  for (const el of all) {
    const cs = getComputedStyle(el);
    if (!['auto', 'scroll'].includes(cs.overflowY) || el.scrollHeight <= el.clientHeight + 2 || el.clientHeight < 4) continue;
    const edge = el.getBoundingClientRect().top + el.clientTop + el.clientHeight;
    const cut = [...el.children].find(ch => { const r = ch.getBoundingClientRect(); return r.height > 4 && r.top < edge - 2 && r.bottom > edge + 2; });
    if (cut)
      out.push({kind: 'cut-off', selector: path(el), detail: el.scrollHeight + 'px of content in a ' + el.clientHeight + 'px scrolling box, and ' + path(cut) + ' is cut in half at the edge'});
  }
  // 3. controls that overlap, and controls too small to hit
  const controls = all.filter(el => el.matches('button, a[href], input, select, textarea, summary, [role="button"], [role="tab"], [role="switch"], [tabindex]:not([tabindex="-1"])'));
  const rects = controls.map(el => el.getBoundingClientRect());
  for (let i = 0; i < controls.length; i++) {
    const a = rects[i];
    if ((a.width < %(min)d || a.height < %(min)d) && controls[i].matches('button, summary, [role="button"], [role="switch"], input:not([type=text]):not([type=email])'))
      out.push({kind: 'small-target', selector: path(controls[i]), detail: Math.round(a.width) + 'x' + Math.round(a.height) + 'px, under %(min)dx%(min)d'});
    for (let j = i + 1; j < controls.length; j++) {
      if (controls[i].contains(controls[j]) || controls[j].contains(controls[i])) continue;
      const b = rects[j];
      const w = Math.min(a.right, b.right) - Math.max(a.left, b.left), h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (w <= 0 || h <= 0) continue;
      const share = (w * h) / Math.min(a.width * a.height, b.width * b.height);
      if (share >= %(share)f)
        out.push({kind: 'overlap', selector: path(controls[j]), detail: 'over ' + path(controls[i]) + ' (' + Math.round(share * 100) + '%% of the smaller one)'});
    }
  }
  return out;
})()
""" % {"min": MIN_TARGET, "share": OVERLAP_SHARE}

# The main control to hover: the largest visible button-like element that isn't a toggle.
MAIN_CONTROL_JS = r"""
(() => {
  const vw = window.innerWidth, vh = window.innerHeight;
  const cands = [...document.querySelectorAll('button, a[href], [role="button"], input[type="submit"]')].filter(el => {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 20 && r.height > 12 && r.top < vh && r.left < vw && r.bottom > 0 && r.right > 0;
  });
  const plain = cands.filter(el => !el.hasAttribute('aria-expanded') && el.tagName !== 'SUMMARY');
  const pool = plain.length ? plain : cands;
  pool.sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; });
  const el = pool[0];
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return {selector: el.id ? '#' + el.id : el.tagName.toLowerCase(), x: r.left + r.width / 2, y: r.top + r.height / 2,
          rect: {x: r.left, y: r.top, width: r.width, height: r.height}};
})()
"""

# The main toggle to click: the first visible element that announces an open/closed state.
TOGGLE_JS = r"""
(() => {
  const vw = window.innerWidth, vh = window.innerHeight;
  const el = [...document.querySelectorAll('[aria-expanded], summary, [aria-controls], [data-toggle], .toggle')].find(el => {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && r.height > 0 && r.top < vh && r.left < vw;
  });
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return {selector: el.id ? '#' + el.id : el.tagName.toLowerCase(), x: r.left + r.width / 2, y: r.top + r.height / 2,
          expanded: el.getAttribute('aria-expanded')};
})()
"""


def _mouse(page, kind, x, y, **extra):
    params = {"type": kind, "x": float(x), "y": float(y)}
    params.update(extra)
    page.conn.send("Input.dispatchMouseEvent", params)


def _pad(rect, pad, width, height):
    x = max(0, rect["x"] - pad)
    y = max(0, rect["y"] - pad)
    return {"x": x, "y": y, "width": min(width - x, rect["width"] + 2 * pad), "height": min(height - y, rect["height"] + 2 * pad)}


def _differs(a, b):
    """Whether two PNGs of the same size differ anywhere that matters (more than a handful of pixels)."""
    ia, ib = pixels.decode_png(a), pixels.decode_png(b)
    if (ia.width, ia.height) != (ib.width, ib.height):
        return True
    changed = 0
    for y in range(0, ia.height, 2):
        for x in range(0, ia.width, 2):
            pa, pb = ia.pixel(x, y), ib.pixel(x, y)
            if abs(pa[0] - pb[0]) + abs(pa[1] - pb[1]) + abs(pa[2] - pb[2]) > 24:
                changed += 1
                if changed > 20:
                    return True
    return False


def _write(out_dir, name, data):
    path = os.path.join(out_dir, name + ".png")
    with open(path, "wb") as f:
        f.write(data)
    return path


def look(path, out_dir, hover=None, click=None, browser_path=None, plays=(), walk=True):
    """Render `path`, screenshot it, run the checks, then play it (ADR 0020): walk everything a person could act
    on, and run each scripted play in `plays`. Returns {file, url, shots, findings, hover, toggle, played, plays}."""
    os.makedirs(out_dir, exist_ok=True)
    url = pathlib.Path(path).resolve().as_uri()
    result = {"file": os.path.abspath(path), "url": url, "shots": [], "findings": [], "hover": None, "toggle": None,
              "played": {}, "plays": []}
    with cdp.Browser(path=browser_path, width=DESKTOP[0], height=DESKTOP[1]) as browser:
        page = browser.new_page()
        play.install(page)
        page.navigate(url, settle=0.3)
        result["shots"].append({"name": "desktop", "viewport": list(DESKTOP), "path": _write(out_dir, "desktop", page.screenshot())})
        result["findings"] += [dict(f, state="desktop") for f in page.evaluate(CHECKS_JS)]

        visual = {"desktop": page.evaluate("__look.mainVisual()")}
        moves = page.evaluate("__look.motion()")

        target = page.evaluate(_pick_js(MAIN_CONTROL_JS, hover))
        if target:
            clip = _pad(target["rect"], 40, DESKTOP[0], DESKTOP[1])
            before = page.screenshot(clip=clip)
            label = page.evaluate("__look.textBoxAt(%f, %f)" % (target["x"], target["y"]))
            at_rest = play.contrast(page.screenshot(clip=label)) if label else None
            began = time.time()
            _mouse(page, "mouseMoved", target["x"], target["y"])
            through = []                              # the label's contrast on the way to the hovered look
            for moment in (0.1, 0.25, 0.5):
                time.sleep(max(0.0, began + moment - time.time()))
                if moment == 0.1:
                    during = page.evaluate("__look.motion()")
                    moves = {"long": max(moves["long"], during["long"]), "endless": max(moves["endless"], during["endless"]),
                             "asks": moves["asks"]}
                if label:
                    through.append(play.contrast(page.screenshot(clip=label)))
            time.sleep(max(0.0, began + SETTLE - time.time()))
            after = page.screenshot(clip=clip)
            settled = play.contrast(page.screenshot(clip=label)) if label else None
            result["findings"] += _washed_out(target["selector"], at_rest, through, settled)
            changed = _differs(before, after)
            result["hover"] = {"selector": target["selector"], "changed": changed,
                               "path": _write(out_dir, "hover", after)}
            result["shots"].append({"name": "hover", "viewport": list(DESKTOP), "path": result["hover"]["path"]})
            if not changed:
                result["findings"].append({"kind": "hover-static", "selector": target["selector"], "state": "desktop",
                                           "detail": "nothing visible changes while the pointer rests on it"})
            _mouse(page, "mouseMoved", 2, DESKTOP[1] - 2)
            time.sleep(0.3)

        toggle = page.evaluate(_pick_js(TOGGLE_JS, click))
        if toggle:
            _mouse(page, "mouseMoved", toggle["x"], toggle["y"])
            _mouse(page, "mousePressed", toggle["x"], toggle["y"], button="left", clickCount=1)
            _mouse(page, "mouseReleased", toggle["x"], toggle["y"], button="left", clickCount=1)
            time.sleep(SETTLE)
            now = page.evaluate("(() => { const el = document.querySelector(%s); return el ? el.getAttribute('aria-expanded') : null; })()" % json.dumps(toggle["selector"]))
            result["toggle"] = {"selector": toggle["selector"], "before": toggle.get("expanded"), "after": now,
                                "path": _write(out_dir, "open", page.screenshot())}
            result["shots"].append({"name": "open", "viewport": list(DESKTOP), "path": result["toggle"]["path"]})
            result["findings"] += [dict(f, state="open") for f in page.evaluate(CHECKS_JS)]

        if not moves["asks"] and (moves["endless"] or moves["long"]):
            result["findings"].append({"kind": "no-reduced-motion", "selector": "html", "state": "desktop",
                                       "detail": "%d animation%s here (%d never stop%s) and the page never asks "
                                                 "prefers-reduced-motion" % (moves["endless"] + moves["long"],
                                                                             " runs" if moves["endless"] + moves["long"] == 1 else "s run",
                                                                             moves["endless"], "s" if moves["endless"] == 1 else "")})
        _play(page, url, "desktop", DESKTOP, out_dir, result, walk)
        for n, script in enumerate(plays, 1):
            page.navigate(url, settle=0.3)
            known = {(f["kind"], f["selector"]) for f in result["findings"]}
            ran = play.run(page, script, checks_js=CHECKS_JS, known=known)
            result["plays"].append({"script": script, "actions": ran["actions"], "expects": ran["expects"]})
            result["shots"].append({"name": "play-%d" % n, "viewport": list(DESKTOP),
                                    "path": _write(out_dir, "play-%d" % n, page.screenshot())})
            result["findings"] += [dict(f, state="play %d%s" % (n, ", " + f["state"] if f.get("state") else "")) for f in ran["findings"]]

        page.set_viewport(PHONE[0], PHONE[1], mobile=True)
        page.navigate(url, settle=0.3)
        result["shots"].append({"name": "phone", "viewport": list(PHONE), "path": _write(out_dir, "phone", page.screenshot())})
        result["findings"] += [dict(f, state="phone") for f in page.evaluate(CHECKS_JS)]
        visual["phone"] = page.evaluate("__look.mainVisual()")
        result["findings"] += _covered(visual)
        if toggle:
            t2 = page.evaluate(_pick_js(TOGGLE_JS, click))
            if t2:
                _mouse(page, "mousePressed", t2["x"], t2["y"], button="left", clickCount=1)
                _mouse(page, "mouseReleased", t2["x"], t2["y"], button="left", clickCount=1)
                time.sleep(SETTLE)
                result["shots"].append({"name": "phone-open", "viewport": list(PHONE), "path": _write(out_dir, "phone-open", page.screenshot())})
                result["findings"] += [dict(f, state="phone-open") for f in page.evaluate(CHECKS_JS)]
        _play(page, url, "phone", PHONE, out_dir, result, walk)
        result["sheet"] = _sheet(page, out_dir, result["shots"])
    result["findings"] = _dedupe(result["findings"])
    return result


SHEET_WIDTH = 1300
SHOT_LABELS = {"desktop": "desktop 1280x800, as loaded", "hover": "pointer resting on the main control", "open": "main toggle open",
               "desktop-played": "desktop, after the walk", "phone": "phone 390x844, as loaded", "phone-open": "phone, toggle open",
               "phone-played": "phone, after the walk"}


def _sheet(page, out_dir, shots):
    """Every shot side by side on one labelled image, laid out by the browser: one Read instead of five."""
    tiles = []
    for shot in shots:
        n = shot["name"]
        label = SHOT_LABELS.get(n) or ("after scripted play %s" % n.split("-")[-1] if n.startswith("play-") else n)
        tiles.append('<figure><img src="%s"><figcaption>%s</figcaption></figure>' % (os.path.basename(shot["path"]), label))
    html = ('<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#18181b;color:#e4e4e7;font:13px/1.4 system-ui,sans-serif}'
            'main{display:flex;flex-wrap:wrap;gap:14px;padding:14px;align-items:flex-start}figure{margin:0}'
            'img{display:block;max-height:400px;max-width:640px;border:1px solid #52525b}figcaption{padding-top:4px}</style>'
            '<main>%s</main>' % "".join(tiles))
    source = os.path.join(out_dir, "sheet.html")
    with open(source, "w", encoding="utf-8") as f:
        f.write(html)
    page.set_viewport(SHEET_WIDTH, 800, mobile=False)
    page.navigate(pathlib.Path(source).resolve().as_uri(), settle=0.3)
    height = page.evaluate("Math.ceil(document.documentElement.scrollHeight)")
    data = page.screenshot(clip={"x": 0, "y": 0, "width": SHEET_WIDTH, "height": min(int(height), 4000)})
    return _write(out_dir, "sheet", data)


COVERED = 0.30        # share of the main visual under other elements on a phone before it is worth saying
COVERED_MORE = 0.15   # ...and how much more than on a laptop, so a heads-up display that is there by design stays quiet


def _covered(visual):
    """A panel that sits beside the main visual on a laptop and on top of it on a phone (test 19's lemons)."""
    desk, phone = visual.get("desktop"), visual.get("phone")
    if not desk or not phone or desk["key"] != phone["key"]:
        return []
    if phone["covered"] >= COVERED and phone["covered"] - desk["covered"] >= COVERED_MORE:
        return [{"kind": "covered", "selector": phone["show"], "state": "phone",
                 "detail": "%s covers %d%% of it at phone width (%d%% at desktop width)"
                           % (phone["by"] or "other content", round(100 * phone["covered"]), round(100 * desk["covered"]))}]
    return []


def _washed_out(selector, at_rest, through, settled):
    """A label that could be read before the hover and can't be read partway through it, or once it has settled."""
    if not at_rest or at_rest < 3 or settled is None:
        return []
    worst = min([c for c in through if c] + [settled])
    if worst >= 3 or worst >= 0.6 * at_rest:
        return []
    when = "while the pointer rests on it" if settled < 3 else "partway through its hover transition"
    return [{"kind": "washed-out", "selector": selector, "state": "desktop",
             "detail": "its label drops to %.1f:1 against what is behind it %s (%.1f:1 at rest)" % (worst, when, at_rest)}]


def _play(page, url, name, viewport, out_dir, result, walk=True):
    """Play the page from a fresh load at this viewport (play.py), and keep what the walk found."""
    page.navigate(url, settle=0.3)
    if name == "desktop":
        result["findings"] += [dict(f, state=name) for f in play.focus_walk(page)]
    if not walk:
        return
    known = {(f["kind"], f["selector"]) for f in result["findings"]}
    walked = play.walk(page, checks_js=CHECKS_JS, known=known)
    result["played"][name] = walked["steps"]
    if any(s["changed"] is not False for s in walked["steps"]):
        result["shots"].append({"name": name + "-played", "viewport": list(viewport),
                                "path": _write(out_dir, name + "-played", page.screenshot())})
    if name == "desktop":
        result["findings"] += [dict(f, state=name) for f in play.unreachable(walked["steps"])]
    result["findings"] += [dict(f, state="%s, %s" % (name, f["state"]) if f.get("state") else name) for f in walked["findings"]]


def _pick_js(default_js, selector):
    """The caller's selector wins over the automatic pick."""
    if not selector:
        return default_js
    return ("(() => { const el = document.querySelector(%s); if (!el) return null; const r = el.getBoundingClientRect();"
            " return {selector: %s, x: r.left + r.width / 2, y: r.top + r.height / 2, rect: {x: r.left, y: r.top, width: r.width, height: r.height},"
            " expanded: el.getAttribute('aria-expanded')}; })()" % (json.dumps(selector), json.dumps(selector)))


PLAYED = ("uneven", "js-error", "dead")   # found by playing: one finding per element, with every width it showed at


def _dedupe(findings):
    seen, out = {}, []
    for f in findings:
        key = (f["kind"], f["selector"]) if f["kind"] in PLAYED else (f["kind"], f["selector"], f.get("detail"))
        if key not in seen:
            seen[key] = f
            out.append(f)
        elif f["kind"] in PLAYED and f.get("state") and f["state"] not in seen[key]["state"].split(", "):
            seen[key]["state"] += ", " + f["state"]
    return out


def report(result):
    lines = ["Looked at %s" % result["file"]]
    for shot in result["shots"]:
        lines.append("  %-14s %dx%d  %s" % (shot["name"], shot["viewport"][0], shot["viewport"][1], shot["path"]))
    if result.get("sheet"):
        lines.append("  %-14s all of the above on one labelled image: %s" % ("sheet", result["sheet"]))
    if result.get("hover"):
        h = result["hover"]
        lines.append("  hover on %s: %s" % (h["selector"], "something changes" if h["changed"] else "nothing visible changes"))
    if result.get("toggle"):
        t = result["toggle"]
        lines.append("  clicked %s: aria-expanded %s -> %s" % (t["selector"], t.get("before"), t.get("after")))
    played = result.get("played") or {}
    told = {name: play.account(played[name]) for name in ("desktop", "phone") if played.get(name)}
    if len(told) == 2 and told["desktop"] == told["phone"]:
        told = {"desktop and phone": told["desktop"]}
    for name, account in told.items():
        lines.append("Played it at %s width, %d actions:" % (name, len(played[name.split(" ")[0]])))
        lines += ["  %d. %s" % (i, line) for i, line in enumerate(account, 1)]
    for n, ran in enumerate(result.get("plays") or [], 1):
        failed = sum(1 for e in ran["expects"] if not e["ok"])
        held = ("no expectations" if not ran["expects"] else "all %d expectations held" % len(ran["expects"]) if not failed
                else "%d of %d expectations failed" % (failed, len(ran["expects"])))
        lines.append("Play %d: %d actions, %s" % (n, ran["actions"], held))
    if result["findings"]:
        lines.append("Things to look at (not rules):")
        for f in result["findings"]:
            lines.append("  - %-13s %-28s %s  [%s]" % (f["kind"], f["selector"], f.get("detail", ""), f.get("state", "")))
    else:
        lines.append("No layout problems found by the checks.")
    lines.append("Read the desktop and phone shots with the Read tool%s. Then two questions. Would a stranger who saw it for one "
                 "second name what the user asked for, or something else? And does it read as the user's words, at full strength? "
                 "Fix what you see and look again." % ("; the sheet lays every state side by side for a quick pass" if result.get("sheet") else ""))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render a built page, screenshot it, and list what a grader would see.")
    ap.add_argument("page", help="the HTML file to look at")
    ap.add_argument("--out", help="folder for the screenshots (default: a temp folder)")
    ap.add_argument("--hover", help="CSS selector of the control to hover (default: the largest button)")
    ap.add_argument("--click", help="CSS selector of the toggle to click (default: the first [aria-expanded] or summary)")
    ap.add_argument("--play", action="append", default=[], metavar="STEPS",
                    help="a scripted play to run from a fresh load, steps split by ';': click SEL; hover SEL; type TEXT into SEL; "
                         "press KEY; drag SEL by DX,DY; wait MS; expect TEXT; expect SEL says TEXT; expect no TEXT. Repeatable")
    ap.add_argument("--no-walk", action="store_true", help="skip the automatic walk (scripted plays still run)")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    args = ap.parse_args(argv)
    found = tools.find_browser()
    if not found["found"]:
        print("No Chromium-family browser found, so there is nothing to look with; skip this step. %s" % (found.get("hint") or ""))
        return 0
    out_dir = args.out or tempfile.mkdtemp(prefix="look-")
    try:
        result = look(args.page, out_dir, hover=args.hover, click=args.click, browser_path=found["path"],
                      plays=args.play, walk=not args.no_walk)
    except (cdp.BrowserUnavailable, cdp.CDPError, OSError) as exc:
        print("The browser could not render the page (%s); skip this step." % exc)
        return 0
    print(json.dumps(result, indent=1) if args.json else report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
