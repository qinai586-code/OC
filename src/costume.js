// costume.js: layered clothing built like the body, from cross-sections, so it turns with the body continuously.
//   drawGarmentBack / drawGarmentFront: an open outer layer (ChatGPT's coat, Claude's cardigan). The back pass paints
//   the inside visible through the front opening; the front pass paints the two outer panels with their turned-back
//   lining lapels. drawSleeve: a sleeve around the arm bones with a cuff opening. drawShirt: shirt, collar, tie.

function garmentSec(G, k) { return [lerp(G.a[0], G.a[1], Math.pow(k, G.pow || 1)), lerp(G.bf[0], G.bf[1], k), lerp(G.bb[0], G.bb[1], k), -.004]; }
function garmentY(G, k) { return lerp(G.y0, G.y1, k); }
// world point of the garment surface at (k, th) under yaw phi; hem sway px added toward the bottom
function garmentAt(F, P, G, k, th, phi) {
  const s = garmentSec(G, k), [u, d] = surf(s[0], s[1], s[2], s[3], th, phi), y = garmentY(G, k);
  const sway = (P.coatSway || 0) * k * k, map = y > PROP.waist - .03 ? F.upper : (p => F.raw(p[0], p[1]));
  return add2(map([u, y]), [sway, -d * F.h * .09 * k * k]);
}
function drawGarmentBack(F, P, G) {
  const phi = P.yawC * TU, L = [], R = [];
  for (let i = 0; i <= 8; i++) {
    const k = i / 8, s = garmentSec(G, k), [a, b] = secLR(s[0], s[1], s[2], s[3], phi), y = garmentY(G, k);
    const map = y > PROP.waist - .03 ? F.upper : (p => F.raw(p[0], p[1])), sway = (P.coatSway || 0) * k * k;
    L.push(add2(map([a, y]), [sway, 0])); R.push(add2(map([b, y]), [sway, 0]));
  }
  // hem: the back half of the hem ellipse (seen from above, it sits higher than the front)
  const hem = []; for (let i = 0; i <= 12; i++) { const th = -Math.PI / 2 - phi + Math.PI + Math.PI * i / 12; hem.push(garmentAt(F, P, G, 1, th, phi)); }
  const C = spline(L.concat(hem.reverse().slice(1, -1)).concat(R.reverse()), true, 3);
  fillPts(C, G.cols.inside);
  if (G.cols.insideDeep) clipTo(C, () => {   // the far inside of the back panel, seen through the opening, is darker
    const m = F.raw(0, lerp(G.y0, G.y1, .6)), w = (R[4][0] - L[4][0]) * .28;
    fillPts(ellipsePts(m[0], m[1] + F.h * .06, w, F.h * .2, 20), G.cols.insideDeep, .8);
  });
  outline(C, lw(F), G.cols.line, { shade: .4, seed: 51 });
}
function drawGarmentFront(F, P, G) {
  const phi = P.yawC * TU, h = F.h, out = [];
  for (const side of [-1, 1]) {
    const lim = side * Math.PI / 2 - phi;   // the limb azimuth on this side
    const range = k => {   // visible azimuth interval of this panel at level k
      const o = lerp(G.open[0], G.open[1], Math.pow(k, .8)), vis0 = -Math.PI / 2 - phi, vis1 = Math.PI / 2 - phi;
      let a = side > 0 ? o : -Math.PI, b = side > 0 ? Math.PI : -o;
      a = Math.max(a, vis0); b = Math.min(b, vis1);
      return b - a > .02 ? [a, b, o] : null;
    };
    const Lp = [], Rp = [], lap = [];
    let ok = true;
    for (let i = 0; i <= 8; i++) {
      const k = i / 8, r = range(k); if (!r) { ok = false; break; }
      Lp.push(garmentAt(F, P, G, k, r[0], phi)); Rp.push(garmentAt(F, P, G, k, r[1], phi));
      // lapel strip along the front edge (turned-back lining), only where the front edge itself faces us
      const fe = side * r[2], fc = Math.cos(fe + phi);
      if (fc > .05 && k <= (G.lapelTo ?? 1)) lap.push([garmentAt(F, P, G, k, fe, phi), garmentAt(F, P, G, k, fe + side * G.lapel * lerp(1, .5, k), phi)]);
    }
    if (!ok) continue;
    const r1 = range(1);
    // build: down the left boundary, across the hem (left → right), up the right boundary
    const hemLR = []; for (let i = 1; i < 10; i++) hemLR.push(garmentAt(F, P, G, 1, lerp(r1[0], r1[1], i / 10), phi));
    const S2 = spline(Lp.concat(hemLR).concat(Rp.slice().reverse()), true, 3);
    fillPts(S2, G.cols.out);
    clipTo(S2, () => {
      // cel shade: the panel's half turned from the light, plus a soft fold under the arm
      const shadeSide = side * Math.cos(phi) > 0 ? 1 : -1;
      const sh = []; for (let i = 0; i <= 8; i++) { const k = i / 8, r = range(k); if (!r) continue; const m = lerp(r[0], r[1], shadeSide > 0 ? .55 : .45); sh.push(garmentAt(F, P, G, k, m, phi)); }
      const edge = shadeSide > 0 ? Rp : Lp;
      fillPts(spline(sh.concat(edge.slice().reverse()), true, 3), G.cols.outSh, .7);
      if (G.inside) G.inside(side, k => range(k), phi);
      // lapel lining strip
      if (lap.length > 1) fillPts(spline(lap.map(q => q[0]).concat(lap.map(q => q[1]).reverse()), true, 3), G.cols.lining);
    });
    outline(S2, lw(F), G.cols.line, { shade: .5, seed: 60 + side });
    if (lap.length > 1) line(lap.map(q => q[1]), lw(F, .6), G.cols.line, { taper: [.1, .3], min: .2, shade: 0 });
    out.push({ side, S: S2, range });
  }
  return out;
}
// Sleeve around an arm. SL.w = [top, elbow, cuff] widths (units h); SL.start = how far down the upper arm it starts
// (0..1); SL.over = extension past the wrist (units h).
function drawSleeve(F, arm, SL, far) {
  const h = F.h, S0 = lerp2(arm.S, arm.E, SL.start || 0), ext = add2(arm.W, mul2(norm2(sub2(arm.W, arm.E)), SL.over * h));
  const cl = [S0, lerp2(S0, arm.E, .5), arm.E, lerp2(arm.E, ext, .5), ext], ws = [SL.w[0], (SL.w[0] + SL.w[1]) / 2, SL.w[1], (SL.w[1] + SL.w[2]) / 2 * (SL.puff || 1), SL.w[2]].map(w => w * h);
  const N = normals(cl, false), L = [], R = [];
  cl.forEach((p, i) => { L.push(add2(p, mul2(N[i], ws[i] / 2))); R.push(sub2(p, mul2(N[i], ws[i] / 2))); });
  // cuff: a rounded end; the opening is drawn after
  const d = norm2(sub2(ext, arm.E)), cuffC = add2(ext, mul2(d, h * .004));
  const C = spline(L.concat([add2(cuffC, mul2(N[4], -ws[4] * .1))]).concat(R.reverse()), true, 4);
  const col = far ? SL.colFar || mixCol(SL.col, '#000000', .18) : SL.col;
  fillPts(C, col);
  clipTo(C, () => {
    // shade along the underside of the arm, and a fold at the elbow
    const sd = arm.side * (arm.depth < 0 ? -1 : 1);
    fillPts(spline(cl.map((p, i) => add2(p, mul2(N[i], -ws[i] * .5 * sd))).concat(cl.slice().reverse().map((p, i) => add2(p, mul2(N[4 - i], -ws[4 - i] * .05 * sd)))), true, 3), SL.colSh, .6);
    if (SL.inside) SL.inside(cl, N, ws);
  });
  outline(C, lw(F), SL.line, { shade: .5, seed: 70 + arm.side });
  // elbow fold line
  line([add2(arm.E, mul2(N[2], ws[2] * .3)), add2(arm.E, mul2(add2(N[2], mul2(d, .6)), ws[2] * .05))], lw(F, .55), SL.line, { taper: [.2, .5], min: .1, shade: 0 });
  // cuff opening (lining) as an ellipse across the sleeve end
  const ang = Math.atan2(N[4][1], N[4][0]), ow = ws[4] * .46, oh = ws[4] * .16;
  X.save(); X.translate(cuffC[0], cuffC[1]); X.rotate(ang);
  X.fillStyle = SL.lining; X.beginPath(); X.ellipse(0, 0, ow, oh, 0, 0, TAU); X.fill();
  X.lineWidth = lw(F, .7); X.strokeStyle = SL.line; X.stroke();
  if (SL.rib) { for (let i = -3; i <= 3; i++) { X.beginPath(); X.moveTo(i * ow * .25, -oh * 1.6); X.lineTo(i * ow * .25, -oh * .2); X.lineWidth = lw(F, .4); X.stroke(); } }
  X.restore();
  return { C, cuff: cuffC, cuffDir: d };
}

