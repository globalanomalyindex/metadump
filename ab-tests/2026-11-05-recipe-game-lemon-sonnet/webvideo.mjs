// Make web copies of a recorded video, in headless Chrome (no ffmpeg, no installs):
//   --mp4 OUT   a smaller MP4 for GitHub Pages (re-recorded from playback at --bitrate, scaled to --mp4-width)
//   --webp OUT  an animated WebP preview for the README (GitHub strips <video> tags but plays animated images):
//               frames sampled at --fps, scaled to --width, encoded by the browser, identical frames merged.
// Usage: node webvideo.mjs IN.mp4 [--mp4 OUT.mp4 --bitrate 4000000 --mp4-width 720] [--webp OUT.webp --width 432 --fps 8 --quality 0.6]
import { createServer } from 'node:http'
import { readFileSync, writeFileSync, statSync } from 'node:fs'
import { dirname, basename, resolve } from 'node:path'
import { launch } from './native/cdp.mjs'

const argv = process.argv.slice(2), opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d }
const IN = resolve(argv[0]), MP4 = opt('--mp4', null), WEBP = opt('--webp', null)
const BITRATE = +opt('--bitrate', 4e6), MP4W = +opt('--mp4-width', 0), WIDTH = +opt('--width', 432), FPS = +opt('--fps', 8), QUALITY = +opt('--quality', 0.6)
const PORT = 8791, CDP = 9475

const PAGE = `<!doctype html><body style="margin:0"><script>
const load = () => new Promise((ok, no) => { const v = document.createElement('video'); v.muted = true; v.preload = 'auto'; v.src = '/video.mp4'
  v.onloadeddata = async () => {   // MediaRecorder MP4s carry no duration until the end has been seeked to
    if (!isFinite(v.duration) || v.duration < 1) { v.currentTime = 1e9; await new Promise(r => v.ontimeupdate = r); v.ontimeupdate = null; v.currentTime = 0; await new Promise(r => v.onseeked = r) }
    ok(v) }
  v.onerror = () => no(new Error('video failed to load')); document.body.append(v) })
const toB64 = async blob => { const b = new Uint8Array(await blob.arrayBuffer()); let s = ''; for (let i = 0; i < b.length; i += 32768) s += String.fromCharCode(...b.subarray(i, i + 32768)); return btoa(s) }
window.out = null
window.transcode = async (bitrate, width) => {
  const v = await load(), w = width || v.videoWidth, h = Math.round(v.videoHeight * w / v.videoWidth)
  // draw each decoded frame onto a canvas of the target size and record that, so the copy is smaller in pixels too
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d', { alpha: false })
  const type = ['video/mp4;codecs=avc1.640028', 'video/mp4;codecs=avc1.42E01E', 'video/mp4'].find(t => MediaRecorder.isTypeSupported(t))
  const rec = new MediaRecorder(c.captureStream(30), { mimeType: type, videoBitsPerSecond: bitrate }), parts = []
  rec.ondataavailable = e => e.data.size && parts.push(e.data)
  const done = new Promise(r => rec.onstop = r)
  const paint = () => { g.drawImage(v, 0, 0, w, h); if (!v.ended) v.requestVideoFrameCallback(paint) }
  v.currentTime = 0; await new Promise(r => v.onseeked = r); g.drawImage(v, 0, 0, w, h)
  rec.start(1000); v.requestVideoFrameCallback(paint); await v.play()
  await new Promise(r => v.onended = r); await new Promise(r => setTimeout(r, 200)); rec.stop(); await done
  window.out = await toB64(new Blob(parts, { type })); return window.out.length
}
// Animated WebP: RIFF/WEBP with VP8X (animation flag), ANIM, then one ANMF per distinct frame.
window.webp = async (width, fps, quality) => {
  const v = await load(), h = Math.round(v.videoHeight * width / v.videoWidth)
  const c = document.createElement('canvas'); c.width = width; c.height = h; const g = c.getContext('2d', { alpha: false })
  const u24 = n => [n & 255, (n >> 8) & 255, (n >> 16) & 255], u32 = n => [n & 255, (n >> 8) & 255, (n >> 16) & 255, (n >>> 24) & 255]
  const chunk = (tag, data) => { const pad = data.length & 1; return [...tag].map(ch => ch.charCodeAt(0)).concat(u32(data.length), Array.from(data), pad ? [0] : []) }
  const frames = [], step = 1 / fps
  for (let t = 0; t < v.duration - step / 2; t += step) {
    v.currentTime = t; await new Promise(r => v.onseeked = r)
    g.drawImage(v, 0, 0, width, h)
    const bytes = new Uint8Array(await (await new Promise(r => c.toBlob(r, 'image/webp', quality))).arrayBuffer())
    // walk the browser's RIFF/WEBP chunks and keep only the image ones (ALPH, VP8 or VP8L); skip VP8X, ICCP, EXIF
    const parts = []
    for (let o = 12; o + 8 <= bytes.length;) {
      const tag = String.fromCharCode(...bytes.subarray(o, o + 4)), size = bytes[o + 4] | bytes[o + 5] << 8 | bytes[o + 6] << 16 | bytes[o + 7] << 24
      const end = o + 8 + size + (size & 1)
      if (tag === 'ALPH' || tag === 'VP8 ' || tag === 'VP8L') parts.push(bytes.subarray(o, end))
      o = end
    }
    const img = new Uint8Array(parts.reduce((n, x) => n + x.length, 0)); let k = 0; for (const x of parts) { img.set(x, k); k += x.length }
    const last = frames[frames.length - 1]
    if (last && last.img.length === img.length && last.img.every((b, i) => b === img[i])) last.ms += 1000 * step
    else frames.push({ img, ms: 1000 * step })
  }
  let parts = chunk('VP8X', [0x02, 0, 0, 0, ...u24(width - 1), ...u24(h - 1)]).concat(chunk('ANIM', [255, 255, 255, 255, 0, 0]))
  const blobs = [new Uint8Array(parts)]
  for (const f of frames) blobs.push(new Uint8Array(chunk('ANMF', [...u24(0), ...u24(0), ...u24(width - 1), ...u24(h - 1), ...u24(Math.round(f.ms)), 0x02, ...f.img])))
  const total = blobs.reduce((n, b) => n + b.length, 0)
  const head = new Uint8Array([...'RIFF'].map(ch => ch.charCodeAt(0)).concat(u32(total + 4), [...'WEBP'].map(ch => ch.charCodeAt(0))))
  window.out = await toB64(new Blob([head, ...blobs], { type: 'image/webp' })); return { frames: frames.length, width, height: h, duration: v.duration, b64: window.out.length }
}
window.chunk = (i, n) => window.out.slice(i, i + n)
</script>`

