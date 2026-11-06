#!/usr/bin/env python3
"""Render the text tasks' markdown answers as cards and count what can be counted.

Usage: python3 textcards.py t3-poem
Writes <task>/cards/<run>.html (also used by the showcase), <task>/shots/<run>-card.png,
and <task>/functional.json (poem: its lines, and whether its last line ends with a question mark).
Python 3.9 standard library plus the installed Chrome for the screenshot.
"""
import html, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"(?<![\w])_([^_\n]+)_(?![\w])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md_to_html(md):
    """Small markdown subset: headings, lists, quotes, rules, paragraphs; single newlines kept (poems)."""
    out, para, lst = [], [], None

    def flush():
        nonlocal para, lst
        if para:
            out.append("<p>" + "<br>".join(inline(l) for l in para) + "</p>")
            para = []
        if lst:
            tag, items = lst
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % "<br>".join(inline(x) for x in it) for it in items), tag))
            lst = None

    for raw in md.splitlines():
        line = raw.rstrip()
        m_h = re.match(r"^(#{1,6})\s+(.*)$", line)
        m_ol = re.match(r"^\s*(\d+)[.)]\s+(.*)$", line)
        m_ul = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if not line.strip():
            flush()
        elif m_h:
            flush(); n = len(m_h.group(1)); out.append("<h%d>%s</h%d>" % (n, inline(m_h.group(2)), n))
        elif re.match(r"^\s*(---|\*\*\*|___)\s*$", line):
            flush(); out.append("<hr>")
        elif m_ol or m_ul:
            if para:
                out.append("<p>" + "<br>".join(inline(l) for l in para) + "</p>"); para = []
            tag = "ol" if m_ol else "ul"
            if not lst or lst[0] != tag:
                if lst:
                    flush()
                lst = (tag, [])
            lst[1].append([(m_ol or m_ul).group(2 if m_ol else 1)])
        elif line.startswith(">"):
            flush(); out.append("<blockquote>%s</blockquote>" % inline(line.lstrip("> ")))
        elif lst and raw.startswith(("  ", "\t")):
            lst[1][-1].append(line.strip())
        else:
            if lst:
                flush()
            para.append(line.strip())
    flush()
    return "\n".join(out)


CARD_CSS = """
:root{color-scheme:light}html,body{margin:0;min-height:100%}body{background:#fbfaf7;font:18px/1.6 ui-serif,Georgia,serif;color:#1d1c1a}
.card{max-width:680px;margin:0 auto;padding:30px 30px 40px;box-sizing:border-box}
.card.short{min-height:100vh;display:flex;flex-direction:column;justify-content:center;font-size:26px;line-height:1.5;padding:36px 36px}
.card.short p{margin:0 0 22px}.card.short p:last-child{margin:0}
h1,h2,h3{font:600 20px/1.3 system-ui,sans-serif;margin:18px 0 8px}h1{font-size:23px}p{margin:0 0 12px}
ol,ul{padding-left:24px;margin:0 0 12px}li{margin:0 0 12px}code{font:14px ui-monospace,monospace;background:#f1efe9;padding:1px 4px;border-radius:4px}
blockquote{margin:0 0 12px;padding-left:12px;border-left:3px solid #ddd;color:#555}hr{border:0;border-top:1px solid #e6e3dc;margin:16px 0}a{color:#1d4ed8}
"""


def card_html(body, title, short=False):
    return "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>%s</title><style>%s</style><div class='card%s'>%s</div>%s" % (
        html.escape(title), CARD_CSS, " short" if short else "", body, FIT_JS)


# Keep the writer's line breaks: verse lines never wrap; the card's type shrinks until the longest line fits.
FIT_JS = """<script>(() => { const c = document.querySelector('.card'), base = parseFloat(getComputedStyle(c).fontSize)
  const verse = [...c.querySelectorAll('p')].filter(p => p.innerHTML.includes('<br') || p.textContent.length < 70)
  verse.forEach(p => { p.style.whiteSpace = 'nowrap' })
  const fit = () => { let fs = base; c.style.fontSize = fs + 'px'
    while (fs > 11 && verse.some(p => p.scrollWidth > p.clientWidth + 1)) { fs -= 0.5; c.style.fontSize = fs + 'px' } }
  fit(); addEventListener('resize', fit) })()</script>"""


def poem_lines(md):
    """The poem: the longest run of consecutive short, non-heading lines (blank lines between stanzas allowed)."""
    lines = [re.sub(r"^>\s?", "", l).strip() for l in md.splitlines()]
    best, cur, gap = [], [], 0
    for l in lines + ["#end"]:
        if l and not l.startswith("#") and len(l) < 90 and not l.startswith(("(", "*Note", "Note")):
            cur.append(l); gap = 0
        elif not l and cur and gap == 0:
            gap = 1
        else:
            if len(cur) > len(best):
                best = cur
            cur, gap = [], 0
    return [re.sub(r"[*_]", "", l) for l in best]


def main(task):
    d = os.path.join(HERE, task)
    os.makedirs(os.path.join(d, "cards"), exist_ok=True)
    func = {}
    for f in sorted(os.listdir(os.path.join(d, "runs"))):
        if not f.endswith(".md"):
            continue
        run = f[:-3]
        md = open(os.path.join(d, "runs", f), encoding="utf-8").read()
        page = card_html(md_to_html(md), run, short=len(md.split()) < 60)
        cp = os.path.join(d, "cards", run + ".html")
        open(cp, "w", encoding="utf-8").write(page)
        shot = os.path.join(d, "shots", run + "-card.png")
        with tempfile.TemporaryDirectory() as prof:
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--user-data-dir=" + prof, "--window-size=720,1100",
                            "--screenshot=" + shot, "file://" + cp], capture_output=True, timeout=60)
        words = len(md.split())
        lines = poem_lines(md)
        last = re.sub(r"[\s*_\"'”’»)\]]+$", "", lines[-1]) if lines else ""
        func[run] = {"poem_lines": len(lines), "ends_with_question": last.endswith("?"), "last_line": lines[-1] if lines else "", "words_total": words}
        print(run, json.dumps(func[run], ensure_ascii=False))
    json.dump(func, open(os.path.join(d, "functional.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
