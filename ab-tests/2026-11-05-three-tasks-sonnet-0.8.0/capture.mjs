// Capture the HTML tasks in headless Chrome over CDP.
// Usage: node capture.mjs t1-button|t3-toast
// Writes <task>/shots/<run>-{desktop,mobile,interact}.png and <task>/functional.json.
//   t1-button:  hover the main button; frames of hover in and out, cropped around it.
//   t3-toast:   click the toggle; frames of it opening and closing, plus the open state on desktop and phone, and how dark the surface is.
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
// The toast toggle: aria-expanded, a summary, or a button that says it opens or closes something.
const FIND_TOGGLE = `(() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 6 && r.height > 6 && getComputedStyle(e).visibility !== 'hidden' }
  const name = e => ((e.getAttribute('aria-label') || '') + ' ' + (e.innerText || '') + ' ' + (e.title || '')).toLowerCase()
  let el = [...document.querySelectorAll('[aria-expanded]')].find(vis)
    || [...document.querySelectorAll('summary')].find(vis)
    || [...document.querySelectorAll('button, [role=button]')].find(e => vis(e) && /expand|collapse|details|toggle|more|show|open|track|chevron|view/.test(name(e)))
    || [...document.querySelectorAll('button, [role=button]')].find(vis)
  if (!el) return null
  window.__toggle = el
  const box = el.closest('[role=status], [role=alert], [role=region], [role=dialog], [aria-live], [class*=toast i]') || el.parentElement
  window.__box = box
  const r = el.getBoundingClientRect(), b = box.getBoundingClientRect()
  return { x: r.x + r.width / 2, y: r.y + r.height / 2, expanded: el.getAttribute('aria-expanded') ?? (el.closest('details')?.open ? 'open' : 'closed'),
           box: { x: b.x, y: b.y, w: b.width, h: b.height }, label: name(el).trim().slice(0, 40) }
})()`
const BOX_NOW = `(() => { const b = window.__box.getBoundingClientRect(), el = window.__toggle;
  return { box: { x: b.x, y: b.y, w: b.width, h: b.height }, expanded: el.getAttribute('aria-expanded') ?? (el.closest('details')?.open ? 'open' : 'closed') } })()`
// Relative luminance (0 black .. 1 white) of the first opaque background at or above the toast box.
const BOX_LUMINANCE = `(() => { let e = window.__box
  const lin = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4) }
  while (e) { const m = getComputedStyle(e).backgroundColor.match(/[\\d.]+/g)
    if (m && (m.length < 4 || +m[3] > 0.5)) { const [r, g, b] = m.map(Number); return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b) }
    e = e.parentElement }
  return null })()`

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
  } else if (TASK === 't3-toast') {
    const tg = await evaluate(FIND_TOGGLE)
    res.toggle_found = !!tg
    if (tg) {
      res.collapsed_height_px = Math.round(tg.box.h)
      const lum = await evaluate(BOX_LUMINANCE)
      res.surface_luminance = lum == null ? null : Math.round(lum * 1000) / 1000
      res.dark_surface = lum != null && lum < 0.2
      frames.push({ b64: await shot(), cap: 'collapsed' })
      const before = await shot()
      await mouse('mouseMoved', tg.x, tg.y); await mouse('mousePressed', tg.x, tg.y); await mouse('mouseReleased', tg.x, tg.y)
      let tPrev = 0
      for (const t of [120, 300, 700]) { await sleep(t - tPrev); tPrev = t; frames.push({ b64: await shot(), cap: `open +${t} ms` }) }
      const after = await evaluate(BOX_NOW)
      res.expanded_height_px = Math.round(after.box.h)
      const ux = Math.min(tg.box.x, after.box.x) - 40, uy = Math.min(tg.box.y, after.box.y) - 40
      const ur = Math.max(tg.box.x + tg.box.w, after.box.x + after.box.w) + 40, ub = Math.max(tg.box.y + tg.box.h, after.box.y + after.box.h) + 40
      res._crop = { x: Math.max(0, ux), y: Math.max(0, uy), w: Math.min(1280, ur) - Math.max(0, ux), h: Math.min(800, ub) - Math.max(0, uy) }
      res.state_changes = after.expanded !== tg.expanded || Math.abs(after.box.h - tg.box.h) > 8 || frames[frames.length - 1].b64 !== before
      writeFileSync(join(DIR, 'shots', run + '-open-desktop.png'), Buffer.from(await shot(), 'base64'))
      const t2 = await evaluate(FIND_TOGGLE)
      if (t2) { await mouse('mousePressed', t2.x, t2.y); await mouse('mouseReleased', t2.x, t2.y); await sleep(700); frames.push({ b64: await shot(), cap: 'closed again' }) }
      await phone(); await send('Page.navigate', { url }); await sleep(1000)
      const tp = await evaluate(FIND_TOGGLE)
      if (tp) { await mouse('mousePressed', tp.x, tp.y); await mouse('mouseReleased', tp.x, tp.y); await sleep(700) }
      writeFileSync(join(DIR, 'shots', run + '-open-mobile.png'), Buffer.from(await shot(), 'base64'))
    }
    res.works = !!(res.toggle_found && res.state_changes)
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
  if (frames.length) await strip(frames, `${run}: ${({ 't1-button': 'hover in, then mouse leaves (cropped around the button)', 't3-toast': 'clicking the toggle open, then closed again (cropped to the toast)', 't4-figma': 'one frame every 0.5 s across the 5 s loop (desktop, scaled)' })[TASK]}`,
    join(DIR, 'shots', run + '-interact.png'), TASK === 't1-button' ? 3 : 5, res._crop)
  delete res._crop
  results[run] = res
  console.log(run, JSON.stringify(res))
}
writeFileSync(join(DIR, 'functional.json'), JSON.stringify(results, null, 1))
ws.close(); chrome.kill(); process.exit(0)
