#!/usr/bin/env python3
"""A page for people, not graders: every build of the confirmation test, live and labelled, one task at a time.
Each card runs the build itself (scaled from a 1280x800 desktop), with its arm, run, scores from both grading passes, and the
angle it was dealt (full build) or the kind it built (quick mode). "Open" shows it full size with the graders' notes.
Usage: python3 gallery.py      Writes gallery.html next to this file; then python3 gallery_server.py and open
http://localhost:8137/gallery.html (the server keeps the builds' saved state apart)."""
import glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = [("t1-pelican", "Pelican", "an SVG animation of a pelican riding a bike"),
         ("t2-ascii", "ASCII mixer", "a simple interactive ascii color mixing engine"),
         ("t3-bento", "Bento menu", "a bento box-inspired collapsible UI menu component for a fictional coffee company site"),
         ("t4-blocks", "Block world", "a simple block-building sandbox game with a 32x32 block world")]
ARMS = [("A", "Prompt alone", "the task and nothing else"),
        ("F", "Full build", "a lite dump built by the swarm, read with use mode"),
        ("Q", "Quick mode", "the builder writes its own one-pass dump first")]


def notes(results, run):
    return [{"grader": k.rsplit("/", 1)[0], "note": v} for k, v in sorted(results["notes"].items()) if k.endswith("/" + run)]


