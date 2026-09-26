// core.js: constants, time, easing, deterministic noise, the history integrator, the 2D camera, paper and render hooks.
//
// THE MOTION CONTRACT
//   A frame is a pure function of absolute time t. Nothing survives between frames: no counters, no Math.random(),
//   no simulation state carried over. Frames render in parallel and out of order.
//   Secondary motion (tail, hair, cloth, follow-through) is still physically integrated, but each frame re-integrates
//   a short window of history ending at t, on a fixed grid anchored to absolute time (DT = 1/240 s). Two frames that
//   overlap in history therefore compute the SAME trajectory, so the result is continuous, frame-rate independent and
//   reproducible (see simulate()). The window is long enough that the start-up transient has decayed below 1e-3.
//
//   Motion frequency and texture frequency are separate: every character transform is continuous at 60 fps; only
//   background brush textures boil (PROJECT.boil Hz, see plates.js). Characters never boil.

const SW = 1920, SH = 1080;
const FPS = PROJECT.fps || 60, BPM = PROJECT.bpm, BEAT = 60 / BPM, BAR = 4 * BEAT, OFF = PROJECT.offset || 0;
const DUR = PROJECT.duration, TAU = Math.PI * 2, DT = 1 / 240;

// ---------- scalar helpers ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, k) => a + (b - a) * k;
const invLerp = (a, b, x) => (x - a) / (b - a);
const seg = (t, a, b) => clamp((t - a) / (b - a));
const frac = x => x - Math.floor(x);
const sgn = x => (x < 0 ? -1 : 1);
const lerp2 = (p, q, k) => [lerp(p[0], q[0], k), lerp(p[1], q[1], k)];
const add2 = (p, q) => [p[0] + q[0], p[1] + q[1]];
const sub2 = (p, q) => [p[0] - q[0], p[1] - q[1]];
const mul2 = (p, k) => [p[0] * k, p[1] * k];
const len2 = p => Math.hypot(p[0], p[1]);
const rot2 = (p, a) => { const c = Math.cos(a), s = Math.sin(a); return [p[0] * c - p[1] * s, p[0] * s + p[1] * c]; };
const angLerp = (a, b, k) => a + (((b - a + Math.PI) % TAU + TAU) % TAU - Math.PI) * k;

// time of bar b, beat k (both 1-based), in seconds
const bar = (b, beat = 1) => OFF + ((b - 1) * 4 + (beat - 1)) * BEAT;
const bpOf = t => (t - OFF) / BEAT;
const pulse = (t, k = 6) => Math.exp(-frac(bpOf(t)) * k);

// ---------- easing (all map 0..1 → 0..1, clamped) ----------
const ease = x => { x = clamp(x); return x * x * (3 - 2 * x); };                       // smoothstep
const ease5 = x => { x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10); };        // smootherstep (C2)
const eIn = x => Math.pow(clamp(x), 3);
const eOut = x => 1 - Math.pow(1 - clamp(x), 3);
const eInOut = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const eOutQuint = x => 1 - Math.pow(1 - clamp(x), 5);
const eInQuad = x => clamp(x) * clamp(x);
const eSine = x => .5 - .5 * Math.cos(Math.PI * clamp(x));
const backOut = (x, s = 1.7) => { x = clamp(x) - 1; return 1 + (s + 1) * x * x * x + s * x * x; };
const EASE = { lin: x => clamp(x), ease, ease5, in: eIn, out: eOut, inout: eInOut, outq: eOutQuint, sine: eSine, back: backOut };

// Keyframes: kf(t, [[t0, v0], [t1, v1, easing?], ...], defaultEasing). Values may be numbers or arrays.
// The easing on a key shapes the segment ARRIVING at that key.
function kf(t, keys, e = ease5) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t < keys[i][0]) {
      const [a, va] = keys[i - 1], [b, vb, ei] = keys[i], fe = typeof ei === 'string' ? EASE[ei] : ei || e, k = fe((t - a) / (b - a));
      return Array.isArray(va) ? va.map((v, j) => lerp(v, vb[j], k)) : lerp(va, vb, k);
    }
  }
  return keys[keys.length - 1][1];
}

// ---------- deterministic randomness and noise ----------
const hash = i => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const hashS = s => { let h = 2166136261; for (const c of String(s)) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return (h >>> 0) / 4294967296; };
// smooth 1D value noise in -1..1 (C1 continuous), seeded
function vnoise(x, seed = 0) {
  const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
  return lerp(hash(i + seed * 57.13) * 2 - 1, hash(i + 1 + seed * 57.13) * 2 - 1, u);
}
const fbm = (x, seed = 0) => vnoise(x, seed) * .6 + vnoise(x * 2.03 + 11, seed) * .28 + vnoise(x * 4.1 + 23, seed) * .12;

