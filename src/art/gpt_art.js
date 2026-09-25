// gpt_art.js: ChatGPT as layered cel artwork (the ART MODEL GATE). Model space: reference pixels of
// reference/chatgpt_dragon_ref.png, re-posed to a neutral stance on the centre line x = 500, ground y = 1512,
// h = 1426 (6.6 heads; the approved head is the procedural one from chatgpt.js at the same scale).
// Landmarks (y): crown 86 · chin 300 · shoulder joints 378 · chest 454 · waist/belt 560 · hip joints 768 ·
// skirt hem 792 · knee 1047 · ankle 1392 · ground 1512.

const GA = {
  skin: '#FCE9E1', skinSh: '#EFCCC2', skinLine: '#A36B63',
  shirt: '#F7F3EF', shirtSh: '#DCD6D9', shirtSh2: '#C6BFC6', shirtLine: '#6E6872', trim: '#3F8F89',
  bow: '#20504F', bowSh: '#143A3A', bowLine: '#0A2223',
  coat: '#2C2C33', coatSh: '#1C1C21', coatRim: '#40414B', coatLine: '#0C0C10', lining: '#EAE7E5', liningSh: '#C9C5C7', pipe: '#3F8D87',
  sleeveIn: '#2E6B67', sleeveInSh: '#1F4C49',
  skirt: '#3B3841', skirtSh: '#2A2830', skirtHi: '#4C4954', skirtLine: '#111015', stitch: '#7A7581',
  belt: '#1E1C21', metal: '#C2C6CA', metalSh: '#80858B',
  sock: '#28262D', sockSh: '#1C1A20', sockHi: '#3F3C46', sockLine: '#0E0D10',
  shoe: '#242127', shoeHi: '#6C6774', shoeSole: '#141216', shoeLine: '#09080B',
  tassel: '#4E9C94', tasselSh: '#357570', tasselLine: '#15403C', mark: '#6DB4AB',
  tail: '#28383E', tailSh: '#1B272C', tailBelly: '#3E5B5F', tailLine: '#0D1E22', mane: '#5DB2A3', maneLight: '#AEE6D8', maneLine: '#1C4E48',
};

// ---------- reusable art pieces ----------
// A tassel hanging from (x, y): cord, knot, fringe. len = total length.
function tasselArt(x, y, len, lwb, sway = 0) {
  const cord = [[x, y], [x + sway * .3, y + len * .22]], k = [x + sway * .35, y + len * .26];
  stroke(spline(cord, false, 4), lwb * 1.1, GA.tasselLine, { taper: [.05, .05], min: .8, shade: 0 });
  X.fillStyle = GA.metal; X.beginPath(); X.ellipse(k[0], k[1], len * .045, len * .045, 0, 0, TAU); X.fill();
  const top = [k[0], k[1] + len * .05], w = len * .1;
  const body = [[top[0] - w * .45, top[1], 1], [top[0] + w * .45, top[1], 1], [top[0] + w * .62 + sway * .6, y + len, 1], [top[0] - w * .62 + sway * .6, y + len, 1]];
  drawPart({ id: 'tassel', pts: body, fill: GA.tassel, line: GA.tasselLine, w: .7, shade: [{ pts: [[top[0], top[1]], [top[0] + w * .45, top[1]], [top[0] + w * .62 + sway * .6, y + len], [top[0] + w * .1 + sway * .6, y + len]], col: GA.tasselSh, a: .8 }],
    lines: [0, 1, 2].map(i => ({ pts: [[top[0] + (i - 1) * w * .28, top[1] + len * .12], [top[0] + (i - 1) * w * .36 + sway * .6, y + len * .96]], w: .35, col: GA.tasselLine })) }, lwb);
  drawPart({ id: 'tasselcap', pts: [[top[0] - w * .5, top[1] - len * .02], [top[0] + w * .5, top[1] - len * .02], [top[0] + w * .52, top[1] + len * .06], [top[0] - w * .52, top[1] + len * .06]], fill: GA.tasselSh, line: GA.tasselLine, w: .6 }, lwb);
}

