// A seeded model of a hand on a mouse. It only plans: every method returns timed steps
// ({ dt, type: 'move' | 'down' | 'up' | 'wheel', x, y, dy }) relative to the start of that segment,
// and keeps the hand's position. The recorder plays the steps through CDP in real time.
//
// - Moves follow a cubic Bezier bowed to one side, with jittered control points.
// - Duration follows Fitts's law: MT = a + b * log2(D / W + 1), with a little per-move variance.
// - Speed follows a minimum-jerk profile, skewed so the peak comes early and the landing is slow.
// - Long moves often overshoot and correct, or land a touch short and creep in.
// - Physiological tremor (8-12 Hz, sub-pixel to ~1 px) rides on top; rests drift and settle.

export function mulberry32(seed) {
  let a = seed >>> 0
  return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296 }
}
export function seedFor(name, base = 1) {
  let h = (2166136261 ^ base) >>> 0
  for (const c of name) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0 }
  return h
}

const HZ = 60, DT = 1000 / HZ
const minJerk = t => t * t * t * (10 - 15 * t + 6 * t * t)

export class Hand {
  constructor(seed, start) {
    this.r = mulberry32(seed)
    this.p = { x: start.x, y: start.y }
    this.clock = 0   // planned ms, only used for tremor phase
    this.ph = Array.from({ length: 6 }, () => this.r() * Math.PI * 2)
    this.fr = [8.3 + this.r(), 9.9 + this.r(), 11.2 + this.r()]
  }
  rand(a, b) { return a + (b - a) * this.r() }
  gauss() { let u = 0; for (let i = 0; i < 6; i++) u += this.r(); return (u - 3) / Math.SQRT1_2 / 1.41 }
  tremor(amp) {
    const t = this.clock / 1000, f = this.fr, p = this.ph
    return { x: amp * (0.5 * Math.sin(2 * Math.PI * f[0] * t + p[0]) + 0.3 * Math.sin(2 * Math.PI * f[1] * t + p[1]) + 0.2 * Math.sin(2 * Math.PI * f[2] * t + p[2])),
             y: amp * (0.5 * Math.sin(2 * Math.PI * f[1] * t + p[3]) + 0.3 * Math.sin(2 * Math.PI * f[2] * t + p[4]) + 0.2 * Math.sin(2 * Math.PI * f[0] * t + p[5])) }
  }

  // One ballistic stroke from the current point to b over ms, bowed by `bend` px (signed).
  stroke(b, ms, bend, skew = 0.86) {
    const a = { ...this.p }, dx = b.x - a.x, dy = b.y - a.y, D = Math.hypot(dx, dy) || 1
    const nx = -dy / D, ny = dx / D
    const c1k = this.rand(0.2, 0.36), c2k = this.rand(0.62, 0.8), b2 = bend * this.rand(0.35, 1.1)
    const c1 = { x: a.x + dx * c1k + nx * bend + this.gauss() * D * 0.015, y: a.y + dy * c1k + ny * bend + this.gauss() * D * 0.015 }
    const c2 = { x: a.x + dx * c2k + nx * b2 + this.gauss() * D * 0.015, y: a.y + dy * c2k + ny * b2 + this.gauss() * D * 0.015 }
    const out = [], n = Math.max(2, Math.round(ms / DT))
    for (let i = 1; i <= n; i++) {
      const u = minJerk(Math.pow(i / n, skew)), v = 1 - u
      const x = v * v * v * a.x + 3 * v * v * u * c1.x + 3 * v * u * u * c2.x + u * u * u * b.x
      const y = v * v * v * a.y + 3 * v * v * u * c1.y + 3 * v * u * u * c2.y + u * u * u * b.y
      this.clock += DT
      const tr = this.tremor(i === n ? 0.25 : 0.45)
      out.push({ dt: i * DT, type: 'move', x: x + tr.x, y: y + tr.y })
    }
    this.p = { x: b.x, y: b.y }
    return out
  }
  fitts(D, W, a = 240, b = 150) { return (a + b * Math.log2(D / Math.max(8, W) + 1)) * this.rand(0.9, 1.12) }

