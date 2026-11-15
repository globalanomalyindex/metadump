#!/usr/bin/env python3
"""Play a built page the way a person would, and watch for what should never happen while they do (ADR 0020).

The look (look.py) used to render a page, hover one control and click one toggle. In A/B test 19 five of the eight
tic tac toe games had rows that changed height once marks landed, and nothing saw it, because nothing played them.
This module is the playing half of the look: it finds what a person could act on (buttons, cells, inputs, sliders,
a canvas to drag), acts on each thing once in page order, and after every action checks a few invariants that hold
for any page: no script errors, matching siblings stay the same size unless you opened one of them, nothing new is
clipped or overlapping. It also keeps a short account of what the page said along the way, so a builder can read
what happened without opening a screenshot.

Used through look.py; nothing here is a command. Python 3.9+, standard library only.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixels  # noqa: E402

SETTLE = 0.3        # seconds after an action before the page is read again
WALK_STEPS = 24     # actions per walk
GROUP_CAP = 9       # actions spent on one group of matching siblings (nine cells, a row of swatches)
RESET_LIKE = re.compile(r"\b(reset|restart|clear|new game|new round|play again|start over|again|undo|delete|remove|"
                        r"close|dismiss|cancel|stop|skip)\b", re.I)

# Runs before the page's own scripts: blocking dialogs would freeze the walk, so they are recorded instead.
GUARD_JS = r"""
(() => {
  window.__look_dialogs = [];
  window.alert = (m) => { window.__look_dialogs.push(String(m)); };
  window.confirm = (m) => { window.__look_dialogs.push(String(m)); return true; };
  window.prompt = (m) => { window.__look_dialogs.push(String(m)); return ''; };
  window.print = () => {};
  window.open = () => null;
})();
"""

# The page-side half: everything that has to read the DOM. Installed on every load as window.__look.
HELPER_JS = r"""
(() => {
  if (window.__look) return;
  const esc = (s) => (window.CSS && CSS.escape) ? CSS.escape(s) : s;
  const uniqueId = (e) => e.id && document.querySelectorAll('#' + esc(e.id)).length === 1;
  // A selector that finds exactly this element again after the page re-renders.
  const path = (el) => {
    if (el === document.body) return 'body';
    const parts = [];
    for (let e = el; e && e.nodeType === 1 && e !== document.body; e = e.parentElement) {
      if (uniqueId(e)) { parts.unshift('#' + esc(e.id)); break; }
      let s = e.tagName.toLowerCase();
      const sib = e.parentElement ? [...e.parentElement.children].filter(c => c.tagName === e.tagName) : [];
      if (sib.length > 1) s += ':nth-of-type(' + (sib.indexOf(e) + 1) + ')';
      parts.unshift(s);
    }
    return parts.join(' > ');
  };
  // The short name findings use: an id when there is one, else the last three steps of the path.
  const show = (el) => {
    if (el === document.body) return 'body';
    if (el.id) return '#' + el.id;
    return path(el).split(' > ').slice(-3).join(' > ');
  };
  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const label = (el) => {
    const t = el.getAttribute('aria-label') || el.innerText || el.value || el.getAttribute('placeholder') || el.title || el.alt || '';
    return String(t).replace(/\s+/g, ' ').trim().slice(0, 40);
  };

  const NATIVE = 'button, [role="button"], input:not([type="hidden"]), select, textarea, summary, [role="tab"], [role="switch"], ' +
    '[role="checkbox"], [role="radio"], [role="menuitem"], [role="option"], [role="gridcell"], [role="slider"], a[href^="#"], ' +
    '[onclick], [tabindex]:not([tabindex="-1"]), [contenteditable=""], [contenteditable="true"], canvas';
  const kindOf = (el) => {
    const t = el.tagName, type = (el.getAttribute('type') || '').toLowerCase();
    if (t === 'CANVAS') return 'canvas';
    if (t === 'SELECT') return 'select';
    if (t === 'TEXTAREA' || el.isContentEditable) return 'text';
    if (t === 'INPUT') {
      if (type === 'range') return 'range';
      if (['checkbox', 'radio', 'button', 'submit', 'reset', 'image'].includes(type)) return 'click';
      if (['file', 'color', 'date', 'time', 'datetime-local', 'month', 'week'].includes(type)) return 'skip';
      return 'text';
    }
    return 'click';
  };
  // What a person could act on, in page order. Elements with a pointer cursor count too: many builds wire clicks
  // to plain divs.
  const actionables = () => {
    const native = [...document.querySelectorAll(NATIVE)];
    const set = new Set(native);
    for (const el of document.body.querySelectorAll('*')) {
      if (set.has(el) || getComputedStyle(el).cursor !== 'pointer') continue;
      if (el.parentElement && getComputedStyle(el.parentElement).cursor === 'pointer') continue;   // the pointer is inherited
      if (native.some(n => n.contains(el) || el.contains(n))) continue;
      set.add(el);
    }
    const list = [...set].filter(visible);
    list.sort((a, b) => (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) ? -1 : 1);
    return list.map(el => {
      const r = el.getBoundingClientRect();
      return {key: path(el), show: show(el), kind: kindOf(el), label: label(el),
              group: el.parentElement ? path(el.parentElement) + ' > ' + el.tagName.toLowerCase() : '',
              disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true', keyboard: el.tabIndex >= 0,
              numeric: el.type === 'number', multiline: el.tagName === 'TEXTAREA' || el.isContentEditable,
              w: r.width, h: r.height};
    });
  };
  const locate = (key) => {
    const el = document.querySelector(key);
    if (!el || !visible(el)) return null;
    el.scrollIntoView({block: 'center', inline: 'center', behavior: 'instant'});
    const r = el.getBoundingClientRect();
    return {x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height};
  };

  // Groups of matching siblings: three or more children of one parent with the same tag and the same size.
  // While a page is used they stay the same size as each other, unless the one you acted on opens.
  const size = (el) => { const r = el.getBoundingClientRect(); return [r.width, r.height]; };
  const same = (a, b, tol) => Math.abs(a - b) <= tol;
  let tracked = [];
  const findGroups = () => {
    const out = [];
    for (const p of [document.body, ...document.body.querySelectorAll('*')]) {
      const byTag = {};
      for (const k of p.children) (byTag[k.tagName] = byTag[k.tagName] || []).push(k);
      for (const tag in byTag) {
        const kids = byTag[tag];
        if (kids.length < 3) continue;
        // the members are the children that share the commonest size
        let best = [];
        for (const k of kids) {
          if (!visible(k)) continue;
          const [w, h] = size(k);
          const mates = kids.filter(o => visible(o) && same(size(o)[0], w, 1.5) && same(size(o)[1], h, 1.5));
          if (mates.length > best.length) best = mates;
        }
        if (best.length < 3) continue;
        out.push({parent: p, tag, count: kids.length, members: best.map(k => kids.indexOf(k)), last: best.map(size)});
      }
    }
    return out;
  };
  const rest = () => {
    tracked = findGroups();
    return {texts: texts(), sig: sig(), href: location.href};
  };
  // After an action on `key`: which tracked groups stopped matching because of it.
  const uneven = (key) => {
    const target = key ? document.querySelector(key) : null;
    const found = [];
    for (const g of tracked) {
      if (!g.parent.isConnected) continue;
      const kids = [...g.parent.children].filter(k => k.tagName === g.tag);
      if (kids.length !== g.count) { g.stale = true; continue; }
      const now = g.members.map(i => size(kids[i]));
      const acted = target ? g.members.findIndex(i => kids[i] === target || kids[i].contains(target)) : -1;
      const others = (list) => list.filter((_s, i) => i !== acted);
      const spread = (list, d) => list.length ? Math.max(...list.map(s => s[d])) - Math.min(...list.map(s => s[d])) : 0;
      for (const d of [0, 1]) {
        const base = Math.max(...g.last.map(s => s[d]));
        const tol = Math.max(3, 0.06 * base);
        if (spread(others(now), d) - spread(others(g.last), d) > tol && !g.reported) {
          g.reported = true;
          found.push({selector: show(g.parent), n: g.members.length, tag: g.tag.toLowerCase(),
                      was: g.last[0].map(Math.round), dim: d ? 'heights' : 'widths',
                      min: Math.round(Math.min(...now.map(s => s[d]))), max: Math.round(Math.max(...now.map(s => s[d])))});
        }
      }
      g.last = now;
    }
    return found;
  };

  const texts = () => document.body.innerText.split('\n').map(s => s.replace(/\s+/g, ' ').trim()).filter(Boolean).slice(0, 200);
  // A cheap fingerprint of everything an action could change in the DOM.
  const sig = () => {
    let h = 0;
    const add = (s) => { s = String(s); for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; };
    add(document.body.innerText);
    for (const el of document.body.querySelectorAll('*')) {
      add(el.tagName);
      for (const a of el.attributes) add(a.name + '=' + a.value);
      if (typeof el.value === 'string') add(el.value);
      if (typeof el.checked === 'boolean') add(el.checked);
    }
    return h;
  };
  const after = (key) => ({uneven: uneven(key), texts: texts(), sig: sig(), href: location.href,
                           dialogs: window.__look_dialogs.splice(0)});

  const fire = (el, names) => { for (const n of names) el.dispatchEvent(new Event(n, {bubbles: true})); };
  // Move a slider to its far end; choose the next option of a select.
  const slide = (key) => {
    const el = document.querySelector(key); if (!el) return null;
    const min = parseFloat(el.min || 0), max = parseFloat(el.max || 100), v = parseFloat(el.value);
    el.value = String(v < (min + max) / 2 ? max : min);
    fire(el, ['input', 'change']);
    return el.value;
  };
  const choose = (key) => {
    const el = document.querySelector(key); if (!el || el.options.length < 2) return null;
    el.selectedIndex = (el.selectedIndex + 1) % el.options.length;
    fire(el, ['input', 'change']);
    return el.options[el.selectedIndex].text;
  };
  const clearField = (key) => {
    const el = document.querySelector(key); if (!el) return false;
    el.focus();
    if (typeof el.select === 'function') el.select(); else document.execCommand('selectAll');
    return true;
  };

  // Keyboard focus: what the Tab key just landed on.
  const focused = () => {
    const el = document.activeElement;
    if (!el || el === document.body || el === document.documentElement) return null;
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    return {key: path(el), show: show(el), x: r.left, y: r.top, w: r.width, h: r.height,
            seen: r.width > 0 && r.height > 0 && !!top && (top === el || el.contains(top)),   // not clipped away or covered
            outlined: (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) || cs.boxShadow !== 'none'};
  };
  // The box the text of the control at a point is drawn in (the glyphs, not the whole control).
  const textBoxAt = (x, y) => {
    let el = document.elementFromPoint(x, y);
    if (!el) return null;
    el = el.closest('button, a, [role="button"], label, summary') || el;
    const range = document.createRange(), walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let box = null;
    while (walker.nextNode()) {
      if (!walker.currentNode.nodeValue.trim()) continue;
      range.selectNodeContents(walker.currentNode);
      for (const r of range.getClientRects()) {
        if (r.width < 1 || r.height < 1) continue;
        box = box ? {l: Math.min(box.l, r.left), t: Math.min(box.t, r.top), r: Math.max(box.r, r.right), b: Math.max(box.b, r.bottom)}
                  : {l: r.left, t: r.top, r: r.right, b: r.bottom};
      }
    }
    return box && box.r - box.l >= 8 && box.b - box.t >= 6 ? {x: box.l, y: box.t, width: box.r - box.l, height: box.b - box.t} : null;
  };
  // Running animations that last, and whether the page ever asks if the person wants less motion.
  const motion = () => {
    let long = 0, endless = 0;
    for (const a of (document.getAnimations ? document.getAnimations() : [])) {
      const t = a.effect && a.effect.getComputedTiming ? a.effect.getComputedTiming() : {};
      if (t.iterations === Infinity) endless++;
      else if ((t.duration || 0) * (t.iterations || 1) >= 600) long++;
    }
    return {long, endless, asks: /prefers-reduced-motion/.test(document.documentElement.outerHTML)};
  };
  // The main visual (the largest canvas, svg, image or video that takes a real share of the screen), and how much
  // of it other painted elements sit on top of.
  const paints = (top, stop) => {
    for (let e = top; e && e !== stop && !e.contains(stop); e = e.parentElement) {
      const cs = getComputedStyle(e);
      const m = /rgba?\(([^)]+)\)/.exec(cs.backgroundColor);
      const alpha = m ? (m[1].split(',').length > 3 ? parseFloat(m[1].split(',')[3]) : 1) : 0;
      if (alpha > 0.3 || cs.backgroundImage !== 'none' || (cs.backdropFilter && cs.backdropFilter !== 'none')) return e;
      if (['IMG', 'CANVAS', 'VIDEO', 'SVG'].includes(e.tagName.toUpperCase())) return e;
    }
    return null;
  };
  const mainVisual = () => {
    const vw = window.innerWidth, vh = window.innerHeight;
    let best = null, area = 0;
    for (const el of document.querySelectorAll('canvas, svg, img, video')) {
      if (!visible(el) || getComputedStyle(el).pointerEvents === 'none') continue;
      const r = el.getBoundingClientRect();
      const w = Math.min(r.right, vw) - Math.max(r.left, 0), h = Math.min(r.bottom, vh) - Math.max(r.top, 0);
      if (w > 0 && h > 0 && w * h > area) { area = w * h; best = el; }
    }
    if (!best || area < 0.12 * vw * vh) return null;
    const r = best.getBoundingClientRect();
    const x0 = Math.max(r.left, 0), y0 = Math.max(r.top, 0), x1 = Math.min(r.right, vw), y1 = Math.min(r.bottom, vh);
    let covered = 0, n = 0;
    const by = {};
    for (let i = 0; i < 10; i++) for (let j = 0; j < 10; j++) {
      n++;
      const top = document.elementFromPoint(x0 + (x1 - x0) * (i + 0.5) / 10, y0 + (y1 - y0) * (j + 0.5) / 10);
      if (!top || top === best || best.contains(top) || top.contains(best)) continue;
      const painter = paints(top, best);
      if (painter) { covered++; const name = show(painter); by[name] = (by[name] || 0) + 1; }
    }
    const most = Object.keys(by).sort((a, b) => by[b] - by[a])[0] || null;
    return {key: path(best), show: show(best), share: area / (vw * vh), covered: covered / n, by: most};
  };

  window.__look = {path, show, visible, actionables, locate, rest, after, texts, sig, slide, choose, clearField,
                   focused, textBoxAt, motion, mainVisual};
})();
"""


def install(page):
    """Arrange for the guard and the helper to be on every page this target loads, and for script errors to queue."""
    page._enable("Page")
    page._enable("Runtime")
    page.conn.send("Page.addScriptToEvaluateOnNewDocument", {"source": GUARD_JS + HELPER_JS})


def mouse(page, kind, x, y, **extra):
    params = {"type": kind, "x": float(x), "y": float(y)}
    params.update(extra)
    page.conn.send("Input.dispatchMouseEvent", params)


def click(page, x, y):
    mouse(page, "mouseMoved", x, y)
    mouse(page, "mousePressed", x, y, button="left", buttons=1, clickCount=1)
    mouse(page, "mouseReleased", x, y, button="left", clickCount=1)


def drag(page, x, y, dx, dy, steps=8):
    mouse(page, "mouseMoved", x, y)
    mouse(page, "mousePressed", x, y, button="left", buttons=1, clickCount=1)
    for i in range(1, steps + 1):
        mouse(page, "mouseMoved", x + dx * i / steps, y + dy * i / steps, button="left", buttons=1)
    mouse(page, "mouseReleased", x + dx, y + dy, button="left", clickCount=1)


KEYS = {"Enter": ("Enter", 13, "\r"), "Tab": ("Tab", 9, None), "Escape": ("Escape", 27, None), " ": ("Space", 32, " "),
        "Space": ("Space", 32, " "), "ArrowLeft": ("ArrowLeft", 37, None), "ArrowUp": ("ArrowUp", 38, None),
        "ArrowRight": ("ArrowRight", 39, None), "ArrowDown": ("ArrowDown", 40, None), "Home": ("Home", 36, None),
        "End": ("End", 35, None), "Backspace": ("Backspace", 8, None), "Delete": ("Delete", 46, None)}


def press(page, key):
    """Press and release one key by its DOM name ("Enter", "ArrowLeft", "a")."""
    code, vk, text = KEYS.get(key, (None, None, None))
    name = " " if key == "Space" else key
    if code is None:
        code, vk, text = ("Key" + key.upper() if len(key) == 1 and key.isalpha() else key), (ord(key.upper()) if len(key) == 1 else 0), (key if len(key) == 1 else None)
    down = {"type": "keyDown", "key": name, "code": code, "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk}
    if text:
        down["text"] = text
    page.conn.send("Input.dispatchKeyEvent", down)
    page.conn.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": name, "code": code, "windowsVirtualKeyCode": vk,
                                              "nativeVirtualKeyCode": vk})


def errors(page):
    """Script errors the page has thrown since the last call (uncaught exceptions and console.error)."""
    out = []
    router = page.conn.router
    while True:
        ev = router.take_event("Runtime.exceptionThrown")
        if ev is None:
            break
        d = ev.get("exceptionDetails") or {}
        out.append(str((d.get("exception") or {}).get("description") or d.get("text") or "script error").split("\n")[0][:200])
    while True:
        ev = router.take_event("Runtime.consoleAPICalled", lambda p: p.get("type") == "error")
        if ev is None:
            break
        args = ev.get("args") or []
        out.append("console.error: " + " ".join(str(a.get("value", a.get("description", ""))) for a in args)[:200])
    router.clear("Runtime.consoleAPICalled")
    return out


FRAME_SCALE = 0.25


def frame(page, scale=FRAME_SCALE):
    """A small screenshot of the viewport, for telling whether anything visible changed."""
    size = page.evaluate("[window.innerWidth, window.innerHeight]")
    return page.screenshot(clip={"x": 0, "y": 0, "width": size[0], "height": size[1], "scale": scale})


def differs(a, b, step=1, tolerance=24, enough=12, ignore=None):
    """Whether two PNGs of the same size differ anywhere that matters (more than a handful of pixels).
    `ignore` lists boxes (x0, y0, x1, y1) in image pixels left out of the comparison."""
    ia, ib = pixels.decode_png(a), pixels.decode_png(b)
    if (ia.width, ia.height) != (ib.width, ib.height):
        return True
    changed = 0
    for y in range(0, ia.height, step):
        for x in range(0, ia.width, step):
            if ignore and any(box[0] <= x <= box[2] and box[1] <= y <= box[3] for box in ignore):
                continue
            pa, pb = ia.pixel(x, y), ib.pixel(x, y)
            if abs(pa[0] - pb[0]) + abs(pa[1] - pb[1]) + abs(pa[2] - pb[2]) > tolerance:
                changed += 1
                if changed > enough:
                    return True
    return False


def _linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def contrast(png):
    """How far apart the light and dark ends of a small picture are, as a WCAG contrast ratio. Over the box a
    label is drawn in, that is the label against what is behind it: the glyphs are one end and the ground the other."""
    img = pixels.decode_png(png)
    lums = sorted(0.2126 * _linear(p[0]) + 0.7152 * _linear(p[1]) + 0.0722 * _linear(p[2])
                  for p in (img.pixel(x, y) for y in range(img.height) for x in range(img.width)))
    if not lums:
        return None
    lo, hi = lums[int(0.03 * (len(lums) - 1))], lums[int(0.97 * (len(lums) - 1))]
    return (hi + 0.05) / (lo + 0.05)


FOCUS_TABS = 14     # Tab presses at most
FOCUS_CHECKS = 6    # controls whose focused and unfocused looks are compared


def focus_walk(page):
    """Tab through the page. A control that looks the same with keyboard focus as without it leaves a keyboard
    user with no idea where they are, and so does one that takes focus where nobody can see it. Returns findings."""
    size = page.evaluate("[window.innerWidth, window.innerHeight]")
    mouse(page, "mouseMoved", 2, size[1] - 2)          # hover styles are not focus styles
    seen, pending, same, hidden = set(), None, [], []

    def settle(pending):
        info, clip, lit = pending
        if not differs(lit, page.screenshot(clip=clip)):
            same.append(info)

    for _ in range(FOCUS_TABS):
        press(page, "Tab")
        time.sleep(0.15)
        info = page.evaluate("typeof __look === 'object' ? __look.focused() : null")
        if pending:
            settle(pending)
            pending = None
        if not info or info["key"] in seen:
            break
        seen.add(info["key"])
        inside = info["x"] >= 0 and info["y"] >= 0 and info["x"] + info["w"] <= size[0] and info["y"] + info["h"] <= size[1]
        if not info["seen"]:
            hidden.append(info)
        elif len(seen) <= FOCUS_CHECKS and inside:
            x, y = max(0, info["x"] - 6), max(0, info["y"] - 6)
            clip = {"x": x, "y": y, "width": min(size[0] - x, info["w"] + 12), "height": min(size[1] - y, info["h"] + 12)}
            pending = (info, clip, page.screenshot(clip=clip))
    if pending:
        page.evaluate("document.activeElement && document.activeElement.blur()")
        time.sleep(0.1)
        settle(pending)
    page.evaluate("document.activeElement && document.activeElement.blur()")
    findings = []
    if same:
        names = ", ".join(i["show"] for i in same[:4]) + (" and %d more" % (len(same) - 4) if len(same) > 4 else "")
        why = ("a focus outline is set but none shows; an ancestor with overflow hidden may be clipping it"
               if all(i["outlined"] for i in same) else "no ring, no change")
        findings.append({"kind": "focus-static", "selector": same[0]["show"],
                         "detail": "%s the same with keyboard focus as without: %s" % (
                             "it looks" if len(same) == 1 else "%d controls (%s) look" % (len(same), names), why)})
    if hidden:
        names = ", ".join(i["show"] for i in hidden[:4]) + (" and %d more" % (len(hidden) - 4) if len(hidden) > 4 else "")
        findings.append({"kind": "focus-hidden", "selector": hidden[0]["show"],
                         "detail": "the Tab key lands on %d control%s nobody can see (%s): collapsed, covered or off screen, "
                                   "but still in the tab order" % (len(hidden), "" if len(hidden) == 1 else "s", names)})
    return findings


def unreachable(steps):
    """Things that answered a click in the walk but that the Tab key can never land on."""
    mouse_only = [s for s in steps if s["kind"] == "click" and not s["keyboard"] and s["changed"]]
    if not mouse_only:
        return []
    first = mouse_only[0]
    groups = {s["group"] for s in mouse_only}
    where = first["show"] if len(mouse_only) == 1 else (first["show"].rsplit(" > ", 1)[0] if len(groups) == 1 and " > " in first["show"] else first["show"])
    count = "it answers" if len(mouse_only) == 1 else "%d things here answer" % len(mouse_only)
    return [{"kind": "no-keyboard", "selector": where,
             "detail": "%s a click but the Tab key never reaches it: not a button or link, and no tabindex" % count}]


def _reset_like(a):
    return bool(RESET_LIKE.search(a.get("label") or ""))


def _next(acts, done, per_group):
    live = [a for a in acts if a["key"] not in done and not a["disabled"] and a["kind"] != "skip"
            and a["w"] >= 4 and a["h"] >= 4 and per_group.get(a["group"], 0) < GROUP_CAP]
    first = [a for a in live if not _reset_like(a)]
    return (first or live or [None])[0]


def _perform(page, a):
    """Act on one thing the way a person would. Returns (verb, where it was), or None when it is no longer there."""
    key = json.dumps(a["key"])
    at = page.evaluate("__look.locate(%s)" % key)
    if not at:
        return None
    kind = a["kind"]
    if kind == "range":
        page.evaluate("__look.slide(%s)" % key)
        return "slid", at
    if kind == "select":
        page.evaluate("__look.choose(%s)" % key)
        return "chose from", at
    if kind == "text":
        click(page, at["x"], at["y"])
        page.evaluate("__look.clearField(%s)" % key)
        page.conn.send("Input.insertText", {"text": "7" if a.get("numeric") else "Lemon 12"})
        if not a.get("multiline"):
            press(page, "Enter")
        return "typed in", at
    if kind == "canvas":
        drag(page, at["x"], at["y"], at["w"] * 0.25, 0)
        drag(page, at["x"], at["y"], 0, at["h"] * 0.2)
        return "dragged", at
    click(page, at["x"], at["y"])
    return "clicked", at


def walk(page, limit=WALK_STEPS, checks_js=None, known=()):
    """Act on everything on the page once, in page order, resets last. Returns {"steps": [...], "findings": [...]}.
    `checks_js` is the look's layout pass (an expression returning [{kind, selector, detail}]); it is run again after
    every action, and what it finds that is not already in `known` ((kind, selector) pairs) is reported with the
    action that brought it out."""
    known = set(known)
    rest = page.evaluate("__look.rest()")
    errors(page)                                    # anything thrown while loading is the load's, not the walk's
    steps, findings, done, per_group = [], [], set(), {}
    texts, sig = rest["texts"], rest["sig"]
    shot = frame(page)
    time.sleep(SETTLE)
    still = frame(page)
    moving = differs(shot, still)                   # a page that animates by itself: a pixel change proves nothing
    shot, last_own = still, []
    while len(steps) < limit:
        acts = page.evaluate("typeof __look === 'object' ? __look.actionables() : null")
        nxt = _next(acts, done, per_group) if acts else None
        if nxt is None:
            break
        done.add(nxt["key"])
        per_group[nxt["group"]] = per_group.get(nxt["group"], 0) + 1
        did = _perform(page, nxt)
        if did is None:
            continue
        verb, at = did
        time.sleep(SETTLE)
        now = page.evaluate("typeof __look === 'object' ? __look.after(%s) : null" % json.dumps(nxt["key"]))
        if now is None:                             # the page went somewhere else
            break
        seen = frame(page)
        # a focus ring or hover style arriving on this control, or leaving the last one, is not the page changing
        own = [FRAME_SCALE * v for v in (at["x"] - at["w"] / 2 - 8, at["y"] - at["h"] / 2 - 8,
                                         at["x"] + at["w"] / 2 + 8, at["y"] + at["h"] / 2 + 8)]
        if now["sig"] != sig:
            changed = True
        elif moving:
            changed = None                          # can't tell: the picture changes on its own
        else:
            changed = differs(shot, seen, ignore=([] if nxt["kind"] == "canvas" else [own]) + last_own)
        last_own = [own]
        step = {"n": len(steps) + 1, "verb": verb, "kind": nxt["kind"], "key": nxt["key"], "show": nxt["show"],
                "label": nxt["label"], "group": nxt["group"], "changed": changed, "keyboard": nxt["keyboard"],
                "of": sum(1 for a in acts if a["group"] == nxt["group"]),      # siblings with the same parent and tag
                "said": [t for t in now["texts"] if t not in texts and len(t) > 1][:3], "errors": errors(page)}
        steps.append(step)
        shot = seen
        what = _name(step)
        for message in step["errors"]:
            if not any(f["kind"] == "js-error" and message in f["detail"] for f in findings):
                findings.append({"kind": "js-error", "selector": step["show"],
                                 "detail": "%s, thrown when the look %s (action %d)" % (message, what, step["n"])})
        for u in now["uneven"]:
            findings.append({"kind": "uneven", "selector": u["selector"],
                             "detail": "after the look %s (action %d) its %d matching <%s> children are no longer one size: %s run %d to %dpx "
                                       "(all %dx%d before)" % (what, step["n"], u["n"], u["tag"], u["dim"], u["min"], u["max"],
                                                               u["was"][0], u["was"][1])})
        if checks_js:
            for f in page.evaluate(checks_js) or []:
                if (f["kind"], f["selector"]) not in known:
                    known.add((f["kind"], f["selector"]))
                    findings.append(dict(f, state="after the look %s (action %d)" % (what, step["n"])))
        texts, sig = now["texts"], now["sig"]
    findings += _dead(steps)
    return {"steps": steps, "findings": findings}


def _unquote(text):
    text = text.strip()
    return text[1:-1] if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'" else text


def parse_steps(script):
    """A scripted play, one step per `;` or line:
    `click SEL`, `hover SEL`, `type TEXT into SEL`, `press KEY`, `drag SEL by DX,DY`, `wait MS`,
    `expect TEXT` (the page says it), `expect SEL says TEXT`, `expect no TEXT`. TEXT may be a /regex/."""
    steps = []
    for raw in re.split(r"[;\n]", script):
        raw = raw.strip()
        if not raw:
            continue
        verb, _, rest = raw.partition(" ")
        verb, rest = verb.lower(), rest.strip()
        if verb in ("click", "hover") and rest:
            steps.append({"do": verb, "sel": rest, "raw": raw})
        elif verb == "type" and " into " in rest:
            text, _, sel = rest.rpartition(" into ")
            steps.append({"do": "type", "text": _unquote(text), "sel": sel.strip(), "raw": raw})
        elif verb == "press" and rest:
            steps.append({"do": "press", "key": rest, "raw": raw})
        elif verb == "drag" and " by " in rest:
            sel, _, by = rest.rpartition(" by ")
            dx, _, dy = by.partition(",")
            steps.append({"do": "drag", "sel": sel.strip(), "dx": float(dx), "dy": float(dy or 0), "raw": raw})
        elif verb == "wait" and rest:
            steps.append({"do": "wait", "ms": float(rest), "raw": raw})
        elif verb == "expect" and rest:
            if rest.lower().startswith("no "):
                steps.append({"do": "expect", "text": _unquote(rest[3:]), "negate": True, "raw": raw})
            elif " says " in rest:
                sel, _, text = rest.partition(" says ")
                steps.append({"do": "expect", "sel": sel.strip(), "text": _unquote(text), "raw": raw})
            else:
                steps.append({"do": "expect", "text": _unquote(rest), "raw": raw})
        else:
            raise ValueError("a play step the look doesn't know: %r (steps are click, hover, type ... into, press, "
                             "drag ... by, wait, expect)" % raw)
    return steps


def _says(seen, text):
    m = re.match(r"^/(.*)/([a-z]*)$", text, re.S)
    if m:
        return bool(re.search(m.group(1), seen, re.I if "i" in m.group(2) else 0))
    return text.casefold() in seen.casefold()


TEXT_OF_JS = ("(() => { const sel = %s; const el = sel ? document.querySelector(sel) : document.body; if (!el) return null;"
              " return String(el.innerText || el.value || el.textContent || '').replace(/\\s+/g, ' ').trim(); })()")


def run(page, script, checks_js=None, known=()):
    """Run one scripted play from the page as loaded, holding it to the walk's invariants at every action.
    Returns {"actions": n, "expects": [{ok, raw, saw}], "findings": [...]}."""
    known = set(known)
    try:
        steps = parse_steps(script)
    except ValueError as exc:
        return {"actions": 0, "expects": [], "findings": [{"kind": "play", "selector": "body", "detail": str(exc)}]}
    rest = page.evaluate("__look.rest()")
    errors(page)
    texts, last_said, actions, expects, findings = rest["texts"], [], 0, [], []
    for n, st in enumerate(steps, 1):
        if st["do"] == "wait":
            time.sleep(st["ms"] / 1000.0)
            continue
        if st["do"] == "expect":
            sel = st.get("sel")
            seen = page.evaluate(TEXT_OF_JS % json.dumps(sel))
            ok = seen is not None and (_says(seen, st["text"]) != bool(st.get("negate")))
            expects.append({"ok": ok, "raw": st["raw"], "saw": seen})
            if not ok:
                after = "after %d action%s" % (actions, "" if actions == 1 else "s")
                if seen is None:
                    told = "nothing on the page matches %s" % sel
                elif st.get("negate"):
                    told = "it does"
                elif sel:
                    told = 'it says "%s"' % seen[:120]
                else:
                    told = ("the last thing it said was %s" % _quoted(last_said)) if last_said else "it said nothing new"
                findings.append({"kind": "expect", "selector": sel or "body",
                                 "detail": "expected %s %sto say \"%s\" %s; %s" % (sel or "the page", "not " if st.get("negate") else "",
                                                                                 st["text"], after, told)})
            continue
        key = None
        if st["do"] == "press":
            press(page, st["key"])
        else:
            key = st["sel"]
            try:
                at = page.evaluate("__look.locate(%s)" % json.dumps(key))
            except Exception:
                at = None
            if not at:
                findings.append({"kind": "play", "selector": key,
                                 "detail": "step %d (%s): nothing visible on the page matches %s, so the play stopped there "
                                           "after %d action%s" % (n, st["raw"], key, actions, "" if actions == 1 else "s")})
                break
            if st["do"] == "click":
                click(page, at["x"], at["y"])
            elif st["do"] == "hover":
                mouse(page, "mouseMoved", at["x"], at["y"])
            elif st["do"] == "drag":
                drag(page, at["x"], at["y"], st["dx"], st["dy"])
            else:
                click(page, at["x"], at["y"])
                page.evaluate("__look.clearField(%s)" % json.dumps(key))
                page.conn.send("Input.insertText", {"text": st["text"]})
        actions += 1
        time.sleep(SETTLE)
        now = page.evaluate("typeof __look === 'object' ? __look.after(%s) : null" % json.dumps(key))
        if now is None:
            break
        said = [t for t in now["texts"] if t not in texts and len(t) > 1]
        last_said = said or last_said
        where = "after step %d (%s)" % (n, st["raw"])
        for message in errors(page):
            if not any(f["kind"] == "js-error" and message in f["detail"] for f in findings):
                findings.append({"kind": "js-error", "selector": key or "body", "detail": "%s, thrown %s" % (message, where)})
        for u in now["uneven"]:
            findings.append({"kind": "uneven", "selector": u["selector"],
                             "detail": "%s its %d matching <%s> children are no longer one size: %s run %d to %dpx "
                                       "(all %dx%d before)" % (where, u["n"], u["tag"], u["dim"], u["min"], u["max"],
                                                               u["was"][0], u["was"][1])})
        if checks_js:
            for f in page.evaluate(checks_js) or []:
                if (f["kind"], f["selector"]) not in known:
                    known.add((f["kind"], f["selector"]))
                    findings.append(dict(f, state=where))
        texts = now["texts"]
    return {"actions": actions, "expects": expects, "findings": findings}


def _dead(steps):
    """A page where nothing a person clicks has any effect: no text, no state, no pixel. One control that does
    nothing proves little (a pager dot for the page already showing), so single ones are told in the account of
    the walk and only a page with no response at all is reported."""
    clicks = [s for s in steps if s["kind"] == "click"]
    if len(clicks) >= 2 and all(s["changed"] is False for s in clicks):
        return [{"kind": "dead", "selector": "body",
                 "detail": "the look clicked %d controls and nothing on the page changed: no text, no state, no pixel. "
                           "Is the script running?" % len(clicks)}]
    return []


def _quoted(lines, most=5):
    lines = list(dict.fromkeys(lines))
    if len(lines) > most:
        return ", ".join('"%s"' % t for t in lines[:2]) + ", ... " + ", ".join('"%s"' % t for t in lines[-2:])
    return ", ".join('"%s"' % t for t in lines)


def _outcome(steps):
    said = [t for s in steps for t in s["said"]]
    if said:
        return "the page said " + _quoted(said)
    if any(s["changed"] for s in steps):
        return "the page changed"
    if all(s["changed"] is False for s in steps):
        return "nothing changed"
    return "the page animates by itself, so the look can't tell what that did"


def account(steps):
    """The walk as a few lines a builder can read instead of a screenshot: what was done, and what the page said."""
    runs = []                                  # consecutive steps on sibling controls with the same kind of outcome
    for s in steps:
        mood = "said" if s["said"] or s["changed"] else ("none" if s["changed"] is False else "unknown")
        if runs and s["of"] > 2 and runs[-1]["group"] == s["group"] and runs[-1]["mood"] == mood:
            runs[-1]["steps"].append(s)
        else:
            runs.append({"group": s["group"], "mood": mood, "steps": [s]})
    lines, last = [], None
    for run in runs:
        first, n = run["steps"][0], len(run["steps"])
        if first["of"] > 2 and (n > 1 or last == run["group"]):
            home = first["show"].rsplit(" > ", 1)[0] if " > " in first["show"] else "the page"
            what = ("%s %d more" % (first["verb"], n) if last == run["group"]
                    else "%s %d of the %d matching controls in %s" % (first["verb"], n, first["of"], home))
        else:
            what = _name(first)
        thrown = [e for s in run["steps"] for e in s["errors"]]
        lines.append("%s: %s%s" % (what, _outcome(run["steps"]), " (threw %s)" % thrown[0] if thrown else ""))
        last = run["group"]
    return lines


def _name(step):
    """How a step reads in a sentence: `clicked "New game"`, `clicked #board > button:nth-of-type(3)`."""
    return "%s %s" % (step["verb"], ('"%s"' % step["label"]) if step["label"] else step["show"])
