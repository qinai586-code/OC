// chatgpt.js: ChatGPT, redesigned for animation from reference/chatgpt_dragon_ref.png.
// Kept: teal-glass swept horns, the X clip, ink-black layered hair with a teal sheen and a teal inner layer, jade
// eyes, the oversized black coat worn off the shoulder with teal lining, white shirt + teal ribbon tie, dark pleated
// skirt with a sash, mismatched legwear (right: thigh-high; left: bare thigh with the small diamond mark + knee sock),
// black loafers, and the long scaled tail fading from dark teal to a jade fin-tuft.
// Simplified: fewer tassels (none on the model; props can add them), no chains or charms, hair as six masses.

const GPT = {
  skin: '#FCE9E1', skinSh: '#EDC6BC', skinLine: '#A06A62', blush: .25, blushCol: '#F29A9A', blushLine: '#E07A7A',
  mouthLine: '#8A4A46', mouthIn: '#7A3238', tongue: '#DB8C8C', browCol: '#2A2A33', lineDark: '#141218',
  eye: { sep: .205, w: .23, h: .255, open: 1, heavy: 0, slope: .1, flick: .22, lash: .19, iris: 1.0, pupil: 1,
         irisCols: ['#0D4545', '#1A968A', '#62D3BD', '#B5F3E4'], ring: '#0A3131', pupilCol: '#052423', white: '#FBFAF7', lidShadow: '#A9C4C2', lashCol: '#1C1922' },
  hair: { base: '#2C303A', shade: '#1C1F27', sheen: '#56767E', line: '#0D0F14', inner: '#2E6C69', innerLine: '#123230' },
  horn: { base: '#72B3AC', light: '#C4ECE3', dark: '#3E7B76', line: '#244846' },
  shirt: { base: '#F8F4EF', shade: '#D7D2D6', line: '#7F7984' }, collarTip: .34,
  tie: { base: '#1E5E5B', shade: '#134240', line: '#0B2726' },
  skirt: '#38353E', skirtSh: '#27252C', skirtLine: '#121016', skirtTop: .662, skirtHem: .493, skirtFlare: 1,
  shoe: '#2B272E', shoeLine: '#0F0D11',
  legs: {
    R: { top: .435, col: '#25232A', band: (F, leg, y) => garter(F, leg, y, '#1A181D', '#8EA3A0') },
    L: { top: .238, col: '#25232A', pattern: null },
  },
  tail: { root: '#1F3B42', mid: '#2C6064', belly: '#467E7E', tuft: '#5DB6A4', tuftLight: '#A9E6D5', line: '#0E2427', ridge: '#15292E' },
};
const COAT = {   // worn off the shoulders: the collar rides at the elbows, the body flares to mid-thigh
  y0: .69, y1: .405, a: [.118, .19], bf: [.07, .12], bb: [.08, .15], open: [1.05, 1.3], lapel: .3, pow: .8, lapelTo: 1,
  cols: { out: '#2A2A31', outSh: '#1C1C22', lining: '#2D6D6A', inside: '#1F4847', line: '#0E0E12' },
};
const GPT_SLEEVE = { w: [.064, .092, .15], start: .62, over: .045, puff: 1.12, col: '#2A2A31', colSh: '#1B1B21', lining: '#2D6D6A', line: '#0E0E12' };
const GPT_SHIRT_SLEEVE = { w: [.046, .04, .036], start: 0, over: -.01, puff: 1, col: '#F8F4EF', colSh: '#D7D2D6', lining: '#E9E4E6', line: '#7F7984' };

function garter(F, leg, y, col, metal) {
  const h = F.h, d = norm2(sub2(leg.K, leg.H)), n = [-d[1], d[0]], c = [lerp(leg.H[0], leg.K[0], invLerp(leg.H[1], leg.K[1], y + h * .035)), y + h * .035];
  const w = h * .04, pts = [add2(c, mul2(n, w)), add2(c, mul2(n, -w))];
  stroke(pts, h * .008, col, { taper: [.05, .05], min: .8, shade: 0 });
  X.fillStyle = metal; X.beginPath(); X.ellipse(c[0], c[1], h * .005, h * .005, 0, 0, TAU); X.fill();
}

