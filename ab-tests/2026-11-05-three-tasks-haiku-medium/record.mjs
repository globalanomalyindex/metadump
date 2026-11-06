// Film the showcase scenes and encode MP4s for LinkedIn (1080x1350, 4:5), with no installs: headless Chrome's
// screencast captures each scene while a scripted cursor hovers or clicks, then a canvas page replays the
// frames on their original timing into MediaRecorder (H.264). Also writes one poster still per task.
// Usage: node record.mjs   (after showcase.py)   ->  video/*.mp4, ../../docs/showcase/posters/*.jpg
import { spawn } from 'node:child_process'
import { mkdirSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { tmpdir } from 'node:os'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const SHOWCASE = join(HERE, '..', '..', 'docs', 'showcase')
const VIDEO = join(HERE, 'video'), POSTERS = join(SHOWCASE, 'posters')
const REC = mkdtempSync(join(tmpdir(), 'metadump-rec-'))
mkdirSync(VIDEO, { recursive: true }); mkdirSync(POSTERS, { recursive: true })
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const PORT = 9371, SITE = 8766, RECPORT = 8767
const sleep = ms => new Promise(r => setTimeout(r, ms))
const site = spawn('python3', ['-m', 'http.server', String(SITE), '--bind', '127.0.0.1', '--directory', SHOWCASE], { stdio: 'ignore' })
const recsrv = spawn('python3', ['-m', 'http.server', String(RECPORT), '--bind', '127.0.0.1', '--directory', REC], { stdio: 'ignore' })
const chrome = spawn(CHROME, ['--headless=new', '--hide-scrollbars', '--autoplay-policy=no-user-gesture-required', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${mkdtempSync(join(tmpdir(), 'cdp-'))}`, '--window-size=1080,1350', 'about:blank'], { stdio: 'ignore' })
let t
for (let i = 0; i < 60 && !t; i++) { try { t = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find(x => x.type === 'page') } catch {} if (!t) await sleep(200) }
const ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r))
let id = 0; const pending = new Map(); let frames = null
ws.addEventListener('message', m => {
  const d = JSON.parse(m.data)
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id) }
  else if (d.method === 'Page.screencastFrame') {
    if (frames) frames.push({ data: d.params.data, t: d.params.metadata.timestamp * 1000 })
    ws.send(JSON.stringify({ id: ++id, method: 'Page.screencastFrameAck', params: { sessionId: d.params.sessionId } }))
  }
})
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })) })
const evaluate = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result?.result?.value
const mouse = (type, x, y) => send('Input.dispatchMouseEvent', { type, x, y, button: type === 'mouseMoved' ? 'none' : 'left', clickCount: type === 'mouseMoved' ? 0 : 1 })
await send('Page.enable'); await send('Runtime.enable')
await send('Emulation.setDeviceMetricsOverride', { width: 1080, height: 1350, deviceScaleFactor: 1, mobile: false })

async function glide(to, ms) {   // move the drawn cursor and the real pointer together
  await evaluate(`cursorTo(${to.x}, ${to.y}, ${ms})`)
  const steps = Math.max(1, Math.round(ms / 40))
  for (let i = 1; i <= steps; i++) { await mouse('mouseMoved', to.x, to.y); await sleep(ms / steps) }
}
const SCRIPTS = {
  intro: async () => { await sleep(3200) },
  outro: async () => { await sleep(4200) },
  hover: async () => {
    await sleep(700)
    const a = await evaluate(`targetIn('fa', 'hover')`), b = await evaluate(`targetIn('fb', 'hover')`)
    if (a) { await glide(a, 650); await sleep(2000) }
    if (b) { await glide(b, 750); await sleep(2200) }
    await glide({ x: 540, y: 1250 }, 600); await sleep(700)
  },
  click: async () => {
    await sleep(800)
    const a = await evaluate(`targetIn('fa', 'click')`)
    if (a) { await glide(a, 650); await mouse('mousePressed', a.x, a.y); await mouse('mouseReleased', a.x, a.y); await sleep(1700) }
    const b = await evaluate(`targetIn('fb', 'click')`)
    if (b) { await glide(b, 750); await mouse('mousePressed', b.x, b.y); await mouse('mouseReleased', b.x, b.y); await sleep(2300) }
    await glide({ x: 540, y: 1250 }, 500); await sleep(500)
  },
  drag: async () => {
    await sleep(1600)
    for (const id of ['fa', 'fb']) {
      const p = await evaluate(`targetIn('${id}', 'drag')`)
      if (!p) continue
      await glide(p, 650); await mouse('mousePressed', p.x, p.y)
      const to = { x: p.x + (p.x % 540 > 270 ? -150 : 150), y: Math.max(380, p.y - 330) }
      for (let i = 1; i <= 14; i++) { const q = { x: p.x + (to.x - p.x) * i / 14, y: p.y + (to.y - p.y) * i / 14 }; await evaluate(`cursorTo(${q.x}, ${q.y}, 0)`); await mouse('mouseMoved', q.x, q.y); await sleep(35) }
      await mouse('mouseReleased', to.x, to.y); await sleep(1700)
    }
    await glide({ x: 540, y: 1250 }, 500); await sleep(400)
  },
  watch: async () => { await evaluate(`cursorTo(-80, -80, 0)`); await sleep(6200) },
  text: async () => { await sleep(900); await evaluate(`cursorTo(-80, -80, 0)`); await sleep(4600) },
  longtext: async () => { await evaluate(`cursorTo(-80, -80, 0)`); await sleep(1600); await evaluate(`scrollFrames(7000)`); await sleep(1400) },
}
const TASKS = [['t1-button', 'hover'], ['t2-sandbox', 'drag'], ['t3-poem', 'text'], ['t4-figma', 'watch']]
const SCENES = [['intro', 'intro'], ...TASKS, ['outro', 'outro']]

const manifest = {}
for (const [scene, kind] of SCENES) {
  await send('Page.navigate', { url: `http://127.0.0.1:${SITE}/scene.html?task=${scene}` }); await sleep(1800)
  await mouse('mouseMoved', 1079, 1349)
  frames = []
  const start = Date.now()
  await send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: 1080, maxHeight: 1350, everyNthFrame: 1 })
  await SCRIPTS[kind]()
  await send('Page.stopScreencast')
  const dur = Date.now() - start
  const fs = frames.filter(f => f.t >= start - 50); frames = null
  mkdirSync(join(REC, scene), { recursive: true })
  manifest[scene] = { duration: dur, frames: fs.map((f, i) => { writeFileSync(join(REC, scene, `${i}.jpg`), Buffer.from(f.data, 'base64')); return { src: `${scene}/${i}.jpg`, t: Math.max(0, f.t - start) } }) }
  if (kind === 'hover' || kind === 'click' || kind === 'drag' || kind === 'watch') {   // poster: the frame halfway through the right side's interaction
    const pick = fs[Math.floor(fs.length * 0.8)] || fs[fs.length - 1]
    if (pick) writeFileSync(join(POSTERS, scene + '.jpg'), Buffer.from(pick.data, 'base64'))
  } else if ((kind === 'text' || kind === 'longtext') && fs.length) writeFileSync(join(POSTERS, scene + '.jpg'), Buffer.from(fs[0].data, 'base64'))
  console.log(scene, dur + ' ms', fs.length + ' frames')
}
writeFileSync(join(REC, 'manifest.json'), JSON.stringify(manifest))
writeFileSync(join(REC, 'compose.html'), `<!doctype html><body style="margin:0"><canvas id="c" width="1080" height="1350"></canvas><script>
window.compose = async (scenes) => {
  const man = await (await fetch('manifest.json')).json(), c = document.getElementById('c'), g = c.getContext('2d')
  const parts = []
  for (const s of scenes) { const fr = []; for (const f of man[s].frames) fr.push({ t: f.t, img: await createImageBitmap(await (await fetch(f.src)).blob()) }); parts.push({ dur: man[s].duration, fr }) }
  const type = ['video/mp4;codecs=avc1.640028', 'video/mp4;codecs=avc1.42E01E', 'video/mp4'].find(t => MediaRecorder.isTypeSupported(t))
  const rec = new MediaRecorder(c.captureStream(30), { mimeType: type, videoBitsPerSecond: 8e6 }), chunks = []
  rec.ondataavailable = e => e.data.size && chunks.push(e.data)
  g.drawImage(parts[0].fr[0].img, 0, 0); rec.start(250)
  for (const p of parts) {
    const t0 = performance.now(); let i = 0
    while (performance.now() - t0 < p.dur) {
      const now = performance.now() - t0
      while (i + 1 < p.fr.length && p.fr[i + 1].t <= now) i++
      if (p.fr[i]) g.drawImage(p.fr[i].img, 0, 0)
      await new Promise(r => setTimeout(r, 15))
    }
  }
  rec.stop(); await new Promise(r => rec.onstop = r)
  window.__buf = new Uint8Array(await new Blob(chunks, { type }).arrayBuffer())
  return window.__buf.length
}
window.chunk = (i, n) => { let s = ''; const a = window.__buf.subarray(i, i + n); for (let k = 0; k < a.length; k += 0x8000) s += String.fromCharCode.apply(null, a.subarray(k, k + 0x8000)); return btoa(s) }
</script>`)

async function encode(scenes, out) {
  await send('Page.navigate', { url: `http://127.0.0.1:${RECPORT}/compose.html` }); await sleep(800)
  const size = await evaluate(`compose(${JSON.stringify(scenes)})`)
  const parts = []
  for (let i = 0; i < size; i += 1 << 20) parts.push(Buffer.from(await evaluate(`chunk(${i}, ${1 << 20})`), 'base64'))
  writeFileSync(out, Buffer.concat(parts))
  console.log('wrote', out, (size / 1e6).toFixed(1) + ' MB')
}
await encode(SCENES.map(s => s[0]), join(VIDEO, 'metadump-ab-linkedin.mp4'))
for (const [scene] of TASKS) await encode([scene], join(VIDEO, `metadump-ab-${scene}.mp4`))
ws.close(); chrome.kill(); site.kill(); recsrv.kill(); rmSync(REC, { recursive: true, force: true }); process.exit(0)