// Dragon tail from a centreline (control points, root → end): a scaled dark body, a translucent jade mane along its
// outer side, and a large flame tuft of curling jade locks. locks: [[pts...], w] authored per view.
function tailArt(center, widths, maneSide, locks, lwb) {
  const C = spline(center, false, 8), n = C.length, N = normals(C, false), L = [], R = [];
  const wAt = k => { const f = k * (widths.length - 1), i = Math.min(widths.length - 2, Math.floor(f)); return lerp(widths[i], widths[i + 1], f - i); };
  for (let i = 0; i < n; i++) { const w = wAt(i / (n - 1)) / 2; L.push(add2(C[i], mul2(N[i], w))); R.push(sub2(C[i], mul2(N[i], w))); }
  // mane: long translucent strands trailing along the outer side (behind the body)
  const side = maneSide;
  for (let j = 0; j < 3; j++) {
    const S = [];
    for (let i = Math.floor(n * (.15 + j * .08)); i < n; i += 3) S.push(add2(C[i], mul2(N[i], side * (wAt(i / (n - 1)) * (.35 + j * .12) + 6 + j * 7))));
    if (S.length > 3) { const lock = lockPts(S, 22 - j * 4, 0, .3, 0, .1); X.globalAlpha = .75; fillPts(spline(lock, true, 2), j % 2 ? GA.mane : mixCol(GA.mane, GA.tail, .35)); X.globalAlpha = 1; outline(spline(lock, true, 2), lwb * .45, GA.maneLine, { shade: .2 }); }
  }
  const body = L.concat(R.slice().reverse());
  const g = X.createLinearGradient(C[0][0], C[0][1], C[n - 1][0], C[n - 1][1]);
  g.addColorStop(0, GA.tail); g.addColorStop(.75, mixCol(GA.tail, GA.mane, .25)); g.addColorStop(1, mixCol(GA.tail, GA.mane, .55));
  X.fillStyle = g; pathOf(body); X.fill();
  clipTo(body, () => {
    // belly band on the inner side, dark back ridge, overlapping scale arcs
    fillPts(C.map((p, i) => add2(p, mul2(N[i], -side * wAt(i / (n - 1)) * .15))).concat((side > 0 ? R : L).slice().reverse()), GA.tailBelly, .5);
    fillPts(C.map((p, i) => add2(p, mul2(N[i], side * wAt(i / (n - 1)) * .25))).concat((side > 0 ? L : R).slice().reverse()), GA.tailSh, .6);
    for (let i = 4; i < n - 4; i += 4) {
      const w = wAt(i / (n - 1)), p = C[i], d = norm2(sub2(C[i + 1], C[i - 1]));
      for (const off of [-.25, .15]) {
        const c = add2(p, mul2(N[i], off * w * side)), a = add2(c, add2(mul2(N[i], -w * .22), mul2(d, -w * .1))), b = add2(c, add2(mul2(N[i], w * .22), mul2(d, -w * .1))), m = add2(c, mul2(d, w * .12));
        stroke(spline([a, m, b], false, 5), lwb * .35, hexA(GA.tailLine, .55), { taper: [.3, .3], shade: 0 });
      }
    }
  });
  outline(spline(body, true, 1), lwb, GA.tailLine, { shade: .5, seed: 93 });
  // flame tuft: outline pass, then fill pass, so the locks merge into one flame with a single outer contour
  const shapes = locks.map(([pts, w, curl]) => ({ S: spline(lockPts(pts, w, 0, .35, curl || 0, .12), true, 2), a: pts[0], b: pts[pts.length - 1] }));
  for (const t of shapes) outline(t.S, lwb * 1.7, GA.maneLine, { shade: .3 });
  for (const t of shapes) { const gg = X.createLinearGradient(t.a[0], t.a[1], t.b[0], t.b[1]); gg.addColorStop(0, mixCol(GA.mane, GA.tail, .2)); gg.addColorStop(.55, GA.mane); gg.addColorStop(1, GA.maneLight); X.fillStyle = gg; pathOf(t.S); X.fill(); }
  for (const [pts] of locks) if (pts.length > 3) stroke(spline(pts.slice(1, -1), false, 5), lwb * .35, hexA(GA.maneLine, .55), { taper: [.4, .6], shade: 0 });
}

