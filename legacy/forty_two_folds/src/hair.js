// hair.js: hair built from CLUMPS: each clump is one curved, pointed lock (a root on the scalp and a short path),
// drawn as a single filled shape with one outline. Overlapping clumps make a mass with a natural jagged edge, and
// their outlines become the strand lines, which is how anime hair is split into parts for rigging. Clumps live in head
// space (head units, x across, v down from the crown, z toward the viewer), so a head turn carries them around the
// skull continuously. Long clumps can hang from chains (dyn.js); short ones can take a sway offset.
//
// Occlusion: every clump has a depth at its root; clumps behind the head are painted before the skull/face, the rest
// after. A clump that has turned behind the head but still hangs beside it is painted in front with the head's
// silhouette cut out of it, so it tucks behind the cheek instead of popping.

// head-local 3D point on the hair surface at azimuth th (0 = front, + = character's left), v, plus puff (thickness)
function scalp(th, v, puff = .06) {
  const s = secAt(HEADSEC, clamp(v, 0, 1)), a = s[1] + puff, bf = s[2] + puff, bb = s[3] + puff * 1.4;
  const top = v < 0 ? -v : 0;
  return [a * Math.sin(th) * (1 - top), v, s[4] + (Math.cos(th) >= 0 ? bf : bb) * Math.cos(th) * (1 - top)];
}
const projH = (F, phi, p) => { const c = Math.cos(phi), s = Math.sin(phi); return F.head(p[0] * c + p[2] * s, p[1]); };
const depthH = (phi, p) => -p[0] * Math.sin(phi) + p[2] * Math.cos(phi);