// ---------- the history integrator ----------
// simulate(t, win, init, step, n): integrate a state vector (Float64Array of length n) along the absolute grid
// k·DT from k0 = floor((t - win)/DT) to t. init(τ) returns the starting state at τ = k0·DT; step(s, τ, dt) advances s
// in place from τ to τ + dt. Returns the state at exactly t, linearly interpolated between the two grid states that
// bracket it (both on the same trajectory, so consecutive frames are consistent).
const SIM_MEMO = new Map();
function simulate(t, win, init, step, memoKey) {
  if (memoKey) { const m = SIM_MEMO.get(memoKey); if (m && m.t === t) return m.s; }
  const k0 = Math.floor((t - win) / DT), k1 = Math.floor(t / DT);
  const s = init(k0 * DT);
  for (let k = k0; k < k1; k++) step(s, k * DT, DT);
  const a = Float64Array.from(s); step(s, k1 * DT, DT);
  const w = (t - k1 * DT) / DT, out = new Float64Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = a[i] + (s[i] - a[i]) * w;
  if (memoKey) SIM_MEMO.set(memoKey, { t, s: out });
  return out;
}

// follow(t, x, f, z): a damped second-order follower of the input function x(τ), natural frequency f (Hz) and damping
// ratio z (<1 overshoots and settles, 1 = critical). This is how overlapping action is built: every body level follows
// the same attention signal with its own (f, z), so the eyes arrive first and the hips last, continuously, with no
// discrete delays. Pure function of t.
function follow(t, x, f = 3, z = .7, win) {
  const w = TAU * f, W = win ?? Math.max(1.2, 7 / (z * w));
  const r = simulate(t, W,
    tau => Float64Array.of(x(tau), (x(tau + DT) - x(tau - DT)) / (2 * DT)),
    (s, tau, dt) => { const a = w * w * (x(tau) - s[0]) - 2 * z * w * s[1]; s[1] += a * dt; s[0] += s[1] * dt; });
  return r[0];
}
// followV: the same for an array-valued input (one follower per component, one shared pass over the input)
function followV(t, x, f = 3, z = .7, win) {
  const w = TAU * f, W = win ?? Math.max(1.2, 7 / (z * w)), n = x(t).length;
  const r = simulate(t, W,
    tau => { const a = x(tau), b = x(tau + DT), c = x(tau - DT), s = new Float64Array(2 * n); for (let i = 0; i < n; i++) { s[i] = a[i]; s[n + i] = (b[i] - c[i]) / (2 * DT); } return s; },
    (s, tau, dt) => { const v = x(tau); for (let i = 0; i < n; i++) { const a = w * w * (v[i] - s[i]) - 2 * z * w * s[n + i]; s[n + i] += a * dt; s[i] += s[n + i] * dt; } });
  return Array.from(r.slice(0, n));
}
// Closed-form damped kick (no history needed): 0 before t0, then a decaying oscillation. For impacts and pops.
const spring = (t, t0, k = 6, w = 18) => t < t0 ? 0 : Math.exp(-k * (t - t0)) * Math.sin(w * (t - t0));
// Closed-form underdamped step response 0 → 1 (starts with zero velocity), frequency f Hz, damping z < 1.
function stepResp(tau, f = 2, z = .5) {
  if (tau <= 0) return 0;
  const w = TAU * f, wd = w * Math.sqrt(1 - z * z);
  return 1 - Math.exp(-z * w * tau) * (Math.cos(wd * tau) + z / Math.sqrt(1 - z * z) * Math.sin(wd * tau));
}

// ---------- 2D camera over the output context ----------
// camBegin(cx, cy, zoom, rot): world point (cx, cy) lands at screen centre. Always pair with camEnd().
let CAM = null, LAST_CAM = null, X = null;   // X: the 2D context every drawing function paints into
function camBegin(cx = SW / 2, cy = SH / 2, zoom = 1, rot = 0) {
  X.save(); X.translate(SW / 2, SH / 2); X.rotate(rot); X.scale(zoom, zoom); X.translate(-cx, -cy);
  CAM = LAST_CAM = { cx, cy, zoom, rot };
}
function camEnd() { X.restore(); CAM = null; }
function toScreen(x, y, cam = CAM) {
  if (!cam) return [x, y];
  const c = Math.cos(cam.rot), s = Math.sin(cam.rot), dx = (x - cam.cx) * cam.zoom, dy = (y - cam.cy) * cam.zoom;
  return [SW / 2 + dx * c - dy * s, SH / 2 + dx * s + dy * c];
}