const server = createServer((req, res) => {
  if (req.url === '/video.mp4') {   // byte ranges: Chrome needs them to seek in an MP4
    const buf = readFileSync(IN), m = /bytes=(\d*)-(\d*)/.exec(req.headers.range || '')
    if (!m) { res.writeHead(200, { 'content-type': 'video/mp4', 'content-length': buf.length, 'accept-ranges': 'bytes' }); res.end(buf); return }
    const a = m[1] ? +m[1] : buf.length - +m[2], b = m[1] && m[2] ? +m[2] : buf.length - 1
    res.writeHead(206, { 'content-type': 'video/mp4', 'content-length': b - a + 1, 'content-range': `bytes ${a}-${b}/${buf.length}`, 'accept-ranges': 'bytes' }); res.end(buf.subarray(a, b + 1))
  }
  else { res.writeHead(200, { 'content-type': 'text/html' }); res.end(PAGE) }
}).listen(PORT, '127.0.0.1')
const c = await launch({ port: CDP, width: 800, height: 600 })
await c.send('Page.navigate', { url: `http://127.0.0.1:${PORT}/` }); await new Promise(r => setTimeout(r, 800))
const save = async (len, out) => {
  let b64 = ''; for (let i = 0; i < len; i += 1 << 20) b64 += await c.evaluate(`chunk(${i}, ${1 << 20})`)
  writeFileSync(out, Buffer.from(b64, 'base64')); console.log('wrote', out, (statSync(out).size / 1e6).toFixed(2) + ' MB')
}
try {
  if (MP4) await save(await c.evaluate(`transcode(${BITRATE}, ${MP4W})`), resolve(MP4))
  if (WEBP) { const r = await c.evaluate(`webp(${WIDTH}, ${FPS}, ${QUALITY})`); console.log(basename(IN), r.duration.toFixed(1) + ' s', r.frames, 'distinct frames', r.width + 'x' + r.height); await save(r.b64, resolve(WEBP)) }
} finally { c.close(); server.close() }
process.exit(0)
