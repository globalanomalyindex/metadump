// Raw Chrome DevTools Protocol over WebSocket: launch headless Chrome, send commands, listen to events.
import { spawn } from 'node:child_process'
import { mkdtempSync } from 'node:fs'
import { join } from 'node:path'
import { tmpdir } from 'node:os'

export const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
export const sleep = ms => new Promise(r => setTimeout(r, ms))

export async function launch({ port = 9471, width = 1080, height = 1350, args = [] } = {}) {
  const proc = spawn(CHROME, ['--headless=new', '--hide-scrollbars', '--autoplay-policy=no-user-gesture-required',
    '--allow-file-access-from-files', '--force-color-profile=srgb', `--remote-debugging-port=${port}`,
    `--user-data-dir=${mkdtempSync(join(tmpdir(), 'cdp-native-'))}`, `--window-size=${width},${height}`, ...args, 'about:blank'], { stdio: 'ignore' })
  let t
  for (let i = 0; i < 80 && !t; i++) { try { t = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(x => x.type === 'page') } catch {} if (!t) await sleep(200) }
  if (!t) throw new Error('Chrome did not start on port ' + port)
  const ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r))
  let id = 0; const pending = new Map(), listeners = new Map()
  ws.addEventListener('message', m => {
    const d = JSON.parse(m.data)
    if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id) }
    else if (d.method) for (const f of listeners.get(d.method) || []) f(d.params)
  })
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })) })
  const on = (method, f) => { if (!listeners.has(method)) listeners.set(method, []); listeners.get(method).push(f) }
  const evaluate = async expr => {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })
    if (r.result?.exceptionDetails) throw new Error('page: ' + (r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text))
    return r.result?.result?.value
  }
  await send('Page.enable'); await send('Runtime.enable')
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false })
  const close = () => { try { ws.close() } catch {} proc.kill() }
  return { send, on, evaluate, close, ws }
}
