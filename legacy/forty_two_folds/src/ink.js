// ink.js: the cel layer's drawing primitives (Canvas2D, into X).
// Characters are clean anime line art over flat cel colour: tapered strokes with weight variation (thin on the lit
// top-left, heavier on the shadow side), coloured lines (a dark tone of each part's fill, not flat black), cel shadows
// clipped inside each shape. Line texture is seeded per part and NEVER changes with time: faces and silhouettes are
// stable. The handmade texture of the world comes from the painted plates, the paper and the grain.

// Centripetal Catmull-Rom through the points. closed: wrap around. n: samples per span.
function spline(P, closed = false, n = 8) {
  const m = P.length; if (m < 3) return P.slice();
  const out = [], get = i => closed ? P[(i + m) % m] : P[clamp(i, 0, m - 1)];
  const spans = closed ? m : m - 1;
  for (let i = 0; i < spans; i++) {
    const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
    const d = (a, b) => Math.max(1e-4, Math.pow(Math.hypot(b[0] - a[0], b[1] - a[1]), .5));
    const t0 = 0, t1 = t0 + d(p0, p1), t2 = t1 + d(p1, p2), t3 = t2 + d(p2, p3);
    for (let k = 0; k < n; k++) {
      const t = lerp(t1, t2, k / n), q = [];
      for (let j = 0; j < 2; j++) {
        const A1 = (t1 - t) / (t1 - t0) * p0[j] + (t - t0) / (t1 - t0) * p1[j];
        const A2 = (t2 - t) / (t2 - t1) * p1[j] + (t - t1) / (t2 - t1) * p2[j];
        const A3 = (t3 - t) / (t3 - t2) * p2[j] + (t - t2) / (t3 - t2) * p3[j];
        const B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2;
        const B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3;
        q.push((t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2);
      }
      out.push(q);
    }
  }
  if (!closed) out.push(P[m - 1]);
  return out;
}

function pathOf(pts, closed = true) {
  X.beginPath(); X.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) X.lineTo(pts[i][0], pts[i][1]);
  if (closed) X.closePath();
}
function fillPts(pts, col, alpha = 1) { if (pts.length < 3) return; X.globalAlpha = alpha; X.fillStyle = col; pathOf(pts); X.fill(); X.globalAlpha = 1; }
// clip(pts, fn): draw fn() only inside the shape (cel shadows, highlights, patterns, features inside a face)
function clipTo(pts, fn) { X.save(); pathOf(pts); X.clip(); fn(); X.restore(); }

