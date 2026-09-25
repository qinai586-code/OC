// body.js: the anatomy and clothing construction shared by both characters (legs, shoes, torso, shirt, skirt, arms,
// hands, neck, face, eyes, brows, mouth). Character files supply a style S (palette, eye design, legwear, skirt cut)
// and draw their own hair, outerwear and signature parts (tail, horns / star clip) around these calls.
//
// Every function takes F (the frame from makeFrame), S (style), P (the solved pose at this instant). Nothing here
// reads the clock or random(): identical pose → identical drawing, so faces and silhouettes never shimmer.

const lw = (F, k = 1) => Math.max(.7, F.h / 330) * k;   // line weight scales with the character's screen size

// ---------- legs ----------
// Leg polygon from hip joint H, knee K, ankle A (world px): thigh wide at the top, calf bulge on the back side.
function legPts(F, H, K, A, fwd, outSide = 0) {
  const h = F.h, wT = .086 * h, wK = .046 * h, wC = .052 * h, wA = .027 * h;
  const t1 = sub2(K, H), t2 = sub2(A, K), n1 = norm2([-t1[1], t1[0]]), n2 = norm2([-t2[1], t2[0]]);
  const nk = norm2(add2(n1, n2));
  const side = outSide || fwd;   // which way the calf bulges (profile: behind; front: outward)
  const L = [], R = [];
  const put = (p, n, wl, wr) => { L.push(add2(p, mul2(n, wl))); R.push(sub2(p, mul2(n, wr))); };
  put(H, n1, wT * .55, wT * .55);
  put(lerp2(H, K, .4), n1, wT * .43, wT * .43);
  put(lerp2(H, K, .75), n1, wT * .33, wT * .33);
  put(K, nk, wK * .5, wK * .5);
  const c = lerp2(K, A, .3); put(c, n2, wC * (.5 + .12 * side), wC * (.5 - .12 * side));
  put(lerp2(K, A, .75), n2, wA * .62, wA * .62);
  put(A, n2, wA * .5, wA * .5);
  return L.concat(R.reverse());
}
const norm2 = p => { const d = len2(p) || 1; return [p[0] / d, p[1] / d]; };

// sock/stocking: the part of the leg below a line at height topY (px, world) is covered
function legwear(C, topY, col, line, F) {
  clipTo(C, () => {
    X.fillStyle = col; X.fillRect(-1e5, topY, 2e5, 1e5);
  });
  // the band at the top of the sock follows the leg's width
  const xs = C.filter(p => Math.abs(p[1] - topY) < F.h * .03).map(p => p[0]);
  if (xs.length > 1) line2([[Math.min(...xs), topY + F.h * .002], [Math.max(...xs), topY - F.h * .002]], lw(F, .8), line);
}
const line2 = (pts, w, col) => stroke(pts, w, col, { taper: [.1, .1], min: .5, shade: 0 });

// Loafer at ankle A, pointing along facing yaw phi (radians), sized by h.
function shoe(F, A, phi, S, far) {
  const h = F.h, c = Math.cos(phi), s = Math.sin(phi), L = .1 * h, w = .042 * h, top = .045 * h;
  const pts = [];
  // sole outline (an egg: toe forward) and the ankle collar, projected; the hull of both is the shoe
  for (let i = 0; i < 20; i++) {
    const a = i / 20 * TAU, x = Math.cos(a) * w / 2 * (Math.sin(a) > 0 ? 1 : .9), z = Math.sin(a) * L / 2 + L * .18;
    pts.push([A[0] + x * c + z * s, A[1] + top - (-x * s + z * c) * .12]);
  }
  for (let i = 0; i < 12; i++) {
    const a = i / 12 * TAU, x = Math.cos(a) * w * .42, z = Math.sin(a) * w * .42 - L * .08;
    pts.push([A[0] + x * c + z * s, A[1] + top * .1 - (-x * s + z * c) * .12]);
  }
  for (let i = 0; i < 8; i++) {   // the instep: the top of the foot rises from the toe box to the ankle
    const a = i / 8 * TAU, x = Math.cos(a) * w * .38, z = L * .22 + Math.sin(a) * w * .3;
    pts.push([A[0] + x * c + z * s, A[1] + top * .55 - (-x * s + z * c) * .12]);
  }
  const hull = convexHull(pts), col = far ? mixCol(S.shoe, '#000000', .25) : S.shoe;
  cel(hull, { fill: col, line: S.shoeLine, w: lw(F, 1.05), n: 3, inside: () => {
    fillPts(ellipsePts(A[0] - .012 * h, A[1] + top * .05, .03 * h, .012 * h, 16), mixCol(col, '#ffffff', .18), .55);   // shine
  } });
  // vamp strap across the instep
  const k = Math.abs(s);
  line2([[A[0] + (-w * .45 * c + L * .05 * s), A[1] + top * .5], [A[0] + (w * .45 * c + L * .05 * s), A[1] + top * .5]].map((p, i) => [p[0], p[1] - k * h * .004 * i]), lw(F, .7), S.shoeLine);
}
function convexHull(P) {
  const p = P.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]), cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = [];
  for (const q of p) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
  for (let i = p.length - 1; i >= 0; i--) { const q = p[i]; while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
  return lo.slice(0, -1).concat(up.slice(0, -1));
}