// ---------- the tail ----------
// Rest shape in character space: down and back from the sacrum, sweeping to her left and curling up at the tip.
const TAIL_N = 14;
function tailRestDirs(k) {
  const x = .12 + .5 * ease(clamp((k - .25) / .6)) + .35 * ease(clamp((k - .75) / .25));
  const y = 1 - .45 * ease(clamp((k - .55) / .35)) - .75 * ease(clamp((k - .85) / .15));
  const z = lerp(-.5, -.2, k);
  return [x, y, z];
}
function tailRest(F, phi) {
  const c = Math.cos(phi), s = Math.sin(phi), ang = [];
  for (let i = 0; i < TAIL_N; i++) { const [x, y, z] = tailRestDirs(i / (TAIL_N - 1)); ang.push(Math.atan2(x * c + z * s, y)); }
  return ang;
}
function tailRoot(F, phi) { return F.raw(-.05 * Math.sin(phi), .565); }
const TAIL_SPEC = h => ({
  n: TAIL_N, len: i => .046 * h * (i > 10 ? .85 : 1),
  k: i => lerp(95, 30, i / (TAIL_N - 1)), c: i => lerp(9, 3.2, i / (TAIL_N - 1)), couple: .55,
  inertia: i => lerp(.35, .9, i / (TAIL_N - 1)),
  rest: (i, d) => i === 0 ? 0 : angDiff(d.rest[i], d.rest[i - 1]),
  grav: i => 0,
  wind: (i, tau, d, th) => d.wind ? d.wind * Math.cos(th) * lerp(.2, 1, i / TAIL_N) : 0,
});
function drawTail(F, S, pts, phi) {
  const T = S.tail, h = F.h, C = spline(pts, false, 6), n = C.length, N = normals(C, false), L = [], R = [], mid = [];
  const width = k => h * (k < .78 ? lerp(.056, .026, Math.pow(k / .78, .9)) : lerp(.026, .012, (k - .78) / .22));
  for (let i = 0; i < n; i++) { const k = i / (n - 1), w = width(k) / 2; L.push(add2(C[i], mul2(N[i], w))); R.push(sub2(C[i], mul2(N[i], w))); }
  const body = L.concat(R.slice().reverse());
  // body: dark teal fading toward the tip, a lighter belly band, dorsal ridge serrations
  const g = X.createLinearGradient(C[0][0], C[0][1], C[n - 1][0], C[n - 1][1]);
  g.addColorStop(0, T.root); g.addColorStop(.7, T.mid); g.addColorStop(1, T.tuft);
  X.fillStyle = g; pathOf(body); X.fill();
  clipTo(body, () => {
    const B = []; for (let i = 0; i < n; i++) { const k = i / (n - 1); B.push(sub2(C[i], mul2(N[i], width(k) * .08))); }
    fillPts(B.concat(R.slice().reverse()), T.belly, .55);
    // scale chevrons along the back
    for (let i = 3; i < n - 6; i += 3) { const k = i / (n - 1), w = width(k), p = C[i], q = add2(p, mul2(N[i], w * .35)), dd = norm2(sub2(C[i + 1], C[i - 1]));
      line([add2(q, mul2(dd, -w * .3)), add2(p, mul2(N[i], w * .05)), add2(q, mul2(dd, w * .3))], lw(F, .45), hexA(T.line, .6), { taper: [.3, .3], shade: 0 }); }
  });
  outline(spline(body, true, 1), lw(F), T.line, { shade: .5, seed: 91 });
  // fin-tuft: four flame locks from the last third, each lagging a little more (curl from the chain's own bend)
  const tip = C[n - 1], bend = angDiff(Math.atan2(C[n - 1][0] - C[n - 4][0], C[n - 1][1] - C[n - 4][1]), Math.atan2(C[n - 6][0] - C[n - 10][0], C[n - 6][1] - C[n - 10][1]));
  const tufts = [[.7, 1.05, .9], [.78, 1.25, -.7], [.86, 1.35, .5], [.93, 1.2, -.4]];
  for (const [k0, len, sd] of tufts) {
    const i0 = Math.round(k0 * (n - 1)), p = C[i0], dd = norm2(sub2(C[Math.min(n - 1, i0 + 3)], C[Math.max(0, i0 - 3)])), nn = N[i0];
    const base = add2(p, mul2(nn, sd * width(k0) * .3)), L2 = h * .07 * len;
    const a = add2(base, add2(mul2(dd, L2 * .45), mul2(nn, sd * L2 * .28 + bend * L2 * .2)));
    const b = add2(base, add2(mul2(dd, L2), mul2(nn, sd * L2 * .15 + bend * L2 * .45)));
    const lock = lockPts([base, a, b], width(k0) * 1.3, 0, .45);
    const gg = X.createLinearGradient(base[0], base[1], b[0], b[1]); gg.addColorStop(0, T.tuft); gg.addColorStop(1, T.tuftLight);
    X.fillStyle = gg; pathOf(spline(lock, true, 2)); X.fill();
    outline(spline(lock, true, 2), lw(F, .7), T.line, { shade: .3 });
  }
}

