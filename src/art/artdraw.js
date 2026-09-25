// artdraw.js: layered cel artwork for the character layer.
//
// A character view is a list of PARTS drawn back to front. Each part is authored as control points in the model's own
// space (reference pixels: ground at y = 1512, centre line x = 500, canonical height h = 1426 px, so 1 head = 216 px),
// smoothed into clean curves, filled with flat cel colour, shaded with authored shadow shapes, and inked with the same
// tapered, light-weighted outline as the head. Parts are separate so a rig can move them (pivot = part.pivot).
//
// Point syntax: [x, y] is a smooth point; [x, y, 1] is a CORNER (the curve breaks there). A part may be mirrored
// across the centre line with mirror: true (then it is drawn twice).

const MODEL = { cx: 500, gy: 1512, h: 1426 };

// smooth a control polygon into a curve, respecting corners
function curvePts(ctrl, closed = true, n = 6) {
  const P = ctrl.map(p => [p[0], p[1]]), cor = ctrl.map(p => !!p[2]);
  if (!cor.some(Boolean)) return spline(P, closed, n);
  let pts = P, cs = cor.slice();
  if (closed) { const i0 = cor.indexOf(true); pts = P.slice(i0).concat(P.slice(0, i0), [P[i0]]); cs = cor.slice(i0).concat(cor.slice(0, i0), [true]); }
  else { cs[0] = true; cs[cs.length - 1] = true; }
  const out = []; let start = 0;
  for (let i = 1; i < pts.length; i++) if (cs[i]) {
    const seg = pts.slice(start, i + 1), s = seg.length >= 3 ? spline(seg, false, n) : seg;
    out.push(...(out.length ? s.slice(1) : s)); start = i;
  }
  if (closed) out.pop();
  return out;
}
const mirX = p => [2 * MODEL.cx - p[0], p[1], p[2]];
const mirPts = pts => pts.map(mirX).reverse();

// draw one part. p: { pts, fill, line, w (line weight ×), shade: [{ pts, col, a }], lines: [{ pts, w, col, closed }],
//   grad: [x0, y0, x1, y1, [[stop, col], ...]], alpha, noLine, lineOnly: [i0, i1] to ink only part of the outline }
function drawPart(p, lwBase) {
  const C = curvePts(p.pts, true, p.n || 6);
  if (p.grad) { const [x0, y0, x1, y1, stops] = p.grad, g = X.createLinearGradient(x0, y0, x1, y1); for (const [s, c] of stops) g.addColorStop(s, c); X.globalAlpha = p.alpha ?? 1; X.fillStyle = g; pathOf(C); X.fill(); X.globalAlpha = 1; }
  else if (p.fill) fillPts(C, p.fill, p.alpha ?? 1);
  if (p.shade || p.inside) clipTo(C, () => {
    for (const s of p.shade || []) fillPts(curvePts(s.pts, true, 5), s.col, s.a ?? 1);
    if (p.inside) p.inside(C);
  });
  if (p.line && !p.noLine) {
    if (p.open) stroke(curvePts(p.open, false, 6), lwBase * (p.w || 1), p.line, { taper: [.08, .08], min: .35, shade: .5 });
    else outline(C, lwBase * (p.w || 1), p.line, { shade: .55, seed: hashS(p.id || '') * 100 });
  }
  for (const l of p.lines || []) {
    const L = curvePts(l.pts, !!l.closed, 6);
    if (l.closed) outline(L, lwBase * (l.w || .5), l.col || p.line, { shade: .3 });
    else stroke(L, lwBase * (l.w || .5), l.col || p.line, { taper: l.taper || [.3, .3], min: l.min ?? .1, shade: 0 });
  }
  return C;
}
// draw a list of parts, expanding mirrored ones
function drawParts(parts, lwBase) {
  for (const p of parts) {
    if (p.skip) continue;
    if (p.fn) { p.fn(lwBase); continue; }
    drawPart(p, lwBase);
    if (p.mirror) drawPart(mirrorPart(p), lwBase);
  }
}
function mirrorPart(p) {
  const q = { ...p, id: (p.id || '') + '_m', pts: mirPts(p.pts), mirror: false };
  if (p.shade) q.shade = p.shade.map(s => ({ ...s, pts: mirPts(s.pts) }));
  if (p.lines) q.lines = p.lines.map(l => ({ ...l, pts: l.closed ? mirPts(l.pts) : l.pts.map(mirX) }));
  if (p.open) q.open = p.open.map(mirX);
  if (p.grad) { const [x0, y0, x1, y1, st] = p.grad; q.grad = [2 * MODEL.cx - x0, y0, 2 * MODEL.cx - x1, y1, st]; }
  return q;
}
// place model space into the world: model (cx, gy) lands on (x, groundY), scaled so the model's h becomes h
function modelBegin(x, groundY, h) { const s = h / MODEL.h; X.save(); X.translate(x, groundY); X.scale(s, s); X.translate(-MODEL.cx, -MODEL.gy); }
function modelEnd() { X.restore(); }

// images (reference overlays for tracing QA)
const IMGS = {};
function loadImg(src) {
  if (!IMGS[src]) IMGS[src] = new Promise(ok => { const im = new Image(); im.onload = () => ok(im); im.onerror = () => ok(null); im.src = src; });
  return IMGS[src];
}
