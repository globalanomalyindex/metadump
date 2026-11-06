// Capture the HTML tasks in headless Chrome over CDP.
// Usage: node capture.mjs t1-button|t2-sandbox|t4-figma
// Writes <task>/shots/<run>-{desktop,mobile,interact}.png and <task>/functional.json.
//   t1-button:  hover the main button; frames of hover in and out, cropped around it.
//   t2-sandbox: drag the lowest box (found through window.boxes()) up and let go; frames of the drag and the fall.
//   t4-figma:   frames every 0.5 s across the loop, and the pixel difference between frames 5 s apart (the loop seam).
import { spawn } from 'node:child_process'
import { readdirSync, readFileSync, writeFileSync, mkdtempSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { tmpdir } from 'node:os'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const TASK = process.argv[2]
const DIR = join(HERE, TASK)
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const PORT = 9361
const sleep = ms => new Promise(r => setTimeout(r, ms))
const SHEETS = mkdtempSync(join(tmpdir(), 'sheets-'))
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--hide-scrollbars', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${mkdtempSync(join(tmpdir(), 'cdp-'))}`, '--window-size=1280,800', 'about:blank'], { stdio: 'ignore' })
let t
for (let i = 0; i < 50 && !t; i++) { try { t = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find(x => x.type === 'page') } catch {} if (!t) await sleep(200) }
const ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r))
let id = 0; const pending = new Map(); const errors = []
ws.addEventListener('message', m => {
  const d = JSON.parse(m.data)
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id) }
  else if (d.method === 'Runtime.exceptionThrown') errors.push(d.params.exceptionDetails?.exception?.description || d.params.exceptionDetails?.text)
  else if (d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error') errors.push(d.params.args?.map(a => a.value ?? a.description).join(' '))
})
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })) })
const evaluate = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result?.result?.value
const shot = async (clip) => (await send('Page.captureScreenshot', { format: 'png', ...(clip ? { clip: { ...clip, scale: 1 } } : {}) })).result.data
const mouse = (type, x, y) => send('Input.dispatchMouseEvent', { type, x, y, button: type === 'mouseMoved' ? 'none' : 'left', clickCount: type === 'mouseMoved' ? 0 : 1 })
const desktop = () => send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false })
const phone = () => send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true })
await send('Page.enable'); await send('Runtime.enable')

// The main button: the largest visible button-like element.
const FIND_BUTTON = `(() => {
  const els = [...document.querySelectorAll('button, a, [role=button], input[type=button], input[type=submit]')]
    .map(e => [e, e.getBoundingClientRect()]).filter(([e, r]) => r.width > 20 && r.height > 14 && r.bottom > 0 && r.top < innerHeight)
  els.sort((a, b) => b[1].width * b[1].height - a[1].width * a[1].height)
  if (!els.length) return null
  const [e, r] = els[0]
  return { x: r.x, y: r.y, w: r.width, h: r.height, label: (e.innerText || e.getAttribute('aria-label') || '').trim().slice(0, 40), n: els.length }
})()`
async function strip(frames, title, path, cols, crop) {
  // crop (optional): {x, y, w, h} region of full 1280x800 frames to show
  const w = Math.min(1300, 40 + cols * 330)
  const cell = f => crop
    ? `<div class="crop" style="aspect-ratio:${crop.w}/${crop.h}"><img src="data:image/png;base64,${f.b64}" style="width:${1280 / crop.w * 100}%;left:${-crop.x / crop.w * 100}%;top:${-crop.y / crop.h * 100}%"></div>`
    : `<img src="data:image/png;base64,${f.b64}">`
  const html = `<!doctype html><style>body{margin:0;padding:10px;background:#ddd;font:12px system-ui;width:${w - 20}px}
    .g{display:grid;grid-template-columns:repeat(${cols},1fr);gap:6px}figure{margin:0;background:#fff}img{width:100%;display:block}
    .crop{position:relative;overflow:hidden;width:100%}.crop img{position:absolute;max-width:none}figcaption{padding:2px 4px}</style>
    <p>${title}</p><div class="g">${frames.map(f => `<figure>${cell(f)}<figcaption>${f.cap}</figcaption></figure>`).join('')}</div>`
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: 900, deviceScaleFactor: 1, mobile: false })
  // a file, not a data: URL: ten full-size frames exceed Chrome's 2 MB URL limit and render blank
  const sheet = join(SHEETS, 'sheet.html'); writeFileSync(sheet, html)
  await send('Page.navigate', { url: 'file://' + sheet }); await sleep(900)
  const h = await evaluate('Math.ceil(document.body.getBoundingClientRect().height + 20)')
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: Math.min(h, 2400), deviceScaleFactor: 1, mobile: false }); await sleep(200)
  writeFileSync(path, Buffer.from(await shot(), 'base64'))
}

