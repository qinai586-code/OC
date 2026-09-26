// timeline.js: the shot list and standalone loops.
// shots([[t0, fn], ...]) registers shots; fn(t, lt, dur) paints the whole frame and is a pure function of t.
// LOOPS.name = t => {...}; LOOPS.name.len = seconds: model sheets, scale sheets, motion tests (render with --loop=name).
const SHOTS = [];
function shots(list) { SHOTS.push(...list); SHOTS.sort((a, b) => a[0] - b[0]); }
const LOOPS = {};

async function drawWorld(t) {
  if (window.LOOP) return window.LOOP(t);
  if (!SHOTS.length) return;
  let i = 0; while (i + 1 < SHOTS.length && t >= SHOTS[i + 1][0]) i++;
  const t0 = SHOTS[i][0], end = i + 1 < SHOTS.length ? SHOTS[i + 1][0] : DUR;
  await SHOTS[i][1](t, t - t0, end - t0);
  CAM = null;
}

// labels are allowed on reference sheets only (never in the film)
function label(txt, x, y, size = 22, col = '#4A4050', align = 'center') {
  X.save(); X.font = `${size}px sans-serif`; X.fillStyle = col; X.textAlign = align; X.fillText(txt, x, y); X.restore();
}
function floorLine(y, x0 = 40, x1 = SW - 40) { line([[x0, y + 2], [SW / 2, y], [x1, y + 3]], 1.2, 'rgba(90,70,80,.5)', { taper: [.05, .05], min: .6, shade: 0 }); }
function guideLine(y, txt) {
  X.save(); X.setLineDash([6, 8]); X.strokeStyle = 'rgba(120,90,100,.35)'; X.lineWidth = 1; X.beginPath(); X.moveTo(20, y); X.lineTo(SW - 20, y); X.stroke(); X.restore();
  if (txt) label(txt, 24, y - 4, 14, 'rgba(90,70,80,.7)', 'left');
}
