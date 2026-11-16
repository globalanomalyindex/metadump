// Film the showcase as a person would on a Mac: each scene sits in a Chrome-for-macOS window, and a native
// macOS cursor, moved by a seeded model of a hand (native/human.mjs), hovers, clicks, reads and scrolls.
// The real pointer events go to the page through CDP (Input.dispatchMouseEvent) so hovers and toggles react;
// headless screencasts carry no OS cursor, so the system's own cursor art is composited on top afterwards,
// at the exact recorded positions. MP4 is encoded in the page with MediaRecorder (no ffmpeg, no installs).
//
// Usage:
//   node record-native.mjs [--showcase DIR] [--tasks LIST] [--out DIR] [--seed N] [--no-cards] [--trace DIR]
//                          [--scene PATH] [--name FILE] [--bare]
//   LIST is comma-separated slug[:kind][@a/b/c], kind = steps | solo | still | hover | click | text | watch | play | turn (default: "steps"
//   when the scene gives steps for every run shown, else from the scene's DATA), a/b/c = the runs to show for the prompt
//   alone, quick mode and the full build (default: the scene's own choice, each side's best-scoring build). Defaults: docs/showcase/round-3, test 24's tasks, ./video. Writes OUT/metadump-ab-linkedin.mp4 (intro, tasks,
//   results, outro), OUT/metadump-ab-<slug>.mp4 and OUT/posters/<slug>.jpg.
// Copied from ab-tests/2026-11-05-recipe-game-lemon-sonnet/ for test 24. Added: the "steps" kind (each build's own
// clicks, taps, slider drags and paint strokes, listed in the scene), three sides per scene (fa, fb, fc), a results card
// between the tasks and the outro. Later, for the block-world case study (native/case.html): --scene, --name, --bare,
// the "solo" kind (one build filling the frame) and the "still" kind (a card with no pointer), scene-set lengths (HOLD),
// go() when filming starts and ['call', name, arg] steps. That cut:
//   node record-native.mjs --bare --no-cards --scene /__native/case.html --tasks Q:solo,A:solo,F:solo,results:still,outro:still \
//     --out video/case-study --name metadump-1.1-block-case-study.mp4
// Ports: CDP 9471, site 8776, frames 8777.
import { spawn } from 'node:child_process'
import { mkdirSync, writeFileSync, readFileSync, mkdtempSync, rmSync, copyFileSync } from 'node:fs'
import { join, dirname, resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { fileURLToPath } from 'node:url'
import { launch, sleep } from './native/cdp.mjs'
import { Hand, seedFor } from './native/human.mjs'

const HERE = dirname(fileURLToPath(import.meta.url)), NATIVE = join(HERE, 'native')
const argv = process.argv.slice(2), opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d }
const SHOWCASE = resolve(opt('--showcase', join(HERE, '..', '..', 'docs', 'showcase', 'round-3')))
const TASKS = opt('--tasks', 't1-pelican,t2-ascii,t3-bento,t4-blocks').split(',').filter(Boolean).map(s => {
  const [head, pair] = s.split('@'), [slug, kind] = head.split(':'), [a, b, c] = (pair || '').split('/')
  return { slug, kind, a, b, c }
})
const OUT = resolve(opt('--out', join(HERE, 'video'))), POSTERS = join(OUT, 'posters'), SEED = +opt('--seed', 12), CARDS = !argv.includes('--no-cards')
const TRACE = opt('--trace', null)
// --scene: the page that lays out each scene (default the showcase's scene.html; the block-world case study is
// /__native/case.html). --name: the main video's file name. A scene page may set window.HOLD = { slug: ms } to fix how
// long a card lasts, or how long a build scene lasts at least.
const SCENE = opt('--scene', '/scene.html'), NAME = opt('--name', 'metadump-ab-linkedin.mp4')
// --bare: no Chrome window drawn around the scene; it fills the frame. A scene page may define go(), called the moment
// filming starts (captions and count-ups begin there), and functions its steps call with ['call', name, arg].
const BARE = argv.includes('--bare')
const CDP_PORT = 9471, SITE = 8776, RECPORT = 8777
const CS = 2   // cursor art scale: px per macOS point (a Retina recording)
mkdirSync(POSTERS, { recursive: true }); if (TRACE) mkdirSync(TRACE, { recursive: true })

