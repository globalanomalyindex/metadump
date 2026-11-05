// Drive each shopping component in headless Chrome over CDP: does it actually work?
// Usage: node functional.mjs  -> writes functional.json
import { spawn } from 'node:child_process'
import { readdirSync, writeFileSync, mkdtempSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { tmpdir } from 'node:os'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const PORT = 9338
const sleep = ms => new Promise(r => setTimeout(r, ms))
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${mkdtempSync(join(tmpdir(), 'cdp-'))}`, '--window-size=1280,800', 'about:blank'], { stdio: 'ignore' })
async function target() {
  for (let i = 0; i < 50; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); const p = l.find(t => t.type === 'page'); if (p) return p } catch {}
    await sleep(200)
  }
  throw new Error('chrome did not start')
}
const t = await target()
const ws = new WebSocket(t.webSocketDebuggerUrl)
await new Promise(r => ws.addEventListener('open', r))
let id = 0; const pending = new Map(); const events = []
ws.addEventListener('message', m => {
  const d = JSON.parse(m.data)
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id) } else events.push(d)
})
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })) })
const evaluate = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result?.result?.value
await send('Page.enable'); await send('Runtime.enable')

const SNAP = `(() => JSON.stringify({
  text: document.body ? document.body.innerText : '',
  inputs: [...document.querySelectorAll('input, select')].map(i => i.value + (i.checked ? '*' : '')),
  attrs: [...document.querySelectorAll('*')].map(e => (e.getAttribute('aria-pressed') || '') + (e.getAttribute('aria-expanded') || '') + (e.getAttribute('data-state') || '') + (e.getAttribute('class') || '') + (e.disabled ? 'D' : '')).join('|')
}))()`
const nameOf = `e => ((e.getAttribute('aria-label') || '') + ' ' + (e.innerText || '') + ' ' + (e.getAttribute('title') || '') + ' ' + (e.value || '')).trim()`
// Primary action: prefer "add to cart/bag", then "add", "buy", "checkout", then a cart/bag button.
const CLICK_ACTION = `(() => {
  const name = ${nameOf}
  const tiers = [/add to (cart|bag|basket)/i, /^\\s*add\\b/i, /\\bbuy\\b/i, /check ?out/i, /\\b(cart|bag|basket)\\b/i]
  const cands = [...document.querySelectorAll('button, [role=button], input[type=submit], input[type=button], a[href]')].filter(e => !e.disabled)
  for (const re of tiers) { const e = cands.find(c => re.test(name(c))); if (e) { const label = name(e).slice(0, 60); e.click(); return label } }  // read the label before clicking: buttons that turn into spinners have none after
  return null
})()`
const CLICK_PLUS = `(() => {
  const name = ${nameOf}
  const cands = [...document.querySelectorAll('button, [role=button]')].filter(e => !e.disabled)
  const e = cands.find(c => /^\\s*\\+\\s*$|increase|increment|add one|more/i.test(name(c)))
  if (!e) return null
  const label = name(e).slice(0, 40); e.click(); return label
})()`
const UNNAMED = `(() => [...document.querySelectorAll('button, [role=button]')].filter(e => !((e.getAttribute('aria-label') || e.innerText || e.getAttribute('title') || e.getAttribute('aria-labelledby') || '').trim())).length)()`
const OVERFLOW = `(() => document.documentElement.scrollWidth - window.innerWidth)()`

const results = {}
const files = readdirSync(join(HERE, 'runs')).filter(f => f.endsWith('.html')).sort()
for (const f of files) {
  const url = 'file://' + join(HERE, 'runs', f)
  await send('Emulation.clearDeviceMetricsOverride')
  events.length = 0
  await send('Page.navigate', { url }); await sleep(1200)
  const r = {}
  const s0 = await evaluate(SNAP)
  r.action = await evaluate(CLICK_ACTION)
  await sleep(500); const s1 = await evaluate(SNAP)
  r.action_found = !!r.action
  r.action_changes_state = !!r.action && s1 !== s0
  r.plus = await evaluate(CLICK_PLUS)
  await sleep(400); const s2 = await evaluate(SNAP)
  r.qty_found = !!r.plus
  const digits = s => { const o = JSON.parse(s); return o.text.replace(/\D/g, '') + '|' + o.inputs.join() }
  r.qty_changes_number = !!r.plus && digits(s2) !== digits(s1)
  r.unnamed_buttons = await evaluate(UNNAMED)
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true })
  await send('Page.navigate', { url }); await sleep(1000)
  r.mobile_overflow_px = await evaluate(OVERFLOW)
  r.mobile_no_overflow = r.mobile_overflow_px <= 1
  r.js_errors = events.filter(e => e.method === 'Runtime.exceptionThrown').length  // desktop load + clicks + mobile load
  r.works = r.action_found && r.action_changes_state && r.js_errors === 0
  results[f.replace('.html', '')] = r
  console.log(f, JSON.stringify(r))
}
writeFileSync(join(HERE, 'functional.json'), JSON.stringify(results, null, 1))
ws.close(); chrome.kill()
process.exit(0)