// Solve and draw both legs. P.feet = { R: [u, lift], L: [u, lift] } in h units relative to the root (optional).
// Returns the solved joints (so contact can be audited, and costume layers can attach).
function solveLegs(F, P) {
  const phi = P.yawP * TU, c = Math.cos(phi), s = Math.sin(phi), h = F.h, out = {};
  for (const side of [-1, 1]) {   // -1: the character's right leg, +1: left
    const key = side < 0 ? 'R' : 'L';
    const hx = side * PROP.hipJointX, H = F.raw(hx * c, PROP.hipJointY + (P.hipDrop?.[key] || 0));
    const ft = P.feet?.[key] || [side * .052, 0];
    const A = [F.x + h * (ft[0] * c + (ft[2] || 0) * s + (P.dx || 0)), F.gy - h * (PROP.ankleY + ft[1])];
    const fwd = s >= 0 ? 1 : -1;
    // knees bend toward the facing direction; in front view they bow a hair outward (bend +1 puts the knee on the
    // screen-left of the hip→ankle line)
    const K = ik2(H, A, PROP.thigh * h, PROP.shin * h, Math.abs(s) > .15 ? -fwd : -side);
    out[key] = { H, K, A, depth: -hx * s, side, fwd };
  }
  return out;
}
function drawLeg(F, S, leg, key, phi) {
  const prof = Math.abs(Math.sin(phi)), outS = prof > .3 ? leg.fwd : -leg.side * .5;
  const C = spline(legPts(F, leg.H, leg.K, leg.A, leg.fwd, outS), true, 5);
  const far = leg.depth < -1e-3 && Math.abs(Math.sin(phi)) > .2;
  const skin = far ? S.skinSh : S.skin, wear = S.legs[key];
  fillPts(C, skin);
  clipTo(C, () => {   // soft cel shade on the shadow side of the leg
    const sh = legPts(F, add2(leg.H, [F.h * .012, 0]), add2(leg.K, [F.h * .01, 0]), add2(leg.A, [F.h * .006, 0]), leg.fwd, outS);
    fillPts(spline(sh, true, 5).map(p => [p[0] + F.h * .018, p[1]]), S.skinSh, .7);
  });
  if (wear) {
    const topY = F.gy - F.h * wear.top;
    legwear(C, topY, far ? mixCol(wear.col, '#000000', .2) : wear.col, S.lineDark, F);
    if (wear.pattern) clipTo(C, () => wear.pattern(F, leg, topY));
    if (wear.band) wear.band(F, leg, topY);
  }
  outline(C, lw(F), S.skinLine, { shade: .5, seed: key === 'R' ? 11 : 12 });
  if (wear) clipTo(C, () => outline(C, lw(F) * 1.3, S.lineDark, { shade: .4 }));   // darker line where covered
  shoe(F, leg.A, phi, S, far);
}

