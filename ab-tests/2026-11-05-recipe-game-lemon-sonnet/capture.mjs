// Capture the HTML tasks in headless Chrome over CDP.
// Usage: node capture.mjs t2-tictactoe|t3-lemon
// Writes <task>/shots/<run>-{desktop,mobile,interact}.png and <task>/functional.json.
//   t2-tictactoe: find the 3x3 board (nine cells, or a square canvas/svg split in thirds), play a scripted game by clicking
//                 the first empty cell in the order 0,3,1,4,2,5,6,7,8 until the page announces an end, shoot the end state,
//                 then press restart and check the board clears.
//   t3-lemon:     frames over 2 s untouched (auto motion), then a horizontal and a vertical drag across the model;
//                 whether it moves, which renderer the source uses, and the share of lemon-yellow pixels at rest.
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
const chrome = spawn(CHROME, ['--headless=new', '--hide-scrollbars', `--remote-debugging-port=${PORT}`,
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
const drag = (type, x, y) => send('Input.dispatchMouseEvent', { type, x, y, button: 'left', buttons: type === 'mouseReleased' ? 0 : 1, clickCount: type === 'mouseMoved' ? 0 : 1 })
const desktop = () => send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false })
const phone = () => send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true })
await send('Page.enable'); await send('Runtime.enable')

// The board: nine similar, roughly square elements sharing a parent in a 3x3 layout; else a square canvas or svg split in thirds.
const FIND_BOARD = `(() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width >= 24 && r.height >= 24 && r.width <= 320 && r.height <= 320 && r.bottom > 0 && r.top < innerHeight && getComputedStyle(e).visibility !== 'hidden' }
  // nine visible children of one parent whose centres fall in three columns and three rows (rows may differ in height)
  const bands = vs => { const s = [...vs].sort((a, b) => a - b), g = [[s[0]]]; for (const v of s.slice(1)) { if (v - g[g.length - 1].slice(-1)[0] > 8) g.push([v]); else g[g.length - 1].push(v) } return g.length }
  for (const p of document.querySelectorAll('body, body *')) {
    const kids = [...p.children].filter(vis); if (kids.length !== 9) continue
    const rs = kids.map(e => e.getBoundingClientRect())
    if (bands(rs.map(r => r.x + r.width / 2)) !== 3 || bands(rs.map(r => r.y + r.height / 2)) !== 3) continue
    const order = kids.map((e, i) => [e, rs[i]]).sort((a, b) => (Math.abs(a[1].y + a[1].height / 2 - b[1].y - b[1].height / 2) > 8 ? a[1].y - b[1].y : a[1].x - b[1].x))
    window.__cells = order.map(o => o[0])
    const x0 = Math.min(...rs.map(r => r.x)), y0 = Math.min(...rs.map(r => r.y))
    return { kind: 'dom', cells: order.map(([e, r]) => ({ x: r.x + r.width / 2, y: r.y + r.height / 2 })), box: { x: x0, y: y0, w: Math.max(...rs.map(r => r.right)) - x0, h: Math.max(...rs.map(r => r.bottom)) - y0 } } }
  const sq = [...document.querySelectorAll('canvas, svg')].filter(vis).map(e => [e, e.getBoundingClientRect()]).filter(([e, r]) => r.width >= 150 && Math.abs(r.width - r.height) < r.width * 0.2)
  sq.sort((a, b) => b[1].width * b[1].height - a[1].width * a[1].height)
  if (!sq.length) return null
  const r = sq[0][1]; window.__cells = null; const cells = []
  for (let i = 0; i < 9; i++) cells.push({ x: r.x + r.width * ((i % 3) + 0.5) / 3, y: r.y + r.height * (Math.floor(i / 3) + 0.5) / 3 })
  return { kind: sq[0][0].tagName.toLowerCase(), cells, box: { x: r.x, y: r.y, w: r.width, h: r.height } }
})()`
const CELL_TEXT = `(window.__cells || []).map(e => ((e.innerText || '') + ' ' + (e.getAttribute('aria-label') || '') + ' ' + (e.dataset.value || e.dataset.mark || e.dataset.player || '')).trim())`
const MARKED = `(window.__cells || []).map(e => /\\b[XOxo]\\b|[✕✖×○◯⭕]/.test((e.innerText || '') + ' ' + (e.dataset.value || e.dataset.mark || e.dataset.player || '') + ' ' + (e.className.baseVal ?? e.className)) || e.querySelector('svg, img, [class*=mark i], [class*=x i], [class*=o i]') !== null)`
const RESTART = `(() => { const b = [...document.querySelectorAll('button, [role=button], a, input[type=button]')].find(e => { const r = e.getBoundingClientRect(); return r.width > 4 && r.height > 4 && /restart|reset|new game|play again|new round|rematch/i.test((e.innerText || '') + ' ' + (e.getAttribute('aria-label') || '') + ' ' + (e.value || '')) })
  if (!b) return null; const r = b.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2, label: (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30) } })()`