const results = {}
for (const f of readdirSync(join(DIR, 'runs')).filter(f => f.endsWith('.html')).sort()) {
  const run = f.replace('.html', ''), url = 'file://' + join(DIR, 'runs', f), src = readFileSync(join(DIR, 'runs', f), 'utf8')
  errors.length = 0
  const res = {}
  // phone first: layout and overflow at rest
  await phone(); await send('Page.navigate', { url }); await sleep(1200)
  res.mobile_overflow_px = await evaluate('Math.max(0, document.documentElement.scrollWidth - innerWidth)')
  res.mobile_no_overflow = res.mobile_overflow_px <= 1
  writeFileSync(join(DIR, 'shots', run + '-mobile.png'), Buffer.from(await shot(), 'base64'))
  await desktop(); await send('Page.navigate', { url }); await sleep(1200)
  await mouse('mouseMoved', 2, 2)
  writeFileSync(join(DIR, 'shots', run + '-desktop.png'), Buffer.from(await shot(), 'base64'))
  const frames = []
  if (TASK === 't1-button') {
    const presets = new Set(['0.25,0.1,0.25,1', '0.42,0,1,1', '0,0,0.58,1', '0.42,0,0.58,1', '0,0,1,1'])
    const beziers = [...src.matchAll(/cubic-bezier\(\s*([^)]+)\)/g)].map(m => m[1].split(',').map(s => +s.trim()).join(','))
    res.custom_beziers = [...new Set(beziers.filter(b => !presets.has(b)))].length
    res.reduced_motion = /prefers-reduced-motion/.test(src)
    const b = await evaluate(FIND_BUTTON)
    res.button_found = !!b
    if (b) {
      const pad = 90, clip = { x: Math.max(0, b.x - pad), y: Math.max(0, b.y - pad), width: Math.min(1280, b.w + 2 * pad), height: Math.min(800, b.h + 2 * pad) }
      const rest = await shot(clip)
      frames.push({ b64: rest, cap: 'rest' })
      await mouse('mouseMoved', b.x + b.w / 2, b.y + b.h / 2)
      let tPrev = 0
      for (const t of [60, 140, 240, 400, 700]) { await sleep(t - tPrev); tPrev = t; frames.push({ b64: await shot(clip), cap: `hover +${t} ms` }) }
      res.hover_changes = frames[frames.length - 1].b64 !== rest
      await mouse('mouseMoved', 2, 2); tPrev = 0
      for (const t of [80, 200, 500]) { await sleep(t - tPrev); tPrev = t; frames.push({ b64: await shot(clip), cap: `leave +${t} ms` }) }
    }
    res.works = !!(res.button_found && res.hover_changes)
  } else if (TASK === 't2-sandbox') {
    await sleep(800)
    const BOXES = `(() => { try { const b = window.boxes && window.boxes(); return Array.isArray(b) ? b.filter(o => o && isFinite(o.x) && isFinite(o.y)).map(o => ({ x: +o.x, y: +o.y, w: +o.w || 0, h: +o.h || 0 })) : null } catch (e) { return null } })()`
    const before = await evaluate(BOXES)
    res.boxes_hook = Array.isArray(before) && before.length > 0
    res.box_count = before ? before.length : 0
    if (res.boxes_hook) {
      // drag the lowest box up and to the side, then let go
      const pick = before.reduce((m, b) => (b.y > m.y ? b : m), before[0])
      const nearest = (list, p) => list.reduce((m, b) => (Math.hypot(b.x - p.x, b.y - p.y) < Math.hypot(m.x - p.x, m.y - p.y) ? b : m), list[0])
      const to = { x: Math.max(80, Math.min(1200, pick.x + (pick.x > 640 ? -260 : 260))), y: Math.max(80, pick.y - 300) }
      frames.push({ b64: await shot(), cap: 'before drag' })
      await mouse('mouseMoved', pick.x, pick.y); await mouse('mousePressed', pick.x, pick.y)
      for (let i = 1; i <= 10; i++) { await mouse('mouseMoved', pick.x + (to.x - pick.x) * i / 10, pick.y + (to.y - pick.y) * i / 10); await sleep(30) }
      const mid = await evaluate(BOXES)
      frames.push({ b64: await shot(), cap: 'dragging' })
      const held = mid && mid.length ? nearest(mid, to) : null
      res.drag_moves_box = !!held && Math.hypot(held.x - to.x, held.y - to.y) < 90 && Math.hypot(held.x - pick.x, held.y - pick.y) > 60
      await mouse('mouseReleased', to.x, to.y)
      let tPrev = 0, last = held
      for (const t of [150, 400, 900, 1600]) {
        await sleep(t - tPrev); tPrev = t
        frames.push({ b64: await shot(), cap: `released +${t} ms` })
        const now = await evaluate(BOXES); if (now && now.length && last) last = nearest(now, last)
      }
      res.falls_after_release = !!(held && last && last.y > held.y + 40)
      await sleep(1500)
      const end = await evaluate(BOXES) || []
      const vw = 1280, vh = 800
      res.boxes_in_view = end.length ? Math.round(100 * end.filter(b => b.x > -20 && b.x < vw + 20 && b.y > -300 && b.y < vh + 40).length / end.length) : 0
    }
    res.works = !!(res.boxes_hook && res.drag_moves_box && res.falls_after_release)
  } else if (TASK === 't4-figma') {
    const t0 = Date.now()
    const at = async ms => { const w = ms - (Date.now() - t0); if (w > 0) await sleep(w); return { b64: await shot(), t: Date.now() - t0 } }
    for (let k = 1; k <= 10; k++) { const f = await at(k * 500); frames.push({ b64: f.b64, cap: `t = ${(f.t / 1000).toFixed(1)} s` }) }
    const a1 = await at(5600), half = await at(8100), a2 = await at(10600)   // a1 and a2 are 5 s apart; half sits between
    res.animating = new Set(frames.map(f => f.b64)).size > 1
    const DIFF = imgs => `(async () => { const load = s => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = 'data:image/png;base64,' + s })
      const [a, b, c] = await Promise.all(${JSON.stringify(imgs)}.map(load)); const W = 320, H = 200
      const px = i => { const cv = document.createElement('canvas'); cv.width = W; cv.height = H; const g = cv.getContext('2d'); g.drawImage(i, 0, 0, W, H); return g.getImageData(0, 0, W, H).data }
      const d = (p, q) => { let s = 0; for (let k = 0; k < p.length; k += 4) s += Math.abs(p[k] - q[k]) + Math.abs(p[k + 1] - q[k + 1]) + Math.abs(p[k + 2] - q[k + 2]); return s / (p.length / 4) / 3 }
      const A = px(a), B = px(b), C = px(c); return { seam: d(A, B), half: d(A, C) } })()`
    // Post hoc (added after test 11's first capture): frames as fast as CDP gives them for 5.5 s, at quarter scale.
    // A snap at the loop's wrap shows as one frame-to-frame change far larger than the typical one.
    const dense = [], d0 = Date.now()
    while (Date.now() - d0 < 5500) dense.push({ b64: (await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: 1280, height: 800, scale: 0.25 } })).result.data, t: Date.now() - d0 })
    await send('Page.navigate', { url: 'about:blank' }); await sleep(200)
    const dd = await evaluate(DIFF([a1.b64, a2.b64, half.b64]))
    const STEPS = `(async () => { const s = ${JSON.stringify(dense.map(f => f.b64))}; const load = b => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = 'data:image/png;base64,' + b })
      const W = 320, H = 200, cv = document.createElement('canvas'); cv.width = W; cv.height = H; const g = cv.getContext('2d'); const px = []
      for (const b of s) { g.drawImage(await load(b), 0, 0, W, H); px.push(g.getImageData(0, 0, W, H).data) }
      const d = (p, q) => { let t = 0; for (let k = 0; k < p.length; k += 4) t += Math.abs(p[k] - q[k]) + Math.abs(p[k + 1] - q[k + 1]) + Math.abs(p[k + 2] - q[k + 2]); return t / (p.length / 4) / 3 }
      return px.slice(1).map((p, i) => d(px[i], p)) })()`
    const steps = dense.length > 2 ? await evaluate(STEPS) : null
    if (steps && steps.length) {
      const per = steps.map((v, i) => v / Math.max(1, dense[i + 1].t - dense[i].t) * 100)   // change per 100 ms
      const sorted = [...per].sort((a, b) => a - b), med = sorted[Math.floor(sorted.length / 2)]
      res.dense_frames = dense.length
      res.max_step_per_100ms = Math.round(Math.max(...per) * 10) / 10
      res.median_step_per_100ms = Math.round(med * 10) / 10
      res.max_jump_ratio = med > 0.05 ? Math.round(Math.max(...per) / med * 10) / 10 : null   // high = a jump somewhere in the 5.5 s
    }
    res.loop_seam_diff = dd ? Math.round(dd.seam * 10) / 10 : null       // mean abs RGB difference, 0-255, frames 5 s apart
    res.half_loop_diff = dd ? Math.round(dd.half * 10) / 10 : null       // the same, 2.5 s apart, for scale
    res.seamless = !!(dd && dd.seam < Math.max(2, dd.half * 0.35))
    res.works = res.animating
  }
  res.js_errors = errors.length
  res.js_error_text = errors.slice(0, 2).map(e => String(e).slice(0, 160))
  res.works = res.works && res.js_errors === 0
  if (frames.length) await strip(frames, `${run}: ${({ 't1-button': 'hover in, then mouse leaves (cropped around the button)', 't2-sandbox': 'dragging the lowest box up and letting go (desktop, scaled)', 't4-figma': 'one frame every 0.5 s across the 5 s loop (desktop, scaled)' })[TASK]}`,
    join(DIR, 'shots', run + '-interact.png'), TASK === 't4-figma' ? 5 : 3)
  results[run] = res
  console.log(run, JSON.stringify(res))
}
writeFileSync(join(DIR, 'functional.json'), JSON.stringify(results, null, 1))
ws.close(); chrome.kill(); process.exit(0)