// ---------- horns ----------
// Crescent horns from the temples: up and out, then curling back and in (reference: teal glass with faint rings).
const HORN_PATH = [[.3, .17, .06], [.43, .02, -.02], [.47, -.11, -.14], [.41, -.2, -.3], [.3, -.22, -.44]];
function drawHorn(F, S, phi, side) {
  const hh = PROP.head * F.h, c = Math.cos(phi), s = Math.sin(phi);
  const P3 = HORN_PATH.map(([x, v, z]) => { x *= side; return F.head(x * c + z * s, v); });
  const C = spline(P3, false, 6), H2 = S.horn;
  const shape = spline(lockPts(P3, hh * .14, hh * .012, .02), true, 2);
  fillPts(shape, H2.base);
  clipTo(shape, () => {
    fillPts(lockPts(P3.map(p => add2(p, [-side * hh * .018, -hh * .012])), hh * .05, 0, .1), H2.light, .8);   // glassy highlight
    fillPts(lockPts(P3.map(p => add2(p, [side * hh * .03, hh * .02])), hh * .06, 0, .1), H2.dark, .45);
    for (let i = 1; i < 5; i++) { const j = Math.round(i / 5 * (C.length - 1)), p = C[j], dd = norm2(sub2(C[Math.min(C.length - 1, j + 1)], C[Math.max(0, j - 1)])), nn = [-dd[1], dd[0]], w = hh * .14 * (1 - i / 5 * .85);
      line([add2(p, mul2(nn, w * .6)), add2(add2(p, mul2(nn, -w * .6)), mul2(dd, hh * .015))], lw(F, .45), hexA(H2.dark, .9), { taper: [.2, .2], shade: 0 }); }
  });
  outline(shape, lw(F, .8), H2.line, { shade: .4 });
  return shape;
}