// clump: { th, v, puff, path: [[dx, dv, dz], ...] (offsets from the root, head units), w (root width, head units),
//          bulge, tip (width at the tip, 0 = pointed), layer: 'back' | 'front', col: 'base'|'inner'|..., sway: [dx, dv] }
function clumpGeom(F, phi, cl, sw = [0, 0]) {
  const r = scalp(cl.th, cl.v, cl.puff ?? .06), P3 = [r];
  cl.path.forEach(([dx, dv, dz = 0], i) => {
    const k = (i + 1) / cl.path.length, s = cl.swayK ?? 1;
    P3.push([r[0] + dx + sw[0] * k * k * s, r[1] + dv + sw[1] * k * k * s, r[2] + dz]);
  });
  const pts = P3.map(p => projH(F, phi, p));
  return { pts, d: depthH(phi, r), dTip: depthH(phi, P3[P3.length - 1]) };
}
function clumpShape(F, g, cl) {
  const hh = PROP.head * F.h;
  return lockPts(g.pts, (cl.w || .15) * hh, (cl.tip || 0) * hh, cl.bulge ?? .25, cl.curl || 0, cl.rootK ?? .2);
}
// A single lock outline: a pointed ribbon along the polyline C (world pts), width w0 at the root → w1 at the tip.
// curl bends the tip's width to one side (a comma shape).
function lockPts(C, w0, w1 = 0, bulge = .2, curl = 0, rootK = 0) {
  const S = spline(C, false, 6), n = S.length, L = [], R = [], N = normals(S, false);
  for (let i = 0; i < n; i++) {
    const k = i / (n - 1), rt = rootK > 0 ? lerp(.3, 1, ease(k / rootK)) : 1;
    const w = rt * (lerp(w0, w1, Math.pow(k, 1.25)) * (1 + bulge * Math.sin(Math.PI * Math.min(1, k * 1.3)))) / 2;
    const off = curl * w * k * k;
    L.push(add2(S[i], mul2(N[i], w + off))); R.push(sub2(S[i], mul2(N[i], w - off)));
  }
  return L.concat(R.reverse());
}
// paint a list of clumps. pass: 'back' paints clumps behind the head, 'front' the rest. cut = the head silhouette
// (world pts) to carve out of front-layer clumps that have rotated behind it.
function drawClumps(F, phi, list, pal, pass, cut, sway = {}) {
  const items = list.map(cl => ({ cl, g: clumpGeom(F, phi, cl, sway[cl.id] || cl.sw || [0, 0]) }));
  const isBack = it => it.cl.layer === 'back' ? it.g.d < .35 : false;
  const sel = items.filter(it => pass === 'back' ? isBack(it) : !isBack(it)).sort((a, b) => (a.cl.z || 0) - (b.cl.z || 0));
  for (const it of sel) {
    const C = spline(clumpShape(F, it.g, it.cl), true, 2), c = pal[it.cl.col || 'base'] || pal.base, ln = pal[(it.cl.col || 'base') + 'Line'] || pal.line;
    const tuck = pass === 'front' && it.g.d < 0 && cut;
    if (tuck) { X.save(); X.beginPath(); X.rect(-1e5, -1e5, 2e5, 2e5); pathOf(cut); X.clip('evenodd'); }
    fillPts(C, c);
    if (it.cl.shade !== 0) clipTo(C, () => {   // a shade stripe on the side away from the light, near the root
      const S = spline(it.g.pts, false, 4), hh = PROP.head * F.h, N = normals(S, false), w = (it.cl.w || .15) * hh;
      const sh = S.map((p, i) => add2(p, mul2(N[i], w * .18))).concat(S.slice().reverse().map((p, i) => add2(p, mul2(N[S.length - 1 - i], w * .6))));
      fillPts(sh, pal[(it.cl.col || 'base') + 'Sh'] || pal.shade, .55);
      // sheen: a short highlight streak on the lit side of the clump's upper part (the anime "angel ring")
      const sheen = pal[(it.cl.col || 'base') === 'base' ? 'sheen' : (it.cl.col + 'Sheen')];
      if (sheen && it.cl.sheen !== 0 && S.length > 6) {
        const a = Math.floor(S.length * (it.cl.sheenAt ?? .22)), b = Math.floor(S.length * ((it.cl.sheenAt ?? .22) + .26));
        const seg = S.slice(a, b + 1).map((p, i) => add2(p, mul2(N[a + i], -w * .16)));
        if (seg.length > 2) fillPts(lockPts(seg, w * .22, 0, .4), sheen, .75);
      }
    });
    outline(C, lw(F, it.cl.lw || .85), ln, { shade: .5, seed: (it.cl.id || 0) * 7 + 3 });
    if (tuck) X.restore();
  }
}
// The skull/crown mass: a rounded dome down to vBase at the sides, filling behind the fringe clumps.
function domePts(F, phi, vBase = .6, puff = .07, back = .08, squar = 2.4) {
  const q = v => { const s = secAt(HEADSEC, v); return secLR(s[1] + puff, s[2] + puff, s[3] + puff + back, s[4], phi); };
  const [l, r] = q(.42), cx = (l + r) / 2, rx = (r - l) / 2, cv = .42, rv = cv + puff * 1.25, pts = [];
  for (let i = 0; i <= 5; i++) { const v = lerp(vBase, cv, i / 5); pts.push(F.head(q(v)[0], v)); }
  const n = 26; for (let i = 1; i < n; i++) {
    const g = Math.PI - Math.PI * i / n, c = Math.cos(g), s = Math.sin(g);
    pts.push(F.head(cx + Math.sign(c) * Math.pow(Math.abs(c), 2 / squar) * rx, cv - Math.pow(s, 2 / squar) * rv));
  }
  for (let i = 0; i <= 5; i++) { const v = lerp(cv, vBase, i / 5); pts.push(F.head(q(v)[1], v)); }
  return pts;
}
function strands(F, list, col, w = .55) {
  for (const s of list) line(s, lw(F, w), col, { taper: [.5, .1], min: .05, shade: 0 });
}
// A hair mass: one filled shape with its outline and an optional painter for interior shading.
function hairMass(F, pts, col, o = {}) {
  const C = spline(pts, true, o.n || 4);
  fillPts(C, col.base);
  if (o.inside) clipTo(C, () => o.inside(C));
  outline(C, lw(F, o.w || 1), col.line, { shade: .55, seed: o.seed || 7 });
  return C;
}