// Relaxed anime hand, hand-local: wrist at the origin, fingers along +y, thumb toward −x (mirror flips). len px.
const HAND_ART = {
  relax: { back: [[-13, -2, 1], [13, -2, 1], [16, 18], [17, 38], [14, 56], [9, 70], [2, 77], [-5, 73], [-9, 60], [-12, 38]],
           thumb: [[-11, 10], [-19, 24], [-21, 38], [-16, 47], [-10, 40], [-8, 24]],
           lines: [[[1, 44], [4, 70]], [[8, 42], [11, 62]], [[-4, 46], [-4, 66]]] },
  pinch: { back: [[-13, -2, 1], [13, -2, 1], [17, 18], [18, 36], [12, 52], [4, 62], [-4, 60], [-10, 50], [-13, 32]],
           thumb: [[-11, 8], [-20, 24], [-18, 44], [-6, 62], [-3, 58], [-9, 42], [-8, 22]],
           lines: [[[4, 40], [8, 56]], [[-2, 44], [0, 60]]] },
};
function handArt(W, a, pose, mirror, lwb, len = 78) {
  const H2 = HAND_ART[pose] || HAND_ART.relax, s = len / 78;
  X.save(); X.translate(W[0], W[1]); X.rotate(-a); X.scale(mirror * s, s);
  const lw2 = lwb / s;
  drawPart({ id: 'hand', pts: H2.back, fill: GA.skin, line: GA.skinLine, w: .8, shade: [{ pts: [[4, 10], [16, 18], [17, 38], [14, 56], [9, 70], [8, 50], [9, 26]], col: GA.skinSh, a: .8 }], lines: H2.lines.map(l => ({ pts: l, w: .55 })) }, lw2);
  drawPart({ id: 'thumb', pts: H2.thumb, fill: GA.skin, line: GA.skinLine, w: .8 }, lw2);
  X.restore();
}