// ---------- hair: clumps traced from the reference ----------
// Swept fringe parted on her right (screen-left), one strand between the eyes, cheek-framing strands, a flared
// layered bob to the collarbone flicking outward, a teal under-layer at the sides, two flyaway strands on the crown.
const GPT_HAIR = [
  // back layer (behind the head)
  { id: 26, layer: 'back', th: 3.14, v: .35, w: .6, path: [[0, .45], [0, .85], [0, 1.12]], bulge: .1, z: 0 },
  { id: 27, layer: 'back', col: 'inner', th: -1.62, v: .62, w: .24, path: [[-.1, .3], [-.16, .62], [-.12, .9]], z: 1, curl: .3 },
  { id: 28, layer: 'back', col: 'inner', th: 1.62, v: .62, w: .24, path: [[.1, .3], [.16, .62], [.13, .88]], z: 1, curl: -.3 },
  { id: 22, layer: 'back', th: -2.2, v: .45, w: .34, path: [[0, .42], [-.04, .82], [0, 1.1]], z: 2, curl: .3 },
  { id: 25, layer: 'back', th: 2.2, v: .45, w: .34, path: [[0, .42], [.04, .8], [.02, 1.06]], z: 2, curl: -.3 },
  { id: 21, layer: 'back', th: -1.8, v: .42, w: .3, path: [[-.02, .42], [-.07, .8], [-.17, 1.02]], z: 3, curl: .6 },
  { id: 24, layer: 'back', th: 1.8, v: .42, w: .3, path: [[.02, .42], [.08, .78], [.19, .98]], z: 3, curl: -.6 },
  { id: 20, layer: 'back', th: -1.5, v: .36, w: .26, path: [[-.03, .36], [-.09, .66], [-.24, .84]], z: 4, curl: .8 },
  { id: 23, layer: 'back', th: 1.5, v: .36, w: .26, path: [[.03, .36], [.1, .64], [.26, .8]], z: 4, curl: -.8 },
  // side locks (in front, beside the face, down to the collarbone)
  { id: 13, layer: 'front', th: -1.12, v: .42, w: .15, path: [[-.02, .38], [-.06, .7], [-.15, .9]], z: 10, curl: .7 },
  { id: 14, layer: 'front', th: 1.15, v: .42, w: .14, path: [[.02, .36], [.07, .68], [.17, .86]], z: 10, curl: -.7 },
  { id: 11, layer: 'front', th: -1.2, v: .32, w: .18, path: [[.01, .36], [.0, .72], [.05, .98]], z: 11, curl: -.4, bulge: .15 },
  { id: 12, layer: 'front', th: 1.2, v: .32, w: .17, path: [[-.01, .36], [0, .74], [-.04, 1.02]], z: 11, curl: .4, bulge: .15 },
  // cheek-framing strands and the fringe
  { id: 9, layer: 'front', th: -.8, v: .24, w: .07, path: [[-.03, .3], [0, .62], [.05, .82]], z: 12, bulge: .1 },
  { id: 10, layer: 'front', th: .88, v: .28, w: .07, path: [[.02, .3], [-.02, .58], [.02, .76]], z: 12, bulge: .1 },
  { id: 7, layer: 'front', th: -.92, v: .12, w: .2, path: [[-.04, .2], [-.07, .42], [-.03, .64]], z: 13 },
  { id: 8, layer: 'front', th: 1.0, v: .18, w: .19, path: [[.02, .2], [.04, .42], [.01, .64]], z: 13 },
  { id: 6, layer: 'front', th: -.62, v: .05, w: .23, path: [[-.02, .2], [-.03, .36], [.02, .5]], z: 14 },
  { id: 4, layer: 'front', th: .6, v: .1, w: .21, path: [[.08, .16], [.12, .3], [.1, .5]], z: 14, curl: -.3 },
  { id: 3, layer: 'front', th: .22, v: .05, w: .25, path: [[.12, .16], [.2, .3], [.23, .48]], z: 15, curl: -.4 },
  { id: 2, layer: 'front', th: -.12, v: .02, w: .28, path: [[.12, .18], [.25, .33], [.34, .46]], z: 16, curl: -.5 },
  { id: 1, layer: 'front', th: -.42, v: .01, w: .3, path: [[.1, .2], [.23, .38], [.29, .52]], z: 17, curl: -.5 },
  { id: 5, layer: 'front', th: -.3, v: .06, w: .09, path: [[.05, .25], [.09, .46], [.07, .72]], z: 18, bulge: .15 },
  // crown flyaways
  { id: 30, layer: 'front', th: -.25, v: .0, w: .05, path: [[-.05, -.07], [-.13, -.09]], z: 19, puff: .06, shade: 0, sheen: 0, rootK: 0 },
  
];
// ---------- the whole character ----------
function drawChatGPT(x, gy, h, P, D = {}) {
  P = poseDefaults(P); const S = GPT, F = makeFrame(x, gy, h, P);
  const phiC = P.yawC * TU, phiP = P.yawP * TU, phiH = P.yawH * TU, hc = S.hair;
  const legs = solveLegs(F, P), aR = solveArm(F, P, -1), aL = solveArm(F, P, 1);
  const tailPts = D.tail || chainPts(tailRoot(F, phiP), tailRest(F, phiP), Array.from({ length: TAIL_N }, (_, i) => TAIL_SPEC(h).len(i)));
  const tailDepth = -.05 * Math.cos(phiP) + .3 * Math.sin(-phiP) * .2;   // + in front of the body
  const backView = Math.cos(phiH) < 0;
  const arms = [aR, aL].sort((a, b) => a.depth - b.depth);
  const drawArm = (arm, far) => {
    drawSleeve(F, arm, GPT_SHIRT_SLEEVE, far);
    if (arm.hand !== 'hidden') drawHand(F, S, arm.W, arm.handA, arm.hand, arm.mirror, far);
    drawSleeve(F, arm, GPT_SLEEVE, far);
  };

  if (tailDepth <= 0) drawTail(F, S, tailPts, phiP);
  drawGarmentBack(F, P, COAT);
  const hp = { base: hc.base, shade: hc.shade, sheen: hc.sheen, line: hc.line, inner: hc.inner, innerSh: hc.innerLine, innerLine: hc.innerLine, innerSheen: '#5FA7A0' };
  if (!backView) drawClumps(F, phiH, GPT_HAIR, hp, 'back', null, D.hairSway);
  if (arms[0].depth < -.01 && !P.arms?.[arms[0].side < 0 ? 'R' : 'L']?.front) drawArm(arms[0], true);
  const lg = [legs.R, legs.L].sort((a, b) => a.depth - b.depth);
  for (const l of lg) drawLeg(F, S, l, l.side < 0 ? 'R' : 'L', phiP);
  if (tailDepth > 0 && tailDepth < .03) drawTail(F, S, tailPts, phiP);
  drawSkirt(F, S, P);
  // sash belt
  const belt = torsoPts(F, S.skirtTop + .012, S.skirtTop - .008, phiC, phiP, .006, 2);
  cel(belt, { fill: '#1F1D23', line: '#0B0A0D', w: lw(F, .8), n: 2 });
  drawNeck(F, S, P);
  drawShirt(F, S, P);
  gptTie(F, S, P);
  drawGarmentFront(F, P, COAT);
  for (const arm of arms) { const far = arm === arms[0] && arm.depth < -.01; if (far || P.arms?.[arm.side < 0 ? 'R' : 'L']?.front) continue; drawArm(arm, false); }
  // head: back clumps → far horn → dome → face → near horn → front clumps → clip → brows
  const farHorn = Math.sin(phiH) >= 0 ? 1 : -1;   // her left horn is the far one when she faces screen-right
  const dome = domePts(F, phiH, .62, .07, .1);
  let face = null;
  if (!backView) {
    if (Math.abs(Math.sin(phiH)) > .15) drawHorn(F, S, phiH, farHorn);
    const domeC = hairMass(F, dome, hc, { seed: 5 });
    face = drawFace(F, S, P);
    if (Math.abs(Math.sin(phiH)) <= .15) drawHorn(F, S, phiH, farHorn);
    drawHorn(F, S, phiH, -farHorn);
    drawClumps(F, phiH, GPT_HAIR, hp, 'front', dome.concat([]), D.hairSway);
    // X clip on her left side
    const q = projH(F, phiH, scalp(.72, .3, .09)), fc = Math.cos(.72 + phiH);
    if (fc > .15) { const r = PROP.head * h * .085 * Math.max(.5, fc); for (const a of [.75, -.75]) line([add2(q, rot2([-r, 0], a + F.lean + F.tilt)), add2(q, rot2([r, 0], a + F.lean + F.tilt))], PROP.head * h * .032, '#3E9C93', { taper: [.05, .05], min: .8, shade: 0 }); }
    drawBrows(F, S, P, phiH);
  } else {
    drawClumps(F, phiH, GPT_HAIR.filter(c => c.layer === 'front'), hp, 'front', null, D.hairSway);
    drawHorn(F, S, phiH, farHorn); drawHorn(F, S, phiH, -farHorn);
    hairMass(F, dome, hc, { seed: 5 });
    drawClumps(F, phiH, GPT_HAIR.filter(c => c.layer === 'back').map(c => ({ ...c, layer: 'front' })), hp, 'front', null, D.hairSway);
  }
  for (const arm of arms) if (P.arms?.[arm.side < 0 ? 'R' : 'L']?.front) drawArm(arm, false);
  if (tailDepth >= .03) drawTail(F, S, tailPts, phiP);
  return { F, legs, arms: { R: aR, L: aL }, tail: tailPts };
}
function gptTie(F, S, P) {
  const phi = P.yawC * TU, q = torsoAt(F, PROP.neckBase - .018, 0, phi, .012); if (q.fc < -.1) return;
  const h = F.h, c = q.p, t = S.tie, sway = P.tieSway || 0, k = Math.max(.35, q.fc);
  for (const side of [-1, 1]) {   // tails
    const a = add2(c, [side * h * .006 * k, h * .006]), b = add2(c, [side * h * .016 * k + sway * .5, h * .06]), e = add2(c, [side * h * .012 * k + sway, h * .09]);
    cel(lockPts([a, b, e], h * .016, h * .014, 0), { fill: t.base, line: t.line, w: lw(F, .7), n: 2, shade: .2 });
  }
  for (const side of [-1, 1]) {   // loops
    cel([c, add2(c, [side * h * .03 * k, -h * .014]), add2(c, [side * h * .036 * k, h * .006]), add2(c, [side * h * .012 * k, h * .008])], { fill: t.base, line: t.line, w: lw(F, .7), n: 4, shade: .2,
      inside: () => fillPts(ellipsePts(c[0] + side * h * .02 * k, c[1] + h * .002, h * .01 * k, h * .006, 10), t.shade, .8) });
  }
  cel(ellipsePts(c[0], c[1], h * .007 * k, h * .008, 10), { fill: t.shade, line: t.line, w: lw(F, .6), n: 1 });
}

// Pose defaults shared by both characters.
function poseDefaults(P = {}) {
  return { yawH: 0, yawC: 0, yawP: 0, lean: 0, tilt: 0, bob: 0, gazeX: 0, gazeY: 0, ...P,
    yawC: P.yawC ?? P.yawP ?? P.yawH ?? 0, yawP: P.yawP ?? P.yawC ?? P.yawH ?? 0, yawH: P.yawH ?? P.yawC ?? 0 };
}