// Shirt: torso from the neck base to the skirt, collar flaps, buttons. Tie drawn by the character (it differs).
function drawShirt(F, S, P) {
  const phiC = P.yawC * TU, phiP = P.yawP * TU, h = F.h, c = S.shirt;
  const C = spline(torsoPts(F, PROP.neckBase + .006, S.skirtTop - .02, phiC, phiP, .004, 10), true, 3);
  fillPts(C, c.base);
  clipTo(C, () => {
    // shadow under the chest and down the side away from the light
    const sd = Math.sin(phiC) >= 0 ? -1 : 1, pts = [];
    for (let i = 0; i <= 8; i++) { const y = lerp(PROP.neckBase, S.skirtTop - .02, i / 8), q = torsoAt(F, y, sd * 1.25, phiC, .01); pts.push(q.p); }
    for (let i = 8; i >= 0; i--) { const y = lerp(PROP.neckBase, S.skirtTop - .02, i / 8), q = torsoAt(F, y, sd * 2.4, phiC, .01); pts.push(q.p); }
    fillPts(spline(pts, true, 3), c.shade, .6);
    const ub = []; for (let i = 0; i <= 8; i++) { const th = lerp(-1.3, 1.3, i / 8); ub.push(torsoAt(F, PROP.underbust - .005, th, phiC).p); }
    for (let i = 8; i >= 0; i--) { const th = lerp(-1.3, 1.3, i / 8); ub.push(add2(torsoAt(F, PROP.underbust + .012, th, phiC).p, [0, 0])); }
    fillPts(spline(ub, true, 3), c.shade, .45);
    // buttons down the front
    for (let i = 0; i < 3; i++) { const y = .745 - i * .035, q = torsoAt(F, y, 0, phiC, .002); if (q.fc > .15) fillPts(ellipsePts(q.p[0], q.p[1], h * .004 * q.fc, h * .004, 8), c.line, .7); }
  });
  outline(C, lw(F), c.line, { shade: .5, seed: 81 });
  // collar: two pointed flaps from the sides of the neck to the front
  for (const side of [-1, 1]) {
    const a = torsoAt(F, PROP.neckBase + .004, side * 1.25, phiC, .006), b = torsoAt(F, PROP.neckBase - .026, side * S.collarTip, phiC, .008), m = torsoAt(F, PROP.neckBase - .004, side * .1, phiC, .008);
    if (a.fc < -.2 && b.fc < 0) continue;
    const back = torsoAt(F, PROP.neckBase + .012, side * 1.9, phiC, .004);
    cel([back.p, a.p, b.p, m.p, torsoAt(F, PROP.neckBase + .012, side * .4, phiC, .004).p], { fill: c.base, line: c.line, w: lw(F, .85), n: 4, shade: .3 });
  }
}