// The model: the largest visible canvas or svg, else the largest element with a 3D transform, else the viewport centre.
const FIND_MODEL = `(() => { const vis = e => { const r = e.getBoundingClientRect(); return r.width > 60 && r.height > 60 && r.bottom > 0 && r.top < innerHeight }
  let els = [...document.querySelectorAll('canvas, svg')].filter(vis)
  if (!els.length) els = [...document.querySelectorAll('body *')].filter(e => vis(e) && /preserve-3d/.test(getComputedStyle(e).transformStyle))
  els = els.map(e => [e, e.getBoundingClientRect()]).sort((a, b) => b[1].width * b[1].height - a[1].width * a[1].height)
  if (!els.length) return { tag: 'none', x: innerWidth / 2, y: innerHeight / 2, box: { x: 0, y: 0, w: innerWidth, h: innerHeight } }
  const [e, r] = els[0]; const cx = Math.max(0, r.x), cy = Math.max(0, r.y), cw = Math.min(innerWidth, r.right) - cx, ch = Math.min(innerHeight, r.bottom) - cy
  return { tag: e.tagName.toLowerCase(), x: cx + cw / 2, y: cy + ch / 2, box: { x: cx, y: cy, w: cw, h: ch } } })()`
// Mean absolute RGB difference (0-255) between screenshots, and the share of lemon-yellow pixels, computed on about:blank.
const PIXELS = (pairs, yellowOf) => `(async () => { const load = s => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = 'data:image/png;base64,' + s })
  const W = 320, H = 200, px = async s => { const cv = document.createElement('canvas'); cv.width = W; cv.height = H; const g = cv.getContext('2d'); g.drawImage(await load(s), 0, 0, W, H); return g.getImageData(0, 0, W, H).data }
  const d = (p, q) => { let t = 0; for (let k = 0; k < p.length; k += 4) t += Math.abs(p[k] - q[k]) + Math.abs(p[k + 1] - q[k + 1]) + Math.abs(p[k + 2] - q[k + 2]); return t / (p.length / 4) / 3 }
  const diffs = []; for (const [a, b] of ${JSON.stringify(pairs)}) diffs.push(d(await px(a), await px(b)))
  const y = await px(${JSON.stringify(yellowOf)}); let n = 0
  for (let k = 0; k < y.length; k += 4) { const r = y[k] / 255, g = y[k + 1] / 255, b = y[k + 2] / 255, mx = Math.max(r, g, b), mn = Math.min(r, g, b)
    if (mx < 0.45 || mx - mn < 0.3 * mx) continue; let h = mx === r ? ((g - b) / (mx - mn)) % 6 : mx === g ? (b - r) / (mx - mn) + 2 : (r - g) / (mx - mn) + 4; h *= 60; if (h < 0) h += 360
    if (h >= 40 && h <= 70) n++ }
  return { diffs, yellow: n / (y.length / 4) } })()`

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
  if (TASK === 't2-tictactoe') {
    const bd = await evaluate(FIND_BOARD)
    res.board = bd ? bd.kind : null
    if (bd) {
      const pad = 150, crop = { x: Math.max(0, bd.box.x - pad), y: Math.max(0, bd.box.y - pad), w: 0, h: 0 }
      crop.w = Math.min(1280, bd.box.x + bd.box.w + pad) - crop.x; crop.h = Math.min(800, bd.box.y + bd.box.h + pad) - crop.y
      res._crop = crop
      const textBefore = await evaluate('document.body.innerText')
      frames.push({ b64: await shot(), cap: 'start' })
      const order = [0, 3, 1, 4, 2, 5, 6, 7, 8], clicked = []
      let ended = false, firstMarked = null
      for (let move = 0; move < 9 && !ended; move++) {
        if (bd.kind === 'dom') await evaluate(FIND_BOARD)   // re-find: a board may re-render its cells after every move
        const marked = bd.kind === 'dom' ? await evaluate(MARKED) : Array(9).fill(false).map((_, i) => clicked.includes(i))
        const i = order.find(k => !marked[k] && !clicked.includes(k))
        if (i === undefined) break
        clicked.push(i)
        // where the cell is now: a board whose rows resize as marks land must still be clicked where a person would click
        const at = bd.kind === 'dom' ? ((await evaluate(FIND_BOARD)) || bd).cells[i] : bd.cells[i]
        await mouse('mouseMoved', at.x, at.y); await mouse('mousePressed', at.x, at.y); await mouse('mouseReleased', at.x, at.y)
        await sleep(650)
        if (firstMarked === null) firstMarked = bd.kind === 'dom' ? (await evaluate(FIND_BOARD), (await evaluate(MARKED))[i]) : frames[0].b64 !== await shot()
        frames.push({ b64: await shot(), cap: `click cell ${i + 1}` })
        const now = await evaluate('document.body.innerText')
        const fresh = now.split('\n').map(l => l.trim()).filter(l => l && !textBefore.includes(l))
        if (fresh.some(l => /wins?\b|won\b|winner|draw|tie\b|stalemate|game over/i.test(l))) { ended = true; res.end_text = fresh.find(l => /wins?\b|won\b|winner|draw|tie\b|stalemate|game over/i.test(l)).slice(0, 60) }
      }
      res.clicks = clicked.length
      res.marks_appear = !!firstMarked
      res.end_announced = ended
      writeFileSync(join(DIR, 'shots', run + '-end.png'), Buffer.from(await shot(), 'base64'))
      const rs = await evaluate(RESTART)
      res.restart_found = !!rs
      if (rs) {
        await mouse('mouseMoved', rs.x, rs.y); await mouse('mousePressed', rs.x, rs.y); await mouse('mouseReleased', rs.x, rs.y); await sleep(600)
        frames.push({ b64: await shot(), cap: `after "${rs.label}"` })
        res.restart_clears = bd.kind === 'dom' ? (await evaluate(FIND_BOARD), !(await evaluate(MARKED)).some(Boolean)) : frames[frames.length - 1].b64 !== frames[frames.length - 2].b64
      }
    }
    res.works = !!(res.board && res.marks_appear && res.end_announced)
  } else if (TASK === 't3-lemon') {
    res.renderer = /getContext\(\s*['"]webgl2/.test(src) ? 'webgl2' : /getContext\(\s*['"](experimental-)?webgl/.test(src) ? 'webgl' : /getContext\(\s*['"]2d/.test(src) ? 'canvas2d'
      : /preserve-3d/.test(src) ? 'css3d' : /<svg/i.test(src) ? 'svg' : 'other'
    const m = await evaluate(FIND_MODEL)
    res.model_element = m.tag
    res._crop = m.box.w * m.box.h > 1280 * 800 * 0.9 ? null : (() => { const p = 40, x = Math.max(0, m.box.x - p), y = Math.max(0, m.box.y - p); return { x, y, w: Math.min(1280, m.box.x + m.box.w + p) - x, h: Math.min(800, m.box.y + m.box.h + p) - y } })()
    const rest = await shot()
    frames.push({ b64: rest, cap: 'rest' })
    for (const t of [500, 1000, 1500]) { await sleep(500); frames.push({ b64: await shot(), cap: `untouched +${t} ms` }) }
    const beforeDrag = frames[frames.length - 1].b64
    await mouse('mouseMoved', m.x - 120, m.y); await drag('mousePressed', m.x - 120, m.y)
    for (let k = 1; k <= 12; k++) { await drag('mouseMoved', m.x - 120 + k * 20, m.y); await sleep(30) }
    frames.push({ b64: await shot(), cap: 'dragging right' })
    await drag('mouseReleased', m.x + 120, m.y); await sleep(300)
    frames.push({ b64: await shot(), cap: 'released' })
    const afterH = frames[frames.length - 1].b64
    await drag('mousePressed', m.x, m.y + 80)
    for (let k = 1; k <= 10; k++) { await drag('mouseMoved', m.x, m.y + 80 - k * 16); await sleep(30) }
    await drag('mouseReleased', m.x, m.y - 80); await sleep(300)
    frames.push({ b64: await shot(), cap: 'after dragging up' })
    const afterV = frames[frames.length - 1].b64
    await send('Page.navigate', { url: 'about:blank' }); await sleep(200)
    const px = await evaluate(PIXELS([[rest, beforeDrag], [beforeDrag, afterH], [afterH, afterV]], rest))
    res.untouched_motion = px ? Math.round(px.diffs[0] * 10) / 10 : null
    res.drag_horizontal_change = px ? Math.round(px.diffs[1] * 10) / 10 : null
    res.drag_vertical_change = px ? Math.round(px.diffs[2] * 10) / 10 : null
    res.yellow_share = px ? Math.round(px.yellow * 1000) / 1000 : null
    res.renders = !!(px && px.yellow > 0.01)
    res.turns_when_dragged = !!(px && (px.diffs[1] > 0.5 || px.diffs[2] > 0.5))
    res.works = res.renders
  }
  res.js_errors = errors.length
  res.js_error_text = errors.slice(0, 2).map(e => String(e).slice(0, 160))
  res.works = res.works && res.js_errors === 0
  if (frames.length) await strip(frames, `${run}: ${({ 't2-tictactoe': 'a scripted game: clicking the first empty cell in the order 1,4,2,5,3,6,7,8,9 until the page announces an end, then restart (cropped around the board)', 't3-lemon': 'frames over 1.5 s untouched, then dragging right across the model, releasing, and dragging up (cropped to the model)' })[TASK]}`,
    join(DIR, 'shots', run + '-interact.png'), 4, res._crop)
  delete res._crop
  results[run] = res
  console.log(run, JSON.stringify(res))
}
writeFileSync(join(DIR, 'functional.json'), JSON.stringify(results, null, 1))
ws.close(); chrome.kill(); process.exit(0)