  // Aim at `to` (target width W): primary stroke, maybe overshoot or undershoot, then a corrective stroke.
  moveTo(to, W = 40, opts = {}) {
    const a = { ...this.p }, dx = to.x - a.x, dy = to.y - a.y, D = Math.hypot(dx, dy)
    if (D < 2) return []
    const ux = dx / D, uy = dy / D, nx = -uy, ny = ux
    const side = opts.side ?? (this.r() < 0.5 ? -1 : 1)
    const bend = side * D * this.rand(0.04, 0.14)
    const roll = this.r()
    let end = to
    if (D > 160 && roll < (opts.overshoot ?? 0.4)) {            // overshoot past the target, then come back
      const k = D * this.rand(0.03, 0.065), j = this.rand(-3, 3)
      end = { x: to.x + ux * k + nx * j, y: to.y + uy * k + ny * j }
    } else if (D > 70 && roll < 0.8) {                            // land a little short and creep in
      const k = D * this.rand(0.01, 0.04), j = this.rand(-2.5, 2.5)
      end = { x: to.x - ux * k + nx * j, y: to.y - uy * k + ny * j }
    }
    const primary = this.stroke(end, opts.ms || this.fitts(D, W), bend)
    if (end === to) return primary
    const d2 = Math.hypot(to.x - end.x, to.y - end.y)
    const pause = this.rest(this.rand(40, 110), 0.25)
    const corr = this.stroke(to, Math.max(110, this.fitts(d2, W, 120, 90)), this.rand(-1, 1) * d2 * 0.2, 1)
    return this.concat(primary, pause, corr)
  }

  // Idle hand: slow drift around an anchor with tremor and an occasional small slip; amp in px.
  rest(ms, amp = 1) {
    const out = [], n = Math.max(1, Math.round(ms / DT)), base = { ...this.p }
    let ox = 0, oy = 0, vx = 0, vy = 0, slipAt = this.rand(700, 1800), ax = 0, ay = 0
    for (let i = 1; i <= n; i++) {
      const t = i * DT
      if (amp >= 0.6 && t > slipAt) { ax += this.gauss() * 2.2 * amp; ay += this.gauss() * 1.6 * amp; ax = Math.max(-5 * amp, Math.min(5 * amp, ax)); ay = Math.max(-4 * amp, Math.min(4 * amp, ay)); slipAt = t + this.rand(800, 2000) }
      vx += (ax - ox) * 0.02 + this.gauss() * 0.05 * amp; vy += (ay - oy) * 0.02 + this.gauss() * 0.05 * amp
      vx *= 0.86; vy *= 0.86; ox += vx; oy += vy
      this.clock += DT
      const tr = this.tremor(0.35 * amp)
      out.push({ dt: t, type: 'move', x: base.x + ox + tr.x, y: base.y + oy + tr.y })
    }
    this.p = { x: base.x + ox, y: base.y + oy }
    return out
  }

  // Follow a line of text the way people trace what they read: short glides with small stops.
  read(x0, x1, y) {
    const steps = [this.moveTo({ x: x0, y: y + this.rand(-2, 2) }, 30)]
    let x = x0
    while (x < x1 - 8) {
      const nx = Math.min(x1, x + this.rand(55, 120))
      steps.push(this.stroke({ x: nx, y: y + this.rand(-2.5, 2.5) }, (nx - x) / this.rand(0.17, 0.26), this.rand(-2, 2), 1))
      steps.push(this.rest(this.rand(80, 230), 0.4))
      x = nx
    }
    return this.concat(...steps)
  }

  click(hold) {
    const h = hold ?? this.rand(70, 120), p = this.p
    return [{ dt: 0, type: 'down', x: p.x, y: p.y }, { dt: h, type: 'up', x: p.x, y: p.y }]
  }

  // A two-finger flick on a Mac: a short push of growing deltas, then momentum that decays.
  wheel(total) {
    const out = [], push = [0.15, 0.35, 0.6, 0.85, 1]
    let d = [], v = 0
    for (const k of push) d.push(k)
    v = 1; while (v > 0.03) { v *= this.rand(0.88, 0.93); d.push(v) }
    const sum = d.reduce((a, b) => a + b, 0)
    d.forEach((k, i) => out.push({ dt: (i + 1) * DT, type: 'wheel', x: this.p.x, y: this.p.y, dy: total * k / sum }))
    return out
  }

  // Join step lists end to end in time.
  concat(...lists) {
    const out = []; let t0 = 0
    for (const l of lists.flat(0)) {
      const arr = Array.isArray(l) ? l : [l]
      for (const s of arr) out.push({ ...s, dt: t0 + s.dt })
      if (arr.length) t0 += arr[arr.length - 1].dt
    }
    return out
  }
}