// ---------- FRONT VIEW (neutral) ----------
const LEG_L = [[428, 740], [419, 820], [414, 900], [418, 980], [426, 1040], [420, 1100], [413, 1165], [418, 1245], [428, 1322], [433, 1380], [435, 1398, 1], [463, 1398, 1], [464, 1350], [471, 1270], [481, 1190], [484, 1122], [476, 1064], [474, 1034], [482, 972], [494, 900], [502, 830], [506, 760]];
const SHOE_L = [[416, 1392], [407, 1410], [400, 1434], [396, 1460], [394, 1482], [397, 1498], [410, 1508], [440, 1512], [470, 1508], [483, 1498], [486, 1482], [484, 1460], [480, 1434], [473, 1410], [464, 1392]];
function gptFrontParts(P = {}) {
  const parts = [];
  const add = p => parts.push(p);
  // back hair is drawn by the caller before these parts (it is part of the approved head)
  // tail: emerges from behind the coat at her left (screen-right), hangs beside the leg, flame tuft at the ankle
  add({ id: 'tail', fn: lwb => tailArt([[640, 860], [674, 950], [694, 1050], [688, 1150], [664, 1230], [638, 1292]], [74, 68, 60, 50, 40, 32], 1, [
    [[[676, 1172], [706, 1240], [722, 1300], [716, 1350]], 20, .3],
    [[[668, 1200], [690, 1286], [700, 1360], [690, 1418], [676, 1440]], 30, .4],
    [[[652, 1215], [652, 1300], [650, 1372], [666, 1438], [688, 1458]], 34, .5],
    [[[640, 1232], [616, 1300], [598, 1356], [604, 1404], [626, 1436]], 34, -.5],
    [[[636, 1262], [600, 1296], [576, 1326], [578, 1366], [592, 1384]], 22, -.6],
  ], lwb) });
  // coat: the back drape (an A-line from behind the shoulders to mid-thigh), seen below and beside the arms
  add({ id: 'coatBack', pts: [[440, 392], [560, 392], [612, 420], [642, 470], [690, 600], [730, 720], [758, 840], [768, 884, 1], [700, 906], [600, 916], [500, 920], [400, 916], [300, 906], [232, 884, 1], [242, 840], [270, 720], [310, 600], [358, 470], [388, 420]],
    fill: GA.coat, line: GA.coatLine, shade: [{ pts: [[400, 600], [500, 560], [600, 600], [640, 920], [360, 920]], col: GA.coatSh, a: .9 }] });
  // legs
  const legInside = (bare) => C => {
    fillPts(curvePts([[436, 790], [506, 780], [506, 842], [470, 830], [430, 836]], true), GA.skinSh, .9);   // cast shadow under the skirt
    fillPts(curvePts([[490, 850], [506, 850], [496, 1000], [480, 1060], [486, 1000]], true), GA.skinSh, .7);    // inner thigh
    fillPts(curvePts([[470, 1080], [484, 1122], [476, 1260], [466, 1350], [470, 1240]], true), GA.skinSh, .7);  // inner calf
    if (!bare) {
      X.fillStyle = GA.sock; pathOf(curvePts([[400, 876], [440, 866], [470, 872], [512, 892], [520, 1500], [390, 1500]], true)); X.fill();
      fillPts(curvePts([[438, 900], [450, 898], [452, 1020], [447, 1150], [450, 1300], [444, 1380], [440, 1300], [441, 1150], [443, 1020]], true), GA.sockHi, .7);
      fillPts(curvePts([[476, 890], [512, 900], [500, 1060], [482, 1130], [476, 1300], [466, 1398], [490, 1398], [520, 900]], true), GA.sockSh, .9);
      // knee fold
      stroke(spline([[430, 1050], [446, 1058], [462, 1054]], false, 4), 1.6, GA.sockLine, { taper: [.4, .4], shade: 0 });
    }
  };
  add({ id: 'legL', pts: LEG_L, fill: GA.skin, line: GA.skinLine, inside: legInside(false) });
  add({ id: 'legR', pts: mirPts(LEG_L), fill: GA.skin, line: GA.skinLine, inside: C => {
    const m = pts => mirPts(pts);
    fillPts(curvePts(m([[436, 790], [506, 780], [506, 842], [470, 830], [430, 836]]), true), GA.skinSh, .9);
    fillPts(curvePts(m([[490, 850], [506, 850], [496, 1000], [480, 1060], [486, 1000]]), true), GA.skinSh, .7);
    fillPts(curvePts(m([[470, 1080], [484, 1122], [476, 1260], [466, 1350], [470, 1240]]), true), GA.skinSh, .7);
    // knee sock
    X.fillStyle = GA.sock; pathOf(curvePts([[520, 1212], [560, 1204], [594, 1214], [610, 1500], [500, 1500]], true)); X.fill();
    fillPts(curvePts([[548, 1240], [558, 1238], [560, 1330], [553, 1392], [547, 1330]], true), GA.sockHi, .6);
    // the small diamond mark on her left thigh
    for (const [dx, dy] of [[0, -11], [11, 0], [0, 11], [-11, 0]]) fillPts([[586 + dx, 861 + dy], [592 + dx, 867 + dy], [586 + dx, 873 + dy], [580 + dx, 867 + dy]], GA.mark, .9);
  } });
  // sock tops (bands) and the garter on her right thigh
  add({ id: 'sockTopL', pts: [[414, 868, 1], [440, 860], [470, 866], [506, 885, 1], [504, 896, 1], [470, 878], [440, 872], [414, 880, 1]], fill: GA.sockSh, line: GA.sockLine, w: .6 });
  add({ id: 'sockTopR', pts: [[515, 1206, 1], [556, 1198], [589, 1208, 1], [588, 1219, 1], [556, 1210], [516, 1217, 1]], fill: GA.sockSh, line: GA.sockLine, w: .6 });
  add({ id: 'garter', pts: [[416, 832, 1], [460, 826], [504, 836, 1], [504, 850, 1], [460, 840], [416, 846, 1]], fill: GA.belt, line: GA.sockLine, w: .7 });
  add({ id: 'garterStrap', pts: [[457, 786, 1], [466, 786, 1], [466, 830, 1], [457, 830, 1]], fill: GA.belt, line: GA.sockLine, w: .5 });
  add({ id: 'garterTassel', fn: lwb => { X.strokeStyle = GA.metal; X.lineWidth = 3; X.beginPath(); X.ellipse(461, 846, 7, 7, 0, 0, TAU); X.stroke(); tasselArt(461, 852, 70, lwb); } });
  // shoes: glossy platform loafers with a strap and a teal charm
  const shoeInside = mir => C => {
    const m = pts => mir ? mirPts(pts) : pts;
    fillPts(curvePts(m([[380, 1484], [440, 1496], [500, 1484], [500, 1520], [380, 1520]]), true), GA.shoeSole);                 // platform sole
    fillPts(curvePts(m([[424, 1384], [458, 1384], [462, 1398], [440, 1406], [420, 1398]]), true), GA.sock);            // ankle opening
    fillPts(curvePts(m([[404, 1458], [416, 1452], [424, 1474], [414, 1486], [402, 1478]]), true), GA.shoeHi, .5);     // toe gloss
    stroke(spline(m([[417, 1476], [419, 1454], [440, 1444], [461, 1454], [463, 1476]]), false, 5), 1.3, GA.shoeHi, { taper: [.2, .2], shade: 0 });   // moc seam
    fillPts(curvePts(m([[404, 1422, 1], [440, 1414], [476, 1422, 1], [478, 1436, 1], [440, 1428], [402, 1436, 1]]), true), GA.shoeSole);   // saddle strap
  };
  add({ id: 'shoeL', pts: SHOE_L, fill: GA.shoe, line: GA.shoeLine, inside: shoeInside(false), lines: [{ pts: [[395, 1485], [440, 1497], [485, 1485]], w: .5, col: GA.shoeHi }] });
  add({ id: 'shoeR', pts: mirPts(SHOE_L), fill: GA.shoe, line: GA.shoeLine, inside: shoeInside(true), lines: [{ pts: mirPts([[395, 1485], [440, 1497], [485, 1485]]).reverse(), w: .5, col: GA.shoeHi }] });
  add({ id: 'charms', fn: lwb => { for (const x of [440, 560]) { fillPts([[x, 1418], [x + 8, 1426], [x, 1434], [x - 8, 1426]], GA.metal); fillPts([[x, 1421], [x + 5, 1426], [x, 1431], [x - 5, 1426]], GA.tassel); } } });
  // skirt: pleated, with alternating shaded pleats and a stitch line near the hem
  const hem = []; for (let i = 0; i <= 12; i++) { const x = lerp(624, 376, i / 12); hem.push([x + (i % 2 ? 2 : -2), 790 + 6 * Math.sin(Math.PI * i / 12) + (i % 2 ? 5 : 0), 1]); }
  add({ id: 'skirt', pts: [[418, 556], [590, 556], [596, 610], [606, 680], [616, 740], ...hem, [384, 740], [394, 680], [404, 610]], fill: GA.skirt, line: GA.skirtLine, w: 1,
    inside: C => {
      for (let i = 0; i < 12; i++) {
        const xt = lerp(422, 578, (i + .5) / 12), xb = lerp(382, 618, (i + .5) / 12), xt2 = lerp(422, 578, (i + 1) / 12), xb2 = lerp(382, 618, (i + 1) / 12);
        if (i % 2) fillPts([[xt, 560], [xt2, 560], [xb2, 800], [xb, 800]], GA.skirtSh, .75);
        else fillPts([[xt + 2, 600], [xt + 5, 600], [xb + 6, 780], [xb + 2, 780]], GA.skirtHi, .6);
        stroke(spline([[xt2, 590], [lerp(xt2, xb2, .5), 690], [xb2, 800]], false, 4), 1.3, GA.skirtLine, { taper: [.7, .05], min: .1, shade: 0 });
      }
      fillPts(curvePts([[410, 556], [590, 556], [594, 600], [500, 596], [406, 600]], true), GA.skirtSh, .7);   // under-belt shadow
      stroke(spline([[380, 772], [500, 780], [620, 772]], false, 6), 1.2, GA.stitch, { taper: [.1, .1], min: .5, shade: 0 });
    } });
  // belt / sash with a silver ring and a teal tassel
  add({ id: 'belt', pts: [[410, 538, 1], [500, 542], [590, 538, 1], [592, 576, 1], [500, 580], [408, 576, 1]], fill: GA.belt, line: GA.skirtLine, w: .8, lines: [{ pts: [[412, 546], [500, 550], [588, 546]], w: .4, col: '#3A3740' }] });
  add({ id: 'beltRing', fn: lwb => { X.strokeStyle = GA.metalSh; X.lineWidth = 7; X.beginPath(); X.ellipse(466, 558, 13, 13, 0, 0, TAU); X.stroke(); X.strokeStyle = GA.metal; X.lineWidth = 4; X.stroke(); tasselArt(468, 572, 110, lwb); } });
  // neck
  add({ id: 'neck', pts: [[476, 282], [473, 318], [466, 352, 1], [534, 352, 1], [527, 318], [524, 282]], fill: GA.skin, line: GA.skinLine, w: .9,
    shade: [{ pts: [[470, 282], [530, 282], [528, 310], [500, 318], [472, 310]], col: GA.skinSh }, { pts: [[466, 340], [534, 340], [534, 356], [466, 356]], col: GA.skinSh, a: .6 }] });
  // white shoulders and upper sleeves (the coat has slipped off the shoulder caps and hangs from the upper arms)
  add({ id: 'sleeveWhite', pts: [[606, 366], [636, 374], [656, 398], [664, 436], [670, 472, 1], [616, 486, 1], [612, 444], [606, 404]], fill: GA.shirt, line: GA.shirtLine, mirror: true,
    shade: [{ pts: [[612, 420], [630, 430], [640, 476], [618, 484]], col: GA.shirtSh }], lines: [{ pts: [[646, 420], [658, 428]], w: .4 }, { pts: [[650, 448], [664, 452]], w: .4 }] });
  // shirt torso (its sides disappear under the lapels)
  add({ id: 'shirt', pts: [[440, 350], [500, 346], [560, 350], [608, 362], [630, 382], [626, 430], [612, 486], [604, 530], [608, 552, 1], [560, 556], [500, 558], [440, 556], [392, 552, 1], [396, 530], [388, 486], [374, 430], [370, 382], [392, 362]], fill: GA.shirt, line: GA.shirtLine,
    shade: [
      { pts: [[408, 474], [432, 486], [470, 488], [494, 476], [486, 494], [452, 500], [420, 494]], col: GA.shirtSh, a: .9 },         // under the chest, left
      { pts: [[506, 476], [530, 488], [568, 486], [592, 474], [580, 494], [548, 500], [514, 494]], col: GA.shirtSh, a: .9 },        // under the chest, right
      { pts: [[396, 530], [440, 540], [500, 546], [560, 540], [604, 530], [608, 556], [500, 560], [392, 556]], col: GA.shirtSh, a: .8 },   // blousing over the belt
      { pts: [[450, 356], [550, 356], [540, 392], [500, 402], [460, 392]], col: GA.shirtSh, a: .8 },
    ],
    lines: [{ pts: [[500, 396], [501, 470], [500, 548]], w: .45 }, { pts: [[438, 516], [450, 540]], w: .4 }, { pts: [[470, 522], [476, 544]], w: .35 }, { pts: [[562, 516], [550, 540]], w: .4 }, { pts: [[530, 522], [524, 544]], w: .35 }] });
  add({ id: 'buttons', fn: () => { for (const y of [436, 488, 528]) fillPts(ellipsePts(504, y, 4, 4, 10), GA.shirtLine, .8); } });
  // coat front panels: lapel from the collarbone down to a turned-out hem corner that shows the pale lining
  add({ id: 'coatFront', pts: [[584, 384, 1], [604, 392], [628, 410], [650, 432, 1], [690, 560], [716, 700], [742, 860], [750, 904, 1], [700, 910], [668, 918, 1], [652, 800], [638, 690], [622, 580], [606, 480], [592, 420]], fill: GA.coat, line: GA.coatLine, mirror: true,
    shade: [{ pts: [[650, 432], [690, 560], [716, 700], [742, 860], [750, 904], [712, 904], [700, 760], [676, 600], [652, 470]], col: GA.coatSh }, { pts: [[586, 388], [604, 396], [612, 470], [622, 560], [608, 520], [596, 440]], col: GA.coatRim, a: .7 },
      { pts: [[634, 660], [646, 740], [656, 820], [668, 918], [704, 912], [692, 860], [674, 790], [652, 710]], col: GA.lining }, { pts: [[668, 918], [704, 912], [692, 860], [684, 890]], col: GA.liningSh }],
    lines: [{ pts: [[586, 386], [596, 430], [606, 480], [622, 580], [638, 690], [652, 800], [666, 910]], w: .7, col: GA.pipe }, { pts: [[652, 710], [674, 790], [692, 860], [702, 908]], w: .5, col: GA.liningSh }, { pts: [[676, 560], [690, 640], [704, 740]], w: .45, col: GA.coatRim }] });
  add({ id: 'lapelGems', fn: () => { for (const x of [616, 384]) { fillPts([[x, 418], [x + 7, 430], [x, 442], [x - 7, 430]], GA.metal); fillPts([[x, 424], [x + 3, 430], [x, 436], [x - 3, 430]], GA.tassel); } } });
  // collar (pointed, teal-edged) over the lapels
  add({ id: 'collarBack', pts: [[452, 346], [500, 336], [548, 346], [546, 356], [500, 350], [454, 356]], fill: GA.shirt, line: GA.shirtLine, w: .7 });
  add({ id: 'collar', pts: [[500, 356, 1], [472, 342], [446, 348], [438, 360, 1], [462, 396, 1], [490, 374]], fill: GA.shirt, line: GA.shirtLine, w: .85, mirror: true,
    shade: [{ pts: [[500, 356], [490, 374], [462, 396], [470, 380], [486, 364]], col: GA.shirtSh }], lines: [{ pts: [[444, 356], [464, 388]], w: .6, col: GA.trim }] });
  // bow tie: dark teal loops, knot and long tails
  add({ id: 'bowTailL', pts: [[494, 378], [486, 420], [478, 470, 1], [492, 476, 1], [500, 426], [504, 382]], fill: GA.bow, line: GA.bowLine, w: .8, shade: [{ pts: [[494, 378], [486, 420], [478, 470], [484, 470], [494, 420], [500, 380]], col: GA.bowSh }] });
  add({ id: 'bowTailR', pts: [[498, 380], [514, 430], [528, 500, 1], [542, 494, 1], [522, 424], [508, 378]], fill: GA.bow, line: GA.bowLine, w: .8, shade: [{ pts: [[508, 378], [522, 424], [542, 494], [534, 496], [514, 428], [502, 380]], col: GA.bowSh }] });
  add({ id: 'bowLoop', pts: [[497, 369], [474, 354], [454, 358], [452, 378], [476, 384], [497, 377]], fill: GA.bow, line: GA.bowLine, w: .85, mirror: true, shade: [{ pts: [[470, 362], [490, 368], [488, 378], [470, 378]], col: GA.bowSh }] });
  add({ id: 'bowKnot', pts: [[492, 364], [508, 364], [510, 380], [490, 380]], fill: GA.bow, line: GA.bowLine, w: .8 });
  // hands, then the bell sleeves (angled outward from the upper arm) over the wrists
  const CUFF = [[700, 800, 1], [730, 786], [764, 779], [792, 780, 1], [770, 797], [736, 806]];
  add({ id: 'hands', fn: lwb => { handArt([744, 798], -.14, 'relax', 1, lwb); handArt([256, 798], .14, 'relax', -1, lwb); } });
  add({ id: 'sleeveCoat', pts: [[614, 476, 1], [642, 462], [670, 452, 1], [704, 540], [742, 650], [772, 740], [792, 780, 1], [760, 792], [700, 800, 1], [684, 740], [660, 650], [636, 560]], fill: GA.coat, line: GA.coatLine, mirror: true,
    shade: [{ pts: [[614, 476], [642, 462], [670, 452], [676, 470], [646, 480], [618, 494]], col: GA.sleeveIn },
      { pts: [[618, 494], [646, 486], [650, 600], [676, 720], [700, 800], [670, 760], [640, 640]], col: GA.coatSh, a: .85 },
      { pts: [[700, 540], [720, 560], [750, 680], [768, 740], [740, 690]], col: GA.coatRim, a: .5 }],
    lines: [{ pts: [[664, 540], [684, 620], [700, 700]], w: .45, col: GA.coatRim }, { pts: [[712, 600], [736, 690], [752, 752]], w: .45, col: GA.coatRim }, { pts: [[676, 470], [686, 492]], w: .4, col: GA.coatRim }] });
  add({ id: 'cuff', pts: CUFF, fill: GA.sleeveIn, line: GA.coatLine, w: .8, mirror: true, shade: [{ pts: [[700, 800], [730, 786], [764, 779], [792, 780], [750, 790]], col: GA.sleeveInSh }] });
  add({ id: 'wrists', fn: lwb => { for (const [x, m, a] of [[744, 1, -.14], [256, -1, .14]]) { X.save(); pathOf(curvePts(m > 0 ? CUFF : mirPts(CUFF), true)); X.clip(); handArt([x, 798], a, 'relax', m, lwb); X.restore(); } } });
  add({ id: 'cuffRim', pts: [[701, 802, 1], [736, 808], [770, 799], [791, 783, 1], [794, 794], [772, 810], [736, 820], [702, 814, 1]], fill: GA.coat, line: GA.coatLine, w: .8, mirror: true, lines: [{ pts: [[704, 810], [736, 814], [770, 805], [792, 790]], w: .6, col: GA.pipe }] });
  add({ id: 'sleeveTassels', fn: lwb => { tasselArt(736, 612, 96, lwb, 4); tasselArt(264, 612, 96, lwb, -4); } });
  return parts;
}

// Draw the front model view with its feet between (x, groundY), canonical height h (screen px).
function drawGPTFront(x, groundY, h, P = {}) {
  const Fh = makeFrame(MODEL.cx, MODEL.gy, MODEL.h, poseDefaults(P));
  const lwb = lw(Fh);
  modelBegin(x, groundY, h);
  gptHeadBack(Fh, poseDefaults(P));
  drawParts(gptFrontParts(P), lwb);
  gptHeadFront(Fh, poseDefaults(P));
  modelEnd();
}