def main():
    process = json.load(open(os.path.join(HERE, "process.json")))
    data = []
    for task, short, prompt in TASKS:
        d = os.path.join(HERE, task)
        reg = json.load(open(os.path.join(d, "results.json")))
        full = json.load(open(os.path.join(d, "results-full.json")))
        func = json.load(open(os.path.join(d, "functional.json")))
        arms = []
        for arm, name, what in ARMS:
            runs = []
            for n in range(1, 5):
                run = "%s-r%d" % (arm, n)
                label = None
                if arm == "F":
                    label = "dealt: " + (process[task][run]["angle"] or "?")
                elif arm == "Q":
                    built = json.load(open(os.path.join(d, "dumps", run + ".metadump.json"))).get("built") or []
                    label = "built: " + (built[0] if built else "?")
                checks = func[run]["checks"]
                runs.append({"run": run, "src": "%s/runs/%s.html" % (task, run), "label": label,
                             "reg": reg["scores"][arm]["per_run_overall"][run], "full": full["scores"][arm]["per_run_overall"][run],
                             "checks": [sum(v is True for v in checks.values()), len(checks)],
                             "failed": [k for k, v in checks.items() if v is False],
                             "notes_reg": notes(reg, run), "notes_full": notes(full, run)})
            arms.append({"arm": arm, "name": name, "what": what, "reg": reg["scores"][arm]["overall"], "full": full["scores"][arm]["overall"],
                         "runs": runs})
        data.append({"id": task, "short": short, "prompt": prompt, "arms": arms})
    html = PAGE.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False))
    with open(os.path.join(HERE, "gallery.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("gallery.html written:", sum(len(a["runs"]) for t in data for a in t["arms"]), "builds")


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Confirmation Test Builds</title>
<style>
:root{--bg:#f6f5f2;--card:#fff;--ink:#17171a;--muted:#62626b;--line:#dcdad4;--chip:#efede8;--accent:#2f5bd3;
  --A:#7b7b86;--F:#b4532a;--Q:#1f7a5a;--shadow:0 1px 2px rgba(0,0,0,.06),0 2px 10px rgba(0,0,0,.04)}
@media (prefers-color-scheme:dark){:root{--bg:#141417;--card:#1d1d22;--ink:#ececf0;--muted:#a0a0aa;--line:#33333b;--chip:#2a2a31;
  --accent:#8aa8ff;--A:#9a9aa6;--F:#e08a5e;--Q:#4fc39a;--shadow:none}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:14px 20px 0}
h1{font-size:18px;margin:0 0 2px;font-weight:650;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:13px;margin:0 0 10px;max-width:110ch}
nav{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);display:flex;gap:4px;overflow-x:auto;padding:0 20px}
nav button{font:inherit;font-weight:550;border:0;background:none;color:var(--muted);padding:8px 12px 10px;border-bottom:2px solid transparent;cursor:pointer;white-space:nowrap}
nav button[aria-selected=true]{color:var(--ink);border-bottom-color:var(--ink)}
nav button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px;border-radius:4px}
main{padding:16px 20px 40px}
.prompt{font-size:15px;margin:0 0 4px}.prompt q{font-weight:600}
.key{color:var(--muted);font-size:13px;margin:0 0 14px}
section.arm{margin:0 0 26px}
.armhead{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:0 0 8px}
.armhead h2{font-size:16px;margin:0;display:flex;align-items:center;gap:8px}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block}
.armhead .what{color:var(--muted);font-size:13px}
.armhead .mean{margin-left:auto;font-size:13px;color:var(--muted)}
.armhead .mean b{color:var(--ink);font-variant-numeric:tabular-nums}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
@media (max-width:1100px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:620px){.grid{grid-template-columns:1fr}header,main,nav{padding-left:16px;padding-right:16px}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;box-shadow:var(--shadow);display:flex;flex-direction:column}
.frame{position:relative;width:100%;aspect-ratio:1280/800;overflow:hidden;background:#fff;border-bottom:1px solid var(--line)}
.frame iframe{position:absolute;left:0;top:0;width:1280px;height:800px;border:0;transform-origin:0 0;transform:scale(var(--s,.25))}
.meta{padding:9px 11px 10px;display:flex;flex-direction:column;gap:5px}
.row1{display:flex;align-items:center;gap:8px}
.run{font-weight:650;font-variant-numeric:tabular-nums}
.scores{margin-left:auto;display:flex;gap:6px;font-size:12.5px;font-variant-numeric:tabular-nums}
.sc{background:var(--chip);border-radius:6px;padding:1px 7px;white-space:nowrap}
.sc b{font-weight:650}
.label{font-size:13px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row2{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.checks{font-size:12px;color:var(--muted)}
.checks.warn{color:var(--F)}
.btns{margin-left:auto;display:flex;gap:6px}
.btn{font:inherit;font-size:13px;font-weight:550;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:7px;padding:4px 10px;cursor:pointer;text-decoration:none;line-height:1.3}
.btn:hover{border-color:var(--muted)}
.btn:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.btn.primary{background:var(--ink);color:var(--card);border-color:var(--ink)}
/* full-size view */
#viewer{position:fixed;inset:0;z-index:20;background:var(--bg);display:none;flex-direction:column}
#viewer.open{display:flex}
.vbar{display:flex;align-items:center;gap:10px;padding:10px 16px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.vtitle{font-weight:650}
.vlabel{color:var(--muted);font-size:13px}
.vbar .sp{flex:1}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{font:inherit;font-size:13px;border:0;background:var(--card);color:var(--muted);padding:5px 10px;cursor:pointer}
.seg button[aria-pressed=true]{background:var(--ink);color:var(--card)}
.vbody{flex:1;display:flex;min-height:0}
.stage{flex:1;display:flex;justify-content:center;align-items:stretch;background:var(--chip);min-width:0;overflow:auto}
.stage iframe{border:0;background:#fff;width:100%;height:100%}
.stage.phone iframe{width:390px;height:844px;max-height:100%;margin:16px auto;border-radius:18px;box-shadow:0 0 0 1px var(--line),0 8px 30px rgba(0,0,0,.15)}
aside{width:340px;border-left:1px solid var(--line);overflow:auto;padding:14px 16px;font-size:13.5px}
aside h3{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:14px 0 6px}
aside h3:first-child{margin-top:0}
aside p{margin:0 0 8px}
aside .g{color:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}
aside.hidden{display:none}
@media (max-width:900px){aside{display:none}}
</style>
</head>
<body>
<header>
  <h1>Confirmation test: every build, live</h1>
  <p class="sub">metadump 1.0.0, frozen before the tasks were known. Each task was built four times three ways by Sonnet 5.5 at medium effort.
  Every card is the real page running at desktop size, scaled down; you can click and type in it. Scores are the mean overall of 10 from three blind graders:
  <b>reg</b> is the registered grading, <b>full</b> is the pass where graders had to open every file.</p>
</header>
<nav role="tablist" id="tabs" aria-label="Tasks"></nav>
<main id="main"></main>

<div id="viewer" role="dialog" aria-modal="true" aria-labelledby="vtitle">
  <div class="vbar">
    <span class="dot" id="vdot"></span><span class="vtitle" id="vtitle"></span><span class="vlabel" id="vlabel"></span>
    <span class="sp"></span>
    <div class="seg" role="group" aria-label="Width">
      <button id="wDesk" aria-pressed="true">Desktop</button><button id="wPhone" aria-pressed="false">Phone</button>
    </div>
    <button class="btn" id="vReload" title="Start the build again, with nothing saved">Restart</button>
    <button class="btn" id="vNotes" aria-pressed="true">Notes</button>
    <a class="btn" id="vTab" target="_blank" rel="noopener">New tab ↗</a>
    <button class="btn" id="vPrev" aria-label="Previous build">←</button>
    <button class="btn" id="vNext" aria-label="Next build">→</button>
    <button class="btn primary" id="vClose">Close</button>
  </div>
  <div class="vbody">
    <div class="stage" id="stage"><iframe id="vframe" title="Build"></iframe></div>
    <aside id="notes"></aside>
  </div>
</div>

<script>
const DATA = /*DATA*/null;
const COLORS = {A: 'var(--A)', F: 'var(--F)', Q: 'var(--Q)'};
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
// gallery_server.py gives each build's saved state a prefix of its own path (seven block worlds share the key "blocks32").
// Restarting a build clears what it saved, so it starts the way it did in the test: in a fresh browser.
const LOADED = Date.now();      // a fresh query per page load, so the browser never shows a copy cached without that prefix
const url = r => r.src + '?g=' + LOADED;
function restart(frame, r) {
  const p = r.src.replace(/\.html$/, '') + ':';
  [localStorage, sessionStorage].forEach(st => { try { Object.keys(st).filter(k => k.startsWith(p)).forEach(k => st.removeItem(k)); } catch (e) {} });
  frame.src = url(r);
}
let current = null, flat = [], vIndex = 0;
const store = {get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
               set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }};

const tabs = $('#tabs');
DATA.forEach(t => {
  const b = document.createElement('button');
  b.setAttribute('role', 'tab'); b.id = 'tab-' + t.id; b.textContent = t.short;
  b.addEventListener('click', () => show(t.id));
  tabs.appendChild(b);
});
tabs.addEventListener('keydown', e => {
  if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
  const i = DATA.findIndex(t => t.id === current), j = (i + (e.key === 'ArrowRight' ? 1 : -1) + DATA.length) % DATA.length;
  show(DATA[j].id); $('#tab-' + DATA[j].id).focus();
});

const ro = new ResizeObserver(entries => entries.forEach(en => en.target.style.setProperty('--s', en.contentRect.width / 1280)));

function show(id) {
  const t = DATA.find(x => x.id === id) || DATA[0];
  const switching = current && current !== t.id;
  current = t.id; store.set('gallery-tab', t.id);
  if (location.hash.slice(1) !== t.id) history.replaceState(null, '', '#' + t.id);
  DATA.forEach(x => $('#tab-' + x.id).setAttribute('aria-selected', x.id === t.id));
  ro.disconnect();
  flat = [];
  let h = '<p class="prompt">Task: <q>' + esc(t.prompt) + '</q></p>' +
          '<p class="key">Rows are the three arms; columns are runs 1 to 4. "Open" shows a build full size with what each grader wrote.</p>';
  t.arms.forEach(a => {
    h += '<section class="arm"><div class="armhead"><h2><span class="dot" style="background:' + COLORS[a.arm] + '"></span>' + a.arm + ' · ' + esc(a.name) +
         '</h2><span class="what">' + esc(a.what) + '</span><span class="mean">mean <b>' + a.reg.toFixed(2) + '</b> reg · <b>' + a.full.toFixed(2) + '</b> full</span></div><div class="grid">';
    a.runs.forEach(r => {
      const i = flat.length; flat.push({t, a, r});
      const warn = r.failed.length ? ' warn' : '';
      h += '<article class="card"><div class="frame"><iframe loading="lazy" src="' + esc(url(r)) + '" title="' + esc(t.short + ' ' + r.run) + '"></iframe></div>' +
           '<div class="meta"><div class="row1"><span class="run">' + r.run + '</span><span class="scores"><span class="sc"><b>' + r.reg.toFixed(2) +
           '</b> reg</span><span class="sc"><b>' + r.full.toFixed(2) + '</b> full</span></span></div>' +
           (r.label ? '<div class="label" title="' + esc(r.label) + '">' + esc(r.label) + '</div>' : '<div class="label">no dump</div>') +
           '<div class="row2"><span class="checks' + warn + '" title="' + esc(r.failed.length ? 'failed: ' + r.failed.join(', ') : 'all scripted checks passed') + '">checks ' +
           r.checks[0] + '/' + r.checks[1] + (r.failed.length ? ' (' + esc(r.failed.join(', ')) + ')' : '') + '</span><span class="btns">' +
           '<button class="btn" data-reload="' + i + '" title="Start this build again, with nothing saved">↻</button><button class="btn primary" data-open="' + i + '">Open</button></span></div></div></article>';
    });
    h += '</div></section>';
  });
  $('#main').innerHTML = h;
  document.querySelectorAll('.frame').forEach(f => ro.observe(f));
  if (switching && window.scrollY > tabs.offsetTop) window.scrollTo(0, tabs.offsetTop);
}

$('#main').addEventListener('click', e => {
  const o = e.target.closest('[data-open]'), r = e.target.closest('[data-reload]');
  if (o) openViewer(+o.dataset.open);
  if (r) restart(r.closest('.card').querySelector('iframe'), flat[+r.dataset.reload].r);
});

function openViewer(i) {
  vIndex = (i + flat.length) % flat.length;
  const {t, a, r} = flat[vIndex];
  $('#vdot').style.background = COLORS[a.arm];
  $('#vtitle').textContent = t.short + ' · ' + a.arm + ' ' + a.name + ' · ' + r.run;
  $('#vlabel').textContent = (r.label ? r.label + ' · ' : '') + r.reg.toFixed(2) + ' reg · ' + r.full.toFixed(2) + ' full';
  $('#vframe').src = url(r); $('#vframe').title = t.short + ' ' + r.run;
  $('#vTab').href = url(r);
  const list = ns => ns.map(n => '<p><span class="g">' + esc(n.grader) + '</span> ' + esc(n.note) + '</p>').join('');
  $('#notes').innerHTML = '<h3>Registered graders</h3>' + list(r.notes_reg) + '<h3>Full-evidence graders</h3>' + list(r.notes_full) +
    '<h3>Scripted checks</h3><p>' + r.checks[0] + ' of ' + r.checks[1] + ' passed' + (r.failed.length ? '; failed: ' + esc(r.failed.join(', ')) +
    '. These failures came from the capture, not the build (see the write-up).' : '.') + '</p>';
  if (!$('#viewer').classList.contains('open')) {
    $('#viewer').classList.add('open'); document.body.style.overflow = 'hidden';
    document.querySelectorAll('#main iframe').forEach(f => f.style.visibility = 'hidden');
    $('#vClose').focus();
  }
}
function closeViewer() {
  $('#viewer').classList.remove('open'); document.body.style.overflow = '';
  $('#vframe').src = 'about:blank';
  document.querySelectorAll('#main iframe').forEach(f => f.style.visibility = '');
  const b = document.querySelector('[data-open="' + vIndex + '"]'); if (b) b.focus();
}
function setWidth(phone) {
  $('#stage').classList.toggle('phone', phone);
  $('#wDesk').setAttribute('aria-pressed', !phone); $('#wPhone').setAttribute('aria-pressed', phone);
  store.set('gallery-width', phone ? 'phone' : 'desktop');
}
$('#vClose').addEventListener('click', closeViewer);
$('#vPrev').addEventListener('click', () => openViewer(vIndex - 1));
$('#vNext').addEventListener('click', () => openViewer(vIndex + 1));
$('#vReload').addEventListener('click', () => restart($('#vframe'), flat[vIndex].r));
$('#wDesk').addEventListener('click', () => setWidth(false));
$('#wPhone').addEventListener('click', () => setWidth(true));
$('#vNotes').addEventListener('click', e => {
  const shown = !$('#notes').classList.toggle('hidden'); e.currentTarget.setAttribute('aria-pressed', shown);
});
document.addEventListener('keydown', e => {
  if (!$('#viewer').classList.contains('open')) return;
  if (e.key === 'Escape') closeViewer();
  else if (e.key === 'ArrowLeft' && e.target.tagName !== 'INPUT') openViewer(vIndex - 1);
  else if (e.key === 'ArrowRight' && e.target.tagName !== 'INPUT') openViewer(vIndex + 1);
});
setWidth(store.get('gallery-width') === 'phone');
show(location.hash.slice(1) || store.get('gallery-tab') || 't4-blocks');
window.addEventListener('hashchange', () => show(location.hash.slice(1)));
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