// ---------- paper and grain (static: the paper is the "screen", it does not move with the camera) ----------
function lcg(seed) { let s = seed; return () => (s = (s * 16807) % 2147483647) / 2147483647; }
const PAPER = '#F3EBDC', INK = '#2A2230';
function makePaper() {
  const g = document.createElement('canvas'); g.width = SW; g.height = SH; const c = g.getContext('2d'), rnd = lcg(11);
  c.fillStyle = PAPER; c.fillRect(0, 0, SW, SH);
  for (let i = 0; i < 70; i++) { const x = rnd() * SW, y = rnd() * SH, r = 120 + rnd() * 380, gr = c.createRadialGradient(x, y, 0, x, y, r), a = .045 * rnd(); gr.addColorStop(0, `rgba(160,125,80,${a})`); gr.addColorStop(1, 'rgba(160,125,80,0)'); c.fillStyle = gr; c.fillRect(x - r, y - r, 2 * r, 2 * r); }
  c.lineWidth = 1;
  for (let i = 0; i < 1400; i++) { const x = rnd() * SW, y = rnd() * SH, l = 6 + rnd() * 26, a = rnd() * TAU; c.strokeStyle = `rgba(110,88,60,${.035 + rnd() * .06})`; c.beginPath(); c.moveTo(x, y); c.quadraticCurveTo(x + Math.cos(a + .6) * l * .5, y + Math.sin(a + .6) * l * .5, x + Math.cos(a) * l, y + Math.sin(a) * l); c.stroke(); }
  return g;
}
function makeGrain() {
  const cv = document.createElement('canvas'); cv.width = SW; cv.height = SH; const c = cv.getContext('2d'), rnd = lcg(5);
  const id = c.createImageData(SW, SH), d = id.data;
  for (let i = 0; i < d.length; i += 4) { const v = 255 - (rnd() < .55 ? rnd() * rnd() * 30 : 0); d[i] = v; d[i + 1] = v - 1; d[i + 2] = v - 3; d[i + 3] = 255; }
  c.putImageData(id, 0, 0);
  const g = c.createRadialGradient(SW / 2, SH / 2, SH * .45, SW / 2, SH / 2, SH * 1.05); g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(1, 'rgba(120,95,70,.3)');
  c.fillStyle = g; c.fillRect(0, 0, SW, SH);
  return cv;
}

// ---------- frame ----------
let T = 0, paperC = null, grainC = null, outC = null;
async function frame(t) {
  T = t; SIM_MEMO.clear();
  X.setTransform(1, 0, 0, 1, 0, 0); X.globalAlpha = 1; X.globalCompositeOperation = 'source-over';
  X.drawImage(paperC, 0, 0);
  CAM = LAST_CAM = null;
  await drawWorld(t);
  X.setTransform(1, 0, 0, 1, 0, 0); X.globalAlpha = 1;
  X.globalCompositeOperation = 'multiply'; X.drawImage(grainC, 0, 0); X.globalCompositeOperation = 'source-over';
}
window.renderAt = async (t, type = 'image/png', q = .92) => { await frame(t); return outC.toDataURL(type, q); };
// Contact sheet of several times (see render.mjs): crop = [x, y, w, h] in frame px; at = [x, y, w, h] follows a WORLD
// point through each frame's camera.
window.renderSheet = async (times, cols = 3, w = 640, crop = null, at = null) => {
  if (at) at = at.map(v => typeof v === 'string' ? (0, eval)(v) : v);
  const [, , cw, ch] = at || crop || [0, 0, SW, SH], h = Math.round(w * ch / cw), rows = Math.ceil(times.length / cols), sc = document.createElement('canvas');
  sc.width = cols * w; sc.height = rows * h; const c = sc.getContext('2d'), ms = [];
  for (let i = 0; i < times.length; i++) {
    const t0 = performance.now(); await frame(times[i]); ms.push(Math.round(performance.now() - t0));
    const x = (i % cols) * w, y = Math.floor(i / cols) * h;
    const [cx, cy] = at ? toScreen(at[0], at[1], LAST_CAM).map((v, j) => v - (j ? ch : cw) / 2) : crop || [0, 0];
    c.drawImage(outC, cx, cy, cw, ch, x, y, w, h); c.fillStyle = 'rgba(0,0,0,.65)'; c.fillRect(x, y, 96, 22); c.fillStyle = '#fff'; c.font = '14px sans-serif'; c.fillText(times[i].toFixed(3) + 's', x + 5, y + 16);
  }
  return { url: sc.toDataURL('image/jpeg', .92), ms };
};

async function boot() {
  outC = document.getElementById('out'); X = outC.getContext('2d');
  paperC = makePaper(); grainC = makeGrain();
  if (typeof initPlates === 'function') await initPlates();
  window.ready = true;
  if (!location.search.includes('render')) devUI();
}
function devUI() {
  const s = document.getElementById('scrub'), lab = document.getElementById('tt'); s.max = window.LOOP ? window.LOOP.len : DUR; s.step = 1 / FPS;
  let busy = false, want = null;
  const go = async () => { if (busy) return; busy = true; while (want != null) { const t = want; want = null; const t0 = performance.now(); await frame(t); lab.textContent = `${t.toFixed(3)}s  ·  ${Math.round(performance.now() - t0)} ms/frame`; } busy = false; };
  s.addEventListener('input', () => { want = +s.value; go(); });
  want = +(new URLSearchParams(location.search).get('t') || 0); s.value = want; go();
}