// ---------- torso / shirt ----------
// Torso silhouette between two heights under the chest (upper) or pelvis (lower) yaw.
function torsoPts(F, y0, y1, phiU, phiL, grow = 0, steps = 10) {
  const L = [], R = [];
  for (let i = 0; i <= steps; i++) {
    const y = lerp(y0, y1, i / steps), s = secAt(TORSO, y), k = clamp(invLerp(PROP.waist + .02, PROP.waist - .04, y));
    const phi = lerp(phiU, phiL, k), [a, b] = secLR(s[1] + grow, s[2] + grow, s[3] + grow, s[4], phi);
    const map = y > PROP.waist - .03 ? F.upper : (p => F.raw(p[0], p[1]));
    L.push(map([a, y])); R.push(map([b, y]));
  }
  return L.concat(R.reverse());
}
// the projected front-centre line of the torso at height y (for collar, tie, buttons)
function torsoFront(F, y, phi, frac = 1) {
  const s = secAt(TORSO, y); const [u] = surf(s[1], s[2] * frac, s[3], s[4], 0, phi);
  return F.upper([u, y]);
}
function torsoAt(F, y, th, phi, grow = 0) {   // a point on the torso surface at azimuth th
  const s = secAt(TORSO, y), [u, d, fc] = surf(s[1] + grow, s[2] + grow, s[3] + grow, s[4], th, phi);
  return { p: F.upper([u, y]), d, fc };
}

// ---------- skirt ----------
// A pleated A-line skirt from the waist (y = S.skirtTop) to the hem (S.skirtHem). sway (px) swings the hem.
function drawSkirt(F, S, P, back) {
  const phi = P.yawP * TU, h = F.h, y0 = S.skirtTop, y1 = S.skirtHem, sw = P.skirtSway || 0;
  const W = y => { const k = invLerp(y0, y1, y); return [lerp(.058, .108 * S.skirtFlare, Math.pow(k, .8)), lerp(.044, .082 * S.skirtFlare, k), lerp(.046, .094 * S.skirtFlare, k)]; };
  const at = (y, th) => { const [a, bf, bb] = W(y), k = invLerp(y0, y1, y); const [u, d, fc] = surf(a, bf, bb, -.004, th, phi); return { p: add2(F.raw(u, y), [sw * k * k, -d * h * .10 * k]), d, fc }; };
  // outline: left/right edges down, then the hem front arc (pleat zigzag) back up
  const edge = (y, side) => { const [a, bf, bb] = W(y), [l, r] = secLR(a, bf, bb, -.004, phi), k = invLerp(y0, y1, y); return add2(F.raw(side < 0 ? l : r, y), [sw * k * k, 0]); };
  const Lp = [], Rp = [];
  for (let i = 0; i <= 4; i++) { const y = lerp(y0, y1, i / 4); Lp.push(edge(y, -1)); Rp.push(edge(y, 1)); }
  // visible hem: azimuths facing the viewer, from the right edge to the left edge
  const th0 = -Math.PI / 2 - phi, hem = [];
  const N = 28;
  for (let i = 0; i <= N; i++) {
    const th = th0 + Math.PI * (1 - i / N), q = at(y1, th);
    const z = (i % 2 ? 1 : -1) * h * .004 * clamp(q.fc * 3);   // pleat points
    hem.push(add2(q.p, [0, z]));
  }
  const shape = Lp.concat(hem.slice(1, -1)).concat(Rp.slice().reverse());
  // what shows below the hem at the back (inner fabric) when seen from slightly above: a darker band
  if (back) return;
  const C = spline([...Lp, ...hem.slice(1, -1).filter((_, i) => i % 1 === 0), ...Rp.reverse()], true, 3);
  fillPts(C, S.skirt);
  clipTo(C, () => {   // pleats: every other pleat in shadow, lines where they fold
    for (let k = -8; k <= 8; k++) {
      const th = k * Math.PI / 9 + .1, a = at(y0, th), b = at(y1, th);
      if (a.fc < .05) continue;
      if (k % 2 === 0) {
        const c2 = at(y1, th + Math.PI / 9), c1 = at(y0, th + Math.PI / 9);
        fillPts([a.p, b.p, c2.p, c1.p], S.skirtSh, .55 * clamp(a.fc * 2));
      }
      stroke([lerp2(a.p, b.p, .25), b.p], lw(F, .55), S.skirtLine, { taper: [.6, .05], min: .1, shade: 0 });
    }
    // shadow under the belt / from the upper body
    fillPts(torsoPts(F, y0 + .01, y0 - .03, P.yawC * TU, phi, .02, 3), S.skirtSh, .5);
  });
  outline(C, lw(F), S.skirtLine, { shade: .5, seed: 31 });
  return C;
}

