// Drive each curves build in headless Chrome over CDP: read window.CURVES, check the running animations use
// those curves, capture an 8-frame strip, check 390 px overflow, and render one standard curve sheet per run
// (graph, 24-step position strip, measured numbers) so graders judge every build's curves the same way.
// Usage: node motion.mjs  -> functional.json, curves/<run>.json, shots/<run>-frames.png, shots/<run>-curves.png
import { spawn } from 'node:child_process'
import { readdirSync, readFileSync, writeFileSync, mkdirSync, mkdtempSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { tmpdir } from 'node:os'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const PORT = 9341
const sleep = ms => new Promise(r => setTimeout(r, ms))
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
const shot = async () => (await send('Page.captureScreenshot', { format: 'png' })).result.data
await send('Page.enable'); await send('Runtime.enable')

// Every easing string the page's animations use: WAAPI/CSS animation effects, their keyframes, and computed styles.
const EASINGS = `(() => {
  const out = []
  for (const a of document.getAnimations()) {
    try { out.push(a.effect.getTiming().easing); for (const k of a.effect.getKeyframes()) out.push(k.easing) } catch {}
  }
  for (const e of document.querySelectorAll('*')) {
    const cs = getComputedStyle(e)
    out.push(cs.animationTimingFunction, cs.transitionTimingFunction)
  }
  return { easings: [...new Set(out.filter(Boolean))], running: document.getAnimations().filter(a => a.playState === 'running').length }
})()`
const nums = s => (s.match(/-?\d*\.?\d+/g) || []).map(Number)
const close = (a, b) => a.length === 4 && b.length === 4 && a.every((v, i) => Math.abs(v - b[i]) < 0.011)

// Cubic bezier easing: progress at time x (bisection on the curve parameter).
function easeAt([x1, y1, x2, y2], x) {
  const bx = s => 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3
  const by = s => 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s * s * y2 + s ** 3
  let lo = 0, hi = 1
  for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; if (bx(m) < x) lo = m; else hi = m }
  return by((lo + hi) / 2)
}
function metrics(b) {
  const ys = Array.from({ length: 201 }, (_, i) => easeAt(b, i / 200))
  const v = ys.slice(1).map((y, i) => (y - ys[i]) * 200)
  const peak = v.reduce((m, x, i) => (Math.abs(x) > Math.abs(v[m]) ? i : m), 0)
  const t90 = ys.findIndex(y => y >= 0.9)
  return {
    overshoot_pct: Math.round(Math.max(0, Math.max(...ys) - 1) * 1000) / 10,
    undershoot_pct: Math.round(Math.max(0, -Math.min(...ys)) * 1000) / 10,
    time_to_90_pct: t90 < 0 ? null : Math.round(t90 / 2),
    start_speed: Math.round((ys[10] - ys[0]) / 0.05 * 100) / 100,   // progress per unit time over the first 5%
    end_speed: Math.round((ys[200] - ys[190]) / 0.05 * 100) / 100,   // over the last 5%
    peak_speed: Math.round(Math.abs(v[peak]) * 100) / 100,
    peak_speed_at_pct: Math.round(peak / 2),
  }
}

function sheetHtml(run, curves) {
  const W = 300, H = 220, pad = 30
  const cells = curves.map(c => {
    const b = c.bezier, m = c.metrics
    const ymin = Math.min(-0.1, ...Array.from({ length: 101 }, (_, i) => easeAt(b, i / 100))) , ymax = Math.max(1.1, ...Array.from({ length: 101 }, (_, i) => easeAt(b, i / 100)))
    const X = x => pad + x * (W - 2 * pad), Y = y => H - pad - (y - ymin) / (ymax - ymin) * (H - 2 * pad)
    const path = Array.from({ length: 101 }, (_, i) => `${i ? 'L' : 'M'}${X(i / 100).toFixed(1)},${Y(easeAt(b, i / 100)).toFixed(1)}`).join(' ')
    const dots = Array.from({ length: 25 }, (_, i) => `<circle cx="${(10 + easeAt(b, i / 24) * 260).toFixed(1)}" cy="12" r="3.2" fill="#111" opacity="${(0.25 + 0.75 * i / 24).toFixed(2)}"/>`).join('')
    return `<div class="c"><h2>${c.name || '(no name)'}</h2>
      <p class="v">cubic-bezier(${b.join(', ')}) · ${c.duration_ms ?? '?'} ms</p>
      <svg width="${W}" height="${H}"><rect x="${pad}" y="${Y(1)}" width="${W - 2 * pad}" height="${Y(0) - Y(1)}" fill="#f2f2f2"/>
        <line x1="${X(0)}" y1="${Y(0)}" x2="${X(b[0])}" y2="${Y(b[1])}" stroke="#bbb"/><line x1="${X(1)}" y1="${Y(1)}" x2="${X(b[2])}" y2="${Y(b[3])}" stroke="#bbb"/>
        <circle cx="${X(b[0])}" cy="${Y(b[1])}" r="4" fill="#bbb"/><circle cx="${X(b[2])}" cy="${Y(b[3])}" r="4" fill="#bbb"/>
        <path d="${path}" fill="none" stroke="#111" stroke-width="2.5"/>
        <text x="${pad}" y="${H - 8}" font-size="11" fill="#666">time →</text><text x="4" y="${pad - 8}" font-size="11" fill="#666">progress</text></svg>
      <svg width="280" height="24"><line x1="10" y1="12" x2="270" y2="12" stroke="#ddd"/>${dots}</svg>
      <p class="m">overshoot ${m.overshoot_pct}% · undershoot ${m.undershoot_pct}% · 90% reached at ${m.time_to_90_pct}% of the time<br>
      start speed ${m.start_speed} · end speed ${m.end_speed} · peak speed ${m.peak_speed} at ${m.peak_speed_at_pct}% of the time</p></div>`
  }).join('')
  return `<!doctype html><meta charset="utf-8"><style>body{margin:0;padding:16px;font:13px system-ui;background:#fff;color:#111;width:1000px}
  .row{display:flex;gap:16px}.c{border:1px solid #ddd;border-radius:8px;padding:10px;width:310px}h2{font-size:15px;margin:0 0 2px}
  .v{font:12px ui-monospace,monospace;margin:0 0 6px;color:#333}.m{font-size:11.5px;color:#444;margin:6px 0 0;line-height:1.45}
  .k{font-size:11.5px;color:#555;margin:0 0 10px}</style>
  <p class="k">Standard curve sheet for ${run}, rendered by the test harness from window.CURVES. Dot strip: position at 24 equal time steps, left to right (bunched dots = slow, spread dots = fast).</p>
  <div class="row">${cells || '<p>window.CURVES missing or invalid</p>'}</div>`
}

