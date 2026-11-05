// Drive each player in headless Chrome over CDP: does it actually work?
// Usage: node functional.mjs  -> writes functional.json
import { spawn } from 'node:child_process'
import { readdirSync, writeFileSync, mkdtempSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { tmpdir } from 'node:os'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const PORT = 9337
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

const SNAP = `(() => {
  const els = [...document.querySelectorAll('*')]
  return JSON.stringify({
    text: document.body ? document.body.innerText : '',
    inputs: [...document.querySelectorAll('input')].map(i => i.value),
    styles: els.map(e => e.getAttribute('style') || '').join('|'),
    attrs: els.map(e => (e.getAttribute('aria-pressed') || '') + (e.getAttribute('aria-label') || '') + (e.getAttribute('data-state') || '') + e.className).join('|')
  })
})()`
// Pick the real control: score buttons by id and aria-label, never containers like .player or "Up next" headings.
const CLICK = kind => `(() => {
  const want = ${JSON.stringify({ play: { ids: ['play', 'playpause', 'play-pause', 'playbtn', 'play-btn', 'toggle', 'btn-play', 'playpausebtn'], label: '^(play|pause|play/pause|toggle play)' }, next: { ids: ['next', 'nextbtn', 'next-btn', 'btn-next', 'skip', 'forward'], label: '^(next|skip forward|skip to next)' } })}[KIND]
  const re = new RegExp(want.label, 'i')
  const cands = [...document.querySelectorAll('button, [role=button]')]
  const score = e => {
    const id = (e.id || '').toLowerCase(), label = (e.getAttribute('aria-label') || e.getAttribute('title') || '').trim()
    let s = 0
    if (want.ids.includes(id)) s += 3
    if (re.test(label)) s += 2
    if (label.length > 25) s -= 3          // queue items like "Play X by Y"
    if (/prev|back|previous/i.test(id + label)) s -= 5
    return s
  }
  const best = cands.map(e => [score(e), e]).filter(x => x[0] > 0).sort((a, b) => b[0] - a[0])[0]
  if (!best) return false
  best[1].click()
  return true
})()`.replace('[KIND]', '[' + JSON.stringify(kind) + ']')

const results = {}
const files = readdirSync(join(HERE, 'runs')).filter(f => f.endsWith('.html')).sort()
for (const f of files) {
  events.length = 0
  await send('Page.navigate', { url: 'file://' + join(HERE, 'runs', f) })
  await sleep(1500)
  const r = { js_errors: 0 }
  const s0 = await evaluate(SNAP)
  r.play_button_found = await evaluate(CLICK('play'))
  await sleep(300); const s1 = await evaluate(SNAP)
  await sleep(2200); const s2 = await evaluate(SNAP)
  r.state_changes_on_play = s1 !== s0
  r.advances_while_playing = s2 !== s1
  const before = JSON.parse(s2).text.replace(/[\d:]/g, '')
  r.next_button_found = await evaluate(CLICK('next'))
  await sleep(400); const s3 = await evaluate(SNAP)
  r.next_changes_track = JSON.parse(s3).text.replace(/[\d:]/g, '') !== before
  await evaluate(CLICK('play'))
  await sleep(400); const s4 = await evaluate(SNAP); await sleep(1500); const s5 = await evaluate(SNAP)
  r.stops_when_paused = s5 === s4
  r.js_errors = events.filter(e => e.method === 'Runtime.exceptionThrown').length
  r.works = r.play_button_found && r.advances_while_playing && r.next_changes_track && r.js_errors === 0
  results[f.replace('.html', '')] = r
  console.log(f, JSON.stringify(r))
}
writeFileSync(join(HERE, 'functional.json'), JSON.stringify(results, null, 1))
ws.close(); chrome.kill()
process.exit(0)