// ---------- arms and hands ----------
// Arm pose (all angles absolute in screen space, 0 = straight down, + = toward screen-right):
//   { a: upper arm, b: forearm, w: hand angle relative to the forearm, hand: 'relax'|'open'|'pinch'|'hold'|'chin'|'fist'|'point' }
//   or { ik: [x, y] world wrist target, bend: ±1 }
const dirA = a => [Math.sin(a), Math.cos(a)];
function solveArm(F, P, side) {
  const phi = P.yawC * TU, c = Math.cos(phi), s = Math.sin(phi), h = F.h;
  const sx = side * PROP.shoulderX, S = F.upper([sx * c, PROP.shoulderY]), depth = -sx * s;
  const A = P.arms?.[side < 0 ? 'R' : 'L'] || {};
  let E, Wr;
  if (A.ik) { E = ik2(S, A.ik, PROP.upperArm * h, PROP.foreArm * h, A.bend || 1); Wr = A.ik; }
  else {
    const a = (A.a ?? side * .2) + F.lean, b = (A.b ?? side * .07) + F.lean;
    E = add2(S, mul2(dirA(a), PROP.upperArm * h)); Wr = add2(E, mul2(dirA(b), PROP.foreArm * h));
  }
  const fa = Math.atan2(Wr[0] - E[0], Wr[1] - E[1]);   // forearm angle (screen, from down)
  return { S, E, W: Wr, depth, side, fa, handA: fa + (A.w || 0), hand: A.hand || 'relax', mirror: A.mirror ?? (side > 0 ? (s > .3 ? -1 : 1) : (s < -.3 ? 1 : -1)), prop: A.prop };
}
function armPts(F, arm) {
  const h = F.h;
  return tubePts(arm.S, arm.E, .042 * h, .03 * h, .002 * h).concat([]) ;
}
function drawArmSkin(F, S, arm, far) {
  const h = F.h, col = far ? S.skinSh : S.skin;
  const up = spline(tubePts(arm.S, arm.E, .04 * h, .029 * h, .002 * h), true, 3);
  const lo = spline(tubePts(arm.E, arm.W, .03 * h, .021 * h, .003 * h), true, 3);
  for (const C of [up, lo]) { fillPts(C, col); outline(C, lw(F, .9), S.skinLine, { shade: .4 }); }
}
// Hand at wrist W, pointing along angle a (screen, from down), mirror ±1 flips the thumb side.
function drawHand(F, S, W, a, pose, mirror = 1, far = false, col) {
  const h = F.h, L = PROP.hand * h, wd = .036 * h;
  X.save(); X.translate(W[0], W[1]); X.rotate(-a); X.scale(mirror, 1);
  const skin = col || (far ? S.skinSh : S.skin), ln = S.skinLine, w = lw(F, .85);
  // local frame: +y along the hand (wrist → fingertips), x across (thumb at −x)
  const shapes = {
    relax: { palm: [[-wd * .45, 0], [wd * .45, 0], [wd * .52, L * .45], [wd * .32, L * .95], [0, L * 1.02], [-wd * .3, L * .9], [-wd * .5, L * .5]],
             thumb: [[-wd * .42, L * .15], [-wd * .72, L * .42], [-wd * .6, L * .62], [-wd * .38, L * .45]], lines: [[[wd * .05, L * .55], [wd * .1, L * .92]]] },
    open:  { palm: [[-wd * .45, 0], [wd * .45, 0], [wd * .6, L * .5], [wd * .5, L * 1.02], [0, L * 1.1], [-wd * .45, L * .98], [-wd * .55, L * .5]],
             thumb: [[-wd * .45, L * .1], [-wd * .95, L * .38], [-wd * .9, L * .52], [-wd * .45, L * .42]], lines: [[[-wd * .12, L * .62], [-wd * .16, L * 1.02]], [[wd * .16, L * .62], [wd * .2, L * 1.0]]] },
    hold:  { palm: [[-wd * .45, 0], [wd * .45, 0], [wd * .55, L * .42], [wd * .45, L * .72], [0, L * .78], [-wd * .45, L * .7], [-wd * .52, L * .4]],
             thumb: [[-wd * .45, L * .12], [-wd * .7, L * .5], [-wd * .45, L * .78], [-wd * .3, L * .5]], lines: [[[-wd * .3, L * .62], [wd * .4, L * .6]]] },
    pinch: { palm: [[-wd * .45, 0], [wd * .45, 0], [wd * .5, L * .42], [wd * .3, L * .78], [-wd * .05, L * .98], [-wd * .35, L * .75], [-wd * .5, L * .4]],
             thumb: [[-wd * .42, L * .15], [-wd * .62, L * .6], [-wd * .12, L * .98], [-wd * .3, L * .55]], lines: [[[wd * .1, L * .45], [wd * .2, L * .7]]] },
    fist:  { palm: [[-wd * .5, 0], [wd * .5, 0], [wd * .58, L * .45], [wd * .4, L * .66], [-wd * .4, L * .66], [-wd * .58, L * .45]],
             thumb: [[-wd * .5, L * .2], [-wd * .66, L * .45], [-wd * .1, L * .58], [-wd * .3, L * .35]], lines: [[[-wd * .35, L * .5], [wd * .4, L * .5]]] },
    chin:  { palm: [[-wd * .45, 0], [wd * .45, 0], [wd * .6, L * .38], [wd * .5, L * .62], [wd * .05, L * .72], [-wd * .45, L * .62], [-wd * .55, L * .38]],
             thumb: [[-wd * .45, L * .15], [-wd * .7, L * .45], [-wd * .55, L * .62], [-wd * .3, L * .4]], lines: [[[-wd * .35, L * .5], [wd * .45, L * .46]], [[-wd * .3, L * .6], [wd * .4, L * .58]]] },
    point: { palm: [[-wd * .45, 0], [wd * .45, 0], [wd * .55, L * .45], [wd * .38, L * .66], [wd * .1, L * .66], [wd * .08, L * 1.12], [-wd * .12, L * 1.12], [-wd * .2, L * .66], [-wd * .5, L * .5]],
             thumb: [[-wd * .45, L * .15], [-wd * .65, L * .42], [-wd * .3, L * .55], [-wd * .3, L * .35]], lines: [] },
  };
  const sh = shapes[pose] || shapes.relax;
  cel(sh.thumb, { fill: skin, line: ln, w, n: 4, shade: .3 });
  cel(sh.palm, { fill: skin, line: ln, w, n: 4, shade: .3 });
  for (const l of sh.lines) line(l, w * .7, ln, { taper: [.3, .4], min: .1, shade: 0 });
  X.restore();
}