const REC = mkdtempSync(join(tmpdir(), 'metadump-native-'))
for (const port of [SITE, RECPORT, CDP_PORT]) {   // a stale server would quietly serve the wrong showcase
  try { await fetch(`http://127.0.0.1:${port}/`); console.error(`port ${port} is already in use; stop that process first`); process.exit(1) } catch {}
}
// python3 on macOS can be a shim with a child process: start each server in its own group and kill the group.
const server = args => spawn('python3', args, { stdio: 'ignore', detached: true })
const site = server([join(NATIVE, 'serve.py'), SHOWCASE, String(SITE)])
const recsrv = server(['-m', 'http.server', String(RECPORT), '--bind', '127.0.0.1', '--directory', REC])
const c = await launch({ port: CDP_PORT, width: 1080, height: 1350 })
const { send, evaluate } = c
const killGroup = p => { try { process.kill(-p.pid) } catch {} }
const cleanup = () => { c.close(); killGroup(site); killGroup(recsrv); rmSync(REC, { recursive: true, force: true }) }
process.on('uncaughtException', e => { console.error(e); cleanup(); process.exit(1) })
for (let i = 0; i < 40; i++) { try { await fetch(`http://127.0.0.1:${SITE}/__native/window.html`); break } catch { await sleep(150) } }

// Cursor art: SVGs converted from the system PDFs (native/cursors.py), scaled to CS for the compositor.
const CUR = JSON.parse(readFileSync(join(NATIVE, 'cursors.json'), 'utf8'))
for (const k of Object.keys(CUR)) {
  const m = CUR[k], svg = readFileSync(join(NATIVE, k + '.svg'), 'utf8')
    .replace(/width="[^"]*" height="[^"]*"/, `width="${m.w * CS}" height="${m.h * CS}"`)
  writeFileSync(join(REC, k + '.svg'), svg)
}

// ---- live recording state ----
let frames = null, track = null, sceneStart = 0, pressed = false, posterAt = null
const markPoster = (delay = 0) => { posterAt = elapsed() + delay }   // the representative moment of a scene
c.on('Page.screencastFrame', p => {
  if (frames) frames.push({ data: p.data, t: p.metadata.timestamp * 1000 })
  send('Page.screencastFrameAck', { sessionId: p.sessionId })
})
const mouse = (type, x, y, extra = {}) => send('Input.dispatchMouseEvent', { type, x, y, button: type === 'mouseMoved' ? (pressed ? 'left' : 'none') : 'left',
  buttons: pressed ? 1 : 0, clickCount: type === 'mouseMoved' ? 0 : 1, ...extra })
const shapeQuery = (e, x, y) => evaluate(`shapeAt(${x}, ${y})`).then(v => { e.shape = v }).catch(() => {})

// Play planned steps in real time; every step is dispatched to the page and logged for the compositor.
async function play(steps) {
  const t0 = Date.now()
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i], wait = t0 + s.dt - Date.now()
    if (wait > 1) await sleep(wait)
    else if (wait < -34 && s.type === 'move' && steps[i + 1]?.type === 'move' && t0 + steps[i + 1].dt <= Date.now()) continue   // running late: drop a sample
    const late = Date.now() - (t0 + s.dt)   // log the planned time unless dispatch fell behind, so the drawn path stays smooth
    const e = { t: (late > 30 ? Date.now() : t0 + s.dt) - sceneStart, x: +s.x.toFixed(2), y: +s.y.toFixed(2), down: pressed }
    if (track.length && e.t < track[track.length - 1].t) e.t = track[track.length - 1].t
    if (s.type === 'move') mouse('mouseMoved', s.x, s.y)   // not awaited: CDP keeps the order, and the hand keeps its timing
    else if (s.type === 'down') { pressed = true; e.down = true; await mouse('mousePressed', s.x, s.y) }
    else if (s.type === 'up') { pressed = false; e.down = false; await mouse('mouseReleased', s.x, s.y) }
    else if (s.type === 'wheel') send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: s.x, y: s.y, deltaX: 0, deltaY: s.dy })
    track.push(e)
    if (s.type !== 'move' || i % 2 === 0 || i === steps.length - 1) shapeQuery(e, s.x, s.y)
  }
}
const elapsed = () => Date.now() - sceneStart