// normals of a polyline
function normals(C, closed) {
  const n = C.length, N = [];
  for (let i = 0; i < n; i++) {
    const a = C[closed ? (i - 1 + n) % n : Math.max(0, i - 1)], b = C[closed ? (i + 1) % n : Math.min(n - 1, i + 1)];
    const dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy) || 1; N.push([-dy / d, dx / d]);
  }
  return N;
}
const LIGHT = [-.55, -.83];   // light from the upper left, in screen space
// stroke(C, w, col, o): a tapered ink stroke along the (already smooth) polyline C.
//   o.taper = [in, out] fraction of length for the entry/exit taper; o.min = the width at the tips (fraction of w);
//   o.shade = 0..1 weight variation with the light (heavier where the normal faces away from the light);
//   o.seed = a stable per-part seed for a subtle pressure wobble (never time-varying).
function stroke(C, w, col, o = {}) {
  const n = C.length; if (n < 2 || w <= 0) return;
  const [ti, to] = o.taper || [.2, .25], mn = o.min ?? .15, sh = o.shade ?? .5, seed = o.seed ?? 0;
  const L = [0]; for (let i = 1; i < n; i++) L.push(L[i - 1] + Math.hypot(C[i][0] - C[i - 1][0], C[i][1] - C[i - 1][1]));
  const tot = L[n - 1] || 1, N = normals(C, false), A = [], B = [];
  for (let i = 0; i < n; i++) {
    const s = L[i] / tot, tp = Math.min(ti > 0 ? ease(s / ti) : 1, to > 0 ? ease((1 - s) / to) : 1);
    const lit = N[i][0] * LIGHT[0] + N[i][1] * LIGHT[1];
    const ww = w * (mn + (1 - mn) * tp) * (1 + sh * .45 * (-lit)) * (1 + .08 * vnoise(L[i] / (w * 9), seed)) / 2;
    A.push([C[i][0] + N[i][0] * ww, C[i][1] + N[i][1] * ww]); B.push([C[i][0] - N[i][0] * ww, C[i][1] - N[i][1] * ww]);
  }
  X.fillStyle = col; X.beginPath(); X.moveTo(A[0][0], A[0][1]);
  for (let i = 1; i < n; i++) X.lineTo(A[i][0], A[i][1]);
  for (let i = n - 1; i >= 0; i--) X.lineTo(B[i][0], B[i][1]);
  X.closePath(); X.fill();
}
// outline(C, w, col, o): a closed outline (C is an already-smooth closed loop) with weight variation, no taper.
function outline(C, w, col, o = {}) {
  const n = C.length; if (n < 3 || w <= 0) return;
  const sh = o.shade ?? .6, seed = o.seed ?? 0, N = normals(C, true);
  // orientation: make normals point outward
  let area = 0; for (let i = 0; i < n; i++) { const a = C[i], b = C[(i + 1) % n]; area += a[0] * b[1] - b[0] * a[1]; }
  const sgnO = area > 0 ? -1 : 1, A = [], B = [];
  let L = 0;
  for (let i = 0; i < n; i++) {
    if (i) L += Math.hypot(C[i][0] - C[i - 1][0], C[i][1] - C[i - 1][1]);
    const nx = N[i][0] * sgnO, ny = N[i][1] * sgnO, lit = nx * LIGHT[0] + ny * LIGHT[1];
    const ww = w * (1 + sh * .5 * (-lit)) * (1 + .07 * vnoise(L / (w * 9), seed)) / 2;
    A.push([C[i][0] + nx * ww, C[i][1] + ny * ww]); B.push([C[i][0] - nx * ww * .6, C[i][1] - ny * ww * .6]);
  }
  X.fillStyle = col; X.beginPath();
  X.moveTo(A[0][0], A[0][1]); for (let i = 1; i < n; i++) X.lineTo(A[i][0], A[i][1]); X.closePath();
  X.moveTo(B[0][0], B[0][1]); for (let i = 1; i < n; i++) X.lineTo(B[i][0], B[i][1]); X.closePath();
  X.fill('evenodd');
}
// cel(): one filled + outlined shape. pts are control points (smoothed here unless o.raw).
//   o.fill, o.line, o.w (line width), o.shadow: a function drawing shadow shapes inside (clipped), o.closed
function cel(pts, o) {
  const C = o.raw ? pts : spline(pts, true, o.n || 6);
  if (o.fill) fillPts(C, o.fill, o.alpha ?? 1);
  if (o.inside) clipTo(C, o.inside);
  if (o.line && o.w > 0) outline(C, o.w, o.line, o);
  return C;
}
// a tapered open line through control points
function line(pts, w, col, o = {}) { stroke(o.raw ? pts : spline(pts, false, o.n || 8), w, col, o); }

// ---------- small shape builders ----------
function ellipsePts(cx, cy, rx, ry, n = 24, rot = 0) { const p = []; for (let i = 0; i < n; i++) { const a = i / n * TAU; p.push(add2([cx, cy], rot2([Math.cos(a) * rx, Math.sin(a) * ry], rot))); } return p; }
// A limb segment as a tapered capsule-ish outline from a (width wa) to b (width wb), bulge = extra width mid-way.
function tubePts(a, b, wa, wb, bulge = 0, side = 0) {
  const d = sub2(b, a), L = len2(d) || 1, u = mul2(d, 1 / L), nn = [-u[1], u[0]];
  const pts = [];
  const prof = k => lerp(wa, wb, k) / 2 + bulge * Math.sin(Math.PI * k) * (1 + side * (k - .5));
  for (let i = 0; i <= 6; i++) { const k = i / 6, c = add2(a, mul2(d, k)); pts.push(add2(c, mul2(nn, prof(k)))); }
  for (let i = 0; i <= 4; i++) { const g = Math.PI * i / 4; pts.push(add2(b, add2(mul2(nn, Math.cos(g) * wb / 2), mul2(u, Math.sin(g) * wb * .35)))); }
  for (let i = 6; i >= 0; i--) { const k = i / 6, c = add2(a, mul2(d, k)); pts.push(sub2(c, mul2(nn, prof(k)))); }
  for (let i = 0; i <= 4; i++) { const g = Math.PI * i / 4; pts.push(sub2(a, add2(mul2(nn, Math.cos(g) * wa / 2), mul2(u, Math.sin(g) * wa * .35)))); }
  return pts;
}
function hexA(col, a) { const n = parseInt(col.slice(1), 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`; }
function mixCol(a, b, k) {
  const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16), c = i => Math.round(lerp((pa >> i) & 255, (pb >> i) & 255, clamp(k)));
  return '#' + ((1 << 24) + (c(16) << 16) + (c(8) << 8) + c(0)).toString(16).slice(1);
}
// soft radial glow (additive light), used for eye shine, the unfolding sky, the paper's glow
function glow(x, y, r, col, a = 1) {
  const g = X.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, hexA(col, .55 * a)); g.addColorStop(.35, hexA(col, .22 * a)); g.addColorStop(1, hexA(col, 0));
  X.save(); X.globalCompositeOperation = 'lighter'; X.fillStyle = g; X.fillRect(x - r, y - r, 2 * r, 2 * r); X.restore();
}
