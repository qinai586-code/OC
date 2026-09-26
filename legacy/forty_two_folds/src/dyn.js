// dyn.js: secondary motion. ChatGPT's tail, Claude's hair masses, locks, ribbons and hems are CHAINS: a root that
// moves with the body, and segments that follow their parent with their own stiffness and damping, so they drag,
// overshoot and settle AFTER the body has stopped, with the tip last.
//
// Everything is integrated with simulate() from core.js: a fixed 240 Hz grid anchored to absolute time, re-run over a
// window of history for every frame. There is no state between frames, so any frame renders identically in any order
// and at any fps; and because the grid is absolute, consecutive frames sample the same continuous trajectory.
//
// A chain is solved in angle space (absolute screen angles, 0 = straight down, + = toward screen-right):
//   target_i = lerp(θ_{i-1} + rest_i, down_i, grav_i)     (follow the parent's bend, or hang with gravity)
//   α_i = k_i·(target_i − θ_i) − c_i·(ω_i − ω_{i-1}·couple) + inertia_i·(root acceleration ⟂ segment) + wind
// Stiffness k and damping c fall toward the tip, so the tip responds latest and settles last.

// Build points from a root and absolute angles.
function chainPts(root, ang, lens) {
  const P = [root]; let p = root;
  for (let i = 0; i < ang.length; i++) { p = add2(p, mul2(dirA(ang[i]), lens[i])); P.push(p); }
  return P;
}

// spec: { n, len(i) px, k(i), c(i), inertia(i), grav(i), rest(i, drv) → relative rest bend,
//         down(i, drv) → absolute gravity angle, wind(i, τ, drv) → angular accel }
// driver(τ) → { root: [x, y], a0: root angle (absolute), acc: [ax, ay] root acceleration (px/s²) }
// Returns { pts, ang } at time t.
function solveChain(t, spec, driver, win = 2.6, key) {
  const n = spec.n, lens = Array.from({ length: n }, (_, i) => spec.len(i));
  const init = tau => {
    const d = driver(tau), s = new Float64Array(2 * n); let prev = d.a0;
    for (let i = 0; i < n; i++) { const tg = restTarget(spec, i, prev, d); s[i] = tg; prev = tg; }
    return s;
  };
  const step = (s, tau, dt) => {
    const d = driver(tau); let prevA = d.a0, prevW = d.w0 || 0;
    for (let i = 0; i < n; i++) {
      const tg = restTarget(spec, i, prevA, d), th = s[i], w = s[n + i];
      const u = dirA(th), perp = [u[1], -u[0]];   // turning direction for + angle
      const inert = -(d.acc[0] * perp[0] + d.acc[1] * perp[1]) / Math.max(1, lens[i]) * spec.inertia(i);
      const wind = spec.wind ? spec.wind(i, tau, d, th) : 0;
      const a = spec.k(i) * angDiff(tg, th) - spec.c(i) * (w - prevW * (spec.couple ?? .6)) + inert + wind;
      s[n + i] = w + a * dt; s[i] = th + s[n + i] * dt;
      prevA = s[i]; prevW = s[n + i];
    }
  };
  const s = simulate(t, win, init, step, key);
  const d = driver(t), ang = Array.from(s.slice(0, n));
  return { pts: chainPts(d.root, ang, lens), ang };
}
function restTarget(spec, i, prevA, d) {
  const rel = prevA + spec.rest(i, d), g = spec.grav ? spec.grav(i, d) : 0;
  return g > 0 ? angLerp(rel, spec.down ? spec.down(i, d) : 0, g) : rel;
}
const angDiff = (a, b) => { let x = (a - b) % TAU; if (x > Math.PI) x -= TAU; if (x < -Math.PI) x += TAU; return x; };

// A driver built from a function giving the root point + angle at time τ: acceleration by central differences.
function driverOf(rootFn) {
  const e = 1 / 120;
  return tau => {
    const a = rootFn(tau - e), b = rootFn(tau), c = rootFn(tau + e);
    return { ...b, acc: [(a.root[0] - 2 * b.root[0] + c.root[0]) / (e * e), (a.root[1] - 2 * b.root[1] + c.root[1]) / (e * e)], w0: angDiff(c.a0, a.a0) / (2 * e) };
  };
}

// Wind: a smooth, deterministic gust field (angular push toward screen-left/right), strength in rad/s².
function windAt(tau, x, y, W) {
  if (!W) return 0;
  const g = W.base + W.gust * (.5 + .5 * fbm(tau * W.freq + x * .0007 - y * .0004, W.seed || 3));
  return g;
}