// ---- what the hand does in each kind of scene ----
const W = { left: 16, right: 1064 }
// The scene's target for a frame; if it sits outside the visible part of the build, scroll it in with the wheel.
async function aim(h, id, kind, arg = null) {
  const q = `target(${JSON.stringify(id)}, ${JSON.stringify(kind)}, ${JSON.stringify(arg)})`
  let t = await evaluate(q)
  for (let i = 0; t && t.offscreen && i < 3; i++) {
    const f = t.frame
    await play(h.moveTo({ x: f.x + h.rand(-40, 40), y: f.y + h.rand(-20, 60) }, 140))
    await play(h.rest(h.rand(150, 250), 0.6)); await play(h.wheel(t.scrollBy)); await play(h.rest(h.rand(450, 600), 0.6))
    t = await evaluate(q)
  }
  return t && !t.offscreen ? t : null
}
async function hoverSide(h, id) {
  const t = await aim(h, id, 'hover'); if (!t) return
  await play(h.moveTo(t, Math.min(t.w, t.h)))
  if (id === 'fb') markPoster(700)
  await play(h.rest(h.rand(1400, 1700), Math.min(1, Math.min(t.w, t.h) / 40)))
  const away = { x: t.x + h.rand(-50, 50), y: t.y + Math.max(t.h / 2, 24) + h.rand(45, 85) }
  await play(h.moveTo(away, 90, { overshoot: 0 }))
  await play(h.rest(h.rand(250, 380), 0.8))
}
// Open the toggle, look, close it. A toast that starts open is closed, then opened again and looked at.
async function clickSide(h, id) {
  let t = await aim(h, id, 'click'); if (!t) return
  const startsOpen = t.expanded === 'true'
  await play(h.moveTo(t, Math.min(t.w, t.h)))
  await play(h.rest(h.rand(260, 400), 0.4))
  await play(h.click())
  if (id === 'fb' && !startsOpen) markPoster(700)
  await play(h.rest(startsOpen ? h.rand(550, 750) : h.rand(1200, 1500), startsOpen ? 0.5 : 0.9))
  t = await aim(h, id, 'click'); if (!t) return
  await play(h.moveTo(t, Math.min(t.w, t.h), { overshoot: 0.2 }))
  await play(h.rest(h.rand(160, 280), 0.4))
  await play(h.click())
  const after = await evaluate(`target('${id}', 'click')`)
  console.log(`  ${id} toggle: ${startsOpen ? 'open -> closed -> ' : 'closed -> open -> '}${after?.expanded === 'true' ? 'open' : after?.expanded === 'false' ? 'closed' : '?'}`)
  if (id === 'fb' && startsOpen) markPoster(700)
  await play(h.rest(startsOpen ? h.rand(1200, 1500) : h.rand(380, 520), 0.8))
}
async function readSide(h, id, nLines = 2) {
  let L = await evaluate(`lines('${id}')`); if (!L || !L.lines.length) return
  const hs = L.lines.map(l => l.h).sort((a, b) => a - b), med = hs[Math.floor(hs.length / 2)]
  let body = L.lines.filter(l => Math.abs(l.h - med) < med * 0.25 && l.x1 - l.x0 > 40)
  if (!body.length) body = L.lines
  if (id === 'fb') markPoster(600)
  for (const l of body.slice(0, nLines)) await play(h.read(l.x0 + 3, Math.min(l.x1 - 4, l.x0 + 170), l.y))
  if (L.scrollable > 60) {                                // more below: a flick, then read on
    await play(h.rest(h.rand(200, 350), 0.5))
    await play(h.wheel(Math.min(L.scrollable, 260)))
    await play(h.rest(h.rand(500, 700), 0.6))
    L = await evaluate(`lines('${id}')`)
    const l = L && L.lines.find(l => l.y > L.box.top + L.box.height * 0.3 && Math.abs(l.h - med) < med * 0.25)
    if (l) await play(h.read(l.x0 + 3, Math.min(l.x1 - 4, l.x0 + 220), l.y))
  }
}
async function readPrompt(h) {
  const p = await evaluate(`rectOf('.prompt')`); if (!p) return
  const y = p.top + 18 * 0.97, x0 = p.left + h.rand(8, 30)
  await play(h.read(x0, x0 + h.rand(120, 160), y))
}
const SCRIPTS = {
  intro: async h => {
    await play(h.rest(1300, 1))
    const r = await evaluate(`rectOf('.card p:nth-of-type(2) b')`)
    if (r) await play(h.moveTo({ x: r.left + r.width * h.rand(0.25, 0.6), y: r.y + h.rand(-3, 3) }, r.height))
    await play(h.rest(Math.max(300, (HOLD_MS ?? 4300) - elapsed()), 1))
  },
  outro: async h => {
    await play(h.rest(h.rand(500, 700), 1))
    const r = await evaluate(`rectOf('.url')`)
    if (r) { const x0 = r.left + r.width * h.rand(0.05, 0.12); await play(h.read(x0, x0 + h.rand(120, 160), r.y)) }
    await play(h.rest(Math.max(300, (HOLD_MS ?? 5500) - elapsed()), 1))
  },
  hover: async h => {
    await play(h.rest(h.rand(350, 500), 1)); await readPrompt(h)
    await hoverSide(h, 'fa'); await hoverSide(h, 'fb')
  },
  click: async h => {
    await play(h.rest(h.rand(450, 650), 1))
    await clickSide(h, 'fa'); await clickSide(h, 'fb')
  },
  text: async h => {
    await play(h.rest(h.rand(450, 650), 1))
    await readSide(h, 'fa'); await play(h.rest(h.rand(200, 350), 0.6)); await readSide(h, 'fb')
  },
  results: async h => {
    await play(h.rest(h.rand(700, 900), 1))
    for (const sel of ['.verdict:nth-of-type(1)', '.verdict:nth-of-type(2)']) {
      const r = await evaluate(`rectOf(${JSON.stringify(sel)})`)
      if (r) { const x0 = r.left + h.rand(150, 190), y = r.top + 20; await play(h.read(x0, x0 + h.rand(260, 340), y)); await play(h.rest(h.rand(700, 900), 0.8)) }
    }
    await play(h.rest(Math.max(300, (HOLD_MS ?? 9000) - elapsed()), 1))
  },
  // A card with no pointer on it: the hand leaves the frame and the card plays out (padded to the scene's HOLD).
  still: async h => { await play(h.moveTo({ x: 1160, y: 1430 }, 80, { overshoot: 0 })) },
  // One build filling the window: its own listed steps, on the frame with id fb.
  solo: async h => {
    await play(h.rest(h.rand(250, 350), 1))
    const S = await evaluate(`document.getElementById('scene').contentWindow.STEPS`)
    await stepsSide(h, 'fb', S[CUR_RUNS.b])
  },
  steps: async h => {
    await play(h.rest(h.rand(450, 650), 1))
    const S = await evaluate(`document.getElementById('scene').contentWindow.STEPS`)
    await stepsSide(h, 'fa', S[CUR_RUNS.a]); await play(h.rest(h.rand(200, 300), 0.8)); await stepsSide(h, 'fb', S[CUR_RUNS.b])
    await play(h.rest(h.rand(200, 300), 0.8)); await stepsSide(h, 'fc', S[CUR_RUNS.c])
  },
  watch: async h => { await play(h.rest(1200, 1)); await play(h.moveTo({ x: 540, y: 1180 }, 80)); await play(h.rest(4800, 1)) },
}
SCRIPTS.drag = SCRIPTS.watch
// One build's listed steps: click or hover a named control, drag a slider, paint a stroke on the drawing surface.
async function stepsSide(h, id, steps) {
  for (const [op, a, b] of steps || []) {
    if (op === 'rest') { await play(h.rest(a, 0.8)); continue }
    if (op === 'poster') { if (id === 'fc') markPoster(a || 0); continue }
    if (op === 'call') { await evaluate(`document.getElementById('scene').contentWindow[${JSON.stringify(a)}](${JSON.stringify(b ?? null)})`); continue }
    const kind = op === 'slide' ? 'range' : op === 'paint' || op === 'tap' ? 'surface' : 'named'
    const t = await aim(h, id, kind, op === 'paint' || op === 'tap' ? null : a)
    if (!t) { console.log(`  ${id}: nothing for ${op} ${a ?? ''}`); continue }
    if (op === 'click' || op === 'hover') {
      await play(h.moveTo(t, Math.min(t.w, t.h)))
      await play(h.rest(h.rand(180, 320), 0.4))
      if (op === 'click') { await play(h.click()); await play(h.rest(h.rand(300, 450), 0.6)) }
      else await play(h.rest(h.rand(900, 1200), 0.6))
    } else if (op === 'slide') {
      await play(h.moveTo(t, 16)); await play(h.rest(h.rand(200, 320), 0.3))
      await play([{ dt: 0, type: 'down', x: h.p.x, y: h.p.y }])
      await play(h.moveTo({ x: t.x + b * t.track, y: t.y + h.rand(-2, 2) }, 16, { overshoot: 0, ms: h.rand(800, 1000) }))
      await play(h.rest(h.rand(120, 200), 0.2)); await play([{ dt: 0, type: 'up', x: h.p.x, y: h.p.y }])
      await play(h.rest(h.rand(300, 450), 0.6))
    } else if (op === 'tap') {   // click the same spot of the drawing surface b times
      const p = { x: t.x - t.sw / 2 + a[0] * t.sw, y: t.y - t.sh / 2 + a[1] * t.sh }
      await play(h.moveTo(p, 30)); await play(h.rest(h.rand(180, 280), 0.3))
      for (let i = 0; i < (b || 1); i++) { await play(h.click()); await play(h.rest(h.rand(200, 300), 0.2)) }
      await play(h.rest(h.rand(300, 450), 0.6))
    } else if (op === 'paint') {
      const pt = ([fx, fy]) => ({ x: t.x - t.sw / 2 + fx * t.sw, y: t.y - t.sh / 2 + fy * t.sh })
      await play(h.moveTo(pt(a[0]), 30)); await play(h.rest(h.rand(180, 280), 0.3))
      await play([{ dt: 0, type: 'down', x: h.p.x, y: h.p.y }])
      for (const p of a.slice(1)) await play(h.moveTo(pt(p), 30, { overshoot: 0, ms: h.rand(420, 600) }))
      await play(h.rest(h.rand(100, 180), 0.2)); await play([{ dt: 0, type: 'up', x: h.p.x, y: h.p.y }])
      await play(h.rest(h.rand(300, 450), 0.6))
    }
  }
}
let CUR_RUNS = {}, HOLD_MS = null
// Play one game on a side: click the next empty cell (the scene picks it) until the page announces an end.
async function playSide(h, id) {
  for (let move = 0; move < 9; move++) {
    const t = await aim(h, id, 'cell'); if (!t) break
    await play(h.moveTo(t, Math.min(t.w, t.h), move ? { overshoot: 0.15 } : {}))
    await play(h.rest(h.rand(140, 260), 0.4)); await play(h.click())
    await play(h.rest(h.rand(380, 560), 0.6))
  }
  if (id === 'fb') markPoster(300)
  await play(h.rest(h.rand(900, 1200), 0.8))
}
// Turn a model: press on it, drag sideways and a little up, let go, watch it settle.
async function turnSide(h, id) {
  const t = await aim(h, id, 'model'); if (!t) return
  const start = { x: t.x - h.rand(70, 100), y: t.y + h.rand(-10, 20) }
  await play(h.moveTo(start, 60)); await play(h.rest(h.rand(200, 320), 0.4))
  await play([{ dt: 0, type: 'down', x: h.p.x, y: h.p.y }])
  await play(h.moveTo({ x: start.x + h.rand(170, 220), y: start.y - h.rand(20, 50) }, 60, { overshoot: 0, ms: h.rand(800, 1000) }))
  await play(h.rest(h.rand(120, 200), 0.3)); await play([{ dt: 0, type: 'up', x: h.p.x, y: h.p.y }])
  if (id === 'fb') markPoster(500)
  await play(h.rest(h.rand(1300, 1600), 0.8))
}
SCRIPTS.play = async h => { await play(h.rest(h.rand(400, 600), 1)); await playSide(h, 'fa'); await playSide(h, 'fb') }
SCRIPTS.turn = async h => { await play(h.rest(h.rand(500, 700), 1)); await turnSide(h, 'fa'); await turnSide(h, 'fb') }