// ---------- neck, face, features ----------
function drawNeck(F, S, P) {
  const h = F.h, top = F.head(0, .82), base = F.upper([0, PROP.neckBase - .01]);
  const C = spline(tubePts(top, base, PROP.neckR * 2 * h, PROP.neckR * 2.3 * h), true, 3);
  fillPts(C, S.skin);
  clipTo(C, () => fillPts(ellipsePts(top[0], top[1] + h * .012, h * .03, h * .018, 16), S.skinSh, .9));   // under-chin shadow
  outline(C, lw(F, .85), S.skinLine, { shade: .3 });
}
// face silhouette (world px), for skin fill and as the clip for features
function facePts(F, phi, v0 = .22) {
  const L = [], R = [];
  for (let i = 0; i <= 16; i++) {
    const v = lerp(v0, 1, i / 16), s = secAt(HEADSEC, v), [a, b] = secLR(s[1], s[2], s[3], s[4], phi);
    L.push(F.head(a, v)); R.push(F.head(b, v));
  }
  return L.concat(R.reverse());
}
// a point on the face surface: u (−.5..5 across the face front, head units), v, depth-of-face k (0..1 of bf)
function faceAt(F, phi, x, v, kz = 1) {
  const s = secAt(HEADSEC, v), a = s[1], z = s[2] * kz * Math.sqrt(Math.max(0, 1 - (x / a) ** 2));
  const c = Math.cos(phi), sn = Math.sin(phi);
  return { p: F.head(x * c + z * sn, v), d: -x * sn + z * c };
}
function drawFace(F, S, P) {
  const phi = P.yawH * TU, h = F.h, hh = PROP.head * h;
  const C = spline(facePts(F, phi), true, 2);
  fillPts(C, S.skin);
  const facing = Math.cos(phi);
  clipTo(C, () => {
    // cel shade on the side turned away from the light (and the jaw underside)
    const sd = Math.sin(phi) >= 0 ? -1 : 1;
    const sh = []; for (let i = 0; i <= 10; i++) { const v = lerp(.3, 1.02, i / 10), s = secAt(HEADSEC, v), [a, b] = secLR(s[1], s[2], s[3], s[4], phi); sh.push(F.head(sd < 0 ? a - .02 : b + .02, v)); }
    for (let i = 10; i >= 0; i--) { const v = lerp(.3, 1.02, i / 10), s = secAt(HEADSEC, v), [a, b] = secLR(s[1], s[2], s[3], s[4], phi), w = .07 + .12 * (1 - Math.abs(facing)); sh.push(F.head(sd < 0 ? a + w : b - w, v)); }
    fillPts(spline(sh, true, 3), S.skinSh, .45);
    // blush
    if ((P.blush ?? S.blush) > .01) for (const sd2 of [-1, 1]) {
      const q = faceAt(F, phi, sd2 * .25, .72, .85); if (q.d < -.05) continue;
      const k = (P.blush ?? S.blush) * clamp(q.d * 3 + .3);
      X.save(); X.globalAlpha = .35 * k; X.fillStyle = S.blushCol; X.beginPath(); X.ellipse(q.p[0], q.p[1], hh * .1 * Math.max(.3, Math.abs(Math.cos(phi + sd2 * .5))), hh * .045, F.lean + F.tilt, 0, TAU); X.fill(); X.restore();
      for (let j = 0; j < 3; j++) { const o = [(j - 1) * hh * .035 * Math.cos(phi + sd2 * .5), 0]; line([add2(q.p, add2(o, [hh * .012, -hh * .02])), add2(q.p, add2(o, [-hh * .012, hh * .02]))], lw(F, .5), hexA(S.blushLine, .6 * k), { taper: [.3, .3], shade: 0 }); }
    }
    drawEyes(F, S, P, phi);
    drawNose(F, S, P, phi);
    drawMouth(F, S, P, phi);
  });
  outline(C, lw(F), S.skinLine, { shade: .5, seed: 41 });
  return C;
}
// eye shape in local eye space (unit box: x −1..1 inner→outer? no: x −1 = screen-left end, y −1 top .. 1 bottom)
function drawEyes(F, S, P, phi) {
  const h = F.h, hh = PROP.head * h, E = S.eye;
  for (const side of [-1, 1]) {
    const x = side * E.sep, th = Math.asin(clamp(x / .4, -1, 1)) * 1.15;
    const fc = Math.cos(th + phi);
    if (fc < .08) continue;
    const q = faceAt(F, phi, x, P.eyeV ?? PROP.eyeV + (P.pitch || 0) * .05, .78);
    const wf = clamp(fc / Math.cos(th), 0, 1.15), ew = E.w * hh * lerp(.35, 1, Math.pow(wf, .8)), eh = E.h * hh;
    const open = clamp(side < 0 ? (P.lidR ?? P.lid ?? E.open) : (P.lidL ?? P.lid ?? E.open)), low = P.lower || 0;
    const outer = side * (Math.sin(phi) * .0 + 1);   // outer corner direction on screen (+1: right)
    eye(F, S, q.p, ew, eh, open, low, outer, P, fc, wf);
  }
}
// One anime eye centred at c. o = outer-corner direction (±1). open 0..1, low 0..1 (lower lid raise / smile)
function eye(F, S, c, ew, eh, open, low, o, P, fc, wf) {
  const E = S.eye, h = F.h, rot = F.lean + F.tilt;
  const T = (x, y) => add2(c, rot2([x * ew * .5 * o, y * eh * .5], rot));   // x: −1 inner … +1 outer; y: −1 top … +1 bottom
  // lid curves: the upper lid slopes down toward the outer corner; heavy lids flatten the arc
  const topY = x => lerp(.95, -1 + E.heavy * .35 + (1 - open) * 1.9, 1) - (1 - x * x) * (.12 - E.heavy * .1) * open + x * E.slope * open;
  const upY = x => { const openY = -1 + E.heavy * .3 - .1 * (1 - x * x) + x * E.slope; const closedY = .55 + .25 * (1 - x * x) * (low > .3 ? -1 : 1); return lerp(closedY, openY, open) + low * .25; };
  const loY = x => lerp(.95 - .15 * (1 - x * x), .5 - .2 * (1 - x * x), low);
  const xs = [-1, -.7, -.35, 0, .35, .7, 1];
  const top = xs.map(x => T(x, upY(x))), bot = xs.map(x => T(x, loY(x))).reverse();
  const white = spline(top.concat(bot), true, 4);
  const openAmt = Math.max(0, loY(0) - upY(0));
  if (openAmt > .08) {
    fillPts(white, E.white);
    clipTo(white, () => {
      // iris: tall ellipse, gaze shifts it; a bit larger than the opening so the lid covers its top
      const gx = clamp(P.gazeX || 0, -1, 1), gy = clamp(P.gazeY || 0, -1, 1);
      const ic = T(clamp(gx * .38 * o, -.5, .5), .08 + gy * .18), irx = ew * .5 * E.iris * Math.max(.45, wf * .9 + .1), iry = eh * .5 * E.iris * 1.12;
      const g = X.createLinearGradient(ic[0], ic[1] - iry, ic[0], ic[1] + iry);
      g.addColorStop(0, E.irisCols[0]); g.addColorStop(.55, E.irisCols[1]); g.addColorStop(1, E.irisCols[2]);
      X.fillStyle = g; X.beginPath(); X.ellipse(ic[0], ic[1], irx, iry, rot, 0, TAU); X.fill();
      X.lineWidth = lw(F, .6); X.strokeStyle = E.ring; X.stroke();
      // pupil and the lid's shadow over the top of the iris
      const pr = (P.pupil ?? 1) * E.pupil;
      X.fillStyle = E.pupilCol; X.beginPath(); X.ellipse(ic[0], ic[1] - iry * .05, irx * .42 * pr, iry * .5 * pr, rot, 0, TAU); X.fill();
      fillPts(spline(top.concat(top.slice().reverse().map(p => add2(p, [0, eh * .22]))), true, 3), E.lidShadow, .35);
      // highlights: a big soft one upper-left (light side), a small one lower-right; they never move with gaze noise
      const hl = add2(ic, rot2([-irx * .38, -iry * .42], rot)), hs = add2(ic, rot2([irx * .35, iry * .38], rot));
      X.fillStyle = 'rgba(255,255,255,.95)'; X.beginPath(); X.ellipse(hl[0], hl[1], irx * .3, iry * .22, rot - .5, 0, TAU); X.fill();
      X.beginPath(); X.ellipse(hs[0], hs[1], irx * .13, iry * .1, rot, 0, TAU); X.fill();
      // a lighter band of colour at the bottom of the iris (anime "reflection")
      X.globalAlpha = .5; X.fillStyle = E.irisCols[3] || E.irisCols[2]; X.beginPath(); X.ellipse(ic[0], ic[1] + iry * .55, irx * .6, iry * .22, rot, 0, TAU); X.fill(); X.globalAlpha = 1;
    });
  }
  // upper lash line: heavy, thicker toward the outer corner, with a small flick
  const lashPts = xs.map(x => T(x * 1.04, upY(x) - .04));
  const flick = [T(1.12, upY(1) - .02 - E.flick * .5), T(1.22 + E.flick * .2, upY(1) - E.flick)];
  stroke(spline(lashPts.concat(flick), false, 6), eh * E.lash * (.55 + .45 * wf), E.lashCol, { taper: [.35, .25], min: .12, shade: 0 });
  // lower lash: short, on the outer half
  if (openAmt > .08) stroke(spline([T(.1, loY(.1) + .03), T(.6, loY(.6) + .02), T(.98, loY(.98) - .04)], false, 5), eh * .05, E.lashCol, { taper: [.6, .3], min: .05, shade: 0 });
  // double-eyelid crease
  if (open > .5) stroke(spline([T(-.3, upY(-.3) - .32), T(.4, upY(.4) - .36), T(.95, upY(.95) - .22)], false, 5), eh * .028, hexA(E.lashCol, .6), { taper: [.5, .5], min: .05, shade: 0 });
}
function drawNose(F, S, P, phi) {
  const q = faceAt(F, phi, 0, .745, 1), h = F.h, hh = PROP.head * h, s = Math.sin(phi);
  const a = add2(q.p, rot2([hh * (-.012 + .02 * s), -hh * .02], F.lean + F.tilt)), b = add2(q.p, rot2([hh * (.004 + .01 * s), hh * .012], F.lean + F.tilt));
  line([a, b], lw(F, .65), S.skinLine, { taper: [.5, .2], min: .1, shade: 0 });
}
function drawMouth(F, S, P, phi) {
  const h = F.h, hh = PROP.head * h, rot = F.lean + F.tilt, open = P.mouthOpen || 0, sm = P.mouthSmile ?? S.mouthRest ?? 0, as = P.mouthAsym || 0;
  const q = faceAt(F, phi, 0, .872, .98), wf = Math.max(.35, Math.cos(phi) * .7 + .3), w = hh * .075 * (P.mouthW || 1) * wf;
  const T = (x, y) => add2(q.p, rot2([x * w + Math.sin(phi) * hh * .02, y * hh], rot));
  const cL = -sm * .018 + as * .012, cR = -sm * .018 - as * .012;   // corner lift (negative y is up)
  if (open < .05) {
    line([T(-1, cL), T(-.3, .004 + sm * .006), T(.3, .004 + sm * .006), T(1, cR)], lw(F, .75), S.mouthLine, { taper: [.35, .35], min: .1, shade: 0 });
  } else {
    const o = open * .06, top = [T(-1, cL), T(-.4, -.004), T(.4, -.004), T(1, cR)], bot = [T(.8, cR + o * .6), T(0, o + sm * .01), T(-.8, cL + o * .6)];
    const C = spline(top.concat(bot), true, 4);
    fillPts(C, S.mouthIn);
    clipTo(C, () => fillPts(ellipsePts(T(0, o * 1.1)[0], T(0, o * 1.1)[1], w * .55, hh * o * .45, 12), S.tongue));
    outline(C, lw(F, .6), S.mouthLine, { shade: 0 });
  }
}
function drawBrows(F, S, P, phi) {
  const h = F.h, hh = PROP.head * h, rot = F.lean + F.tilt;
  for (const side of [-1, 1]) {
    const x = side * S.eye.sep, th = Math.asin(clamp(x / .4, -1, 1)) * 1.15, fc = Math.cos(th + phi); if (fc < .1) continue;
    const wf = clamp(fc / Math.cos(th), 0, 1.1), raise = (P.brow || 0) * .04, tilt = (P.browTilt || 0) * .03;
    const q = faceAt(F, phi, x, .43 - raise, .8), bw = S.eye.w * hh * .5 * lerp(.4, 1, wf);
    const T = (u, v) => add2(q.p, rot2([u * bw * side, v * hh], rot));
    line([T(-.75, tilt), T(0, -.012), T(.8, .012 - tilt * .4)], lw(F, .9), hexA(S.browCol, .8), { taper: [.25, .6], min: .1, shade: 0 });
  }
}