async function capturePage(html, path, w, h) {
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: false })
  await send('Page.navigate', { url: 'data:text/html;base64,' + Buffer.from(html).toString('base64') }); await sleep(500)
  writeFileSync(path, Buffer.from(await shot(), 'base64'))
}

mkdirSync(join(HERE, 'curves'), { recursive: true }); mkdirSync(join(HERE, 'frames'), { recursive: true })
const results = {}
for (const f of readdirSync(join(HERE, 'runs')).filter(f => f.endsWith('.html')).sort()) {
  const run = f.replace('.html', '')
  errors.length = 0
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false })
  await send('Page.navigate', { url: 'file://' + join(HERE, 'runs', f) }); await sleep(1200)
  const raw = await evaluate('JSON.stringify(window.CURVES || null)')
  let curves = []
  try { curves = (JSON.parse(raw) || []).filter(c => c && Array.isArray(c.bezier) && c.bezier.length === 4 && c.bezier.every(Number.isFinite)) } catch {}
  const valid = curves.length === 3 && curves.every(c => c.bezier[0] >= 0 && c.bezier[0] <= 1 && c.bezier[2] >= 0 && c.bezier[2] <= 1)
  const { easings, running } = await evaluate(EASINGS)
  const beziers = easings.flatMap(e => e.split(/,(?![^(]*\))/)).filter(e => e.includes('cubic-bezier')).map(nums)
  const usedCss = curves.filter(c => beziers.some(b => close(b, c.bezier))).length
  const src = readFileSync(join(HERE, 'runs', f), 'utf8')
  const inSource = curves.filter(c => c.bezier.every(v => src.includes(String(v)))).length
  // 8 frames, 150 ms apart
  const frames = []
  for (let i = 0; i < 8; i++) { frames.push(await shot()); if (i < 7) await sleep(150) }
  const animating = new Set(frames).size > 1
  mkdirSync(join(HERE, 'frames', run), { recursive: true })
  frames.forEach((b64, i) => writeFileSync(join(HERE, 'frames', run, `f${i}.png`), Buffer.from(b64, 'base64')))
  // 390 px
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true })
  await sleep(500)
  const overflow = await evaluate('Math.max(0, document.documentElement.scrollWidth - innerWidth)')
  const withMetrics = curves.map(c => ({ ...c, metrics: metrics(c.bezier) }))
  writeFileSync(join(HERE, 'curves', run + '.json'), JSON.stringify(withMetrics, null, 1))
  results[run] = {
    curves_valid: valid, n_curves: curves.length, animating, running_animations: running,
    curves_used_in_css: `${usedCss}/${curves.length}`, curves_in_source: `${inSource}/${curves.length}`,
    curves_used: curves.length > 0 && (usedCss === curves.length || (animating && inSource === curves.length)),
    js_errors: errors.length, js_error_text: errors.slice(0, 2).map(e => String(e).slice(0, 160)), mobile_overflow_px: overflow, mobile_no_overflow: overflow <= 1,
  }
  results[run].works = results[run].curves_valid && results[run].animating && results[run].curves_used && results[run].js_errors === 0
  // frame strip and curve sheet
  const strip = `<!doctype html><style>body{margin:0;padding:10px;background:#ddd;font:12px system-ui;width:1300px}div{display:grid;grid-template-columns:repeat(4,320px);gap:6px}
    figure{margin:0}img{width:320px;display:block}figcaption{padding:2px 0}</style><p>${run}: 8 frames of the running page, 150 ms apart (desktop, scaled to 25%)</p><div>${
    frames.map((b, i) => `<figure><img src="data:image/png;base64,${b}"><figcaption>t = ${i * 150} ms</figcaption></figure>`).join('')}</div>`
  await capturePage(strip, join(HERE, 'shots', run + '-frames.png'), 1320, 520)
  await capturePage(sheetHtml(run, withMetrics), join(HERE, 'shots', run + '-curves.png'), 1040, 470)
  console.log(run, JSON.stringify(results[run]))
}
writeFileSync(join(HERE, 'functional.json'), JSON.stringify(results, null, 1))
ws.close(); chrome.kill(); process.exit(0)