// ---- record every scene ----
const sceneUrl = (slug, a, b, c) => SCENE + '?task=' + slug + (a ? '&a=' + a : '') + (b ? '&b=' + b : '') + (c ? '&c=' + c : '')
const scenes = [...(CARDS ? [{ slug: 'intro', kind: 'intro' }] : []), ...TASKS, ...(CARDS ? [{ slug: 'results', kind: 'results' }, { slug: 'outro', kind: 'outro' }] : [])]
const manifest = {}
let pos = { x: 802, y: 1196 }
for (const sc of scenes) {
  await send('Page.navigate', { url: `http://127.0.0.1:${SITE}/__native/window.html?scene=${encodeURIComponent(sceneUrl(sc.slug, sc.a, sc.b, sc.c))}${BARE ? '&bare=1' : ''}` })
  await sleep(400); await evaluate('ready()'); await sleep(900)
  CUR_RUNS = (await evaluate(`document.getElementById('scene').contentWindow.SHOWN || null`)) || {}
  HOLD_MS = ((await evaluate(`document.getElementById('scene').contentWindow.HOLD || null`)) || {})[sc.slug] ?? null
  if (!sc.kind) {
    const st = await evaluate(`document.getElementById('scene').contentWindow.STEPS || null`)
    if (st && [CUR_RUNS.a, CUR_RUNS.b, CUR_RUNS.c].every(r => r && st[r])) sc.kind = 'steps'
  }
  if (!sc.kind) {
    const data = await evaluate(`document.getElementById('scene').contentWindow.eval('typeof DATA === "undefined" ? null : DATA')`)
    const t = (data || []).find(d => d.slug === sc.slug)
    sc.kind = t?.interaction || (t?.kind === 'text' ? 'text' : 'watch')
  }
  const h = new Hand(seedFor(sc.slug, SEED), pos)
  pressed = false; await mouse('mouseMoved', pos.x, pos.y); await sleep(250)
  frames = []; track = []; posterAt = null; sceneStart = Date.now()
  track.push({ t: 0, x: pos.x, y: pos.y, down: false }); shapeQuery(track[0], pos.x, pos.y)
  await send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: 1080, maxHeight: 1350, everyNthFrame: 1 })
  await evaluate(`(w => { if (w.go) w.go() })(document.getElementById('scene').contentWindow)`)
  await SCRIPTS[sc.kind](h)
  const least = HOLD_MS ?? 6500
  if (!['intro', 'results', 'outro'].includes(sc.kind) && elapsed() < least) await play(h.rest(least - elapsed(), 1))
  await play(h.rest(250, 1))
  await send('Page.stopScreencast'); await sleep(150)
  const dur = elapsed(), fs = frames.filter(f => f.t >= sceneStart - 50); frames = null
  pos = { ...h.p }
  let shape = 'arrow'; for (const e of track) { e.shape = e.shape || shape; shape = e.shape }
  mkdirSync(join(REC, sc.slug), { recursive: true })
  manifest[sc.slug] = { duration: dur, track, posterAt: posterAt ?? dur / 2, frames: fs.map((f, i) => { writeFileSync(join(REC, sc.slug, `${i}.jpg`), Buffer.from(f.data, 'base64')); return { src: `${sc.slug}/${i}.jpg`, t: Math.max(0, f.t - sceneStart) } }) }
  if (TRACE) writeFileSync(join(TRACE, sc.slug + '.json'), JSON.stringify({ kind: sc.kind, duration: dur, track }))
  console.log(sc.slug, sc.kind, dur + ' ms', fs.length + ' frames', track.length + ' pointer events', [...new Set(track.map(e => e.shape))].join('/'))
}
writeFileSync(join(REC, 'manifest.json'), JSON.stringify({ cursors: CUR, cs: CS, scenes: manifest }))
copyFileSync(join(NATIVE, 'compose.html'), join(REC, 'compose.html'))

async function encode(list, out) {
  await send('Page.navigate', { url: `http://127.0.0.1:${RECPORT}/compose.html` }); await sleep(800)
  const size = await evaluate(`compose(${JSON.stringify(list)})`)
  const parts = []
  for (let i = 0; i < size; i += 1 << 20) parts.push(Buffer.from(await evaluate(`chunk(${i}, ${1 << 20})`), 'base64'))
  writeFileSync(out, Buffer.concat(parts))
  console.log('wrote', out, (size / 1e6).toFixed(1) + ' MB')
}
await encode(scenes.map(s => s.slug), join(OUT, NAME))
for (const t of TASKS) await encode([t.slug], join(OUT, `metadump-ab-${t.slug}.mp4`))
for (const t of TASKS) {   // poster: the window composite with the cursor, at the scene's representative moment
  const url = await evaluate(`still(${JSON.stringify(t.slug)})`)
  writeFileSync(join(POSTERS, t.slug + '.jpg'), Buffer.from(url.split(',')[1], 'base64'))
  console.log('wrote', join(POSTERS, t.slug + '.jpg'), 'at', Math.round(manifest[t.slug].posterAt) + ' ms')
}
cleanup(); process.exit(0)
