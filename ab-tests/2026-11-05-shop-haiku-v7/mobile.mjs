// Mobile screenshots with real device emulation (390x844 CSS px). Headless Chrome windows can't go below
// ~500 px wide, so --window-size=390 laid pages out at ~500 px and cropped them (the v1 artifact).
import { spawn } from 'node:child_process'
import { readdirSync, writeFileSync, mkdtempSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { tmpdir } from 'node:os'
import { fileURLToPath } from 'node:url'
const HERE = dirname(fileURLToPath(import.meta.url))
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const PORT = 9339
const sleep = ms => new Promise(r => setTimeout(r, ms))
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--hide-scrollbars', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${mkdtempSync(join(tmpdir(), 'cdp-'))}`, 'about:blank'], { stdio: 'ignore' })
let t
for (let i = 0; i < 50 && !t; i++) { try { t = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find(x => x.type === 'page') } catch {} if (!t) await sleep(200) }
const ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r))
let id = 0; const pending = new Map()
ws.addEventListener('message', m => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id) } })
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })) })
await send('Page.enable')
await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true })
for (const f of readdirSync(join(HERE, 'runs')).filter(f => f.endsWith('.html')).sort()) {
  await send('Page.navigate', { url: 'file://' + join(HERE, 'runs', f) }); await sleep(1500)
  const w = (await send('Runtime.evaluate', { expression: 'innerWidth + "x" + innerHeight + " scrollW=" + document.documentElement.scrollWidth', returnByValue: true })).result.result.value
  const shot = await send('Page.captureScreenshot', { format: 'png' })
  writeFileSync(join(HERE, 'shots', f.replace('.html', '-mobile.png')), Buffer.from(shot.result.data, 'base64'))
  console.log(f, w)
}
ws.close(); chrome.kill(); process.exit(0)
